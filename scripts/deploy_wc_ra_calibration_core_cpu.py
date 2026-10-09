#!/usr/bin/env python3
"""Deploy one committed coarse-calibration core CPU stage; never write GPU/ledger state."""
import base64
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('r1','r2'),default='r1');args=parser.parse_args()
    assert args.attempt == 'r1'
    ref=Path('manifests/wc_ra_calibration_core_cpu_r1_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','show',revision+':'+str(ref)])==ref.read_bytes()
    dest=Path('reports/wc_ra_calibration_core_cpu_'+args.attempt+'_launch_20261010.json');assert not dest.exists()
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for name,digest in reg['payload_sha256'].items():
            raw=Path(name).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
            assert subprocess.check_output(['git','show',revision+':'+name])==raw
            info=tarfile.TarInfo(name);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
        raw=ref.read_bytes();info=tarfile.TarInfo('ra-coarse-cal-core-preregistration.json');info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
    packet={'source_revision':revision,'attempt':args.attempt,'archive':base64.b64encode(buffer.getvalue()).decode(),
            'archive_sha256':hashlib.sha256(buffer.getvalue()).hexdigest()}
    source='P='+repr(packet)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/('.sync/wc-ra-calibration-core-cpu-'+P['attempt']+'-20261010')
assert not stage.exists();raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for item in archive.getmembers():
  path=pathlib.PurePosixPath(item.name);assert item.isfile() and not path.is_absolute() and '..' not in path.parts
 stage.mkdir();archive.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reg=json.loads((stage/'ra-coarse-cal-core-preregistration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
command=['python3',str(stage/'scripts/supervise_wc_ra_calibration_core_cpu.py'),'--project',str(root),'--stage',str(stage),
 '--runtime',str(root/'runtime'),'--source-revision',P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2'),start_new_session=True)
launch={'stage':str(stage),'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'supervisor_pid':child.pid,'command':command,'payload_files':len(reg['payload_sha256']),
 'registration_sha256':sha(stage/'ra-coarse-cal-core-preregistration.json'),'CPU_scope':reg['CPU_scope'],
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    result=json.loads(call.stdout);dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
