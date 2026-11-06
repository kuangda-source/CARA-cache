#!/usr/bin/env python3
"""One bounded resource capture, then strictly offline full96 acceptance."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


REMOTE = r'''
from pathlib import Path
import fcntl,hashlib,json,subprocess,time
job=Path(L['server_job']);w=Path('/data20t/gaokuangda/worldcache_workspace');cache=w/'cache/huggingface/hub'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((job/n).read_text()) if (job/n).exists() else None
v=dict(observed_unix=time.time(),server_job_exists=job.exists(),server_launch=read('launch.json'),server_health=read('server-health.json'),server_manifest=read('manifest.json'),server_result_exists=(job/'server-result.json').exists(),GPU_submissions=0,ledger_written=False)
if job.exists():
 v['server_worker_sha256']=sha(job/'server-worker.py') if (job/'server-worker.py').exists() else None
 v['server_manifest_sha256']=sha(job/'manifest.json') if (job/'manifest.json').exists() else None
launch=v['server_launch'];proc=None
if launch:
 stat=Path('/proc')/str(launch['identity']['pid'])/'stat'
 if stat.exists():
  parts=stat.read_text().rsplit(') ',1)[1].split();proc=dict(pid=launch['identity']['pid'],start_ticks=int(parts[19]),state=parts[0])
v['server_original_docker_PID_live']=bool(proc and proc['start_ticks']==launch['identity']['start_ticks'] and proc['state'] not in ('Z','X')) if launch else None
probe=subprocess.run(['docker','inspect',job.name,'--format','{{.State.Running}}'],capture_output=True,text=True)
v['own_container_running']=probe.returncode==0 and probe.stdout.strip()=='true'
lk=(cache/'.wc-frozen-model-relay-server.lock').open('a')
try:fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_resource_lock_free']=True
except BlockingIOError:v['own_resource_lock_free']=False
lk.close()
if FULL:
 v['server_result']=read('server-result.json');v['independent_remote_hashes']=[]
 M=v['server_manifest'];assert M and len(M['assets'])==96
 for a in M['assets']:
  repo=cache/('models--'+a['repo_id'].replace('/','--'));blob=repo/'blobs'/a['digest'];x=dict(repo_id=a['repo_id'],path=a['path'],status='MISSING',all_original_compatibility_paths_match=False)
  if blob.is_file() and not blob.is_symlink():
   h=hashlib.sha1() if a['git_blob'] else hashlib.sha256()
   if a['git_blob']:h.update(('blob %d\0'%blob.stat().st_size).encode())
   with blob.open('rb') as f:
    for b in iter(lambda:f.read(8<<20),b''):h.update(b)
   got=h.hexdigest();links=all((repo/'snapshots'/r/a['path']).is_symlink() and (repo/'snapshots'/r/a['path']).resolve()==blob.resolve() for r in a['target_revisions'])
   x.update(digest=got,size=blob.stat().st_size,status='PASS' if got==a['digest'] and blob.stat().st_size==a['size'] else 'HASH_OR_SIZE_MISMATCH',all_original_compatibility_paths_match=links)
  v['independent_remote_hashes'].append(x)
print(json.dumps(v))
'''


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',required=True,choices=['admission','halfway','terminal','accept'])
    p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--capture',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():
        print(json.dumps(dict(existing_receipt_only=str(a.output),new_remote_queries=0)));return
    L=json.loads(a.launch_ref.read_text());job=Path(L['job'])
    if a.mode=='accept':
        c=json.loads(a.capture.read_text());r=c.get('result') or {};remote=c.get('remote') or {};sr=remote.get('server_result') or {};sm=remote.get('server_manifest') or {};sl=remote.get('server_launch') or {}
        assets=sm.get('assets',[]);ids=lambda x:(x['repo_id'],x['path'],x.get('digest'),x.get('size'))
        expected={ids(x) for x in assets};files=remote.get('independent_remote_hashes',[]);receipts=r.get('verified_files',[])
        allow={tuple(x) for x in L['allowed_missing_asset_identities']};mirrors=sm.get('modelscope_assets',[])
        checks=dict(original_source=r.get('source_revision')==L['source_revision'],original_worker=c.get('worker_sha256')==L['worker_sha256'],original_manifest=c.get('manifest_sha256')==L['manifest_sha256'],legacy_unchanged=c.get('legacy_helper_sha256')==L['legacy_helper_sha256'],original_R2_unchanged=c.get('original_R2_worker_sha256')==L['original_R2_worker_sha256'],parent_exited=c.get('original_process_live') is False,worker_success=r.get('status')=='FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS',full96_expected=len(expected)==96 and sum(x['size'] for x in assets)==21358871258,full96_worker=len(receipts)==96 and {ids(x) for x in receipts}==expected and all(x.get('status')=='REMOTE_FULL_HASH_PASS' for x in receipts),full96_independent_server=len(files)==96 and {ids(x) for x in files}==expected and all(x.get('status')=='PASS' and x.get('all_original_compatibility_paths_match') is True for x in files),registered_missing_only=all((x['repo_id'],x['path'],x['digest']) in allow for x in r.get('requested_missing_files',[])),server_worker=remote.get('server_worker_sha256')==L['server_worker_sha256'],server_source=sm.get('source_revision')==L['source_revision'] and sr.get('source_revision')==L['source_revision'],server_manifest=remote.get('server_manifest_sha256')==sl.get('manifest_sha256'),four_original_shards=len(mirrors)==4 and sr.get('status')=='FOUR_FIXED_REASON_SHARDS_FULL_HASH_PASS' and {ids(x) for x in sr.get('verified_files',[])}=={ids(x) for x in mirrors},seed_bound=sr.get('seed_prefix_hash_verified') is True and c.get('original_old_seed_preserved') is True,original_server_child_exited=remote.get('server_original_docker_PID_live') is False and remote.get('own_container_running') is False,resource_locks_free=remote.get('own_resource_lock_free') is True and c.get('local_resource_lock_free') is True,new_external_copies_removed=c.get('external_model_copy_count')==0,credentials_only_Mac=r.get('token_exported_to_server') is False,CPU_resource_only=r.get('GPU_submissions')==0 and r.get('ledger_written') is False and r.get('CUDA_initialized') is False and r.get('model_weights_loaded')==0)
        local_m=json.loads((job/'manifest.json').read_text())
        checks['local_manifest_still_unchanged']=sha(job/'manifest.json')==L['manifest_sha256']
        checks['server_preserves_original_frozen96']=sm.get('assets')==local_m['assets'] and mirrors==local_m['modelscope_assets']
        value=dict(status='FIXED96_RESOURCE_INDEPENDENTLY_ACCEPTED_NOT_FULL_ENVIRONMENT' if all(checks.values()) else 'FIXED96_INCOMPLETE_OR_FAILED_RETAINED',frozen_production_model_files_accepted=all(checks.values()),checks=checks,launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref),capture_ref=str(a.capture),capture_sha256=sha(a.capture),full_environment_accepted=False,new_host_production_CPU_accepted=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
    else:
        threshold=L['half_check_not_before_unix'] if a.mode=='halfway' else L['final_check_not_before_unix'] if a.mode=='terminal' else 0
        assert time.time()>=threshold,'Do not SSH before actual not-before'
        ps=subprocess.run(['ps','-ww','-p',str(L['identity']['pid']),'-o','lstart=,command='],capture_output=True,text=True)
        actual=ps.stdout.strip();live=ps.returncode==0 and actual[:24]==L['identity']['ps_start_and_command'][:24] and str(job/'worker.py') in actual and str(job/'manifest.json') in actual
        health=json.loads((job/'health.json').read_text()) if (job/'health.json').exists() else None
        value=dict(status='ORIGINAL_HYBRID_R3_RESOURCE_CAPTURE',mode=a.mode,observed_unix=time.time(),launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref),original_process_live=live,worker_sha256=sha(job/'worker.py'),server_worker_sha256=sha(job/'server-worker.py'),legacy_helper_sha256=sha(job/'legacy_relay.py'),original_R2_worker_sha256=sha(job/'resume_r2.py'),manifest_sha256=sha(job/'manifest.json'),external_volume_mounted=os.path.ismount('/Volumes/data'),health=health,result_exists=(job/'result.json').exists(),GPU_submissions=0,ledger_written=False)
        result=json.loads((job/'result.json').read_text()) if a.mode=='terminal' and value['result_exists'] else None
        full=bool(a.mode=='terminal' and result and result['status']=='FIXED_REGISTERED_PRODUCTION_MODEL_FILES_RELAYED_HASH_PASS' and not live)
        if a.mode=='terminal':
            value['result']=result
            value['external_model_copy_count']=sum(1 for f in job.iterdir() if f.name.endswith('.partial') or len(f.name) in (40,64))
            seed=L['seeded_partial'];old=Path(seed['parent_path'])
            value['original_old_seed_preserved']=old.exists() and old.stat().st_size==seed['bytes'] and sha(old)==seed['sha256']
            lock=(job.parent/'.wc-frozen-model-relay.lock').open('a')
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);value['local_resource_lock_free']=True
            except BlockingIOError:value['local_resource_lock_free']=False
            lock.close()
        host=json.loads(Path('configs/hosts.local.json').read_text())['four_card'];ctrl=json.loads(Path('.sync/four-card-bootstrap-transfer-20261020/owned-model-proxy-r4.json').read_text())
        code='L='+repr(L)+'\nFULL='+repr(full)+'\n'+REMOTE
        args=['ssh','-F','/dev/null','-S',ctrl['control_socket'],'-o','BatchMode=yes','-o','ControlMaster=no','-o','StrictHostKeyChecking=yes','-p',str(host['port']),host['user']+'@'+host['host'],'python3 -c '+shlex.quote(code)]
        try:
            proc=subprocess.run(args,capture_output=True,timeout=900 if full else 180)
        except subprocess.TimeoutExpired:
            value['remote_capture_status']='BOUNDED_COLLECTION_UNKNOWN_RESTORE_ORIGINAL_ONLY'
        else:
            if proc.returncode==0:
                try:value['remote']=json.loads(proc.stdout)
                except (ValueError,UnicodeDecodeError):
                    raw=Path('.sync/four-card-bootstrap-transfer-20261020')/('hybrid-r3-saved-raw-'+str(int(time.time()))+'.private.json');raw.write_bytes(proc.stdout);os.chmod(raw,0o600)
                    value['remote_capture_status']='SAVED_PARSE_UNKNOWN_OFFLINE_REPAIR_ONLY';value['private_raw_path']=str(raw)
            else:value['remote_capture_status']='CONNECTION_OR_READ_UNKNOWN_RESTORE_ORIGINAL_ONLY'
    write(a.output,value)
    print(json.dumps(dict(output=str(a.output),status=value['status'],original_process_live=value.get('original_process_live'),phase=(value.get('health') or {}).get('phase'),remote_capture_status=value.get('remote_capture_status'),complete96_accepted=value.get('frozen_production_model_files_accepted'))))


if __name__=='__main__':main()
