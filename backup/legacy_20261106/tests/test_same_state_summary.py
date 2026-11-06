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


@pytest.mark.parametrize('change',['none','output','config','coefficient','control'])
def test_one_variable_revision_requires_same_official_trajectory_config_and_shrink_control(change):
    from wcomr.same_state_summary import compare_recent_revision
    first,_=fixture();second=copy.deepcopy(first)
    for r in [first,second]:
        r['setup']={'output_dir':'one','worldcache_enabled':True}
        r['sample']={'name':'AV','seed':0}
        r['protocol'].update(sample='AV',calibration_defaults={'decay':.9,'clip':4.})
    second['setup']['output_dir']='two';second['protocol']['calibration_defaults']['decay']=0.
    if change=='output':
        for run in second['runs']:run['video_sha256']='different'
    if change=='config':second['sample']['seed']=1
    if change=='coefficient':second['protocol']['calibration_defaults']['clip']=2.
    if change=='control':second['runs'][1]['shadow_records'][0]['candidates']['shrink']['velocity']['mse']=4.
    if change=='none':
        out=compare_recent_revision(first,second)
        assert out['shrink_scores_identical']
        assert out['scalar_recent_over_initial_sum_mse_ratio']['velocity']==1.
    else:
        with pytest.raises(ValueError):compare_recent_revision(first,second)


def test_decode_audited_video_difference_is_scoped_to_numeric_contrast_not_video_reproducibility():
    from wcomr.same_state_summary import compare_recent_revision
    first,_=fixture();second=copy.deepcopy(first)
    for r in [first,second]:
        r.update(setup={'output_dir':'one'},sample={'name':'AV','seed':0})
        r['protocol'].update(sample='AV',calibration_defaults={'decay':.9})
    second['protocol']['calibration_defaults']['decay']=0.
    for run in second['runs']:run['video_sha256']='different'
    audit={'status':'CROSS_RUN_FULL_DECODE_CHECK','runs':[
        {'video_sha256':sha,'frames':93,'shape':[432,768,3],'all_frames_same_shape':True} for sha in ['video','different']],
        'timestamps_identical':True,'decoded_rgb_identical':False}
    out=compare_recent_revision(first,second,audit)
    assert out['status']=='MATCHED_DENOISER_ONLY_RECENT_PAIR_CONTRAST'
    assert out['artifact_reproducibility']=='POST_MODEL_VIDEO_MISMATCH_UNRESOLVED'
    assert out['decoded_rgb_identical'] is False
    assert out['shrink_scores_identical']
