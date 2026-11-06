"""Stage one bounded GPU-hidden CPU validation; never writes a GPU ledger."""
import sys,json,base64,hashlib,argparse,subprocess
from pathlib import Path
from cara_two_card_transport_r1 import four_ssh,ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import sys,json,base64,subprocess,time,hashlib
from pathlib import Path
p=json.load(sys.stdin);r=Path('/data20t/gaokuangda/worldcache_workspace');s=r/'.sync'/p['name'];assert not s.exists();s.mkdir()
for n,b in p['files'].items():
 f=s/n;f.parent.mkdir(parents=True,exist_ok=True);raw=base64.b64decode(b);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n];f.write_bytes(raw)
reg=dict(host=p['host'],payload_sha256=p['hashes']);(s/'registration.json').write_text(json.dumps(reg))
base=r/'.sync'/p['base'];cmd=json.loads((base/'CPU-command.json').read_text());cmd=[x.replace(str(base),str(s)) for x in cmd];cmd[cmd.index('--name')+1]=s.name+'-cpu';cmd=cmd[:cmd.index('--entrypoint')+3]+[str(s/'scripts/check_wc73_admission_cpu_r1.py'),str(s)]
for n in ('torchinductor','triton','extensions','cuda','xdg'):(s/'CPU-caches'/n).mkdir(parents=True,exist_ok=True)
assert '--gpus' not in cmd and 'NVIDIA_VISIBLE_DEVICES=void' in cmd and 'CUDA_VISIBLE_DEVICES=' in cmd
(s/'CPU-command.json').write_text(json.dumps(cmd));start=time.time()
with (s/'CPU.log').open('x') as log:child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
v=dict(host=p['host'],stage=str(s),container=s.name+'-cpu',pid=child.pid,started_unix=start,GPU_submissions=0,payload_sha256=p['hashes']);(s/'CPU-launch.json').write_text(json.dumps(v));print(json.dumps(v))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',choices=['four_card','two_card'],required=True);a=p.parse_args();suffix='ada' if a.host=='four_card' else 'a6000'
 paths=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'tests/check_wc73_execution_cpu_r1.py',ROOT/'tests/check_wc73_whole_cpu_r1.py']
 files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
 data=dict(host=a.host,name='cara-wc73-admission-CPU-'+suffix+'-r2-20261027',base='cara-dev128-fullCPU-'+suffix+'-r3-20261026',files={n:base64.b64encode(b).decode() for n,b in files.items()},hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
 v=four_ssh(REMOTE,data,timeout=180) if a.host=='four_card' else ssh(REMOTE,data,docker_group=True,timeout=180)
 f=ROOT/('reports/cara_wc73_admission_'+a.host+'_CPU_launch_r2_20261027.json');assert not f.exists();f.write_text(json.dumps(v,indent=2)+'\n');print({k:v[k] for k in ('host','stage','container','started_unix')})
if __name__=='__main__':main()
