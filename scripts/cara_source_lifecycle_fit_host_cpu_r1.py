"""Once-only two-card host FIT CPU probe; source transfer is resumable, work is not."""
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture
from cara_source_lifecycle_p1_linux_cpu_r3 import OVERLAY as ALGORITHM

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-source-lifecycle-P1-FIT-host-CPU-a6000-r1-20261102'
OVERLAY = tuple(dict.fromkeys(ALGORITHM+(
    'src/wcomr/cara_source_lifecycle_fit_broker_r1.py',
    'scripts/cara_source_lifecycle_fit_broker_r1.py',
    'tests/test_cara_source_lifecycle_fit_broker_r1.py',
    'scripts/check_cara_source_lifecycle_fit_host_cpu_r1.py',
    'scripts/cara_source_lifecycle_fit_host_cpu_r1.py',
    'tests/test_cara_source_lifecycle_fit_host_cpu_r1.py',
)))

REMOTE = r'''
import base64,hashlib,json,os,pathlib,shutil,subprocess,sys,time
p=json.load(sys.stdin)
assert p['host']=='two_card' and p['stage_name']=='cara-source-lifecycle-P1-FIT-host-CPU-a6000-r1-20261102'
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=root/'.sync'/p['stage_name']
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def put(path,value):
 with path.open('xb') as f:
  f.write((json.dumps(value,indent=2,allow_nan=False)+'\n').encode());f.flush();os.fsync(f.fileno())
if p['action']=='prepare':
 assert not stage.exists(),'Existing host CPU stage: recover original, never launch again'
 base=pathlib.Path(p['base_stage'])
 assert sha(base/'registration.json')==p['base_registration_sha256']
 inherited=json.loads((base/'registration.json').read_bytes())
 assert inherited['host']=='two_card'
 assert all(sha(root/'runtime'/n)==h for n,h in inherited['runtime_source_sha256'].items())
 mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert {26,27}<=os.sched_getaffinity(0) and mem>=16*2**30 and shutil.disk_usage(root).free>=4*2**30
 stage.mkdir(mode=0o700)
 put(stage/'source-intent.json',dict(source_revision=p['parent_git_revision'],base_registration_sha256=p['base_registration_sha256'],no_replay=True))
 for n,expected in p['hashes'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(p['files'][n]) if n in p['files'] else (base/n).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==expected,'Original source bytes differ: '+n
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 reg=dict(host='two_card',stage=str(stage),payload_sha256=p['hashes'],runtime_source_sha256=inherited['runtime_source_sha256'],
  parent_git_revision=p['parent_git_revision'],source_identity='EXACT_PAYLOAD_HOST_FIT_CPU_ONLY',
  base_registration_sha256=p['base_registration_sha256'],original_source_stage=str(base),CPU_fixture_only=True,
  parent_profile=dict(Docker_container=False,cpuset=[26,27],RLIMIT_AS_bytes=4*2**30,CPU_seconds=1200,wall_seconds=1200),
  score_container_profile=dict(cpus=2,cpuset=[26,27],memory_bytes=8*2**30,swap_bytes=0,network='none',GPU_hidden=True))
 put(stage/'registration.json',reg)
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 from wcomr.cara_budget_original_handles_r1 import observe_original_process
 command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
  str(stage/'scripts/check_cara_source_lifecycle_fit_host_cpu_r1.py'),'probe','--stage',str(stage),'--output',str(stage/'CPU-proof.json')]
 environment=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
  PYTHONPATH=str(stage/'scripts')+':'+str(stage/'src')+':'+str(stage/'tests'),
  OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
 put(stage/'host-launch-intent.json',dict(command=command,command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest(),
  registration_sha256=sha(stage/'registration.json'),started_unix=time.time(),no_replay=True))
 with (stage/'CPU.log').open('x') as log:
  child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=environment,start_new_session=True)
 deadline=time.monotonic()+25
 while not (stage/'host-start.json').exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.05)
 assert (stage/'host-start.json').exists(),'Original host bootstrap unknown: recover only'
 original=json.loads((stage/'host-start.json').read_bytes())
 assert original['identity']['pid']==child.pid and observe_original_process(original['identity'])['original_live'] is True
 launched=dict(status='ORIGINAL_HOST_FIT_CPU_PROBE_LAUNCHED_NOT_GPU',host='two_card',stage=str(stage),
  source_revision=p['parent_git_revision'],registration_sha256=sha(stage/'registration.json'),
  identity=original['identity'],parent_bounds=original['parent_bounds'],started_unix=original['started_unix'],
  parent_Docker_container=False,CPU_fixture_only=True,work_seconds=1200,exit_seconds=60,
  MemAvailable_before=mem,free_disk_before=shutil.disk_usage(root).free,GPU_submissions=0,ledger_written=False)
 put(stage/'CPU-launch.json',launched)
 put(stage/'host-dispatch-grant.json',dict(identity=original['identity'],launch_sha256=sha(stage/'CPU-launch.json')))
 print(json.dumps(launched))
else:
 assert p['action']=='capture'
 reg=json.loads((stage/'registration.json').read_bytes())
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 from wcomr.cara_budget_original_handles_r1 import observe_original_process
 launched=json.loads((stage/'CPU-launch.json').read_bytes()) if (stage/'CPU-launch.json').exists() else None
 start=json.loads((stage/'host-start.json').read_bytes()) if (stage/'host-start.json').exists() else None
 handle=launched['identity'] if launched else start['identity'] if start else None
 observation=observe_original_process(handle) if handle else dict(original_live=None,status='UNKNOWN',reason='ORIGINAL_HOST_START_UNAVAILABLE')
 raw=(stage/'CPU-proof.json').read_bytes() if observation['original_live'] is False and (stage/'CPU-proof.json').exists() else None
 terminal=json.loads((stage/'host-terminal.json').read_bytes()) if observation['original_live'] is False and (stage/'host-terminal.json').exists() else None
 print(json.dumps(dict(status='ORIGINAL_HOST_FIT_CPU_CAPTURE_ONLY',host='two_card',stage=str(stage),launch=launched,
  registration=reg,registration_sha256=sha(stage/'registration.json'),original_host_observation=observation,
  payload_intact=all(sha(stage/n)==h for n,h in reg['payload_sha256'].items()),
  runtime_intact=all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),
  CPU_proof=json.loads(raw) if raw else None,CPU_proof_base64=base64.b64encode(raw).decode() if raw else None,
  CPU_proof_sha256=hashlib.sha256(raw).hexdigest() if raw else None,host_terminal=terminal,
  log_tail=(stage/'CPU.log').read_text(errors='replace')[-4500:] if (stage/'CPU.log').exists() else '',
  observed_unix=time.time(),GPU_submissions=0,ledger_written=False)))
'''


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        sys.argv.pop(1)
        transfer.main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
            transfer_label='cara-V1-P1-FIT-host-CPU-transfer', connect_timeout=60, probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_algorithm_Linux_CPU_capture_r7_20261102.json',
            work_seconds=1200, exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
            '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
            capture_output=True, text=True, timeout=12)
        capture(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=1200, exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
            connect_timeout=60)
