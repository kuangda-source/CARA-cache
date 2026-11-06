import ast,gzip,hashlib,json,subprocess
from pathlib import Path
root='/home/gaokuangda/data/gkd/worldcache_omr'
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
read=lambda n:json.loads(Path(n).read_text())
manifest=read('manifests/wc_next_batch_cpu_analysis_r1_20261006.json');result=read('reports/wc_adaptive_count_scope_cpu_r1_20261006.json')
expected={root+'/outputs/wc-w3-small-cd-r1/diagnostic/receipt.json':result['rows'][0]['original_complete_runner_sha256'],root+'/outputs/wc-w3-small-human-complement-r1/diagnostic/receipt.json':result['rows'][1]['original_complete_runner_sha256'],root+'/outputs/w1-replay-r1/w1-replay.json':manifest['input_sha256']['reports/w1_replay_r1_runner.json'],root+'/reports/budget.json':manifest['input_sha256']['reports/budget.json']}
replay=read('reports/w1_replay_r1_runner.json')
for c in replay['cases']:
 a=c['scalar_off']
 if a['outcome']=='ACCEPTED':expected[a['video_path']]=a['video_sha256']
old=read('manifests/wc_exploratory_hypotheses_r1_20261005.json')
remote='ROOT='+repr(root)+'\nEXPECTED='+repr(expected)+'\nNAMES='+repr([c['name'] for c in replay['cases']])+'\n'+r'''
import json,pathlib,hashlib,os,statistics,time,subprocess
root=pathlib.Path(ROOT)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert all(sha(path)==digest for path,digest in EXPECTED.items())
rows=[]
for run in ['wc-w3-small-cd-r1','wc-w3-small-human-complement-r1']:
 raw=json.loads((root/'outputs'/run/'diagnostic/receipt.json').read_text())
 for r in raw['requests']:
  if len(r.get('children',[]))!=6:continue
  by={c['label']:c for c in r['children']};target=r['target_call'];arms={}
  prefix=[sum(d>0 for i,d in enumerate(r['deep'][:44]) if i%2==s) for s in [0,1]]
  for action in ['C','D']:
   events=by[action+'_first']['record']['action_report']['suffix_events']
   count=lambda seq:[len([e for e in seq if e['actual_action']=='D' and e['cfg_slot']==s]) for s in [0,1]]
   arms[action]={'full_by_CFG':count(events),'before_target':count([e for e in events if e['call']<target]),'target':count([e for e in events if e['call']==target]),'after_target':count([e for e in events if e['call']>target]),'control_wall_median':statistics.median([by[action+'_'+k]['record']['control_wall_seconds'] for k in ['first','second']]),'derived_whole_full_by_CFG':[a+b for a,b in zip(prefix,count(events))]}
  rows.append({'scene':r['sample_name'],'target_call':target,'shared_prefix_full_by_CFG':prefix,'arms':arms})
started=time.monotonic();files=0;videos=[];complete=True;walk_errors=[]
def on_error(e):walk_errors.append(str(e))
for directory,dirs,names in os.walk(root/'outputs',followlinks=False,onerror=on_error):
 for name in names:
  files+=1
  if files>200000 or time.monotonic()-started>20:complete=False;break
  if name.endswith('.mp4') and pathlib.Path(name).stem in NAMES:
   p=pathlib.Path(directory)/name
   videos.append({'path':str(p),'scene':p.stem,'bytes':p.stat().st_size})
 if not complete:break
ledger=json.loads((root/'reports/budget.json').read_text())
print(json.dumps({'status':'EXISTING_NATIVE_ORIGINAL_COUNT_RECOMPUTE_AND_BOUNDED_REFERENCE_INVENTORY_PASS','observed_unix':time.time(),'native_sha256':EXPECTED,'native_source_and_video_count':len(EXPECTED),'independent_counts':rows,'reference_inventory':{'root':str(root/'outputs'),'files_visited':files,'walk_complete_within_bounds':complete,'walk_errors':walk_errors,'matching_video_paths':videos,'compatibility_proven_by_path':False},'budget':ledger,'budget_sha256':sha(root/'reports/budget.json'),'B_output_exists':(root/'outputs/wc-w3-placement-swap-r1').exists(),'B_approval_exists':(root/'manifests/wc_w3_placement_gpu_authorization_20261005.json').exists(),'server_writes':0,'GPU_submissions':0}))
'''
p=subprocess.run(ssh+['python3 -'],input=remote,text=True,capture_output=True,timeout=55);assert p.returncode==0,p.stderr[-1200:]
x=json.loads(p.stdout)
assert x['budget']==read('reports/budget.json')
for output,actual in zip(result['rows'],x['independent_counts']):
 assert output['scene']==actual['scene'] and output['target_call']==actual['target_call']
 for action in ['C','D']:
  a=actual['arms'][action];b=output['arms'][action]
  assert (a['full_by_CFG'],a['before_target'],a['target'],a['after_target'],a['control_wall_median'])==(b['full_calls_by_CFG'],b['before_target_full_by_CFG'],b['target_full_by_CFG'],b['after_target_full_by_CFG'],b['control_wall_median_seconds'])
x.update(analysis_report_sha256=hashlib.sha256(Path('reports/wc_adaptive_count_scope_cpu_r1_20261006.json').read_bytes()).hexdigest(),audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),independent_recompute_imports_analysis_script=False)
out=Path('reports/wc_next_batch_existing_native_audit_r1_20261006.json');assert not out.exists();out.write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps({k:x[k] for k in ['status','native_source_and_video_count','independent_counts','reference_inventory','B_output_exists','B_approval_exists']}))
