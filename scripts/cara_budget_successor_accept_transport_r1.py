"""Once-only CPU invocation of the original successor14 complete reader.

The numerical reader comes exclusively from the original immutable GPU stage.
An existing CPU directory is recovery-only, including unknown launch outcomes.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from cara_two_card_transport_r1 import password

ROOT = Path(__file__).resolve().parents[1]
CPU_NAME = 'cara-budget-successor-accept-CPU-a6000-r1-20261101'
WORKER = r'''
import json,os,pathlib,subprocess,sys,time
cpu=pathlib.Path(sys.argv[1]);plan=json.loads((cpu/'plan.json').read_text())
sys.path[:0]=[plan['stage']+'/src',plan['stage']+'/scripts']
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record
with (cpu/'reader.log').open('xb') as log:
 child=subprocess.Popen(plan['reader_command'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 create_record(cpu/'reader-start.json',dict(identity=bind_original_process(child.pid),started_unix=time.time(),command=plan['reader_command']))
 timed_out=False
 try:code=child.wait(timeout=3600)
 except subprocess.TimeoutExpired:
  timed_out=True;os.killpg(child.pid,15)
  try:code=child.wait(timeout=30)
  except subprocess.TimeoutExpired:os.killpg(child.pid,9);code=child.wait()
 create_record(cpu/'reader-terminal.json',dict(ended_unix=time.time(),exit_code=code,timed_out=timed_out))
sys.exit(code if code>=0 else 1)
'''
REMOTE = r'''
import base64,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
stage=root/'.sync/cara-budget-calibration-GPU-a6000-r3-20261031';cpu=root/'.sync'/p['cpu_name'];name=p['cpu_name']+'-cpu'
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(stage/'GPU-launch.json')==p['launch_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==p['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
from wcomr.cara_budget_original_handles_r1 import observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record
def inspect():
 r=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=20)
 if r.returncode:
  assert 'No such object' in r.stderr or 'No such container' in r.stderr,r.stderr
  return None
 return json.loads(r.stdout)[0]
existing=inspect();created=False
if p['action']=='prepare' and not cpu.exists():
 assert existing is None,'Recover existing original CPU container'
 lifecycle=released_lifecycle(p['capture'],p['launch_sha256'],p['settlement'])
 assert lifecycle['container_exit_success'] and lifecycle['GPU_released'] and lifecycle['cost_settled']
 memory={l.split(':')[0]:int(l.split()[1]) for l in pathlib.Path('/proc/meminfo').read_text().splitlines()}
 assert memory['MemAvailable']>=12*1024**2
 original=json.loads(p['capture']['files']['launch']['raw_utf8'])
 output=root/'outputs'/original['run_id']
 assert not (output/'calibration-frozen-mask.json').exists(),'Original freeze exists: recover, never start a second reader'
 assert os.statvfs(root).f_bavail*os.statvfs(root).f_frsize>=2*2**30
 cpu.mkdir(mode=0o700)
 create_record(cpu/'capture.json',p['capture']);create_record(cpu/'settlement.json',p['settlement'])
 create_record(cpu/'release-accepted.json',lifecycle)
 worker=base64.b64decode(p['worker_base64']);assert hashlib.sha256(worker).hexdigest()==p['worker_sha256']
 (cpu/'worker.py').write_bytes(worker)
 python=original['commands']['runner'][0]
 reader=[python,str(stage/'scripts/accept_cara_budget_complete_r1.py'),'--project',str(root),'--stage',str(stage),'--capture',str(cpu/'capture.json'),'--settlement',str(cpu/'settlement.json'),'--expected-launch-sha256',p['launch_sha256'],'--output',str(cpu/'accepted.json'),'--freeze']
 command=['docker','run','-d','--read-only','--network','none','--pid','host','--name',name,'--label','wcomr.original-launch='+original['launch_id'],'--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--cpuset-cpus','26,27','--memory','8g','--memory-swap','8g','--pids-limit','128','--tmpfs','/tmp:rw,size=512m','-v',str(root)+':'+str(root)+':ro','-v',str(cpu)+':'+str(cpu)+':rw','-v',str(output)+':'+str(output)+':rw','-w',str(root/'runtime')]
 original_command=original['commands']['container_cli']
 for i,arg in enumerate(original_command):
  if arg=='-e':
   value=original_command[i+1];key=value.split('=',1)[0]
   if key in ('LD_LIBRARY_PATH','PATH','PYTHONPATH','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE'):command.extend(['-e',value])
 for value in ['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void','PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2']:
  command.extend(['-e',value])
 command.extend(['--entrypoint',python,reg['container_image'],str(cpu/'worker.py'),str(cpu)])
 create_record(cpu/'plan.json',dict(stage=str(stage),source_revision=reg['source_revision'],launch_sha256=p['launch_sha256'],worker_sha256=p['worker_sha256'],reader_command=reader,container_command=command,created_unix=time.time(),GPU_submissions=0))
 response=subprocess.run(command,capture_output=True,text=True,timeout=45)
 create_record(cpu/'dispatch.json',dict(returncode=response.returncode,stdout=response.stdout,stderr=response.stderr,observed_unix=time.time()))
 assert response.returncode==0,response.stderr
 created=True;existing=inspect()
result=dict(status='ORIGINAL_COMPLETE_READER_CPU_RECOVERY',stage=str(cpu),container=existing,new_CPU_submission=created,GPU_submissions=0,ledger_written=False,observed_unix=time.time())
if cpu.exists():
 result['files']={n:dict(sha256=sha(cpu/n),value=json.loads((cpu/n).read_text())) for n in ['plan.json','dispatch.json','release-accepted.json','reader-start.json','reader-terminal.json'] if (cpu/n).exists()}
 if (cpu/'reader-start.json').exists():result['reader_observation']=observe_original_process(json.loads((cpu/'reader-start.json').read_text())['identity'])
 if existing is not None and not existing['State']['Running'] and existing['State']['Pid']==0:
  if (cpu/'reader.log').exists():result['log_tail']=(cpu/'reader.log').read_text(errors='replace')[-4000:]
  if existing['State']['ExitCode']==0 and (cpu/'accepted.json').exists():
   accepted=json.loads((cpu/'accepted.json').read_text());frozen=pathlib.Path(accepted['freeze_path'])
   assert sha(frozen)==accepted['freeze_sha256']
   result['accepted']=dict(sha256=sha(cpu/'accepted.json'),raw_utf8=(cpu/'accepted.json').read_text(),value=accepted)
   result['frozen']=dict(sha256=sha(frozen),raw_utf8=frozen.read_text(),value=json.loads(frozen.read_text()))
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'capture'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    read = lambda name: json.loads((ROOT / name).read_text())
    original = read('reports/cara_budget_successor_final_capture_r1_20261101.json')
    settled = read('reports/cara_budget_successor_final_settlement_r1_20261101.json')
    assert original['exit_code'] == settled['exit_code'] == 0
    binding = read('reports/cara_budget_successor_actual_start_accepted_r1_20261031.json')
    payload = dict(action=args.action, cpu_name=CPU_NAME, launch_sha256=binding['launch_sha256'],
        source_revision=binding['source_revision'], capture=original['result']['lifecycle'],
        settlement=settled['result']['envelope'], worker_base64=base64.b64encode(WORKER.encode()).decode(),
        worker_sha256=hashlib.sha256(WORKER.encode()).hexdigest())
    code = "import io,sys,json,gzip,base64,hashlib\nsaved=sys.stdout;sys.stdout=io.StringIO()\nexec(" + repr(REMOTE) + ")\nraw=sys.stdout.getvalue().encode();sys.stdout=saved\nprint(json.dumps(dict(body=base64.b64encode(gzip.compress(raw)).decode(),sha256=hashlib.sha256(raw).hexdigest())))"
    packet = base64.b64encode(gzip.compress(json.dumps(dict(code=code, arguments=payload)).encode())).decode()
    secret = password()
    command = "sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c " + shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    started = time.time()
    child = subprocess.Popen(['ssh', '-C', '-F', str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=25', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
        'two_card_lan', command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = child.communicate((secret+'\n'+packet).encode(), timeout=110)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        out, err = child.communicate()
    result = None
    if child.returncode == 0:
        wrapped = json.loads(out); raw = gzip.decompress(base64.b64decode(wrapped['body']))
        assert hashlib.sha256(raw).hexdigest() == wrapped['sha256']
        result = json.loads(raw)
    receipt = dict(action=args.action, started_unix=started, observed_unix=time.time(), exit_code=child.returncode,
        result=result, stderr=err.decode(errors='replace').replace(secret, '[REDACTED]'),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(), worker_sha256=payload['worker_sha256'],
        launch_id=binding['launch_id'], GPU_submissions=0, unknown_requires_original_recovery=True)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode, status=(result or {}).get('status'),
        container_state=((result or {}).get('container') or {}).get('State'),
        accepted=(result or {}).get('accepted', {}).get('value'), error=receipt['stderr'][-1000:])))


if __name__ == '__main__':
    main()
