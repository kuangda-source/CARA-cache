"""Launch the released B36 scorer once; reuse six accepted A pairs and never expose CUDA."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from cara_two_card_transport_r1 import ssh

ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import base64,fcntl,hashlib,importlib.util,json,os,pathlib,subprocess,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=pathlib.Path(p['stage'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();read=lambda path:json.loads(path.read_text())
reg=read(stage/'registration.json');assert sha(stage/'registration.json')==p['registration_sha256']==p['capture']['files']['registration']['sha256']
assert sha(stage/'scripts/dispatch_cara_fast_b36_score_cpu_r2.py')==p['operator_sha256']
assert all(sha(stage/name)==value for name,value in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/name)==value for name,value in reg['runtime_source_sha256'].items())
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_b36_execution_r1 import RUN,SPEC
from wcomr.cara_fast_b36_post_r1 import formal_manifest
from wcomr.cara_fast_b36_terminal_r1 import released_terminal
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
card=load_card(stage,SPEC);capture=p['capture'];settlement=p['settlement'];release=released_terminal(capture,card,settlement)
assert release['technical_accepted'] and release['GPU_released'] and release['cost_settled']
expected=formal_manifest(capture,card,settlement);body=base64.b64decode(p['manifest']);assert hashlib.sha256(body).hexdigest()==p['manifest_sha256']
assert json.loads(body)==expected and expected['A_launch_id']=='5a5ab53ebb604433ab83cea06e1ab412'
assert expected['launch_id']!=expected['A_launch_id'] and len(expected['reused_A_metric_pairs'])==6
out=root/'outputs'/RUN/'B-score-CPU';manifest=out/'manifest.json';out.mkdir(exist_ok=True)
def create(path,value):
 with path.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
 fd=os.open(str(path.parent),os.O_RDONLY);os.fsync(fd);os.close(fd)
with (stage/'B-score-CPU-control.lock').open('a') as control:
 fcntl.flock(control,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=stage/'B-score-CPU-launch.json';intent=stage/'B-score-CPU-intent.json'
 if receipt.exists():
  old=read(receipt);assert old['manifest_sha256']==p['manifest_sha256'];print(json.dumps(old));sys.exit()
 assert not intent.exists(),'Recover the original CPU scorer intent; never relaunch'
 original=subprocess.run(['docker','inspect',stage.name+'-B-score-cpu'],capture_output=True,text=True,timeout=20)
 assert original.returncode==1 and original.stderr.strip() in ('Error: No such object: '+stage.name+'-B-score-cpu','Error: No such container: '+stage.name+'-B-score-cpu'),'Original CPU container state unknown or existing; recover it'
 assert not (out/'scores.json').exists(),'Recover existing CPU scores'
 assert int(next(line.split()[1] for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024>=12*2**30
 assert {26,27}<=os.sched_getaffinity(0)
 assert (pathlib.Path(expected['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth').is_file()
 assert pathlib.Path(expected['piq_site']).is_dir()
 if manifest.exists():assert sha(manifest)==p['manifest_sha256']
 else:
  with manifest.open('xb') as handle:handle.write(body);handle.flush();os.fsync(handle.fileno())
 spec=importlib.util.spec_from_file_location('original_B36_postprocessor',stage/'scripts/postprocess_cara_fast_b36_r1.py')
 helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 command=helper.score_command(root,stage,manifest,out)
 assert '--gpus' not in command and 'CUDA_VISIBLE_DEVICES=' in command and 'NVIDIA_VISIBLE_DEVICES=void' in command
 assert command[command.index('--cpus')+1]=='2' and command[command.index('--memory')+1]=='8g'
 assert command[command.index('--network')+1]=='none' and '--read-only' in command
 for option,value in [('--cpuset-cpus','26,27'),('--memory-swap','8g')]:
  if option in command:command[command.index(option)+1]=value
  else:command[command.index('--entrypoint'):command.index('--entrypoint')]=[option,value]
 command_sha=hashlib.sha256(json.dumps(command,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 fields=dict(run_id=RUN,launch_id=expected['launch_id'],host='two_card',stage=str(stage),
  container=stage.name+'-B-score-cpu',manifest_path=str(manifest),manifest_sha256=sha(manifest),
  command_sha256=command_sha,scorer_source_sha256=expected['scorer_source_sha256'],
  CPU_bound=expected['CPU_bound'],new_metric_computations=26,reused_accepted_A_metric_pairs=6,GPU_released=True,cost_settled=True,GPU_submissions=0,
  operator_sha256=p['operator_sha256'],created_unix=time.time())
 create(intent,fields);atomic_json(stage/'B-score-CPU-command.json',command)
 with (out/'CPU.log').open('x') as log:
  child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 fields.update(status='B36_RELEASED_CPU_SCORE_ONCE_DISPATCHED',process_identity=process_identity(child.pid),
  started_unix=time.time(),new_GPU_submissions=0)
 atomic_json(receipt,fields)
 print(json.dumps(fields))
'''


def main():
    parser=argparse.ArgumentParser()
    for name in ('launch','capture','settlement','manifest','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    launch=json.loads(args.launch.read_text());assert launch['host']=='two_card'
    body=args.manifest.read_bytes()
    data=dict(stage=launch['stage'],registration_sha256=launch['registration_sha256'],
        capture=json.loads(args.capture.read_text()),settlement=json.loads(args.settlement.read_text()),
        manifest=base64.b64encode(body).decode(),manifest_sha256=hashlib.sha256(body).hexdigest(),
        operator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    result=ssh(REMOTE,data,docker_group=True,timeout=120)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
