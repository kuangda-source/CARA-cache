"""Read-only host/storage/source planning profile. Never admits or launches GPU."""
import argparse
import json
from pathlib import Path

from cara_two_card_transport_r1 import four_ssh, ssh

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace')
def command(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=20)
 return dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr[-300:])
paths={}
for name in sorted({str(Path.home()),'/home/gaokuangda','/data20t/gaokuangda/worldcache_workspace'}):
 p=Path(name)
 if not p.exists():paths[name]=dict(exists=False);continue
 s=p.stat();v=os.statvfs(p)
 paths[name]=dict(device=s.st_dev,free_bytes=v.f_bavail*v.f_frsize,
  free_inodes=v.f_favail,mount=command(['findmnt','-T',name,'-J','-o','TARGET,SOURCE,FSTYPE,OPTIONS']))
sources={}
for name in d['sources']:
 p=project/'runtime'/name;sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
assets=[]
for entry in d['assets']:
 p=Path(entry['path']);s=p.stat()
 assets.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,
  expected_bytes=entry['bytes'],historical_sha256=entry['sha256'],live_rehash=False))
ledger=project/'reports/gpu-budget-v2.json'
raw=ledger.read_bytes();value=json.loads(raw)
budget=dict(sha256=hashlib.sha256(raw).hexdigest(),cap_GPUh=value['cap_gpu_hours'],
 used_GPUh=value['used_gpu_hours'],reserved_GPUh=value['reserved_gpu_hours'],
 available_GPUh=value['available_gpu_hours'],
 active_jobs=[dict(job_id=k,host=j.get('host'),status=j['status'],kind=j.get('kind'))
  for k,j in value['jobs'].items() if j['status']=='RESERVED_OR_RUNNING'])
print(json.dumps(dict(host=d['host'],hostname=socket.gethostname(),observed_unix=time.time(),
 storage=paths,block_devices=command(['lsblk','-J','-o','NAME,TYPE,ROTA,SIZE,MOUNTPOINT']),
 GPU_inventory=command(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,compute_mode,memory.used,memory.total,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']),
 supported_GPU_fields=command(['/usr/bin/nvidia-smi','--help-query-gpu']),
 runtime_sha256=sources,asset_stats=assets,ledger_snapshot=budget,
 GPU_submissions=0,ledger_written=False,mode_changes=0,storage_created=False,
 live_admission=False)))
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',choices=['four_card','two_card'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    sources = [
        'cosmos_predict2/_src/predict2/utils/model_loader.py',
        'cosmos_predict2/_src/predict2/models/text2world_model.py',
        'cosmos_predict2/_src/predict2/configs/video2world/experiment/reason_embeddings/model_2B_reason_1p1_rectified_flow.py',
        'cosmos_predict2/_src/predict2/configs/video2world/experiment/specialized_model/SFT_2B_RF.py']
    assets=json.loads((ROOT/'reports/cara_wc73_asset_recheck_20261027.json').read_text())['files'][:6]
    data=dict(host=args.host,sources=sources,assets=assets)
    value=four_ssh(REMOTE,data,timeout=90) if args.host=='four_card' else ssh(REMOTE,data,docker_group=True,timeout=90)
    with args.output.open('x') as handle:
        json.dump(value,handle,indent=2)
        handle.write('\n')
    print(json.dumps(dict(host=args.host,storage=value['storage'],ledger_snapshot=value['ledger_snapshot'],
                          GPU_inventory=value['GPU_inventory'],live_admission=False)))


if __name__=='__main__':
    main()
