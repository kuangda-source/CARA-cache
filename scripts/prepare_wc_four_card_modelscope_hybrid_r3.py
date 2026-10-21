#!/usr/bin/env python3
"""CPU-only anonymous transport for four frozen, byte-identical Reason1 shards.

This module is also the bounded HTTP implementation for the Mac relay. Artifact
identity remains the original HF revision/digest; ModelScope is a transport only.
"""
import argparse
import email.utils
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class TransferError(Exception):
    def __init__(self, code, **details):
        super().__init__(code)
        self.code, self.details = code, details


def error_info(error):
    if isinstance(error, TransferError):
        return dict(code=error.code, **error.details)
    if isinstance(error, urllib.error.HTTPError):
        return dict(code="HTTP_ERROR", http_status=error.code)
    if isinstance(error, urllib.error.URLError):
        return dict(code="URL_TRANSPORT_ERROR", reason_type=type(error.reason).__name__)
    if isinstance(error, (TimeoutError, socket.timeout)):
        return dict(code="SOCKET_TIMEOUT")
    return dict(code="LOCAL_OR_TRANSPORT_ERROR", error_type=type(error).__name__)


def sha(path, git_blob=False):
    path = Path(path)
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(("blob %d\0" % path.stat().st_size).encode())
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


class ScopedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = urllib.parse.urlparse(newurl)
        if new.scheme != "https":
            raise TransferError("NON_HTTPS_REDIRECT")
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new.hostname != urllib.parse.urlparse(req.full_url).hostname:
            result.remove_header("Authorization")
        return result


def request_for(asset, start, end, transport, token=None):
    headers = {"Accept-Encoding": "identity", "User-Agent": "cara-fixed-assets-r3"}
    if transport == "modelscope":
        if token is not None or asset["repo_id"] != "nvidia/Cosmos-Reason1-7B":
            raise TransferError("MIRROR_CREDENTIAL_OR_SCOPE_REJECTED")
        if asset["git_blob"] or asset["path"] not in ["model-%05d-of-00004.safetensors" % i for i in range(1, 5)]:
            raise TransferError("MIRROR_ARTIFACT_SCOPE_REJECTED")
        url = "https://modelscope.cn/api/v1/models/unsloth/Cosmos-Reason1-7B/repo?" + urllib.parse.urlencode(
            {"Revision": "master", "FilePath": asset["path"], "wc_nonce": str(time.time_ns())})
    elif transport == "official_hf":
        if not token or asset["repo_id"] not in {"nvidia/Cosmos-Guardrail1", "nvidia/Cosmos-Reason1-7B", "nvidia/Cosmos-Predict2.5-2B"}:
            raise TransferError("OFFICIAL_HF_SCOPE_REJECTED")
        url = "https://huggingface.co/" + asset["repo_id"] + "/resolve/" + asset["source_revision"] + "/" + urllib.parse.quote(asset["path"], safe="/")
        url += "?download=true&wc_range_start=%d&wc_nonce=%d" % (start, time.time_ns())
        headers["Authorization"] = "Bearer " + token
    else:
        raise TransferError("UNREGISTERED_TRANSPORT")
    ranged = start > 0 or end + 1 != asset["size"]
    if ranged:
        headers["Range"] = "bytes=%d-%d" % (start, end)
    return urllib.request.Request(url, headers=headers), ranged


def retry_delay(error, attempt, policy, now):
    raw = error.headers.get("Retry-After") if isinstance(error, urllib.error.HTTPError) else None
    if raw:
        try:
            delay = float(raw)
        except ValueError:
            try:
                delay = email.utils.parsedate_to_datetime(raw).timestamp() - now
            except (ValueError, TypeError, OverflowError):
                raise TransferError("INVALID_RETRY_AFTER") from None
        if delay > policy["maximum_retry_after_seconds"]:
            raise TransferError("RETRY_AFTER_EXCEEDS_BOUNDED_WINDOW")
        return max(0, delay)
    return min(policy["backoff_cap_seconds"], policy["backoff_initial_seconds"] * 2 ** attempt)


def download(asset, partial, opener, transport, policy, progress, event,
             token=None, deadline=None, sleeper=time.sleep, clock=time.time):
    partial = Path(partial)
    if partial.is_symlink():
        raise TransferError("PARTIAL_SYMLINK_REJECTED")
    if not partial.exists():
        partial.touch(mode=0o600, exist_ok=False)
    if not 0 <= partial.stat().st_size <= asset["size"]:
        raise TransferError("PARTIAL_SIZE_REJECTED")
    with partial.open("r+b") as output:
        output.seek(0, os.SEEK_END)
        while output.tell() < asset["size"]:
            start = output.tell()
            end = min(asset["size"] - 1, start + policy["chunk_bytes"] - 1)
            count = end - start + 1
            for attempt in range(policy["attempts_per_chunk"]):
                if deadline and clock() >= deadline:
                    raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
                began = clock()
                req, ranged = request_for(asset, start, end, transport, token)
                try:
                    with opener.open(req, timeout=policy["socket_timeout_seconds"]) as response:
                        if response.status != (206 if ranged else 200):
                            raise TransferError("UNEXPECTED_HTTP_STATUS", http_status=response.status)
                        if ranged and response.headers.get("Content-Range") != "bytes %d-%d/%d" % (start, end, asset["size"]):
                            raise TransferError("CONTENT_RANGE_MISMATCH")
                        if response.headers.get("Content-Length") != str(count):
                            raise TransferError("CONTENT_LENGTH_MISMATCH")
                        left = count
                        while left:
                            if deadline and clock() >= deadline:
                                raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
                            block = response.read(min(1 << 20, left))
                            if not block or len(block) > left:
                                raise TransferError("SHORT_OR_OVERSIZED_RESPONSE")
                            output.write(block)
                            left -= len(block)
                    output.flush()
                    os.fsync(output.fileno())
                    progress(output.tell(), dict(last_chunk_bytes=count, last_chunk_seconds=clock()-began, last_chunk_attempt=attempt+1))
                    break
                except Exception as error:
                    output.flush()
                    output.truncate(start)
                    output.seek(start)
                    os.fsync(output.fileno())
                    detail = error_info(error)
                    event(dict(range_start=start, range_end=end, attempt=attempt+1, **detail))
                    if detail.get("http_status") in (401, 403, 404) or detail["code"] == "WHOLE_RESOURCE_WALL_LIMIT" or attempt+1 == policy["attempts_per_chunk"]:
                        raise TransferError("BOUNDED_RANGE_ATTEMPTS_EXHAUSTED", last_error=detail) from None
                    delay = retry_delay(error, attempt, policy, clock())
                    if deadline and clock()+delay >= deadline:
                        raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
                    sleeper(delay)
    if partial.stat().st_size != asset["size"] or sha(partial, asset["git_blob"]) != asset["digest"]:
        raise TransferError("COMPLETE_OBJECT_HASH_MISMATCH")


def existing_valid(blob, asset):
    if not blob.exists() and not blob.is_symlink():
        return False
    if blob.is_symlink() or not blob.is_file() or blob.stat().st_size != asset["size"] or sha(blob, asset["git_blob"]) != asset["digest"]:
        raise TransferError("EXISTING_OBJECT_MISMATCH_RETAINED")
    return True


def link_original(blob, repo, asset):
    for revision in asset["target_revisions"]:
        assert len(revision) == 40 and all(c in "0123456789abcdef" for c in revision)
        rel = PurePosixPath(asset["path"])
        assert not rel.is_absolute() and ".." not in rel.parts
        target = repo / "snapshots" / revision / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            assert target.is_symlink() and target.resolve() == blob.resolve()
        else:
            target.symlink_to(os.path.relpath(blob, target.parent))
    if asset.get("main_revision"):
        ref = repo / "refs" / "main"
        ref.parent.mkdir(exist_ok=True)
        assert not ref.exists() or ref.read_text().strip() == asset["main_revision"]
        ref.write_text(asset["main_revision"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    m = json.loads(args.manifest.read_text())
    job, cache = args.manifest.parent, Path("/cache")
    assert not list(Path("/dev").glob("nvidia*"))
    assert sha(Path(__file__)) == m["server_worker_sha256"]
    assets = m["modelscope_assets"]
    assert len(assets) == 4 and sum(a["size"] for a in assets) == 16584414544
    assert all(a["source_revision"] == "3210bec0495fdc7a8d3dbb8d58da5711eab4b423" for a in assets)
    lock = (cache/".wc-frozen-model-relay-server.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (job/"server-dispatch.json").open("x") as f:
        json.dump(dict(pid=os.getpid(), started_unix=time.time(), source_revision=m["source_revision"]), f)
    began = time.time()
    state = dict(status="SERVER_FIXED_REASON_SHARDS_RUNNING", started_unix=began,
        source_revision=m["source_revision"], manifest_sha256=sha(args.manifest),
        worker_sha256=sha(Path(__file__)), verified_files=[], error_events=0,
        GPU_submissions=0, ledger_written=False, model_weights_loaded=0, CUDA_initialized=False)
    def save():
        state["updated_unix"] = time.time()
        atomic(job/"server-health.json", state)
    def event(detail):
        state["error_events"] += 1
        state["last_error"] = detail
        with (job/"server-events.jsonl").open("a") as f:
            f.write(json.dumps(dict(observed_unix=time.time(), path=state.get("current_path"), **detail))+"\n")
        save()
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), ScopedRedirect())
        state["phase"] = "validate-four-original-full-digest-metadata"
        save()
        req = urllib.request.Request("https://modelscope.cn/api/v1/models/unsloth/Cosmos-Reason1-7B/repo/files?Revision=master&Recursive=true")
        with opener.open(req, timeout=30) as response:
            metadata = json.loads(response.read(1 << 20))
        bypath = {x["Path"]: x for x in metadata["Data"]["Files"]}
        assert all(bypath[a["path"]]["Sha256"] == a["digest"] and bypath[a["path"]]["Size"] == a["size"] for a in assets)
        state["transport_provenance"] = dict(repository="unsloth/Cosmos-Reason1-7B", transport_locator_revision="master", artifact_identity_revision=assets[0]["source_revision"], all_four_metadata_match=True)
        partials = job/"partials"
        partials.mkdir(exist_ok=True)
        seed = m["seeded_partial"]
        part = partials/(seed["digest"]+".partial")
        state["phase"] = "receive-old-failed-job-prefix-without-modifying-source"
        save()
        h, remaining = hashlib.sha256(), seed["bytes"]
        with part.open("xb") as out:
            while remaining:
                b = sys.stdin.buffer.read(min(8 << 20, remaining))
                if not b:
                    raise TransferError("SHORT_SEED_STREAM")
                out.write(b); h.update(b); remaining -= len(b)
                state["seed_received_bytes"] = seed["bytes"] - remaining
                save()
            out.flush(); os.fsync(out.fileno())
        if h.hexdigest() != seed["sha256"] or sha(part) != seed["sha256"]:
            raise TransferError("SEED_PREFIX_HASH_MISMATCH")
        state["seed_prefix_hash_verified"] = True
        for asset in assets:
            repo = cache/("models--"+asset["repo_id"].replace("/", "--"))
            blobs = repo/"blobs"
            blobs.mkdir(parents=True, exist_ok=True)
            assert not repo.is_symlink() and not blobs.is_symlink()
            blob = blobs/asset["digest"]
            state.update(current_path=asset["path"], current_size=asset["size"], phase="download-frozen-reason-shard-direct-anonymous-modelscope")
            save()
            reused = existing_valid(blob, asset)
            if not reused:
                part = partials/(asset["digest"]+".partial")
                def progress(done, timing):
                    state.update(current_durable_bytes=done, **timing); save()
                download(asset, part, opener, "modelscope", m["modelscope_policy"], progress, event,
                    deadline=began+m["server_maximum_wall_seconds"])
                assert not blob.exists()
                part.replace(blob)
            # Independent post-publication read, then original HF compatibility paths.
            assert existing_valid(blob, asset)
            link_original(blob, repo, asset)
            state["verified_files"].append(dict(status="REMOTE_FULL_HASH_PASS", repo_id=asset["repo_id"], path=asset["path"], digest=asset["digest"], size=asset["size"], existing_blob_reused=reused, target_revisions=asset["target_revisions"], transport="anonymous_modelscope_exact_frozen_bytes", verified_unix=time.time()))
            save()
        state["status"] = "FOUR_FIXED_REASON_SHARDS_FULL_HASH_PASS"
    except BaseException as error:
        state.update(status="SERVER_MODEL_RESOURCE_FAILURE_RETAINED", failure=error_info(error))
    finally:
        state.update(ended_unix=time.time(), wall_seconds=time.time()-began)
        save(); atomic(job/"server-result.json", state)
    return 0 if state["status"] == "FOUR_FIXED_REASON_SHARDS_FULL_HASH_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
