"""Descriptive CPU reanalysis of frozen observations, with unmatched calls explicit."""
import hashlib
import json
from pathlib import Path

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

old_path='reports/w1d_cal8_r1_runner.json'
new_path='reports/wc_w1_own_state_runner_20261006.json'
audit_path='reports/wc_w1_own_state_final_original_native_audit_20261006.json'
endpoint_path='reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json'
manifest=read('manifests/wc_w1_own_state_execution_20261006.json')
assert sha(old_path)==manifest['payload_sha256'][old_path]
old,new,audit=map(read,[old_path,new_path,audit_path])
assert audit['status']=='OWN_STATE_NATIVE_SOURCE_COST_HANDLES_SIGNED_JOIN_AUDIT_PASS_NOT_CONF'
assert new['source_revision']==audit['GPU_source_revision']
assert new['status']=='OWN_STATE_THREE_SCENE_TECH_PASS_REQUIRES_TERMINAL_AUDIT'

def metric(records,kind):
    a=sum(r['candidates']['official'][kind]['mse'] for r in records)/len(records)
    b=sum(r['candidates']['scalar'][kind]['mse'] for r in records)/len(records)
    return {'calls':[r['call'] for r in records],'official_mean_MSE':a,'scalar_mean_MSE':b,
        'official_minus_scalar':a-b,'relative_reduction_percent':100*(1-b/a) if a>0 else None}

rows=[]
for case in new['cases']:
    assert case['bridge_pass']
    scene=case['name'];prior=next(v for v in old['cases'] if v['name']==scene)['on']['shadow_records']
    current=case['observed']['shadow_records'];selected=[r['call'] for r in current]
    matched=[r['call'] for r in prior if r['call'] in selected]
    pairs=[]
    for records in [current[:2],current[2:]]:
        pairs.append({'solver_update_one_based':(records[0]['call']+1)//2,
            'CFG_calls':[r['call'] for r in records],
            'metrics':{k:metric(records,k) for k in ['prewarp_residual','postwarp_residual','velocity']}})
    comparisons={}
    for kind in ['prewarp_residual','postwarp_residual','velocity']:
        comparisons[kind]={'old_all_recorded_points_descriptive_only':metric(prior,kind),
            'own_all_four_registered_points':metric(current,kind),
            'old_same_calls':metric([r for r in prior if r['call'] in matched],kind) if matched else None,
            'own_same_calls':metric([r for r in current if r['call'] in matched],kind) if matched else None}
    endpoint=next(v['existing_endpoint'] for v in audit['joined_rows'] if v['scene']==scene)
    rows.append({'scene':scene,'old_calls':[r['call'] for r in prior],'own_calls':selected,
        'matched_old_own_calls':matched,'unmatched_old_teacher_is_missing_not_zero':True,
        'same_state_candidates_valid_within_each_current_point':True,'pairs':pairs,
        'descriptive_state_comparison':comparisons,'existing_endpoint':endpoint,
        'same_video_sha256':case['observed']['video_sha256']})
result={'status':'OWN_STATE_CALL_ALIGNED_DESCRIPTIVE_REANALYSIS_NOT_CAUSAL_STATE_DECOMPOSITION',
    'sources':[{'path':p,'sha256':sha(p)} for p in [old_path,new_path,audit_path,endpoint_path]],
    'analysis_code_sha256':sha(__file__),'rows':rows,
    'same_call_different_state_and_history_not_single_variable_intervention':True,
    'branch_MSE_not_actual_CFG_combined_error':True,
    'CFG_error_cross_inner_product_missing':True,
    'phasewise_feature_error_sign_not_endpoint_label':True,
    'three_exposed_scenes_not_independent_confirmation':True,
    'GPU_submissions':0,'new_teacher_observations':0,'LPIPS_rescored':False}
target=Path('reports/wc_w1_own_state_call_alignment_exploratory_20261006.json')
assert not target.exists(),'Preserve original descriptive analysis'
target.write_text(json.dumps(result,indent=2)+'\n')
for row in rows:
    print(json.dumps({'scene':row['scene'],'matched_calls':row['matched_old_own_calls'],
        'pairs':[{ 'calls':p['CFG_calls'],'postwarp_reduction_percent':p['metrics']['postwarp_residual']['relative_reduction_percent'],
            'velocity_reduction_percent':p['metrics']['velocity']['relative_reduction_percent']} for p in row['pairs']],
        'old_matched_velocity':row['descriptive_state_comparison']['velocity']['old_same_calls'],
        'own_matched_velocity':row['descriptive_state_comparison']['velocity']['own_same_calls']}))
