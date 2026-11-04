"""Explicit post-release score/analyze commands. Never dispatches GPU work."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(HERE)]
from cara_f19_speed190_transport_r1 import rpc
from ops import PREFIX,CARD

SCORE=PREFIX+'''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
release=released_lifecycle(p['capture'],sha(stage/'GPU-launch.json'),p['settlement'])
assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
control=stage/'released-score-control';name=stage.name+'-score'
if control.exists():
 q=subprocess.run(['docker','inspect','--format','{{json .State}}',name],capture_output=True,text=True)
 print(json.dumps(dict(status='RECOVER_EXISTING_SCORER_ONLY',state=json.loads(q.stdout) if q.returncode==0 else None)));raise SystemExit
control.mkdir();output=root/'outputs'/run
create(control/'release.json',release);create(control/'capture.json',p['capture']);create(control/'settlement.json',p['settlement'])
config=dict(output=str(output),launch_sha256=sha(stage/'GPU-launch.json'),release_sha256=sha(control/'release.json'),
 collection_sha256=sha(output/'collection.json'),torch_home=str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/torch'),
 piq_site=str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/site'))
create(control/'score-config.json',config)
from four_card_bank24_execution_tools_r1 import process_environment
env=process_environment(root,control/'caches');old=read(base/'GPU-launch.json')['commands']['container_cli']
env['LD_LIBRARY_PATH']=next(v.split('=',1)[1] for v in old if v.startswith('LD_LIBRARY_PATH='))
actual_output=read(stage/'history104-storage.json')['output_mount']
cmd=['docker','run','-d','--name',name,'--network','none','--read-only','--cpus','2','--cpuset-cpus','4,5',
 '--memory','8g','--memory-swap','8g','--pids-limit','256','--tmpfs','/tmp:rw,size=512m',
 '--user',str(os.getuid())+':'+str(os.getgid()),'-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void',
 '-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2',
 '-v',str(root)+':'+str(root)+':ro','-v',str(stage)+':'+str(stage)+':rw',
 '-v',str(output)+':'+str(output)+':ro','-v',actual_output+':'+actual_output+':ro','-w',str(root/'runtime')]
cmd += [x for k,v in env.items() for x in ('-e',k+'='+str(v))]
cmd += [read(stage/'registration.json')['container_image'],'timeout','--signal=TERM','--kill-after=15s','86400',
 str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python'),str(stage/rel/'score.py'),'--manifest',str(card_path),'--stage',str(stage),'--control',str(control)]
create(control/'intent.json',dict(command=cmd,GPU_submissions=0))
q=subprocess.run(cmd,capture_output=True,text=True);result=dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr)
create(control/'launch.json',result);print(json.dumps(result))
'''

ANALYZE=PREFIX+'''
control=stage/'released-score-control';assert read(control/'scores.json')['status']=='COMPLETE_PENDING_ANALYSIS'
output=root/'outputs'/run
cmd=['python3',str(stage/rel/'analyze.py'),'--manifest',str(card_path),
 '--collection',str(output/'collection.json'),'--scores',str(control/'scores.json'),
 '--old-scores',str(base/'released-score-control/scores.json'),'--root',str(output),
 '--output',str(control/'complete_analysis.json')]
q=subprocess.run(cmd,capture_output=True,text=True,timeout=900)
print(json.dumps(dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,output=str(control/'complete_analysis.json'))))
'''

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('score','analyze'))
    parser.add_argument('--input',type=Path);parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=CARD)
    parser.add_argument('--route',choices=('ipv4','v6','relay'),default='ipv4');args=parser.parse_args()
    if args.receipt.exists():raise ValueError('Preserve the original operator response')
    data=json.loads(args.input.read_text()) if args.input else {}
    result=rpc(SCORE if args.action=='score' else ANALYZE,data,route=args.route)
    args.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
