"""One-shot local operator for this run's released CPU scoring; no GPU dispatch."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'plans/cara_next_stage_20261104/sensitivity'), str(ROOT / 'scripts')]
from ops import PREFIX
from cara_f19_speed190_transport_r1 import rpc

SCORE = PREFIX + '''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
release=released_lifecycle(p['capture'],sha(stage/'GPU-launch.json'),p['settlement'])
assert all(release[k] for k in ('cost_settled','GPU_released','mode_restored','original_processes_ended'))
card=read(card_path);assert card['run_id']=='cara-generator-v1-primary11-r1-20261106'
control=stage/'released-primary-score-control';name=stage.name+'-primary-score'
if control.exists():
 q=subprocess.run(['docker','inspect','--format','{{json .State}}',name],capture_output=True,text=True)
 print(json.dumps(dict(status='RECOVER_EXISTING_PRIMARY_SCORER_ONLY',state=json.loads(q.stdout) if q.returncode==0 else None)));raise SystemExit
control.mkdir();create(control/'capture.json',p['capture']);create(control/'settlement.json',p['settlement'])
from four_card_bank24_execution_tools_r1 import process_environment
env=process_environment(root,control/'caches');old=read(base/'GPU-launch.json')['commands']['container_cli']
env['LD_LIBRARY_PATH']=next(x.split('=',1)[1] for x in old if x.startswith('LD_LIBRARY_PATH='))
binding=read(stage/'reports/cara_CAL66_quality_binding_20261025.json')
env.update(PYTHONPATH=str(stage/'src')+':'+str(stage/'scripts')+':'+binding['dependency_overlay']+':'+str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/site'),TORCH_HOME=str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/torch'))
actual=read(stage/'history104-storage.json')['output_mount'];output=root/'outputs'/run
cmd=['docker','run','-d','--name',name,'--network','none','--read-only','--cpus','2','--cpuset-cpus','4,5','--memory','8g','--memory-swap','8g','--pids-limit','256','--tmpfs','/tmp:rw,size=512m','--user',str(os.getuid())+':'+str(os.getgid()),'-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void','-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-v',str(root)+':'+str(root)+':ro','-v',str(stage)+':'+str(stage)+':ro','-v',str(control)+':'+str(control)+':rw','-v',str(output)+':'+str(output)+':ro','-v',actual+':'+actual+':ro','-w',str(root/'runtime')]
for source in (card['inherited_outputs']['output_root'],card['retained_C06']['output_root']):
 cmd+=['-v',source+':'+source+':ro']
cmd += [x for k,v in env.items() for x in ('-e',k+'='+str(v))]
cmd += [read(stage/'registration.json')['container_image'],'timeout','--signal=TERM','--kill-after=15s','7200',str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python'),str(stage/card['postrelease_CPU_entry']),'score','--manifest',str(card_path),'--collection',str(output/'collection.json'),'--capture',str(control/'capture.json'),'--settlement',str(control/'settlement.json'),'--output',str(control/'scores.json')]
create(control/'intent.json',dict(command=cmd,GPU_submissions=0,new_pairs_upper=7))
q=subprocess.run(cmd,capture_output=True,text=True);v=dict(status='PRIMARY_CPU_SCORER_DISPATCHED' if q.returncode==0 else 'CPU_LAUNCH_FAILED',exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,control=str(control),release=release,GPU_submissions=0,ledger_written=False)
create(control/'launch.json',v);print(json.dumps(v))
'''

STATUS = PREFIX + '''
control=stage/'released-primary-score-control';name=stage.name+'-primary-score'
q=subprocess.run(['docker','inspect','--format','{{json .State}}',name],capture_output=True,text=True)
v=dict(state=json.loads(q.stdout) if q.returncode==0 else None)
if (control/'scores.json').exists():v['scores']=read(control/'scores.json')
if v['state'] and not v['state']['Running']:
 q=subprocess.run(['docker','logs','--tail','20',name],capture_output=True,text=True);v['logs']=(q.stdout+q.stderr)[-4000:]
print(json.dumps(v))
'''

ANALYZE = PREFIX + '''
control=stage/'released-primary-score-control';target=control/'complete_analysis.json';card=read(card_path)
if target.exists():
 print(json.dumps(dict(status='RECOVER_EXISTING_ANALYSIS',analysis=read(target))));raise SystemExit
assert read(control/'scores.json')['status']=='ACCEPTED_OUTPUT_SCORES_COMPLETE'
name=stage.name+'-primary-score';state=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',name],text=True))
assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1')
cmd=[str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python'),str(stage/card['postrelease_CPU_entry']),'analyze','--manifest',str(card_path),'--collection',str(root/'outputs'/run/'collection.json'),'--scores',str(control/'scores.json'),'--output',str(target)]
q=subprocess.run(cmd,capture_output=True,text=True,timeout=900,env=env)
print(json.dumps(dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,analysis=read(target) if target.exists() else None)))
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('score', 'status', 'analyze'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--route', choices=('relay',), default='relay')
    args = parser.parse_args()
    if args.receipt.exists():
        raise ValueError('Preserve the original operator response')
    data = json.loads(args.input.read_text()) if args.input else {}
    result = rpc({'score': SCORE, 'status': STATUS, 'analyze': ANALYZE}[args.action], data, route='relay', timeout=180)
    args.receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'exit_code', 'state', 'stderr') if k in result}))
