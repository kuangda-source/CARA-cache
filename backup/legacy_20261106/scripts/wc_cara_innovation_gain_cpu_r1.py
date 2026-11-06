"""Independent GPU-hidden CPU stages on the two registered hosts. No GPU API."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from cara_two_card_transport_r1 import four_ssh, ssh
from wc_four_card_bank24_native_transport_r4 import bridge, RUNTIME_REF

ROOT=Path(__file__).resolve().parents[1]

PREPARE=r'''
import pathlib,sys,json,base64,hashlib,subprocess,time,os,shutil
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
base=root/'.sync/cara-shared66-full-ada-r2-20261025';stage=root/'.sync'/p['stage_name']
assert not stage.exists(),'Recover existing CPU handle; never overwrite'
read=lambda f:json.loads(pathlib.Path(f).read_text())
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
original=read(base/'registration.json')
assert sha(base/'registration.json')=='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561'
assert all(sha(root/'runtime'/n)==h for n,h in original['runtime_source_sha256'].items())
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and shutil.disk_usage(root).free>=2*2**30
stage.mkdir(mode=0o700)
for n,raw in p['files'].items():
 target=stage/n;assert target.is_relative_to(stage) and '..' not in pathlib.Path(n).parts
 data=base64.b64decode(raw);assert hashlib.sha256(data).hexdigest()==p['hashes'][n]
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(stage/'cache').mkdir();(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
reg=dict(namespace='IG_ISOLATED_SOURCE_CPU_R1',stage=str(stage),source_revision=p['revision'],
 payload_sha256=p['hashes'],runtime_source_sha256=original['runtime_source_sha256'],host=p['host'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),
 process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
cmd[cmd.index('--cpus')+1]='2';cmd[cmd.index('--memory')+1]='8g'
i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
cmd=cmd[:i]+[str(stage/'scripts/check_cara_innovation_gain_cpu_r1.py'),'--output',str(stage/'IG-CPU.json'),
 '--artifacts',str(stage/'CPU-artifacts')]
assert '--gpus' not in cmd
(stage/'CPU-command.json').write_text(json.dumps(cmd))
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=pathlib.Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
v=dict(status='IG_GPU_HIDDEN_CPU_LAUNCHED',host=p['host'],project=str(root),stage=str(stage),
 source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),container=stage.name+'-cpu',
 identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=time.time(),GPU_submissions=0,ledger_written=False)
(stage/'CPU-launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

CAPTURE=r'''
import pathlib,sys,json,subprocess,time,hashlib
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=read(s/'registration.json');assert sha(s/'registration.json')==L['registration_sha256']
r=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20)
c=json.loads(r.stdout)[0] if r.returncode==0 else None
proof=s/'IG-CPU.json'
v=dict(status='IG_CPU_CAPTURE',observed_unix=time.time(),launch=L,
 all_payload_hashes_equal=all(sha(s/n)==h for n,h in reg['payload_sha256'].items()),
 runtime_hashes_equal=all(sha(pathlib.Path(L['project'])/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),
 container_state=c['State'] if c else None,device_requests=c['HostConfig']['DeviceRequests'] if c else None,
 proof=read(proof) if proof.exists() else None,proof_sha256=sha(proof) if proof.exists() else None,
 log_tail=(s/'CPU.log').read_text(errors='replace')[-6000:],GPU_submissions=0)
print(json.dumps(v))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','capture'])
    p.add_argument('--host',choices=['four_card','two_card'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--attempt',type=int,default=1);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    def remote(code,data):
        if a.host=='two_card':return ssh(code,data,docker_group=True,timeout=180)
        return four_ssh(bridge(code,json.loads((ROOT/RUNTIME_REF).read_text())),data,timeout=180)
    if a.command=='capture':
        value=remote(CAPTURE,json.loads(a.launch_ref.read_text()))
    else:
        rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]!=rev:
            raise ValueError('Publish exact CPU source first')
        paths=[p for folder in ('src','scripts','tests') for p in (ROOT/folder).rglob('*.py') if '__pycache__' not in p.parts]
        paths += [ROOT/'plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json',
                  ROOT/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json',
                  ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json']
        files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
        for n,data in files.items():
            if subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)!=data:
                raise ValueError('Uncommitted CPU dependency '+n)
        value=remote(PREPARE,dict(host=a.host,stage_name='cara-ig-cpu-'+('ada' if a.host=='four_card' else 'a6000')+
            '-r'+str(a.attempt)+'-20261027',revision=rev,
            files={n:base64.b64encode(v).decode() for n,v in files.items()},
            hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}))
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','host','stage','container_state')}))


if __name__=='__main__':main()
