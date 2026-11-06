#!/usr/bin/env python3
"""Once-only original storage-worker capture and offline acceptance; no execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

REMOTE = r'''
import os,json,pathlib,hashlib,time,stat,fcntl
ops=pathlib.Path(L['ops_dir'])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
launch=json.loads((ops/'launch.json').read_text())
assert launch==L and sha(ops/'maintain_wc_user_storage_r1.py')==L['script_sha256']
result=json.loads((ops/'result.json').read_text())
assert result['run_id']==L['run_id'] and result['script_sha256']==L['script_sha256']
process={'exists':False}
p=pathlib.Path('/proc')/str(L['pid'])/'stat'
if p.is_file():
 a=p.read_text().rsplit(')',1)[1].split();process=dict(exists=True,state=a[0],start_ticks=int(a[19]),same_identity=int(a[19])==L['start_ticks'])
value=dict(observed_unix=time.time(),mode=MODE,launch=launch,worker_source_sha256=L['script_sha256'],process=process,new_executions=0,server_files_modified=False)
if MODE=='halfway':
 value['progress']={k:result.get(k) for k in ['status','phase','updated_unix','hashed_bytes','error_type','error']}
 value['completed_action_kinds']=[a['kind'] for a in result.get('actions',[])]
else:
 value['result']=result
 if result['status']=='COMPLETED_STORAGE_MIGRATION_VERIFIED':
  import sys
  sys.dont_write_bytecode=True;sys.path.insert(0,str(ops));import maintain_wc_user_storage_r1 as worker
  checks={};manifests={}
  for action in result['actions']:
   if action['kind']!='MODEL_TREE_COPIED_HASHED_AND_MIGRATED':continue
   target=pathlib.Path(action['target']);source=pathlib.Path(action['source']);name=target.name
   p=ops/(name+'-private-file-manifest.json');assert sha(p)==action['private_manifest_sha256']
   expected=json.loads(p.read_text());metadata_ok=True
   for rel,entry in expected.items():
    a=source/rel;b=target/rel;s=b.lstat();t=a.lstat()
    assert (s.st_dev,s.st_ino)==(t.st_dev,t.st_ino)
    if entry['type']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==entry['bytes']
    elif entry['type']=='directory':assert stat.S_ISDIR(s.st_mode)
    elif entry['type']=='symlink':assert os.readlink(b)==entry['target'] and os.readlink(a)==entry['target']
   manifests[name]=dict(private_manifest_sha256=sha(p),entries=len(expected),all_metadata_and_old_path_inodes_match=True,worker_full_source_destination_SHA256_match=action['full_SHA256_tree_match'])
  for path,info in result['original_path_bindings'].items():
   p=pathlib.Path(path);target=pathlib.Path(info['target'])
   checks[path]=dict(is_symlink=p.is_symlink(),samefile=os.path.samefile(p,target),on_data=p.stat().st_dev==worker.DATA.stat().st_dev,readable_searchable=os.access(p,os.R_OK|os.X_OK))
  runtime={p:worker.digest(p) for p in result['preserved_runtime_files_before']}
  value['independent_checks']=dict(original_path_checks=checks,model_manifest_checks=manifests,
   runtime_fingerprints_match=runtime==result['preserved_runtime_files_before'],Nano_models_absent=not worker.NANO.exists(),Nano_download_records_retained=(worker.HOME/'cosmos3_nano/download').is_dir(),current_capacity=worker.capacity(),current_home_allocated=worker.du(worker.HOME))
  with (ops/'maintenance.lock').open('r') as h:
   try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);value['maintenance_lock_free']=True;fcntl.flock(h,fcntl.LOCK_UN)
   except BlockingIOError:value['maintenance_lock_free']=False
 if result['status'].startswith('FAILED'):
  value['worker_log_tail']=(ops/'worker.log').read_text(errors='replace')[-16000:]
print(json.dumps(value))
'''


def accept(value):
    r = value['result']; checks = value['independent_checks']
    assert r['status'] == 'COMPLETED_STORAGE_MIGRATION_VERIFIED'
    assert value['maintenance_lock_free'] and not value['process'].get('same_identity', False)
    assert value['worker_source_sha256'] == value['launch']['script_sha256'] == r['script_sha256']
    assert len(r['actions']) == 5 and r['new_GPU_submissions'] == 0
    assert sum(a['kind']=='MODEL_TREE_COPIED_HASHED_AND_MIGRATED' for a in r['actions']) == 2
    assert sum(a['kind']=='EMPTY_PACKAGE_CACHE_REBUILT' for a in r['actions']) == 2
    assert checks['runtime_fingerprints_match'] and checks['Nano_models_absent'] and checks['Nano_download_records_retained']
    assert len(checks['original_path_checks']) == 4
    assert all(all(v.values()) for v in checks['original_path_checks'].values())
    assert len(checks['model_manifest_checks']) == 2
    assert all(v['all_metadata_and_old_path_inodes_match'] and v['worker_full_source_destination_SHA256_match'] for v in checks['model_manifest_checks'].values())
    return dict(status='COMPLETED_STORAGE_MIGRATION_VERIFIED', original_worker_accepted=True,
                source_SHA256=value['worker_source_sha256'], run_id=r['run_id'],
                home_allocated_before=r['home_allocated_before'], home_allocated_after=checks['current_home_allocated'],
                home_allocated_reduction=r['home_allocated_before']-checks['current_home_allocated'],
                original_paths=r['original_path_bindings'], current_capacity=checks['current_capacity'],
                Nano_models_deleted=True, package_caches_rebuilt=True,
                HF_and_Wan_full_copy_hashes_verified=True, installed_runtime_files_preserved=True,
                new_GPU_submissions=0, original_experiments_restarted=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--launch-ref', type=Path)
    ap.add_argument('--mode', choices=['halfway','terminal','accept'], required=True)
    ap.add_argument('--capture', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--maintenance-marker', type=Path)
    a = ap.parse_args()
    assert not a.output.exists(), 'Preserve original receipt; inspect it offline'
    if a.mode == 'accept':
        raw = a.capture.read_bytes(); result = accept(json.loads(raw))
        result.update(capture_ref=str(a.capture), capture_sha256=hashlib.sha256(raw).hexdigest())
        with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        if a.maintenance_marker:
            marker=json.loads(a.maintenance_marker.read_text());marker.update(status=result['status'],acceptance_ref=str(a.output),no_new_GPU_until_storage_acceptance=False)
            a.maintenance_marker.write_text(json.dumps(marker,indent=2)+'\n')
        print(json.dumps(result)); return
    L = json.loads(a.launch_ref.read_text())['dispatch']
    key = 'halfway_not_before_unix' if a.mode == 'halfway' else 'terminal_not_before_unix'
    assert time.time() >= L[key], 'Before original once-only observation time'
    code = 'L='+repr(L)+'\nMODE='+repr(a.mode)+'\n'+REMOTE
    c = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
                        'gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=90)
    if c.returncode:
        value = dict(status='STORAGE_OBSERVATION_UNKNOWN_NOT_WORKER_TERMINAL',error=c.stderr.decode(errors='replace'),launch=L)
        with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
        raise RuntimeError(value['error'])
    value = json.loads(c.stdout)
    with a.output.open('xb') as f:f.write(c.stdout)
    print(json.dumps({k:value[k] for k in value if k not in ['result','independent_checks']}))


if __name__ == '__main__':
    main()
