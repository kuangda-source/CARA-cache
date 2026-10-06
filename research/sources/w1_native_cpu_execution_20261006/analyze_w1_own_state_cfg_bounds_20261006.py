"""CPU partial identification of linear CFG error, without inventing cross terms."""
import hashlib
import json
import math
from pathlib import Path

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

runner_path='reports/wc_w1_own_state_runner_20261006.json'
audit_path='reports/wc_w1_own_state_final_original_native_audit_20261006.json'
runner=read(runner_path);audit=read(audit_path)
native=read('.sync/w1-own-state-native-cfg-source-20261006.json')
denoise=read('.sync/w1-own-state-native-cfg-denoise-20261006.json')
assert audit['status']=='OWN_STATE_NATIVE_SOURCE_COST_HANDLES_SIGNED_JOIN_AUDIT_PASS_NOT_CONF'
assert runner['source_revision']==audit['GPU_source_revision']
assert denoise['budget_sha256']==native['budget_sha256']==audit['budget_sha256']
assert all(r['sha256']==runner['scope']['upstream_source_sha256'][r['path']] for r in native['sources'])
velocity=next(v['source'] for v in denoise['sources'] if v['name']=='velocity_fn')
assert 'cond_v = self.denoise(noise, noise_x, timestep, condition)' in velocity
assert 'uncond_v = self.denoise(noise, noise_x, timestep, uncondition)' in velocity
assert 'velocity_pred = uncond_v + guidance * (cond_v - uncond_v)' in velocity
assert '.float()' in next(v['source'] for v in denoise['sources'] if v['name']=='denoise')

rows=[]
for case,request in zip(runner['cases'],denoise['actual_requests']):
    assert request['name']==case['name'] and request['guidance']==7 and case['bridge_pass']
    g=request['guidance'];weights=[g,1-g];records=case['observed']['shadow_records']
    for pair in [records[:2],records[2:]]:
        assert [v['cfg_branch'] for v in pair]==[0,1]
        assert pair[0]['actual_input_identity']==pair[1]['actual_input_identity']
        bounds={}
        for method in ['official','scalar']:
            a,b=[v['candidates'][method]['velocity']['mse'] for v in pair]
            assert all(math.isfinite(x) and x>=0 for x in [a,b])
            x,y=abs(weights[0])*math.sqrt(a),abs(weights[1])*math.sqrt(b)
            bounds[method]={'branch_MSE':[a,b],'branch_equal_mean_MSE':(a+b)/2,
                'linear_mix_MSE_lower':(x-y)**2,'linear_mix_MSE_upper':(x+y)**2,
                'error_cross_inner_product':None}
        o,s=bounds['official'],bounds['scalar']
        guaranteed_improve=s['linear_mix_MSE_upper']<o['linear_mix_MSE_lower']
        guaranteed_degrade=s['linear_mix_MSE_lower']>o['linear_mix_MSE_upper']
        rows.append({'scene':case['name'],'calls':[v['call'] for v in pair],
            'same_solver_input':True,'branch_weights':weights,'bounds':bounds,
            'scalar_improvement_identified_without_cross_term':guaranteed_improve,
            'scalar_degradation_identified_without_cross_term':guaranteed_degrade,
            'comparison':'SCALAR_LINEAR_MIX_BETTER_BY_SEPARATED_BOUNDS' if guaranteed_improve else
                'SCALAR_LINEAR_MIX_WORSE_BY_SEPARATED_BOUNDS' if guaranteed_degrade else
                'UNIDENTIFIED_OVERLAPPING_BOUNDS_NOT_A_NEGATIVE_EFFECT'})

result={'status':'PINNED_NATIVE_CFG_WEIGHTS_AND_CPU_BOUNDS_COMPLETE_NOT_DIRECT_GUIDED_MSE',
    'sources':[{'path':p,'sha256':sha(p)} for p in [runner_path,audit_path]],
    'analysis_code_sha256':sha(__file__),'native_readonly_source_receipt':native,
    'native_readonly_denoise_and_actual_request_receipt':denoise,
    'native_guidance_formula':'uncond + guidance * (cond - uncond)',
    'actual_guidance':7,'weights_condition_negative_prompt':[7,-6],
    'native_net_to_denoise_transform':'float cast only; no extra output rescaling in denoise',
    'bound_formula':'(|alpha0|*sqrt(MSE0) - |alpha1|*sqrt(MSE1))^2 <= MSE_linear_mix <= (|alpha0|*sqrt(MSE0) + |alpha1|*sqrt(MSE1))^2',
    'bound_scope':'Conservative real-arithmetic linear mixture using recorded FP32-reduced branch MSE; not a bitwise floating-point or solver rollout certificate',
    'actual_CFG_combined_MSE':None,'solver_update_MSE':None,'new_teacher_observations':0,
    'pair_count':len(rows),'identified_better_pairs':sum(r['scalar_improvement_identified_without_cross_term'] for r in rows),
    'identified_worse_pairs':sum(r['scalar_degradation_identified_without_cross_term'] for r in rows),
    'unidentified_pairs':sum(r['comparison'].startswith('UNIDENTIFIED') for r in rows),
    'rows':rows,'new_GPU_submissions':0,'remote_writes':0,'budget_unchanged':True,
    'cross_term_zero_not_assumed':True,'no_Torch_or_generator_import':True,
    'independent_confirmation':False,'formal_refresh_training_labels':False}
target=Path('reports/wc_w1_own_state_cfg_bounds_exploratory_20261006.json')
assert not target.exists(),'Preserve original CPU analysis'
target.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','weights_condition_negative_prompt','pair_count',
    'identified_better_pairs','identified_worse_pairs','unidentified_pairs','new_GPU_submissions']}))
