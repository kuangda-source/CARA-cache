import copy
import pytest
from wcomr.same_state_summary import summarize


def fixture():
    run={'mode':'off','forward_output_sha256':['hash']*72,'block_counts':{'denoiser_calls':72},
         'trace':['same'],'cache_end_sha256':'cache','video_sha256':'video','sampling':{'timesteps':list(range(36))},'shadow_records':[]}
    on=copy.deepcopy(run);on['mode']='on'
    for call in [15,16,37,38]:
        candidates={}
        for mode,value in [('official',2.),('scalar',1.),('shrink',3.)]:
            candidates[mode]={kind:{'status':'OK','mse':value,'reference_mean_square':10.} for kind in ['prewarp_residual','postwarp_residual','velocity']}
            candidates[mode].update(reason=mode,history={'anchor_steps':[0,2]})
        on['shadow_records'].append({'call':call,'cache_counter':call-1,'cfg_branch':(call-1)%2,'candidates':candidates})
    receipt={'status':'SAME_STATE_CANDIDATE_DIAGNOSTIC_PARITY_PASS_SINGLE_SAMPLE','runs':[run,on],
             'checks':{'outputs':True},'protocol':{'shadow_calls':[15,16,37,38]}}
    supervisor={'status':'W1_SAME_STATE_EXITED_REQUIRES_REVIEW','arms':[{'exit_code':0,'stop_reason':None,'wall_seconds':500.}]}
    return receipt,supervisor


def test_mechanism_summary_keeps_scope_and_paired_error_ratios():
    r,s=fixture();out=summarize(r,s)
    assert out['status']=='MECHANISM_ONLY' and out['candidate_screen_signals']==['scalar']
    assert out['candidates']['scalar']['metrics']['velocity']['sum_mse_ratio']==.5
    assert out['candidates']['scalar']['metrics']['velocity']['improved_points']==4
    assert 'not quality' in out['scope']


@pytest.mark.parametrize('failure',['running','output','missing','truth','future','nonfinite'])
def test_unverified_or_noncomparable_receipts_cannot_produce_candidate_signal(failure):
    r,s=fixture()
    if failure=='running':s['status']='RUNNING'
    if failure=='output':r['runs'][1]['video_sha256']='changed'
    if failure=='missing':r['runs'][1]['shadow_records'].pop()
    if failure=='truth':r['runs'][1]['shadow_records'][0]['candidates']['scalar']['velocity']['reference_mean_square']=11.
    if failure=='future':r['runs'][1]['shadow_records'][0]['candidates']['scalar']['history']['anchor_steps']=[14]
    if failure=='nonfinite':r['runs'][1]['shadow_records'][0]['candidates']['scalar']['velocity']['mse']=float('nan')
    with pytest.raises(ValueError):summarize(r,s)
