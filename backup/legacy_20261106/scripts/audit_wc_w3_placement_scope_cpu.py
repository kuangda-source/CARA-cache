#!/usr/bin/env python3
"""Independent raw-parent and complete-control cost audit, pure local CPU."""
import ast,copy,gzip,hashlib,json,math
from pathlib import Path
from wcomr.rv0_placement_scope import validate_scope, scope_from_parents, cost_proposal
from wcomr.rv0_fixed_plan import cfg_full_counts
c=json.loads(Path('configs/wc_w3_placement_scope_r1_draft.json').read_text())
r=json.loads(Path('reports/wc_w3_placement_scope_cpu_preparation_r1_20261004.json').read_text())
old=json.loads(Path('reports/wc_w3_small_window_cpu_preparation_20261004.json').read_text())
before=Path('reports/budget.json').read_bytes()
for n,d in c['source_receipt_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==d,n
assert hashlib.sha256(Path('configs/wc_w3_placement_scope_r1_draft.json').read_bytes()).hexdigest()==r['config_sha256']
validate_scope(c['scope'],old['selected_parent_mask_swaps'])
fair=json.loads(gzip.decompress(Path('reports/wc_fair_cal_r1_runner_20261004.json.gz').read_bytes()))
for scene, request in zip(c['scope']['scenes'],fair['measurements']['requests']):
 phase=next(p for p in request['phases'] if p['workpoint']['name']=='wc006')
 assert scene['scene']==request['sample_name']
 mask=['D' if v['deep_executed'] else 'C' for v in phase['trace']]
 assert [v['call'] for v in phase['trace']]==list(range(1,73))
 assert mask==scene['parent_action_mask']
 for row in scene['swaps']:
  n,m=row['calls'];slot=row['CFG_slot'];modified=mask.copy();modified[n-1],modified[m-1]='D','C'
  assert (n-1)%2==(m-1)%2==slot and mask[n-1]=='C' and mask[m-1]=='D'
  assert [i+1 for i,(a,b) in enumerate(zip(mask,modified)) if a!=b]==[n,m]
  assert cfg_full_counts(mask)==cfg_full_counts(modified)==tuple(scene['parent_full_counts_per_CFG'])
  assert modified[:44]==mask[:44] and modified[68:]==mask[68:]
 assert len(scene['controls'])==8 and sum(x['encode'] for x in scene['controls'])==4
 assert [x['label'] for x in scene['controls']]==['OFF1','OFF2','BASE1','SWAP0_first','SWAP1_first','SWAP1_second','SWAP0_second','BASE2']
assert c['scope']['parent_phases']==2 and c['scope']['complete_suffix_controls']==16 and c['scope']['new_encoded_outputs']==10
assert c['scope']['Native_relative_video_losses']==6 and c['scope']['signed_swap_diagnostics']==4
ref=json.loads(Path('configs/wc_w3_small_cd_production_r1_draft.json').read_text())
assert c['references']==ref['references'] and c['historical_reference_bindings']==ref['historical_reference_bindings']
restore=json.loads(Path('reports/wc_rv0_restore_r1_summary_20261004.json').read_text())
runner=json.loads(Path('reports/wc_rv0_restore_r1_runner_20261004.json').read_text())
summary=json.loads(Path('reports/wc_fair_cal_r1_summary_20261004.json').read_text())
load=runner['load_seconds'];parent=max(x['parent_pipeline_including_diagnostics_wall_seconds']-sum(v['inclusive_wall_seconds'] for v in x['suffixes']) for x in restore['rows'])
suffix=max(v['inclusive_wall_seconds'] for x in restore['rows'] for v in x['suffixes'])
native=max(x['pipeline_wall_seconds'] for x in summary['rows'] if x['variant']=='native35')
nominal=(load+2*parent+16*suffix+8*30+75)*1.2+30
stress=(load+2*parent+16*(native+25)+8*30+75)*1.2+30
assert math.isclose(nominal,r['cost']['nominal_complete_seconds'],rel_tol=0,abs_tol=1e-10)
assert math.isclose(stress,r['cost']['stress_proxy_complete_seconds'],rel_tol=0,abs_tol=1e-10)
assert c['scope']['GPU_timeout_seconds'] is None and c['scope']['GPU_execution_selected'] is False
rejected=[]
def refuse(name,fn):
 try:fn()
 except (ValueError,KeyError):rejected.append(name)
 else:raise AssertionError('Invalid placement scope accepted: '+name)
for name,mutate in [('missing_repeat',lambda x:x['scenes'][0]['controls'].pop()),
 ('fewer_outputs',lambda x:x.update(new_encoded_outputs=8)),
 ('quota_is_seconds',lambda x:x.update(equal_seconds_established=True)),
 ('online_future_mask',lambda x:x.update(online_policy=True)),
 ('single_step_label',lambda x:x.update(single_step_RV_training_labels=True)),
 ('GPU_selected',lambda x:x.update(GPU_execution_selected=True)),
 ('unpriced_timeout',lambda x:x.update(GPU_timeout_seconds=3240))]:
 x=copy.deepcopy(c['scope']);mutate(x);refuse(name,lambda:validate_scope(x,old['selected_parent_mask_swaps']))
x=copy.deepcopy(old['selected_parent_mask_swaps']);x[1]['cfg_slot']=0
refuse('total_count_only_mismatch',lambda:scope_from_parents(x))
x=copy.deepcopy(old['selected_parent_mask_swaps']);x[0]['selection_reads_video_score_or_local_error']=True
refuse('endpoint_selection_leak',lambda:scope_from_parents(x))
refuse('silently_fewer_pairs',lambda:scope_from_parents(old['selected_parent_mask_swaps'][:3]))
refuse('nonfinite_price',lambda:cost_proposal(load,parent,float('nan'),native,7119.663527378818))
for f in ['src/wcomr/rv0_placement_scope.py','scripts/prepare_wc_w3_placement_scope_cpu.py']:ast.parse(Path(f).read_text())
legacy=json.loads(Path('manifests/wc_w3_small_cd_production_cpu_r1_20261004.json').read_text())
for n,d in legacy['payload_sha256'].items():
 assert hashlib.sha256(Path(legacy['source_path_by_stage_path'][n]).read_bytes()).hexdigest()==d,n
assert before==Path('reports/budget.json').read_bytes()
a={'status':'PLACEMENT_SCOPE_RAW_PARENT_FULL_COST_LOCAL_CPU_AUDIT_PASS_NOT_GPU',
 'scope':{'parents':2,'complete_suffixes':16,'new_outputs':10,'science_pairs':4,'Native_relative_losses':6,'signed_diagnostics':4},
 'independent_parent_raw_trace_check':True,'independent_complete_cost_formula_check':True,
 'reject_controls':rejected,'reject_control_count':len(rejected),
 'nominal_complete_seconds':nominal,'stress_proxy_complete_seconds':stress,
 'budget_unchanged':True,'GPU_submissions':0,'real_swap_video_results':0,
 'audit_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'config_sha256':r['config_sha256'],'old_A_CPU80_source_unchanged':True,
 'limits':'Local static science/cost preparation only. Four swaps correlated within two exposed CAL scenes. No branch-own-state GPU legality, equal runtime, online policy or training labels.'}
Path('reports/wc_w3_placement_scope_cpu_audit_r1_20261004.json').write_text(json.dumps(a,indent=2)+'\n')
print(json.dumps(a))
