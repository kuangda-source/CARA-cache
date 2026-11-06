#!/usr/bin/env python3
"""One missing-only resource controller: server Reason shards, Mac official HF rest."""
import argparse
import base64
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import time
import urllib.request


SERVER_BOOTSTRAP = r'''
import base64,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
w=Path(M['workspace']);job=Path(M['server_job']);cache=w/'cache/huggingface/hub'
assert str(job).startswith(str(w/'bootstrap')+'/') and job.parent.resolve()==w/'bootstrap'
assert not job.exists(),'Existing independent R3 stage: recover original only'
assert cache.resolve()==cache
disk=os.statvfs(w);free=disk.f_bavail*disk.f_frsize
assert free >= 64*2**30+21358871258,'Insufficient data-disk headroom'
lock=(cache/'.wc-frozen-model-relay-server.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for a in M['assets']:
 b=cache/('models--'+a['repo_id'].replace('/','--'))/'blobs'
 assert not (b/(a['digest']+'.wc-authorized-relay-r1.partial')).exists(),'Unknown old receiver partial retained'
# Only inspect own possible receiver processes; never alter any process.
receivers=[]
for q in Path('/proc').iterdir():
 if not q.name.isdigit() or int(q.name)==os.getpid():continue
 try:
  if q.stat().st_uid!=os.getuid():continue
  cmd=(q/'cmdline').read_bytes()
  if b"MODE='upload'" in cmd and b'wc-authorized-relay-r1.partial' in cmd:receivers.append(int(q.name))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert not receivers,'Original receiver still writing; preserve and stop new dispatch'
base=w/'bootstrap/wc-fourcard-public-model-assets-r1-20261021/manifest.json'
image=json.loads(base.read_text())['container_image_id']
subprocess.run(['docker','image','inspect',image],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
mem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if v.strip().split() and v.strip().split()[0].isdigit()}
assert mem.get('MemAvailable',0)>=2*2**30
job.mkdir(mode=0o700)
worker=base64.b64decode(WORKER_B64);assert hashlib.sha256(worker).hexdigest()==M['server_worker_sha256']
(job/'server-worker.py').write_bytes(worker)
(job/'manifest.json').write_text(json.dumps(M,indent=2)+'\n')
manifest_sha=hashlib.sha256((job/'manifest.json').read_bytes()).hexdigest()
pre=dict(observed_unix=time.time(),data_disk_free_bytes=free,available_memory_bytes=mem['MemAvailable'],original_receiver_PIDs=receivers,old_receiver_partials_absent=True,resource_lock_probe_free=True,container_image_id=image,GPU_submissions=0,ledger_written=False)
(job/'fresh-preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
with (job/'dispatch-intent.json').open('x') as f:json.dump(dict(source_revision=M['source_revision'],worker_sha256=M['server_worker_sha256'],manifest_sha256=manifest_sha),f)
lock.close()
command=['docker','run','--rm','--interactive','--name',job.name,'--cpus','2','--memory','16g','--pids-limit','128','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--user',str(os.getuid())+':'+str(os.getgid()),'-e','NVIDIA_VISIBLE_DEVICES=void','-e','CUDA_VISIBLE_DEVICES=','-v',str(job)+':/job:rw','-v',str(cache)+':/cache:rw',image,'python','/job/server-worker.py','--manifest','/job/manifest.json']
began=time.time()
with (job/'console.private.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=sys.stdin.buffer,stdout=log,stderr=subprocess.STDOUT)
 ticks=int((Path('/proc')/str(child.pid)/'stat').read_text().rsplit(') ',1)[1].split()[19])
 launch=dict(status='SERVER_MODEL_RESOURCE_CHILD_SINGLE_DISPATCHED',started_unix=began,identity=dict(pid=child.pid,start_ticks=ticks),source_revision=M['source_revision'],worker_sha256=M['server_worker_sha256'],manifest_sha256=manifest_sha,job=str(job),container_name=job.name,container_image_id=image,fresh_preflight=pre,GPU_submissions=0,ledger_written=False)
 with (job/'launch.json').open('x') as f:json.dump(launch,f,indent=2)
 try:code=child.wait(timeout=M['server_maximum_wall_seconds']+1800)
 except subprocess.TimeoutExpired:
  print(json.dumps(dict(status='SERVER_CHILD_WAIT_UNKNOWN_RESTORE_HANDLE_ONLY',launch=launch)));sys.exit(0)
value=dict(status='SERVER_CHILD_TERMINAL_CAPTURE',launch=launch,exit_code=code,observed_unix=time.time(),result=json.loads((job/'server-result.json').read_text()) if (job/'server-result.json').exists() else None)
print(json.dumps(value))
'''


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--hosts", type=Path, required=True)
    p.add_argument("--control-record", type=Path, required=True)
    args = p.parse_args()
    job = args.manifest.parent
    core = load_module("hybrid_core", job/"server-worker.py")
    legacy = load_module("original_receiver", job/"legacy_relay.py")
    prior = load_module("original_inventory", job/"resume_r2.py")
    m = json.loads(args.manifest.read_text())
    assert os.path.ismount('/Volumes/data') and job.stat().st_dev == Path('/Volumes/data').stat().st_dev
    assert core.sha(Path(__file__)) == m['worker_sha256']
    assert core.sha(job/'server-worker.py') == m['server_worker_sha256']
    assert core.sha(job/'legacy_relay.py') == m['legacy_helper_sha256']
    assert core.sha(job/'resume_r2.py') == m['original_R2_worker_sha256']
    assert stat.S_IMODE(args.token_file.stat().st_mode) == 0o600 and args.token_file.stat().st_uid == os.getuid()
    assert len(m['assets']) == 96 and sum(a['size'] for a in m['assets']) == 21358871258
    parent = m['parent_launch']
    proc = subprocess.run(['ps','-ww','-p',str(parent['identity']['pid']),'-o','lstart=,command='],capture_output=True,text=True)
    assert proc.returncode != 0 or proc.stdout.strip()[:24] != parent['identity']['ps_start_and_command'][:24]
    lock = (job.parent/'.wc-frozen-model-relay.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    host = json.loads(args.hosts.read_text())['four_card']
    control = json.loads(args.control_record.read_text())
    ssh = ['ssh','-F','/dev/null','-S',control['control_socket'],'-o','BatchMode=yes','-o','ControlMaster=no','-o','StrictHostKeyChecking=yes','-p',str(host['port']),host['user']+'@'+host['host']]
    def call(code, stream=None, timeout=180):
        try:
            r = subprocess.run(ssh+['python3 -c '+shlex.quote(code)],stdin=stream,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired:
            raise core.TransferError('REMOTE_CALL_TIMEOUT_UNKNOWN_RESTORE_ORIGINAL_ONLY') from None
        if r.returncode:
            # Do not expose private SSH stderr or echoed command/URLs.
            raise core.TransferError('REMOTE_CALL_UNKNOWN_RESTORE_ORIGINAL_ONLY', SSH_exit_code=r.returncode)
        try:
            return json.loads(r.stdout)
        except (ValueError, UnicodeDecodeError):
            raise core.TransferError('REMOTE_JSON_UNKNOWN_RESTORE_ORIGINAL_ONLY') from None
    began = time.time()
    with (job/'dispatch-intent.json').open('x') as f:
        json.dump(dict(pid=os.getpid(),started_unix=began,source_revision=m['source_revision'],manifest_sha256=core.sha(args.manifest)),f)
    state = dict(status='FIXED96_HYBRID_RESOURCE_RUNNING',source_revision=m['source_revision'],worker_sha256=m['worker_sha256'],server_worker_sha256=m['server_worker_sha256'],manifest_sha256=core.sha(args.manifest),started_unix=began,expected_files=96,expected_bytes=21358871258,verified_files=[],requested_missing_files=[],reused_verified_files=0,error_events=0,external_mount='/Volumes/data',local_model_bytes_on_internal_disk=0,token_exported_to_server=False,model_weights_loaded=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False,GPU_dispatch_ready=False,whole_model_resource_acceptance=False)
    def save():
        state['updated_unix'] = time.time(); core.atomic(job/'health.json',state)
    def event(detail):
        state['error_events'] += 1; state['last_error'] = detail
        with (job/'download-events.jsonl').open('a') as f:
            f.write(json.dumps(dict(observed_unix=time.time(),path=state.get('current_path'),**detail))+'\n')
        save()
    try:
        state['phase'] = 'independent-inventory-original96-and-reuse'
        save()
        inventory = call('WORKSPACE='+repr(m['workspace'])+'\nASSETS='+repr(m['assets'])+'\n'+prior.INVENTORY)
        core.atomic(job/'initial-remote-inventory.json',inventory)
        missing = {tuple(x) for x in m['allowed_missing_asset_identities']}
        ident = lambda a:(a['repo_id'],a['path'],a['digest'])
        assert len(inventory) == 96
        for a, f in zip(m['assets'],inventory):
            assert ident(a) == ident(f) and not f['partial_exists']
            assert not f['blob_exists'] or (f['complete_valid'] and f['links_match'])
            assert f['complete_valid'] or ident(a) in missing
        seed = m['seeded_partial']; seed_path = Path(seed['parent_path'])
        assert not seed_path.is_symlink() and seed_path.stat().st_size == seed['bytes'] and core.sha(seed_path) == seed['sha256']
        state['phase'] = 'stream-bound-prefix-and-server-direct-four-Reason-shards'
        save()
        public_keys = ['workspace','server_job','source_revision','server_worker_sha256','assets','modelscope_assets','seeded_partial','modelscope_policy','server_maximum_wall_seconds']
        sm = {k:m[k] for k in public_keys}
        code = 'M='+repr(sm)+'\nWORKER_B64='+repr(base64.b64encode((job/'server-worker.py').read_bytes()).decode())+'\n'+SERVER_BOOTSTRAP
        with seed_path.open('rb') as stream:
            server = call(code,stream,timeout=m['server_maximum_wall_seconds']+2100)
        core.atomic(job/'server-terminal.json',server)
        assert server['status'] == 'SERVER_CHILD_TERMINAL_CAPTURE' and server['exit_code'] == 0
        assert server['result']['status'] == 'FOUR_FIXED_REASON_SHARDS_FULL_HASH_PASS'
        assert len(server['result']['verified_files']) == 4 and server['result']['seed_prefix_hash_verified']
        assert core.sha(seed_path) == seed['sha256'], 'Original prefix must be preserved'
        state['server_four_shards_completed'] = True
        state['phase'] = 'reinventory-all96-before-official-HF-missing-only-relay'
        save()
        inventory = call('WORKSPACE='+repr(m['workspace'])+'\nASSETS='+repr(m['assets'])+'\n'+prior.INVENTORY,timeout=900)
        core.atomic(job/'after-server-remote-inventory.json',inventory)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({'https':m['local_proxy']}),core.ScopedRedirect())
        token = args.token_file.read_text().strip()
        assert token.startswith('hf_')
        mirror_ids = {ident(a) for a in m['modelscope_assets']}
        for a, found in zip(m['assets'],inventory):
            assert ident(a) == ident(found) and not found['partial_exists']
            assert not found['blob_exists'] or (found['complete_valid'] and found['links_match'])
            state.update(current_repo=a['repo_id'],current_path=a['path'],current_size=a['size'],current_durable_bytes=0)
            if found['complete_valid']:
                receipt = dict(status='REMOTE_FULL_HASH_PASS',repo_id=a['repo_id'],path=a['path'],size=a['size'],digest=a['digest'],target_revisions=a['target_revisions'],existing_blob_reused=True,verified_unix=found['verified_unix'])
                state['reused_verified_files'] += 1
            else:
                assert ident(a) in missing and ident(a) not in mirror_ids
                assert os.path.ismount('/Volumes/data') and job.stat().st_dev == Path('/Volumes/data').stat().st_dev
                free = os.statvfs('/Volumes/data')
                assert free.f_bavail*free.f_frsize > a['size']+8*2**30
                partial = job/(a['digest']+'.partial')
                assert not partial.exists() and not partial.is_symlink()
                state['requested_missing_files'].append(dict(repo_id=a['repo_id'],path=a['path'],digest=a['digest'],transport='official_HF_Mac_only'))
                state['phase'] = 'download-only-still-missing-official-file-to-external-volume'; save()
                def progress(done,timing):
                    state.update(current_durable_bytes=done,**timing); save()
                core.download(a,partial,opener,'official_hf',m['official_HF_policy'],progress,event,token=token,deadline=began+m['maximum_wall_seconds'])
                state['phase'] = 'upload-official-file-independent-server-full-hash'; save()
                prefix = "import fcntl\nfrom pathlib import Path\nresource_lock=(Path("+repr(m['workspace'])+")/'cache/huggingface/hub/.wc-frozen-model-relay-server.lock').open('a')\nfcntl.flock(resource_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                code = prefix+'ASSET='+repr(a)+'\nWORKSPACE='+repr(m['workspace'])+"\nMODE='upload'\n"+legacy.REMOTE
                with partial.open('rb') as stream:
                    receipt = call(code,stream,timeout=14400)
                assert receipt['status'] == 'REMOTE_FULL_HASH_PASS' and receipt['digest'] == a['digest']
                partial.unlink()
            receipt['external_relay_copy_removed_after_remote_full_hash'] = True
            state['verified_files'].append(receipt); save()
        state.update(status='FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS',external_relay_model_copies_remaining=0)
    except BaseException as error:
        state.update(status='AUTHORIZED_MODEL_RELAY_FAILURE_RETAINED',failure=core.error_info(error))
    finally:
        state.update(ended_unix=time.time(),wall_seconds=time.time()-began)
        save(); core.atomic(job/'result.json',state)
    return 0 if state['status'] == 'FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
