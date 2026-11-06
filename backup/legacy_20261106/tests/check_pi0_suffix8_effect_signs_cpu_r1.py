"""Planted signed effects: preserve D/P role reversal and harmful states."""
import copy,importlib.util,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('independent_suffix_effects',R/'scripts/analyze_wc_pi0_suffix8_complete_cpu_r1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
states=json.loads((R/'configs/wc_pi0_suffix8_full266_production_r1_20261013.json').read_text())['states']
final={'parents':[],'outputs':[],'comparisons':[]}
planted=[.1,-.05,0.,.02]
for i,s in enumerate(states):
    n=s['chosen']['step'];scene=s['scene'];default=s['default_readout']
    final['parents'].append({'scene':scene,'actual_pair_computations':36+2*(37-n),
        'all36_guided_actions_final_and93RGB_original_equal':True,'default_suffix_all_remaining_original_equal':True})
    branch={}
    for readout in ('C','A'):
        f=[.4+.001*j-(planted[i] if readout=='A' else 0.) for j in range(93)]
        row={'scene':scene,'label':'DEFAULT_PI0' if readout==default else 'ALTERNATIVE','first_readout':readout,
            'LPIPS':{'frame_distances':f,'mean_LPIPS':mean(f)},'instrumented_remaining_main_seconds':10.+(2. if readout=='A' else 0.),
            'actual_suffix_actions':['CC']*(37-n),'actual_suffix_counts':{'CC':37-n}}
        branch[readout]=row;final['outputs'].append(row)
    d,o=branch[default],branch[s['alternative_readout']]
    final['outputs'].append({**copy.deepcopy(d),'label':'PARENT_PI0'})
    final['comparisons'].append({'scene':scene,
        'Y_quality_default_minus_alternative':d['LPIPS']['mean_LPIPS']-o['LPIPS']['mean_LPIPS'],
        'Y_instrumented_time_default_minus_alternative':d['instrumented_remaining_main_seconds']-o['instrumented_remaining_main_seconds']})
out=module.effects(final,states)
assert all(math.isclose(r['A_quality_gain_relative_C'],gain,abs_tol=1e-12) for r,gain in zip(out,planted))
assert [r['A_better_frames'] for r in out]==[93,0,0,93] and [r['A_worse_frames'] for r in out]==[0,93,0,0]
assert all(r['A_compute_interval_time_gain_relative_C']==-2. for r in out)
assert out[0]['Yq_default_minus_alternative']<0 and out[1]['Yq_default_minus_alternative']>0
assert out[3]['Yq_default_minus_alternative']>0
assert math.isclose(mean(r['A_quality_gain_relative_C'] for r in out),.0175,abs_tol=1e-12)
refused=[]
for kind in ('missing_output','wrong_primary_sign','default_not_parent','partial_frames','nonfinite','wrong_future_count'):
    bad=copy.deepcopy(final)
    if kind=='missing_output':bad['outputs'].pop()
    elif kind=='wrong_primary_sign':bad['comparisons'][0]['Y_quality_default_minus_alternative']*=-1
    elif kind=='default_not_parent':bad['outputs'][2]['LPIPS']['frame_distances'][0]+=.1
    elif kind=='partial_frames':bad['outputs'][0]['LPIPS']['frame_distances'].pop()
    elif kind=='nonfinite':bad['outputs'][0]['LPIPS']['frame_distances'][0]=float('nan')
    else:bad['outputs'][0]['actual_suffix_counts']['CC']-=1
    try:module.effects(bad,states)
    except AssertionError:refused.append(kind)
    else:raise AssertionError('Invalid full-scope/sign data accepted: '+kind)
receipt={'status':'PI0_SUFFIX8_SIGN_ORIENTATION_HARMFUL_EQUAL_AND_FULL_SCOPE_CPU_PASS_NOT_VIDEO_RESULT',
    'synthetic_states':4,'frames_per_synthetic_video':93,'known_A_quality_gains':planted,
    'default_role_reversal_and_A_time_penalty_preserved':True,'refusals':refused,'GPU_submissions':0,'ledger_written':False}
print(json.dumps(receipt))
