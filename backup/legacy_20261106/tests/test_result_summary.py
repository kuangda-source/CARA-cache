import copy
import pytest
from wcomr.result_summary import summarize


def records():
    receipts = []
    for mode in ['native', 'worldcache']:
        receipts.append(dict(mode=mode, expected_samples=['a', 'b'], input_sha256='input',
            profile_sha256='profile', sampling_protocol_sha256='protocol', source_completion_commit='source',
            outcome_protocol={'version': 1}, torch='version', cuda='version',
            setup={'output_dir': mode, 'worldcache_enabled': mode == 'worldcache', 'keep_going': True},
            status='ATTEMPTED_ALL_WITH_REJECTIONS', rejections=[{'name':'b', 'outcome':'VIDEO_REJECTED'}],
            samples=[dict(name='a', index=0, cold_first_sample=True, end_to_end_seconds=10 if mode=='native' else 8,
                          stages={'denoising': {'seconds': 6 if mode=='native' else 3}},
                          block_counts={'denoiser_calls':72,'full_calls':72 if mode=='native' else 40,
                                        'skipped_deep_calls':0 if mode=='native' else 32})]))
    supervisor={'status':'PAIR_EXITED_AWAITING_RECEIPT_AND_VIDEO_REVIEW',
                'arms':[dict(mode=m,exit_code=0,stop_reason=None) for m in ['native','worldcache']]}
    return *receipts, supervisor, ['a','b']


def test_complete_attempts_retains_rejected_denominator_and_stage_ratios():
    result=summarize(*records())
    assert result['counts']['native']=={'accepted':1,'rejected':1,'not_recorded':0}
    assert result['pairs'][0]['native_over_worldcache']=={'end_to_end':1.25,'denoising':2}
    assert 'native_over_worldcache' not in result['pairs'][1]
    assert result['quality_status']=='NOT_REVIEWED'


def test_incomplete_arm_has_no_latency_ratio_even_for_existing_pairs():
    n,w,s,e=records(); w['status']='GENERATING'; w['rejections']=[]; s['status']='RUNNING'
    result=summarize(n,w,s,e)
    assert result['status']=='INCOMPLETE_NO_SPEED_CLAIM'
    assert result['counts']['worldcache']['not_recorded']==1
    assert all('native_over_worldcache' not in row for row in result['pairs'])


@pytest.mark.parametrize('failure',['config','duplicate','missing','nan','cold'])
def test_invalid_evidence_is_rejected(failure):
    n,w,s,e=records()
    if failure=='config': w['setup']['keep_going']=False
    if failure=='duplicate': w['samples'].append(copy.deepcopy(w['samples'][0]))
    if failure=='missing': w['rejections']=[]
    if failure=='nan': w['samples'][0]['end_to_end_seconds']=float('nan')
    if failure=='cold': w['samples'][0]['cold_first_sample']=False
    with pytest.raises(ValueError): summarize(n,w,s,e)
