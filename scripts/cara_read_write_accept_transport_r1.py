"""Invoke the immutable M1 readers and recover their original CPU handles."""
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
WORKER = r'''
import hashlib,json,os,pathlib,signal,sys,time
directory=pathlib.Path(sys.argv[1]);plan=json.loads((directory/'plan.json').read_text());stage=pathlib.Path(plan['stage'])
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record
from wcomr.cara_read_write_artifacts_r1 import released_artifacts
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
assert os.sched_getaffinity(0)=={26,27}
identity=bind_original_process(os.getpid());started=time.time()
create_record(directory/'reader-start.json',dict(identity=identity,started_unix=started,plan_sha256=hashlib.sha256((directory/'plan.json').read_bytes()).hexdigest()))
def interrupted(signum,frame):raise TimeoutError('Original M1 artifact reader deadline')
signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted);signal.alarm(1800)
error=None
try:
 packet=released_artifacts(json.loads((directory/'lifecycle.json').read_text()),plan['launch_sha256'],json.loads((directory/'settlement.json').read_text()))
 assert packet['manifest']['physical_paths']==14 and packet['manifest']['identity_controls_passed']==4 and len(packet['manifest']['pairs'])==8
 create_record(directory/'artifact-packet.json',packet)
except BaseException as caught:
 error=dict(type=type(caught).__name__,message=str(caught));raise
finally:
 create_record(directory/'reader-terminal.json',dict(identity=identity,started_unix=started,ended_unix=time.time(),error=error,GPU_submissions=0))
'''

REMOTE = r'''
import base64,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];stage=pathlib.Path(p['stage']);root=stage.parents[1]
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(stage/'GPU-launch.json')==p['launch_sha256'] and sha(stage/'registration.json')==p['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==p['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_search_journal_r1 import create_record
from wcomr.cara_budget_original_handles_r1 import observe_original_process
from wcomr.cara_s_endpoint_lifecycle_r1 import released_lifecycle
from wcomr.cara_read_write_scores_r1 import bind_scorer
from wcomr.cara_read_write_score_dispatch_r1 import dispatch,recover
from wcomr.cara_read_write_identity_r1 import for_run
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
release=released_lifecycle(p['lifecycle'],p['launch_sha256'],p['settlement'])
assert release['container_exit_success'] and release['GPU_released'] and release['cost_settled']
launch=json.loads((stage/'GPU-launch.json').read_text());output=root/'outputs'/launch['run_id']
directory=output/'artifact-accept-CPU';name=stage.name+'-artifact-accept-cpu'
def inspect():
 r=subprocess.run(['docker','inspect','--type','container',name],capture_output=True,text=True,timeout=20)
 if r.returncode:
  assert r.returncode==1 and ('No such object' in r.stderr or 'No such container' in r.stderr),'Original artifact container observation unknown'
  return None
 return json.loads(r.stdout)[0]
existing=inspect();created=False
if p['action']=='artifacts' and not directory.exists():
 assert existing is None,'Existing original artifact reader: recover only'
 available=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert {26,27}<=os.sched_getaffinity(0) and available>=12*2**30 and os.statvfs(output).f_bavail*os.statvfs(output).f_frsize>=2*2**30
 directory.mkdir(mode=0o700)
 create_record(directory/'lifecycle.json',p['lifecycle']);create_record(directory/'settlement.json',p['settlement'])
 worker=base64.b64decode(p['worker_base64']);assert hashlib.sha256(worker).hexdigest()==p['worker_sha256']
 (directory/'reader.py').write_bytes(worker)
 environment=process_environment(root,directory/'caches')
 command=container_command(root,stage,'cpu-worker',p['launch_sha256'],environment,os.getuid(),os.getgid())
 command[command.index('--name')+1]=name;command[command.index('--memory')+1]='8g'
 command[command.index(str(stage)+':'+str(stage)+':rw')]=str(stage)+':'+str(stage)+':ro'
 index=command.index('--entrypoint');command[index:index]=['-d','--memory-swap','8g','--cpuset-cpus','26,27','--cidfile',str(directory/'container.cid'),'-v',str(directory)+':'+str(directory)+':rw']
 command=command[:command.index('--entrypoint')+3]+[str(directory/'reader.py'),str(directory)]
 plan=dict(stage=str(stage),source_revision=p['source_revision'],launch_sha256=p['launch_sha256'],registration_sha256=p['registration_sha256'],worker_sha256=p['worker_sha256'],command=command,created_unix=time.time(),admission=dict(available_memory_bytes=available),wall_limit_seconds=1800,no_replay=True)
 create_record(directory/'plan.json',plan)
 response=subprocess.run(command,capture_output=True,text=True,timeout=45)
 create_record(directory/'dispatch.json',dict(returncode=response.returncode,stdout=response.stdout,stderr=response.stderr,observed_unix=time.time()))
 assert response.returncode==0,response.stderr
 created=True;existing=inspect()
result=dict(status='ORIGINAL_M1_ACCEPTANCE_CPU_RECOVERY',release=release,reader_directory=str(directory),reader_container=existing,new_reader_submission=created,GPU_submissions=0,ledger_written=False,observed_unix=time.time())
def saved(path):
 raw=pathlib.Path(path).read_text();return dict(sha256=sha(path),raw_utf8=raw)
packet_value=None
if directory.exists():
 plan=json.loads((directory/'plan.json').read_text())
 assert plan['stage']==str(stage) and plan['launch_sha256']==p['launch_sha256'] and plan['worker_sha256']==p['worker_sha256']==sha(directory/'reader.py')
 assert json.loads((directory/'lifecycle.json').read_text())==p['lifecycle'] and json.loads((directory/'settlement.json').read_text())==p['settlement']
 result['reader_files']={n:saved(directory/n) for n in ('plan.json','dispatch.json','reader-start.json','reader-terminal.json') if (directory/n).exists()}
 if existing is not None:
  host=existing['HostConfig'];cfg=existing['Config']
  assert existing['Id']==(directory/'container.cid').read_text().strip() and existing['Name']=='/'+name and existing['Image']==reg['container_image']
  assert cfg['Labels']['wcomr.manifest']==p['launch_sha256'] and not host['DeviceRequests'] and not host['Privileged'] and host['ReadonlyRootfs'] and host['NetworkMode']=='none' and host['RestartPolicy']['Name']=='no'
  assert host['Memory']==host['MemorySwap']==8*2**30 and host['NanoCpus']==2*10**9 and host['CpusetCpus']=='26,27'
  if not existing['State']['Running'] and existing['State']['Pid']==0:
   log=subprocess.run(['docker','logs','--tail','40',existing['Id']],capture_output=True,text=True,timeout=20)
   result['reader_log_tail']=(log.stdout+log.stderr)[-6000:]
   started=json.loads((directory/'reader-start.json').read_text());observation=observe_original_process(started['identity']);result['reader_observation']=observation
   terminal=json.loads((directory/'reader-terminal.json').read_text())
   if existing['State']['ExitCode']==0:
    assert observation['original_live'] is False and terminal['identity']==started['identity'] and terminal['error'] is None
    packet_value=json.loads((directory/'artifact-packet.json').read_text());assert packet_value['manifest']['identity_controls_passed']==4
    result['artifact_packet']=saved(directory/'artifact-packet.json')
    result['original_files']={n:saved(path) for n,path in dict(collection=output/'read-write-collection.json',card=stage/for_run(launch['run_id']).manifest).items()}
   else:result['status']='ORIGINAL_M1_ARTIFACT_READER_FAILED'
score_control=stage/'endpoint-score-control'
if (score_control/'intent.json').exists():
 result['score_recovery']=recover(stage)
elif p['action']=='score':
 assert packet_value is not None,'Original complete exited RGB reader required before scoring'
 config=bind_scorer(packet_value,p['score_environment'])
 result['score_recovery']=dispatch(stage,packet_value,config,p['registration_sha256'])
if (score_control/'intent.json').exists():
 result['score_files']={n:saved(score_control/n) for n in ('intent.json','supervisor-start.json','container-cli-start.json','supervisor-terminal.json') if (score_control/n).exists()}
 if result['score_recovery']['status']=='ORIGINAL_COMPLETE8_M1_SCORE_ACCEPTED':
  result['score_original_files']={n:saved(output/'endpoint-score-CPU'/n) for n in ('manifest.json','artifact-packet.json','scores.json')}
print(json.dumps(result))
'''


def main(*,start_ref='reports/cara_read_write_actual_start_accepted_r1_20261101.json',
         terminal_ref='reports/cara_read_write_final_original_r1_20261101.json',
         settlement_ref='reports/cara_read_write_final_settlement_r1_20261101.json'):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['artifacts', 'score', 'capture'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    read = lambda name: json.loads((ROOT / name).read_text())
    start = read(start_ref)
    terminal = read(terminal_ref)
    settled = read(settlement_ref)
    assert terminal['exit_code'] == settled['exit_code'] == 0
    old = read('reports/cara_fast_B36_original_score_manifest_r1_20261029.json')
    arguments = dict(action=args.action, stage=start['stage'], source_revision=start['source_revision'],
        launch_sha256=start['launch_sha256'], registration_sha256=start['container']['manifest_sha256'],
        lifecycle=terminal['result']['lifecycle'], settlement=settled['result']['envelope'],
        score_environment={k: old[k] for k in ('torch_home', 'piq_site', 'weights_sha256')},
        worker_base64=base64.b64encode(WORKER.encode()).decode(), worker_sha256=hashlib.sha256(WORKER.encode()).hexdigest())
    code = "import io,sys,json,gzip,base64,hashlib\n_endpoint7_stdout=sys.stdout;sys.stdout=io.StringIO()\nexec(" + repr(REMOTE) + ")\n_endpoint7_raw=sys.stdout.getvalue().encode();sys.stdout=_endpoint7_stdout\nprint(json.dumps(dict(body=base64.b64encode(gzip.compress(_endpoint7_raw)).decode(),sha256=hashlib.sha256(_endpoint7_raw).hexdigest())))"
    payload = base64.b64encode(gzip.compress(json.dumps(dict(code=code, arguments=arguments)).encode())).decode()
    secret = password()
    bootstrap = "import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])"
    command = "sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c " + shlex.quote(bootstrap)
    started = time.time()
    child = subprocess.Popen(['ssh', '-C', '-F', str(ROOT / '.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=25', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
        'two_card_lan', command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = child.communicate((secret + '\n' + payload).encode(), timeout=110)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        out, err = child.communicate()
    result = None
    if child.returncode == 0:
        wrapper = json.loads(out)
        raw = gzip.decompress(base64.b64decode(wrapper['body']))
        assert hashlib.sha256(raw).hexdigest() == wrapper['sha256']
        result = json.loads(raw)
    report = dict(action=args.action, started_unix=started, observed_unix=time.time(), exit_code=child.returncode,
        result=result, stderr=err.decode(errors='replace').replace(secret, '[REDACTED]'),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(), worker_sha256=arguments['worker_sha256'],
        launch_id=start['launch_id'], GPU_submissions=0, unknown_requires_original_recovery=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode, status=(result or {}).get('status'),
        reader_state=((result or {}).get('reader_container') or {}).get('State'),
        score_status=((result or {}).get('score_recovery') or {}).get('status'), error=report['stderr'][-1600:])))


if __name__ == '__main__':
    main()
