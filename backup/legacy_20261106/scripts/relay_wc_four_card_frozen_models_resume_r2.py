#!/usr/bin/env python3
"""Resume fixed model assets on the external volume without replaying completed files."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import socket
import stat
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request


class TransferError(Exception):
    def __init__(self, code, **details):
        super().__init__(code)
        self.code = code
        self.details = details


def digest(path, git_blob=False):
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(("blob %d\0" % path.stat().st_size).encode())
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def sanitized_error(error):
    if isinstance(error, TransferError):
        return dict(code=error.code, **error.details)
    if isinstance(error, urllib.error.HTTPError):
        return dict(code="HTTP_ERROR", http_status=error.code)
    if isinstance(error, (TimeoutError, socket.timeout)):
        return dict(code="SOCKET_TIMEOUT")
    if isinstance(error, urllib.error.URLError):
        return dict(code="URL_TRANSPORT_ERROR", reason_type=type(error.reason).__name__)
    return dict(code="LOCAL_OR_TRANSPORT_ERROR", error_type=type(error).__name__)


def fixed_range_download(asset, partial, opener, token, policy, progress, event,
                         sleeper=time.sleep, clock=time.time, deadline=None):
    """Commit only exact bounded responses; never put URLs or exception strings in logs."""
    total = asset["size"]
    assert not partial.is_symlink()
    if not partial.exists():
        partial.touch(mode=0o600, exist_ok=False)
    assert 0 <= partial.stat().st_size <= total
    with partial.open("r+b") as output:
        output.seek(0, os.SEEK_END)
        while output.tell() < total:
            if deadline is not None and clock() >= deadline:
                raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
            start = output.tell()
            end = min(total - 1, start + policy["chunk_bytes"] - 1)
            count = end - start + 1
            successful = False
            for attempt in range(policy["attempts_per_chunk"]):
                if deadline is not None and clock() >= deadline:
                    raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
                began = clock()
                encoded = urllib.parse.quote(asset["path"], safe="/")
                url = ("https://huggingface.co/" + asset["repo_id"] + "/resolve/" +
                       asset["source_revision"] + "/" + encoded +
                       "?download=true&wc_range_start=" + str(start) +
                       "&wc_attempt_nonce=" + str(time.time_ns()))
                range_requested = start > 0 or count != total
                headers = {
                    "Authorization": "Bearer " + token,
                    "Accept-Encoding": "identity",
                    "User-Agent": "worldcache-fixed-resource-relay-r2"}
                if range_requested:
                    headers["Range"] = "bytes=%d-%d" % (start, end)
                req = urllib.request.Request(url, headers=headers)
                try:
                    with opener.open(req, timeout=policy["socket_timeout_seconds"]) as response:
                        header_seconds = clock() - began
                        if response.status != (206 if range_requested else 200):
                            raise TransferError("UNEXPECTED_HTTP_STATUS", http_status=response.status)
                        wanted = "bytes %d-%d/%d" % (start, end, total)
                        if range_requested and response.headers.get("Content-Range") != wanted:
                            raise TransferError("CONTENT_RANGE_MISMATCH")
                        if response.headers.get("Content-Length") != str(count):
                            raise TransferError("CONTENT_LENGTH_MISMATCH")
                        remaining = count
                        while remaining:
                            if deadline is not None and clock() >= deadline:
                                raise TransferError("WHOLE_RESOURCE_WALL_LIMIT")
                            block = response.read(min(1 << 20, remaining))
                            if not block:
                                raise TransferError("SHORT_BOUNDED_RESPONSE")
                            if len(block) > remaining:
                                raise TransferError("OVERSIZED_BOUNDED_RESPONSE")
                            output.write(block)
                            remaining -= len(block)
                    output.flush()
                    os.fsync(output.fileno())
                    progress(output.tell(), dict(last_chunk_bytes=count,
                        last_chunk_seconds=clock() - began,
                        last_chunk_header_seconds=header_seconds, last_chunk_attempt=attempt + 1))
                    successful = True
                    break
                except Exception as error:
                    output.flush()
                    output.truncate(start)
                    output.seek(start)
                    os.fsync(output.fileno())
                    detail = sanitized_error(error)
                    event(dict(range_start=start, range_end=end, attempt=attempt + 1,
                               wall_seconds=clock() - began, **detail))
                    fatal = detail.get("http_status") == 401 or detail["code"] == "WHOLE_RESOURCE_WALL_LIMIT"
                    if fatal or attempt + 1 == policy["attempts_per_chunk"]:
                        raise TransferError("BOUNDED_RANGE_ATTEMPTS_EXHAUSTED", last_error=detail) from None
                    delay = min(policy["backoff_cap_seconds"],
                                policy["backoff_initial_seconds"] * 2 ** attempt)
                    sleeper(delay)
            if not successful:
                raise TransferError("BOUNDED_RANGE_NOT_COMMITTED")
    if partial.stat().st_size != total or digest(partial, asset["git_blob"]) != asset["digest"]:
        raise TransferError("COMPLETE_LOCAL_HASH_MISMATCH")


INVENTORY = r'''
from pathlib import Path
import hashlib,json,time
root=Path(WORKSPACE)/'cache/huggingface/hub'
assert root.resolve()==root
out=[]
for a in ASSETS:
 repo=root/('models--'+a['repo_id'].replace('/','--'));blob=repo/'blobs'/a['digest']
 assert not repo.is_symlink() and not (repo/'blobs').is_symlink()
 part=repo/'blobs'/(a['digest']+'.wc-authorized-relay-r1.partial')
 item=dict(repo_id=a['repo_id'],path=a['path'],digest=a['digest'],size=a['size'],
           blob_exists=blob.exists(),partial_exists=part.exists(),complete_valid=False,links_match=False)
 if blob.exists():
  assert not blob.is_symlink() and blob.is_file()
  h=hashlib.sha1() if a['git_blob'] else hashlib.sha256()
  if a['git_blob']:h.update(('blob %d\0'%blob.stat().st_size).encode())
  with blob.open('rb') as f:
   for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  item['complete_valid']=blob.stat().st_size==a['size'] and h.hexdigest()==a['digest']
  item['links_match']=all((repo/'snapshots'/revision/a['path']).resolve()==blob.resolve() for revision in a['target_revisions'])
  item['verified_unix']=time.time()
 out.append(item)
print(json.dumps(out))
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--hosts", type=Path, required=True)
    p.add_argument("--control-record", type=Path, required=True)
    args = p.parse_args()
    m = json.loads(args.manifest.read_text())
    job, mount = Path(m["job"]), Path(m["external_mount"])
    assert mount == Path("/Volumes/data") and os.path.ismount(mount)
    assert job.is_relative_to(mount) and job.stat().st_dev == mount.stat().st_dev
    assert not (job / "dispatch-intent.json").exists()
    assert digest(Path(__file__)) == m["worker_sha256"]
    assert digest(job / "legacy_relay.py") == m["legacy_helper_sha256"]
    assert stat.S_IMODE(args.token_file.stat().st_mode) == 0o600
    assert args.token_file.stat().st_uid == os.getuid()
    assert len(m["assets"]) == 96 and sum(a["size"] for a in m["assets"]) == 21358871258
    spec = importlib.util.spec_from_file_location("fixed_legacy", job / "legacy_relay.py")
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    for a in m["assets"]:
        assert a["repo_id"] in legacy.ALLOWED and len(a["source_revision"]) == 40
        relative = PurePosixPath(a["path"])
        assert not relative.is_absolute() and ".." not in relative.parts
    lock = (job.parent / ".wc-frozen-model-relay.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent = m["parent_original_identity"]
    proc = subprocess.run(["ps", "-p", str(parent["pid"]), "-o", "lstart=,command="],
                          capture_output=True, text=True)
    assert proc.returncode != 0 or proc.stdout.strip()[:24] != parent["ps_start_and_command"][:24]
    host = json.loads(args.hosts.read_text())["four_card"]
    control = json.loads(args.control_record.read_text())
    ssh = ["ssh", "-F", "/dev/null", "-S", control["control_socket"], "-o", "BatchMode=yes",
           "-o", "StrictHostKeyChecking=yes", "-p", str(host["port"]), host["user"] + "@" + host["host"]]
    token = args.token_file.read_text().strip()
    assert token.startswith("hf_")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": m["local_proxy"]}), legacy.ScopedRedirect())
    started = time.time()
    with (job / "dispatch-intent.json").open("x") as f:
        json.dump(dict(pid=os.getpid(),started_unix=started,worker_sha256=m["worker_sha256"]),f)
    state = dict(status="EXTERNAL_DISK_AUTHORIZED_MODEL_RELAY_RUNNING", started_unix=started,
        source_revision=m["source_revision"], manifest_sha256=digest(args.manifest),
        worker_sha256=m["worker_sha256"], expected_files=96, expected_bytes=21358871258,
        verified_files=[], reused_verified_files=0, requested_missing_files=[], error_events=0,
        external_mount=str(mount), local_model_bytes_on_internal_disk=0,
        token_exported_to_server=False, model_weights_loaded=0, CUDA_initialized=False,
        GPU_submissions=0, ledger_written=False, GPU_dispatch_ready=False,
        whole_model_resource_acceptance=False)

    def save():
        state["updated_unix"] = time.time()
        atomic(job / "health.json", state)

    def event(detail):
        record = dict(observed_unix=time.time(), repo_id=state.get("current_repo"),
                      path=state.get("current_path"), **detail)
        with (job / "download-events.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
        state["error_events"] += 1
        state["last_error"] = record
        save()

    def call(code, stream=None, timeout=180):
        try:
            response = subprocess.run(ssh + ["python3 -c " + shlex.quote(code)], stdin=stream,
                                      capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise TransferError("REMOTE_CALL_TIMEOUT_UNKNOWN") from None
        if response.returncode:
            raise TransferError("REMOTE_CALL_FAILED_UNKNOWN", SSH_exit_code=response.returncode)
        try:
            return json.loads(response.stdout)
        except json.JSONDecodeError:
            raise TransferError("REMOTE_JSON_UNREADABLE") from None

    try:
        state["phase"] = "verify-existing-registered-remote-files"
        save()
        inventory = call("WORKSPACE="+repr(m["workspace"])+"\nASSETS="+repr(m["assets"])+"\n"+INVENTORY)
        assert len(inventory) == 96
        atomic(job / "initial-remote-inventory.json", inventory)
        identity = lambda a: (a["repo_id"], a["path"], a["digest"])
        parent_complete = {tuple(a) for a in m["parent_verified_asset_identities"]}
        missing = {tuple(a) for a in m["allowed_missing_asset_identities"]}
        assert parent_complete.isdisjoint(missing) and len(parent_complete | missing) == 96
        for a, found in zip(m["assets"], inventory):
            assert (found["repo_id"],found["path"],found["digest"]) == (a["repo_id"],a["path"],a["digest"])
            assert not found["partial_exists"], "Preserve unknown remote partial"
            if found["blob_exists"]:
                assert found["complete_valid"] and found["links_match"], "Preserve mismatched existing file"
            elif identity(a) not in missing:
                raise TransferError("PREVIOUSLY_VERIFIED_REMOTE_ASSET_MISSING")
        for a, found in zip(m["assets"], inventory):
            state.update(current_repo=a["repo_id"],current_path=a["path"],current_size=a["size"],
                         current_durable_bytes=0,phase="reuse-verified-remote-file")
            if found["complete_valid"]:
                seed_file = job/(a["digest"]+".partial")
                if seed_file.exists():
                    seed = m.get("seeded_partial")
                    assert seed and seed["digest"] == a["digest"]
                    assert not seed_file.is_symlink() and digest(seed_file) == seed["sha256"]
                    seed_file.unlink()
                receipt = dict(status="REMOTE_FULL_HASH_PASS",repo_id=a["repo_id"],path=a["path"],
                    size=a["size"],digest=a["digest"],target_revisions=a["target_revisions"],
                    existing_blob_reused=True,verified_unix=found["verified_unix"],
                    external_relay_copy_removed_after_remote_full_hash=True)
                state["reused_verified_files"] += 1
            else:
                assert identity(a) in missing
                assert os.path.ismount(mount) and job.stat().st_dev == mount.stat().st_dev
                free = os.statvfs(mount)
                assert free.f_bavail * free.f_frsize > a["size"] + 8 * 2**30
                partial, complete = job/(a["digest"]+".partial"), job/a["digest"]
                assert not complete.exists() and not partial.is_symlink()
                seed = m.get("seeded_partial")
                if partial.exists():
                    assert seed and a["digest"]==seed["digest"] and partial.stat().st_size==seed["bytes"]
                    assert digest(partial)==seed["sha256"]
                state["phase"] = "download-to-external-volume"
                state["requested_missing_files"].append(dict(repo_id=a["repo_id"],path=a["path"],digest=a["digest"]))
                def progress(done, timing):
                    state.update(current_durable_bytes=done, **timing)
                    save()
                save()
                fixed_range_download(a, partial, opener, token, m["download_policy"], progress, event,
                                     deadline=started + m["maximum_wall_seconds"])
                partial.replace(complete)
                state["phase"] = "upload-full-object-and-independent-server-hash"
                save()
                code="ASSET="+repr(a)+"\nWORKSPACE="+repr(m["workspace"])+"\nMODE='upload'\n"+legacy.REMOTE
                with complete.open("rb") as stream:
                    receipt = call(code, stream, timeout=14400)
                assert receipt["status"]=="REMOTE_FULL_HASH_PASS" and receipt["digest"]==a["digest"]
                complete.unlink()
                receipt["external_relay_copy_removed_after_remote_full_hash"] = True
            state["verified_files"].append(receipt)
            save()
        state.update(status="FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS",
                     external_relay_model_copies_remaining=0)
    except BaseException as error:
        state.update(status="AUTHORIZED_MODEL_RELAY_FAILURE_RETAINED",error_type=type(error).__name__,
                     failure=sanitized_error(error))
    finally:
        state.update(ended_unix=time.time(),wall_seconds=time.time()-started)
        save()
        atomic(job / "result.json",state)
    return 0 if state["status"]=="FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
