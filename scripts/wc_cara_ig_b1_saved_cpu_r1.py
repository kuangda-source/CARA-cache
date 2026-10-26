"""Launch/capture one GPU-hidden saved-tensor analysis after B1 settlement."""
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from wc_cara_ig_b1_gpu_r2 import ROOT, remote, read, write
from analyze_cara_ig_b1_complete_r1 import analyze

LAUNCH = r'''
import pathlib,json,sys,os,subprocess,time,shutil,base64,hashlib
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
base=pathlib.Path(p['CPU']['launch']['stage']);stage=root/'.sync/cara-ig-b1-saved-analysis-r1-20261027'
source=pathlib.Path(p['capture']['stage']);out=root/'outputs'/p['capture']['files']['auth']['value']['run_id']
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
sys.path[:0]=[str(source/'src'),str(source/'scripts')]
from wcomr.gpu_budget_pool_v2 import same_live_process,process_identity
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.innovation_gain_b1_card_r2 import validate
validate(root,source)
for k,n in [('billing','billing.json'),('B1-results.json','B1-results.json'),('post-results.json','post-results.json')]:
 assert sha(out/n)==p['capture']['files'][k]['sha256']
sup=read(out/'supervisor.json');assert not same_live_process(sup['child_identity'])
assert not observe(p['capture']['files']['auth']['value']['gpu_uuid'])['compute_apps']
assert read(out/'exclusive-monitor-final.json')['accepted']
assert sha(base/'registration.json')==p['CPU']['launch']['registration_sha256']
assert not stage.exists(),'Recover the existing analysis; never relaunch or overwrite'
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and {4,5}<=os.sched_getaffinity(0)
stage.mkdir(mode=0o700);reg=read(base/'registration.json');hashes={}
for n,h in reg['payload_sha256'].items():
 assert sha(base/n)==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target);hashes[n]=h
for n,b64 in p['files'].items():
 raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
 (stage/n).write_bytes(raw);hashes[n]=p['hashes'][n]
(stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
registration=dict(source_revision=p['revision'],payload_sha256=hashes,original_runtime_sha256=reg['runtime_source_sha256'],
 original_B1_result_sha256=p['capture']['files']['B1-results.json']['sha256'],
 original_B1_billing_sha256=p['capture']['files']['billing']['sha256'],central_settlement=p['settlement'])
(stage/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts'),str(root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022')]
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
cmd[cmd.index('--cpus')+1]='2';cmd[cmd.index('--memory')+1]='8g';cmd[2:2]=['--cpuset-cpus','4,5']
i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
cmd=cmd[:i]+[str(stage/'scripts/analyze_cara_ig_b1_saved_r1.py'),'--assets',str(out/'assets'),
 '--original-assets',str(root/'outputs/cara-ig-b1-r1-20261027/assets'),'--output',str(stage/'analysis.json')]
assert '--gpus' not in cmd
(stage/'command.json').write_text(json.dumps(cmd))
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
v=dict(status='B1_SAVED_CPU_ANALYSIS_LAUNCHED',stage=str(stage),container=stage.name+'-cpu',
 registration_sha256=sha(stage/'registration.json'),identity=process_identity(child.pid),started_unix=time.time(),
 GPU_submissions=0,source_revision=p['revision'])
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

CAPTURE = r'''
import pathlib,json,sys,hashlib,subprocess,time
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(s/'registration.json')==L['registration_sha256'];reg=json.loads((s/'registration.json').read_text())
container=json.loads(subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,check=True).stdout)[0]
p=s/'analysis.json'
v=dict(status='B1_SAVED_CPU_ANALYSIS_CAPTURE',observed_unix=time.time(),launch=L,
 original_B1_result_sha256=reg['original_B1_result_sha256'],original_B1_billing_sha256=reg['original_B1_billing_sha256'],
 source_hashes_equal=all(sha(s/n)==h for n,h in reg['payload_sha256'].items()),
 container_state=container['State'],device_requests=container['HostConfig']['DeviceRequests'],
 result=json.loads(p.read_text()) if p.exists() else None,result_sha256=sha(p) if p.exists() else None,
 log_tail=(s/'CPU.log').read_text(errors='replace')[-2000:],GPU_submissions=0)
print(json.dumps(v))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['launch','capture'])
    for n in ('cpu','terminal','settlement','prior','launch-ref','output'):
        p.add_argument('--'+n,type=Path,required=n=='output')
    a=p.parse_args();assert not a.output.exists()
    if a.command=='capture':
        value=remote('two_card',CAPTURE,read(a.launch_ref))
    else:
        terminal,settlement,prior=read(a.terminal),read(a.settlement),read(a.prior)
        analyze(terminal,settlement,prior)
        rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==rev
        names=['scripts/analyze_cara_ig_b1_saved_r1.py','scripts/analyze_cara_ig_b1_raw_r1.py']
        files={n:(ROOT/n).read_bytes() for n in names}
        assert all(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)==b for n,b in files.items())
        value=remote('two_card',LAUNCH,dict(CPU=read(a.cpu),capture=terminal,settlement=settlement,revision=rev,
            files={n:base64.b64encode(b).decode() for n,b in files.items()},
            hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}))
    write(a.output,value)
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
