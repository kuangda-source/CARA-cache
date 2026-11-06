#!/usr/bin/env python3
"""Download fixed assets on an external Mac volume, verify remotely, then unlink.

The approved HF credential stays on the Mac. Only model bytes cross SSH.
This is resource preparation and never imports Torch or starts a GPU job.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import subprocess
import sys
import time
import urllib.parse
import urllib.request


ALLOWED = {"nvidia/Cosmos-Guardrail1", "nvidia/Cosmos-Predict2.5-2B",
           "nvidia/Cosmos-Reason1-7B"}


def digest(path, git_blob=False):
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(("blob %d\0" % path.stat().st_size).encode())
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


class ScopedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlparse(newurl)
        if url.scheme != "https":
            raise ValueError("HTTPS redirect required")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if url.hostname != urllib.parse.urlparse(req.full_url).hostname:
            redirected.remove_header("Authorization")
        return redirected


REMOTE = r'''
import hashlib,json,os,sys,time
from pathlib import Path,PurePosixPath
a=ASSET;root=Path(WORKSPACE)/'cache/huggingface/hub'
assert root.resolve()==root and str(root).startswith('/data20t/gaokuangda/worldcache_workspace/')
repo=root/('models--'+a['repo_id'].replace('/','--'));blobs=repo/'blobs';blobs.mkdir(parents=True,exist_ok=True)
assert not repo.is_symlink() and not blobs.is_symlink()
blob=blobs/a['digest'];part=blobs/(a['digest']+'.wc-authorized-relay-r1.partial')
def fullhash(p):
 h=hashlib.sha1() if a['git_blob'] else hashlib.sha256()
 if a['git_blob']:h.update(('blob %d\0'%p.stat().st_size).encode())
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def valid(p):return p.is_file() and not p.is_symlink() and p.stat().st_size==a['size'] and fullhash(p)==a['digest']
existed=blob.exists()
if MODE=='upload':
 if existed:
  assert valid(blob),'Existing remote blob mismatch'
  for b in iter(lambda:sys.stdin.buffer.read(8<<20),b''):pass
 else:
  assert not part.exists(),'Prior partial retained; recover in a new version'
  with part.open('xb') as f:
   for b in iter(lambda:sys.stdin.buffer.read(8<<20),b''):f.write(b)
   f.flush();os.fsync(f.fileno())
  assert valid(part),'Remote full-object hash differs'
  assert not blob.exists();part.replace(blob)
 assert valid(blob)
 for revision in a['target_revisions']:
  assert len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
  relative=PurePosixPath(a['path']);assert not relative.is_absolute() and '..' not in relative.parts
  snapshot=repo/'snapshots'/revision;target=snapshot.joinpath(*relative.parts);target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() or target.is_symlink():assert target.resolve()==blob.resolve()
  else:target.symlink_to(os.path.relpath(blob,target.parent))
  assert target.resolve()==blob.resolve()
 refs=repo/'refs';refs.mkdir(exist_ok=True)
 main=a.get('main_revision')
 if main:
  previous=(refs/'main').read_text().strip() if (refs/'main').exists() else None
  assert previous in (None,main),'Do not replace another frozen main ref'
  (refs/'main').write_text(main)
 print(json.dumps(dict(status='REMOTE_FULL_HASH_PASS',repo_id=a['repo_id'],path=a['path'],size=a['size'],digest=a['digest'],target_revisions=a['target_revisions'],existing_blob_reused=existed,verified_unix=time.time())))
else:print(json.dumps(dict(existing_complete_blob_valid=valid(blob) if existed else False,blob_exists=existed,partial_exists=part.exists())))
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--hosts", type=Path, required=True)
    p.add_argument("--control-record", type=Path, required=True)
    args = p.parse_args()
    m = json.loads(args.manifest.read_text())
    mount, job = Path(m["external_mount"]), Path(m["job"])
    assert mount == Path("/Volumes/data") and os.path.ismount(mount)
    assert job.is_relative_to(mount) and job.stat().st_dev == mount.stat().st_dev
    assert not (job / "dispatch-intent.json").exists(), "Single-dispatch fence exists"
    assert digest(Path(__file__)) == m["worker_sha256"]
    assert stat.S_IMODE(args.token_file.stat().st_mode) == 0o600
    assert args.token_file.stat().st_uid == os.getuid()
    token = args.token_file.read_text().strip()
    assert token.startswith("hf_")
    host = json.loads(args.hosts.read_text())["four_card"]
    control = json.loads(args.control_record.read_text())
    ssh = ["ssh", "-F", "/dev/null", "-S", control["control_socket"],
           "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-p",
           str(host["port"]), host["user"] + "@" + host["host"]]
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": m["local_proxy"]}), ScopedRedirect())
    started = time.time()
    state = dict(status="EXTERNAL_DISK_AUTHORIZED_MODEL_RELAY_RUNNING", started_unix=started,
        source_revision=m["source_revision"], manifest_sha256=digest(args.manifest),
        worker_sha256=digest(Path(__file__)), expected_files=len(m["assets"]),
        expected_bytes=sum(a["size"] for a in m["assets"]), verified_files=[],
        external_mount=str(mount), local_model_bytes_on_internal_disk=0,
        token_exported_to_server=False, model_weights_loaded=0, CUDA_initialized=False,
        GPU_submissions=0, ledger_written=False, GPU_dispatch_ready=False,
        whole_model_resource_acceptance=False)
    (job / "dispatch-intent.json").write_text(json.dumps(dict(started_unix=started,pid=os.getpid(),worker_sha256=state["worker_sha256"])))

    def save():
        state["updated_unix"] = time.time()
        atomic(job / "health.json", state)

    def remote(asset, mode, stream=None):
        code = "ASSET=" + repr(asset) + "\nWORKSPACE=" + repr(m["workspace"]) + "\nMODE=" + repr(mode) + "\n" + REMOTE
        result = subprocess.run(ssh + ["python3 -c " + shlex.quote(code)], stdin=stream,
                                capture_output=True, timeout=14400 if stream else 90)
        if result.returncode != 0:
            raise RuntimeError("Remote " + mode + " failed; original bytes retained")
        return json.loads(result.stdout)

    try:
        for number, a in enumerate(m["assets"]):
            assert a["repo_id"] in ALLOWED and len(a["source_revision"]) == 40
            assert 0 <= a["size"] <= 6 * 2**30
            path = PurePosixPath(a["path"])
            assert not path.is_absolute() and ".." not in path.parts
            assert os.path.ismount(mount) and job.stat().st_dev == mount.stat().st_dev
            assert time.time() - started < m["maximum_wall_seconds"]
            state.update(current_file=number + 1, current_repo=a["repo_id"], current_path=a["path"],
                         current_size=a["size"], current_durable_bytes=0, phase="check-existing-remote-object")
            save()
            current = remote(a, "check")
            assert not current["partial_exists"], "Prior remote partial retained"
            assert not current["blob_exists"] or current["existing_complete_blob_valid"]
            if current["existing_complete_blob_valid"]:
                with open(os.devnull,"rb") as empty:
                    receipt = remote(a, "upload", empty)
            else:
                free = os.statvfs(mount)
                assert free.f_bavail * free.f_frsize > a["size"] + 8 * 2**30
                partial, complete = job / (a["digest"] + ".partial"), job / a["digest"]
                assert not partial.is_symlink() and not complete.exists()
                url = "https://huggingface.co/" + a["repo_id"] + "/resolve/" + a["source_revision"] + "/" + urllib.parse.quote(a["path"], safe="/")
                state["phase"] = "download-to-external-volume"
                with partial.open("ab") as output:
                    while output.tell() < a["size"]:
                        assert time.time() - started < m["maximum_wall_seconds"]
                        start = output.tell()
                        end = min(a["size"] - 1, start + (16 << 20) - 1)
                        count = end - start + 1
                        for attempt in range(3):
                            try:
                                headers = {"Authorization": "Bearer " + token, "Accept-Encoding": "identity", "User-Agent": "worldcache-fixed-resource-relay"}
                                if a["size"] > 16 << 20:
                                    headers["Range"] = "bytes=%d-%d" % (start, end)
                                req = urllib.request.Request(url + "?download=true&wc_range_start=" + str(start), headers=headers)
                                with opener.open(req, timeout=60) as response:
                                    expected_status = 206 if "Range" in headers else 200
                                    assert response.status == expected_status
                                    if expected_status == 206:
                                        assert response.headers.get("Content-Range") == "bytes %d-%d/%d" % (start,end,a["size"])
                                    assert int(response.headers.get("Content-Length", "-1")) == count
                                    remaining = count
                                    while remaining:
                                        block = response.read(min(1 << 20, remaining))
                                        if not block:
                                            raise ValueError("Short bounded response")
                                        output.write(block)
                                        remaining -= len(block)
                                output.flush()
                                os.fsync(output.fileno())
                                break
                            except Exception:
                                output.flush()
                                output.truncate(start)
                                output.seek(start)
                                if attempt == 2:
                                    raise RuntimeError("Bounded fixed-object download exhausted") from None
                        state["current_durable_bytes"] = output.tell()
                        save()
                assert partial.stat().st_size == a["size"] and digest(partial,a["git_blob"]) == a["digest"]
                partial.replace(complete)
                state["phase"] = "upload-full-object-and-independent-server-hash"
                save()
                with complete.open("rb") as stream:
                    receipt = remote(a, "upload", stream)
                assert receipt["status"] == "REMOTE_FULL_HASH_PASS" and receipt["digest"] == a["digest"]
                complete.unlink()
                receipt["external_relay_copy_removed_after_remote_full_hash"] = True
            state["verified_files"].append(receipt)
            save()
        state.update(status="FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS",
                     external_relay_model_copies_remaining=0)
    except BaseException as error:
        state.update(status="AUTHORIZED_MODEL_RELAY_FAILURE_RETAINED", error_type=type(error).__name__)
    finally:
        state.update(ended_unix=time.time(), wall_seconds=time.time()-started)
        save()
        atomic(job / "result.json", state)
    return 0 if state["status"] == "FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
