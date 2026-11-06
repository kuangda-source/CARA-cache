"""Recover one bounded released-artifact reader and the original P1 score CPU.

All scientific functions come from the sealed R2 GPU stage. Existing reader or
score intents are recovery-only, including an interrupted transport response.
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

from cara_source_lifecycle_p1_control_r1 import wrapped_rpc_code
from cara_two_card_transport_r1 import password

ROOT = Path(__file__).resolve().parents[1]
CPU_NAME = 'cara-P1-successor-released-artifacts-CPU-r2-20261103'
START = 'reports/cara_v1_P1_successor_actual_start_accepted_r2_20261102.json'
CAPTURE = 'reports/cara_v1_P1_successor_terminal_original_status_r1_20261103.json'
SETTLEMENT = 'reports/cara_v1_P1_successor_final_settlement_r1_20261103.json'

WORKER = r'''
import hashlib,json,os,pathlib,signal,sys,time,traceback
cpu=pathlib.Path(sys.argv[1]);plan=json.loads((cpu/'plan.json').read_text());stage=pathlib.Path(plan['stage'])
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record
from wcomr.cara_source_lifecycle_p1_artifacts_r1 import released_artifacts
from wcomr.cara_source_lifecycle_p1_scores_r1 import bind_post_scorer
from wcomr.cara_fast_fidelity_r1 import file_sha
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
assert os.sched_getaffinity(0)=={26,27}
create_record(cpu/'reader-start.json',dict(identity=bind_original_process(os.getpid()),started_unix=time.time()))
def timeout(signum,frame):raise TimeoutError('Original released-artifact reader deadline')
signal.signal(signal.SIGALRM,timeout);signal.signal(signal.SIGTERM,timeout);signal.alarm(3600)
code=1;error=None
try:
 capture=json.loads((cpu/'capture.json').read_text());settlement=json.loads((cpu/'settlement.json').read_text())
 assert file_sha(cpu/'capture.json')==plan['capture_sha256'] and file_sha(cpu/'settlement.json')==plan['settlement_sha256']
 packet=released_artifacts(capture,plan['launch_sha256'],settlement)
 environment=json.loads((stage/'internal-score-environment.json').read_text())
 config=bind_post_scorer(packet,environment)
 create_record(cpu/'artifact-packet.json',packet);create_record(cpu/'score-config.json',config)
 m=packet['manifest']
 create_record(cpu/'accepted.json',dict(status='ORIGINAL_RELEASED_FULL146_READER_ACCEPTED',semantic_denominator=m['semantic_denominator'],physical_paths=m['physical_paths'],physical_model_pairs=m['physical_model_pairs'],source_label_count=m['source_label_count'],identity_controls_passed=m['identity_controls_passed'],quality_positions=len(m['quality_positions']),new_pairs=len(m['new_pairs']),reused_internal_unique_pairs=len(m['internal_rows']),internal_scores_recomputed=0,packet_sha256=file_sha(cpu/'artifact-packet.json'),config_sha256=file_sha(cpu/'score-config.json'),GPU_submissions=0,scientific_accepted=False))
 code=0
except BaseException as exc:
 error=dict(type=type(exc).__name__,message=str(exc));traceback.print_exc()
finally:
 signal.alarm(0);create_record(cpu/'reader-terminal.json',dict(ended_unix=time.time(),exit_code=code,error=error))
sys.exit(code)
'''

REMOTE = r'''
import base64,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];binding=p['binding'];stage=pathlib.Path(binding['stage']);root=stage.parents[1];cpu=root/'.sync'/p['cpu_name'];name=p['cpu_name']+'-cpu'
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
assert sha(stage/'GPU-launch.json')==binding['launch_sha256'] and sha(stage/'registration.json')==binding['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==binding['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_s_endpoint_lifecycle_r1 import released_lifecycle
from wcomr.cara_budget_original_handles_r1 import observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID
assert RUN_ID==binding['run_id']
release=released_lifecycle(p['capture'],binding['launch_sha256'],p['settlement'])
assert release['container_exit_success'] and release['GPU_released'] and release['cost_settled']
def inspect():
 r=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=20)
 if r.returncode:
  assert r.returncode==1 and ('No such object' in r.stderr or 'No such container' in r.stderr),r.stderr
  return None
 return json.loads(r.stdout)[0]
existing=inspect();created=False
if p['action']=='launch-reader' and not cpu.exists():
 assert existing is None and not (stage/'post-score-control/intent.json').exists(),'Recover existing original reader/score intent'
 available=int(next(line.split()[1] for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
 assert available>=12*2**30 and {26,27}<=os.sched_getaffinity(0) and os.statvfs(root).f_bavail*os.statvfs(root).f_frsize>=2*2**30
 cpu.mkdir(mode=0o700)
 create_record(cpu/'capture.json',p['capture']);create_record(cpu/'settlement.json',p['settlement'])
 worker=base64.b64decode(p['worker_base64'],validate=True);assert hashlib.sha256(worker).hexdigest()==p['worker_sha256']
 with (cpu/'worker.py').open('xb') as stream:stream.write(worker);stream.flush();os.fsync(stream.fileno())
 launch=read_record(stage/'GPU-launch.json');python=launch['commands']['runner'][0]
 command=['docker','run','-d','--read-only','--network','none','--pid','host','--name',name,'--label','wcomr.original-launch='+binding['launch_id'],'--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--cpuset-cpus','26,27','--memory','8g','--memory-swap','8g','--pids-limit','128','--tmpfs','/tmp:rw,size=512m','-v',str(root)+':'+str(root)+':ro','-v',str(cpu)+':'+str(cpu)+':rw','-w',str(root/'runtime')]
 original=launch['commands']['container_cli']
 for i,arg in enumerate(original):
  if arg=='-e' and original[i+1].split('=',1)[0] in ('LD_LIBRARY_PATH','PATH','PYTHONPATH','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE'):command.extend(['-e',original[i+1]])
 for value in ['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void','PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2']:command.extend(['-e',value])
 command.extend(['--entrypoint',python,reg['container_image'],str(cpu/'worker.py'),str(cpu)])
 create_record(cpu/'plan.json',dict(stage=str(stage),source_revision=reg['source_revision'],launch_sha256=binding['launch_sha256'],worker_sha256=p['worker_sha256'],capture_sha256=sha(cpu/'capture.json'),settlement_sha256=sha(cpu/'settlement.json'),command=command,created_unix=time.time(),GPU_submissions=0,no_replay=True))
 r=subprocess.run(command,capture_output=True,text=True,timeout=45)
 create_record(cpu/'dispatch.json',dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()))
 assert r.returncode==0,r.stderr
 created=True;existing=inspect()
result=dict(status='ORIGINAL_RELEASED_READER_RECOVERY',reader_stage=str(cpu),reader_exists=cpu.exists(),new_CPU_submission=created,GPU_submissions=0,ledger_written=False,observed_unix=time.time())
reader_complete=False
if cpu.exists():
 assert (cpu/'plan.json').exists(),'Partial original reader intent: recovery only'
 plan=read_record(cpu/'plan.json');assert plan['stage']==str(stage) and plan['source_revision']==binding['source_revision'] and plan['launch_sha256']==binding['launch_sha256']
 assert sha(cpu/'worker.py')==plan['worker_sha256']==p['worker_sha256']
 result['files']={n:dict(sha256=sha(cpu/n),value=read_record(cpu/n)) for n in ['plan.json','dispatch.json','reader-start.json','reader-terminal.json'] if (cpu/n).exists()}
 if existing is not None:
  h=existing['HostConfig'];assert not h['DeviceRequests'] and not h['Devices'] and not h['Privileged'] and not h['CapAdd']
  assert h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==2*10**9 and h['CpusetCpus']=='26,27'
  assert h['NetworkMode']=='none' and h['PidMode']=='host' and h['ReadonlyRootfs'] and h['RestartPolicy']['Name']=='no'
  assert existing['Image']==reg['container_image'] and existing['Config']['Labels']['wcomr.original-launch']==binding['launch_id']
  result['container']=dict(id=existing['Id'],state=existing['State'],host={k:h[k] for k in ['Memory','MemorySwap','NanoCpus','CpusetCpus','DeviceRequests','NetworkMode','ReadonlyRootfs']})
 if (cpu/'reader-start.json').exists():result['reader_observation']=observe_original_process(read_record(cpu/'reader-start.json')['identity'])
 if existing is not None and not existing['State']['Running'] and existing['State']['Pid']==0:
  result['log_tail']=subprocess.run(['docker','logs','--tail','35',existing['Id']],capture_output=True,text=True,timeout=20).stderr[-5000:]
  if existing['State']['ExitCode']==0 and not existing['State']['OOMKilled'] and (cpu/'accepted.json').exists():
   terminal=read_record(cpu/'reader-terminal.json');assert terminal['exit_code']==0 and terminal['error'] is None and result['reader_observation']['original_live'] is False
   accepted=read_record(cpu/'accepted.json');assert accepted['packet_sha256']==sha(cpu/'artifact-packet.json') and accepted['config_sha256']==sha(cpu/'score-config.json')
   assert accepted['semantic_denominator']==146 and accepted['source_label_count']==64 and accepted['identity_controls_passed']==12 and accepted['quality_positions']==52 and accepted['new_pairs']<=32
   result['accepted']=accepted;result['status']='ORIGINAL_RELEASED_FULL146_READER_ACCEPTED';reader_complete=True
if p['action'] in ('dispatch-score','recover-score','complete-export'):
 from wcomr import cara_source_lifecycle_p1_score_dispatch_r1 as score
 if (stage/'post-score-control/intent.json').exists():result['score']=score.recover(stage)
 elif p['action']=='dispatch-score':
  assert reader_complete,'Original complete released reader must end before one score dispatch'
  result['score']=score.dispatch(stage,read_record(cpu/'artifact-packet.json'),read_record(cpu/'score-config.json'),binding['registration_sha256'])
 else:result['score']=dict(status='ORIGINAL_SCORE_INTENT_ABSENT',dispatch_allowed=False)
 result['status']=result['score']['status']
 if p['action']=='complete-export' and result['score']['status']=='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED':
  from wcomr.cara_source_lifecycle_p1_result_bundle_r1 import export
  result['export']=export(stage);path=pathlib.Path(result['export']['bundle_path'])
  assert sha(path)==result['export']['bundle_sha256']
  result['bundle_raw_utf8']=path.read_text();result['status']='P1_ORIGINAL_COMPLETE_RESULT_BUNDLE_EXPORTED'
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('launch-reader', 'capture-reader', 'dispatch-score', 'recover-score', 'complete-export'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    read = lambda name: json.loads((ROOT/name).read_bytes())
    binding, original, settled = read(START), read(CAPTURE), read(SETTLEMENT)
    assert original['exit_code'] == settled['exit_code'] == 0
    payload = dict(action=args.action, binding=binding, capture=original['result']['lifecycle'],
                   settlement=settled['result']['envelope'], cpu_name=CPU_NAME,
                   worker_base64=base64.b64encode(WORKER.encode()).decode(), worker_sha256=hashlib.sha256(WORKER.encode()).hexdigest())
    encoded = base64.b64encode(gzip.compress(json.dumps(dict(code=wrapped_rpc_code(REMOTE), arguments=payload)).encode())).decode()
    secret = password()
    remote = "import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])"
    command = "sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c " + shlex.quote(remote)
    started = time.time()
    child = subprocess.Popen(['ssh', '-C', '-F', str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'),
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=60', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', 'two_card_lan', command],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = child.communicate((secret+'\n'+encoded).encode(), timeout=150)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        out, err = child.communicate()
    result = None
    if child.returncode == 0:
        wire = json.loads(out)
        raw = gzip.decompress(base64.b64decode(wire['gzip_base64']))
        assert hashlib.sha256(raw).hexdigest() == wire['sha256']
        result = json.loads(raw)
    receipt = dict(action=args.action, started_unix=started, observed_unix=time.time(), exit_code=child.returncode, result=result,
        stderr=err.decode(errors='replace').replace(secret, '[REDACTED]'), transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(), worker_sha256=payload['worker_sha256'], launch_id=binding['launch_id'],
        source_revision=binding['source_revision'], GPU_submissions=0, unknown_requires_original_recovery=True)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(action=args.action, exit_code=child.returncode, status=(result or {}).get('status'),
        reader_state=((result or {}).get('container') or {}).get('state'), reader_accepted=(result or {}).get('accepted'),
        error=receipt['stderr'][-1600:])))


if __name__ == '__main__':
    main()
