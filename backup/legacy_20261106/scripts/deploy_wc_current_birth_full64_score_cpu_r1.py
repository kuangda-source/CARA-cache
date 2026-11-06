#!/usr/bin/env python3
"""Deploy the source-frozen whole64 CPU scorer against its original GPU handles."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    reg_path=Path('manifests/wc_current_birth_full64_score_cpu_r1_preregistration_20261010.json')
    reg=json.loads(reg_path.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert reg_path.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(reg_path)])
    result=Path('reports/wc_current_birth_full64_score_cpu_r1_launch_20261010.json');assert not result.exists()
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for n,v in reg['payload_sha256'].items():
            raw=Path(n).read_bytes();assert hashlib.sha256(raw).hexdigest()==v
            assert raw==subprocess.check_output(['git','show',revision+':'+n])
            item=tarfile.TarInfo(n);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
        raw=reg_path.read_bytes();item=tarfile.TarInfo('score-preregistration.json');item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
    raw=stream.getvalue();packet={'archive':base64.b64encode(raw).decode(),'archive_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':revision}
    code='P='+repr(packet)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-current-birth-full64-score-cpu-r1-20261010'
assert not stage.exists();raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for m in archive.getmembers():
  n=pathlib.PurePosixPath(m.name);assert m.isfile() and not n.is_absolute() and '..' not in n.parts
 stage.mkdir();archive.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'score-preregistration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
L=reg['original_launch'];original_stage=pathlib.Path(L['stage'])
assert sha(original_stage/'current-birth-full64-config.json')==L['config_sha256']
assert pathlib.Path('/proc/'+str(L['supervisor_pid'])).exists() or pathlib.Path(L['post_CPU_stage'],'receipt.json').is_file()
before=sha(root/'reports/budget.json')
command=['python3',str(stage/'scripts/supervise_wc_current_birth_full64_score_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'score-preregistration.json'),'payload_files':len(reg['payload_sha256']),
 'original_GPU_run_id':L['run_id'],'planned_scope':reg['scope_counts'],'command':command,
 'budget_before_sha256':before,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    data=json.loads(call.stdout);result.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))


if __name__=='__main__':main()
