#!/usr/bin/env python3
"""Deploy a separate E0 CPU package once; never restart or alter failed64."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    regpath=Path('manifests/wc_full64_partial_recovery_cpu_r1_20261011.json')
    reg=json.loads(regpath.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    result=Path('reports/wc_full64_partial_recovery_cpu_r1_launch_20261011.json')
    if result.exists():raise ValueError('Existing launch must be inspected, not redeployed')
    assert regpath.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(regpath)])
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name,expected in reg['payload_sha256'].items():
            raw=Path(name).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
            assert raw==subprocess.check_output(['git','show',revision+':'+name])
            info=tarfile.TarInfo(name);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
        raw=regpath.read_bytes();info=tarfile.TarInfo('preregistration.json');info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
    raw=stream.getvalue();packet={'archive':base64.b64encode(raw).decode(),'archive_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':revision}
    code='P='+repr(packet)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-full64-partial-recovery-cpu-r1-20261011'
assert not stage.exists()
raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for member in archive.getmembers():
  name=pathlib.PurePosixPath(member.name);assert member.isfile() and not name.is_absolute() and '..' not in name.parts
 stage.mkdir();archive.extractall(stage)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
reg=json.loads((stage/'preregistration.json').read_text());assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in reg['original_PIDs'])
runner=root/'outputs'/reg['original_run_id']/'diagnostic/receipt.json'
assert sha(runner)==reg['original_runner_sha256']
before=sha(root/'reports/budget.json')
command=['python3',str(stage/'scripts/supervise_wc_full64_partial_recovery_cpu.py'),'--project',str(root),'--stage',str(stage),'--source-revision',P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'preregistration.json'),'payload_files':len(reg['payload_sha256']),
 'original_failed_card_unchanged':True,'planned_original_slots':64,'maximum_saved_complete_paths':14,
 'maximum_numerical_paired_scores':8,'command':command,'budget_before_sha256':before,'GPU_submissions':0,
 'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    value=json.loads(call.stdout);result.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
