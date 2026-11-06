#!/usr/bin/env python3
"""Fresh startup CPU directory; preserve accepted historical method bytes."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root=Path(__file__).resolve().parents[1];ref='manifests/wc_e2_startup_cpu_r2_preregistration_20261011.json'
    reg=json.loads((root/ref).read_text());c=json.loads((root/reg['method_config_ref']).read_text())
    target=root/'reports/wc_e2_startup_cpu_r2_launch_20261011.json';assert not target.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    for n in [ref,reg['method_config_ref']]+list(reg['new_payload_sha256']):
        assert (root/n).read_bytes()==subprocess.check_output(['git','show',revision+':'+n],cwd=root),n
    blobs={n:(root/n).read_bytes() for n in reg['new_payload_sha256']}
    for n,data in blobs.items():assert hashlib.sha256(data).hexdigest()==reg['new_payload_sha256'][n]
    protocol=(root/reg['generated_protocol_cache']/'execution-protocol.json').read_bytes()
    assert hashlib.sha256(protocol).hexdigest()==reg['execution_protocol_sha256']
    blobs.update({'registration.json':(root/ref).read_bytes(),'execution-protocol.json':protocol})
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as archive:
        for n,data in blobs.items():
            info=tarfile.TarInfo(n);info.size=len(data);archive.addfile(info,io.BytesIO(data))
    stem='wc-e2-startup-cpu-r2-20261011';path=root/'.sync'/(stem+'.tgz');assert not path.exists();path.write_bytes(buf.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(path),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':hashlib.sha256(buf.getvalue()).hexdigest(),
            'source':revision,'reg':reg,'method_payload':c['payload_sha256']}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');reg=P['reg']
old=root/reg['original_execution_stage'];stage=root/'.sync'/P['stem'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'execution-CPU-receipt.json').read_text())
assert r['exit_code']==r['last_child_exit_code']==0 and r['source_revision']==reg['original_execution_source_revision']
assert sha(old/'execution-CPU-receipt.json')==reg['original_execution_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in [r['pid'],r['child_pid']])
assert sha(old/'execution-protocol.json')==reg['original_execution_protocol_sha256']
original={**P['method_payload'],**reg['original_execution_payload_sha256']}
assert {n:sha(old/n) for n in original}==original
assert sha(old/'e2-config.json')==reg['method_config_sha256']
assert sha(pathlib.Path(P['archive']))==P['archive_sha256'] and not stage.exists();stage.mkdir()
for n in list(original)+['e2-config.json']:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
with tarfile.open(P['archive']) as archive:
 for member in archive.getmembers():
  p=pathlib.PurePosixPath(member.name);assert member.isfile() and not p.is_absolute() and '..' not in p.parts
  assert not (stage/member.name).exists()
 archive.extractall(stage)
c=json.loads((stage/'e2-config.json').read_text());p=json.loads((stage/'execution-protocol.json').read_text())
assert not c['GPU_execution_selected'] and {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
assert {n:sha(stage/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']==reg['execution_payload_sha256']
command=['python3',str(stage/'scripts/check_wc_e2_startup_cpu_r2.py'),'--project',str(root),'--stage',str(stage),'--source-revision',P['source']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source'],'archive_sha256':P['archive_sha256'],
 'config_sha256':sha(stage/'e2-config.json'),'execution_protocol_sha256':sha(stage/'execution-protocol.json'),
 'registration_sha256':sha(stage/'registration.json'),'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    failure=root/'.sync/wc-e2-startup-r2-deployment-transport.json';assert not failure.exists()
    failure.write_text(json.dumps({'returncode':call.returncode,'stdout':call.stdout,'stderr':call.stderr},indent=2)+'\n')
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout);target.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
