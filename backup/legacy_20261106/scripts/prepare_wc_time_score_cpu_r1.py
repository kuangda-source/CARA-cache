"""Fresh CPU-only score overlay; immutable previous audit reused by SHA."""
import argparse,base64,json,hashlib
from pathlib import Path
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import json,sys,base64,hashlib,shutil,subprocess,time,zipfile
from pathlib import Path
p=json.load(sys.stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');stage=root/'.sync'/('wc-time-score-CPU-'+p['host']+'-r1-20261027')
if stage.exists():
 t=stage/'terminal.json'
 if t.exists():print(t.read_text());raise SystemExit(0)
 raise ValueError('Recover existing CPU stage, never replay')
base=root/'.sync'/('cara-dev128-fullCPU-ada-r3-20261026' if p['host']=='four_card' else 'cara-dev128-fullCPU-a6000-r3-20261026')
source=root/'.sync/wc-time-score-assets-r1' if p['host']=='four_card' else Path('/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-native-lpips-audit-r1-20261027')
stage.mkdir();(stage/'torch/hub/checkpoints').mkdir(parents=True);(stage/'site').mkdir()
for name,expected in p['asset_sha256'].items():
 f=source/name
 if name.startswith('vgg') and p['host']=='two_card':f=source/'torch/hub/checkpoints'/name
 assert hashlib.sha256(f.read_bytes()).hexdigest()==expected,name
 dest=stage/name if name=='piq.whl' else stage/'torch/hub/checkpoints'/name
 shutil.copyfile(f,dest)
alex=root/'cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth';assert hashlib.sha256(alex.read_bytes()).hexdigest()==p['alex_sha256'];(stage/'torch/hub/checkpoints'/alex.name).symlink_to(alex)
with zipfile.ZipFile(stage/'piq.whl') as z:
 for n in z.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
 z.extractall(stage/'site')
script=base64.b64decode(p['script']);assert hashlib.sha256(script).hexdigest()==p['script_sha256'];(stage/'worker.py').write_bytes(script)
cmd=json.loads((base/'CPU-command.json').read_text());cmd=[x.replace(str(base),str(stage)) for x in cmd];cmd[cmd.index('--name')+1]=stage.name+'-cpu'
cmd=cmd[:cmd.index('--entrypoint')+3]+[str(stage/'worker.py'),str(stage)]
assert '--gpus' not in cmd and 'NVIDIA_VISIBLE_DEVICES=void' in cmd and 'CUDA_VISIBLE_DEVICES=' in cmd
start=time.time();r=subprocess.run(cmd,capture_output=True,text=True,timeout=210)
v=dict(host=p['host'],stage=str(stage),exit_code=r.returncode,wall_seconds=time.time()-start,asset_sha256=p['asset_sha256'],script_sha256=p['script_sha256'],proof=json.loads((stage/'CPU-proof.json').read_text()) if (stage/'CPU-proof.json').exists() else None,stderr=r.stderr[-1800:],stdout=r.stdout[-500:],GPU_submissions=0)
(stage/'terminal.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',required=True,choices=['four_card','two_card']);a=p.parse_args()
 old=json.loads((ROOT/'reports/wc_native_lpips_official_rescore_accepted_20261027.json').read_text());source=old['source_hashes'];weights=old['result']['weight_sha256']
 assets={'piq.whl':source['piq.whl'],'lpips_weights.pt':source['lpips_weights.pt'],'vgg16-397923af.pth':next(h for n,h in weights.items() if 'vgg16' in n)}
 raw=(ROOT/'scripts/check_wc_time_score_cpu_r1.py').read_bytes();data=dict(host=a.host,asset_sha256=assets,alex_sha256=next(h for n,h in weights.items() if 'alexnet' in n),script=base64.b64encode(raw).decode(),script_sha256=hashlib.sha256(raw).hexdigest())
 r=four_ssh(REMOTE,data,timeout=240) if a.host=='four_card' else ssh(REMOTE,data,docker_group=True,timeout=240)
 out=ROOT/('reports/cara_wc_time_score_'+a.host+'_CPU_r1_20261027.json');assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n');print({k:r[k] for k in ('host','exit_code','wall_seconds','stderr')})
if __name__=='__main__':main()
