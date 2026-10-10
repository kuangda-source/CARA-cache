#!/usr/bin/env python3
"""Fresh CPU-only wrapper directory; copy231 accepted methods read-only."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root=Path(__file__).resolve().parents[1];name='manifests/wc_e2_execution_cpu_r1_preregistration_20261011.json'
    reg=json.loads((root/name).read_text());c=json.loads((root/reg['method_config_ref']).read_text())
    launch=root/'reports/wc_e2_execution_cpu_r1_launch_20261011.json';assert not launch.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    for n in [name,reg['method_config_ref']]+list(reg['execution_payload_sha256']):
        assert (root/n).read_bytes()==subprocess.check_output(['git','show',revision+':'+n],cwd=root),n
    blobs={n:(root/n).read_bytes() for n,h in reg['execution_payload_sha256'].items()}
    for n,data in blobs.items():assert hashlib.sha256(data).hexdigest()==reg['execution_payload_sha256'][n]
    protocol=(root/reg['generated_protocol_cache']/'execution-protocol.json').read_bytes()
    assert hashlib.sha256(protocol).hexdigest()==reg['execution_protocol_sha256']
    blobs.update({'e2-config.json':(root/reg['method_config_ref']).read_bytes(),'registration.json':(root/name).read_bytes(),
                  'execution-protocol.json':protocol})
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as archive:
        for n,data in blobs.items():
            info=tarfile.TarInfo(n);info.size=len(data);archive.addfile(info,io.BytesIO(data))
    stem='wc-e2-execution-cpu-r1-20261011';path=root/'.sync'/(stem+'.tgz');assert not path.exists();path.write_bytes(buf.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(path),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':hashlib.sha256(buf.getvalue()).hexdigest(),
        'source':revision,'original':reg['method_original_stage'],'original_receipt_sha256':reg['method_original_receipt_sha256'],
        'method_payload':c['payload_sha256']}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/P['original'];stage=root/'.sync'/P['stem']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text());assert r['exit_code']==r['child_exit_code']==0
assert sha(old/'receipt.json')==P['original_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in [r['pid'],r['child_pid']])
assert {n:sha(old/n) for n in P['method_payload']}==P['method_payload']==r['payload_after_sha256']
assert sha(pathlib.Path(P['archive']))==P['archive_sha256'] and not stage.exists();stage.mkdir()
for n in P['method_payload']:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
with tarfile.open(P['archive']) as archive:
 for member in archive.getmembers():
  p=pathlib.PurePosixPath(member.name);assert member.isfile() and not p.is_absolute() and '..' not in p.parts
  assert not (stage/member.name).exists()
 archive.extractall(stage)
c=json.loads((stage/'e2-config.json').read_text());p=json.loads((stage/'execution-protocol.json').read_text())
assert not c['GPU_execution_selected'] and {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
assert {n:sha(stage/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']
command=['python3',str(stage/'scripts/check_wc_e2_execution_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',P['source']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
result={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source'],'archive_sha256':P['archive_sha256'],
 'config_sha256':sha(stage/'e2-config.json'),'execution_protocol_sha256':sha(stage/'execution-protocol.json'),
 'registration_sha256':sha(stage/'registration.json'),'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2400:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
