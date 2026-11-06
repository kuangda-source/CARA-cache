"""Separate R2 CPU directory; readonly398 plus explicit GPU-only startup inputs."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root=Path(__file__).resolve().parents[1];name='manifests/wc_p_reference_same_state_production_cpu_r1_preregistration_20261011.json'
    reg=json.loads((root/name).read_text());c=json.loads((root/reg['config_ref']).read_text())
    target=root/'reports/wc_p_reference_same_state_production_cpu_r1_launch_20261011.json';assert not target.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    for n in [name,reg['config_ref']]+reg['new_local_files']:
        assert (root/n).read_bytes()==subprocess.check_output(['git','show',revision+':'+n],cwd=root),n
    blobs={n:(root/n).read_bytes() for n in reg['new_local_files']}
    for n,raw in blobs.items():assert hashlib.sha256(raw).hexdigest()==c['payload_sha256'][n]
    blobs['p-reference-requests.jsonl']=(root/reg['generated_requests_cache']).read_bytes()
    assert hashlib.sha256(blobs['p-reference-requests.jsonl']).hexdigest()==c['payload_sha256']['p-reference-requests.jsonl']
    blobs.update({'registration.json':(root/name).read_bytes(),'p-reference-same-state-config.json':(root/reg['config_ref']).read_bytes()})
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for n,raw in blobs.items():
            entry=tarfile.TarInfo(n);entry.size=len(raw);archive.addfile(entry,io.BytesIO(raw))
    stem='wc-p-reference-same-state-production-cpu-r1-20261011';archive=root/'.sync'/(stem+'.tgz')
    assert not archive.exists();archive.write_bytes(buffer.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(archive),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':hashlib.sha256(buffer.getvalue()).hexdigest(),
        'revision':revision,'original':reg['original_stage'],'original_receipt_sha256':reg['original_receipt_sha256'],
        'copies':reg['copies_readonly_sha256']}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/P['original'];s=root/'.sync'/P['stem']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text());assert r['exit_code']==0 and r['status']=='P_REFERENCE_SAME_STATE_COMPLETE_CPU_PASS_PENDING_INDEPENDENT_CAPTURE'
assert sha(old/'receipt.json')==P['original_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in [r['pid'],r['child_pid']])
assert {n:sha(old/n) for n in P['copies']}==P['copies']==r['payload_after_sha256']
assert not s.exists() and sha(pathlib.Path(P['archive']))==P['archive_sha256'];s.mkdir()
for n in P['copies']:
 target=s/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
with tarfile.open(P['archive']) as archive:
 for member in archive.getmembers():
  p=pathlib.PurePosixPath(member.name);assert member.isfile() and not p.is_absolute() and '..' not in p.parts
  assert not (s/member.name).exists()
 archive.extractall(s)
c=json.loads((s/'p-reference-same-state-config.json').read_text());assert not c['GPU_execution_selected']
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']
command=['python3',str(s/'scripts/check_wc_p_reference_same_state_production_cpu_r1.py'),'--project',str(root),'--stage',str(s),'--source-revision',P['revision']]
with (s/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
value={'status':'P_REFERENCE_ACTUAL_PRODUCTION_CPU_DISPATCHED_NOT_GPU','stage':str(s),'source_revision':P['revision'],
 'supervisor_pid':child.pid,'archive_sha256':P['archive_sha256'],'config_sha256':sha(s/'p-reference-same-state-config.json'),
 'registration_sha256':sha(s/'registration.json'),'payload_files':len(c['payload_sha256']),
 'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    result=json.loads(call.stdout);target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
