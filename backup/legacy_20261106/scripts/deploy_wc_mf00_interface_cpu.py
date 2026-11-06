#!/usr/bin/env python3
"""Transfer the exact committed new Common source and launch one CPU check.

No CUDA or GPU dispatch; the fresh directory cannot overwrite a used identity.
Selected validation is a second, independent CPU directory with unchanged source
payload and a source-bound prior production CPU receipt.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    p=argparse.ArgumentParser();p.add_argument('--selected',action='store_true');a=p.parse_args()
    phase='selected' if a.selected else 'production'
    cfg=Path('configs/wc_mf00_interface_'+phase+'_r1_20261010.json')
    c=json.loads(cfg.read_text());assert c['GPU_execution_selected']==a.selected
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','show',revision+':'+str(cfg)])==cfg.read_bytes()
    prefix='reports/wc_mf00_interface_'+phase+'_cpu_r1_'
    launch=Path(prefix+'launch_20261010.json');assert not launch.exists()
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w:gz') as archive:
        for name,digest in c['payload_sha256'].items():
            local=Path('.sync/mf00-interface-inputs-r1')/name
            raw=local.read_bytes() if local.is_file() else Path(name).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==digest,name
            if Path(name).is_file():assert raw==subprocess.check_output(['git','show',revision+':'+name]),name
            item=tarfile.TarInfo(name);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
        raw=cfg.read_bytes();item=tarfile.TarInfo('native-policy-config.json');item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
        if a.selected and c['single_job_exception_authority'] is not None:
            authority=c['single_job_exception_authority'];raw=Path(authority['ref']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==authority['sha256']
            assert raw==subprocess.check_output(['git','show',revision+':'+authority['ref']])
            item=tarfile.TarInfo(authority['ref']);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
    content=data.getvalue();archive_sha=hashlib.sha256(content).hexdigest()
    packet={'archive':base64.b64encode(content).decode(),'archive_sha256':archive_sha,'source_revision':revision,'phase':phase}
    source='P='+repr(packet)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/('.sync/wc-mf00-interface-'+P['phase']+'-cpu-r1-20261010')
assert not stage.exists();raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for item in archive.getmembers():
  path=pathlib.PurePosixPath(item.name)
  assert item.isfile() and not path.is_absolute() and '..' not in path.parts
 stage.mkdir();archive.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((stage/'native-policy-config.json').read_text())
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
budget_sha=sha(root/'reports/budget.json')
assert sha(stage/'budget-at-preparation.json')==budget_sha
deployment={'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'payload_files':len(c['payload_sha256']),'budget_before_sha256':budget_sha,'phase':P['phase'],'GPU_submissions':0}
(stage/'deployment.json').write_text(json.dumps(deployment,indent=2)+'\n')
command=['python3',str(stage/'scripts/supervise_wc_mf00_interface_production_cpu.py'),
 '--project',str(root),'--stage',str(stage),'--source-revision',P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
result={**deployment,'stage':str(stage),'supervisor_pid':child.pid,'config_sha256':sha(stage/'native-policy-config.json'),
 'command':command,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
