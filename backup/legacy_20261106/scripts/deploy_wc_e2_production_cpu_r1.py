#!/usr/bin/env python3
"""Copy the accepted original E2 payload and deploy one new CPU-only card."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    config=root/'configs/wc_e2_production_r1_20261011.json'
    registration=root/'manifests/wc_e2_production_cpu_r1_preregistration_20261011.json'
    launch=root/'reports/wc_e2_production_cpu_r1_launch_20261011.json';assert not launch.exists()
    reg=json.loads(registration.read_text());c=json.loads(config.read_text());assert not c['GPU_execution_selected']
    assert sha(config)==reg['config_sha256'] and c['payload_sha256']==reg['payload_sha256']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    for p in (config,registration):assert p.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(p.relative_to(root))],cwd=root)
    blobs={}
    for n in reg['new_local_files']:
        p=root/n;raw=p.read_bytes();assert sha(p)==c['payload_sha256'][n]
        assert raw==subprocess.check_output(['git','show',revision+':'+n],cwd=root)
        blobs[n]=raw
    n=reg['generated_requests_file'];p=root/reg['generated_requests_cache']/n
    assert sha(p)==c['payload_sha256'][n];blobs[n]=p.read_bytes()
    blobs['e2-config.json']=config.read_bytes();blobs['registration.json']=registration.read_bytes()
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for n,data in blobs.items():
            item=tarfile.TarInfo(n);item.size=len(data);archive.addfile(item,io.BytesIO(data))
    stem='wc-e2-production-cpu-r1-20261011';local=root/'.sync'/(stem+'.tgz')
    assert not local.exists();local.write_bytes(buffer.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(local),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':sha(local),'revision':revision,
        'copies':reg['copies_readonly_sha256'],'old_stage':reg['copy_original_E2_CPU_stage'],
        'old_source':reg['copy_original_E2_CPU_source'],'config_sha256':sha(config)}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync'/P['stem'];old=root/P['old_stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text());original=json.loads((old/'registration.json').read_text())
assert r['exit_code']==r['child_exit_code']==0 and r['status']=='E2_FULL76_CPU_EXIT0_NOT_REAL_MODEL_OR_LATENCY'
assert r['source_revision']==P['old_source'] and not any(pathlib.Path('/proc/'+str(p)).exists() for p in [r['pid'],r['child_pid']])
assert P['copies']==original['payload_sha256']==r['payload_after_sha256']
assert {n:sha(old/n) for n in P['copies']}==P['copies']
assert sha(pathlib.Path(P['archive']))==P['archive_sha256'] and not stage.exists();stage.mkdir()
for n,h in P['copies'].items():
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
with tarfile.open(P['archive']) as archive:
 for item in archive.getmembers():
  name=pathlib.PurePosixPath(item.name)
  assert item.isfile() and not name.is_absolute() and '..' not in name.parts
  assert not (stage/item.name).exists()
 archive.extractall(stage)
c=json.loads((stage/'e2-config.json').read_text());assert not c['GPU_execution_selected']
assert sha(stage/'e2-config.json')==P['config_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
assert json.loads((root/'reports/budget.json').read_text())['cap_gpu_hours']==c['cumulative_cap_GPUh']
command=['python3',str(stage/'scripts/supervise_wc_e2_production_cpu_r1.py'),'--project',str(root),
 '--stage',str(stage),'--source-revision',P['revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
result={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['revision'],
 'archive_sha256':P['archive_sha256'],'config_sha256':P['config_sha256'],
 'registration_sha256':sha(stage/'registration.json'),'payload_files':len(c['payload_sha256']),
 'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2200:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
