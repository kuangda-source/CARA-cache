import copy
import numpy as np
import pytest
from wcomr.replay_results import strict_parity,candidate_parity,summarize,validate_schedule_receipt
from wcomr.video_difference import score_frames


def fixture():
    schedule=[{'call':i+1,'cache_counter_before':i,'deep_executed':i<6} for i in range(8)]
    arm={k:[] for k in ['guardrail_events','forward_output_sha256','trace','pipeline_events','decoder_calls','decoded_rgb']}
    arm.update(outcome='ACCEPTED',forward_output_sha256=['x']*8,trace=copy.deepcopy(schedule),
        block_counts={'denoiser_calls':8,'full_calls':6,'skipped_deep_calls':2},cache_end_sha256='x',sampling={},
        video_sha256='v',flags_before={},flags_after={},calibration_end_sha256='anchors',shadow_records=[],seconds_with_hashing_and_diagnostics=1,
        replay={'mode':'scalar','calibration_params':{'decay':0},'records':[{'call':i+1,'cache_counter_before':i,'planned_full':i<6,
           'natural_skip':i>=6,'execution_verified':True,'prediction':{'reason':'scalar','history':{'anchor_steps':[2,4],'numerator':1.,'denominator':1.},'beta':1.} if i>=6 else None} for i in range(8)]})
    entry={'name':'0','schedule':schedule,'first_gate_shadow_calls':[7,8]}
    on=copy.deepcopy(arm);on['shadow_records']=[{'call':c,'metrics':{'residual':{'status':'OK','mse':1.,'relative_mse':None,'groups':{}},'velocity':{'status':'OK','mse':1.,'relative_mse':1.,'groups':{}}}} for c in [7,8]]
    return entry,arm,on


def test_schedule_and_candidate_gate_reject_changed_cache_decode_or_future_anchor():
    entry,off,on=fixture()
    assert all(candidate_parity(off,on,entry).values())
    for key in ['cache_end_sha256','calibration_end_sha256','pipeline_events']:
        bad=copy.deepcopy(on);bad[key]='changed'
        with pytest.raises(ValueError):candidate_parity(off,bad,entry)
    bad=copy.deepcopy(off);bad['replay']['records'][-1]['prediction']['history']['anchor_steps']=[6,7]
    with pytest.raises(ValueError,match='future'):validate_schedule_receipt(bad,entry)
    bad=copy.deepcopy(off);bad['trace'][-1]['deep_executed']=True
    with pytest.raises(ValueError,match='trace'):validate_schedule_receipt(bad,entry)


def test_full_summary_revalidates_original_reference_not_just_gate_booleans():
    entry,off,on=fixture()
    cases=[{'name':str(i),'status':'REPLAY_COMPLETED','scalar_off':copy.deepcopy(off)} for i in range(8)]
    cases[0]['scalar_on']=on
    entries=[dict(copy.deepcopy(entry),name=str(i)) for i in range(8)]
    r={'status':'W1_REPLAY_ATTEMPTED_ALL_TECH_PASS','protocol':{'samples':entries,'calibration_defaults':{'decay':0}},
       'cases':cases,'official_gate':copy.deepcopy(off),'gates':{'official_reference_pass':True,'candidate_parity_pass':True}}
    reference={'cases':[{'off':copy.deepcopy(off)}]}
    s=summarize(r,reference=reference);assert s['accepted']==8 and s['status']=='FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED'
    reference['cases'][0]['off']['video_sha256']='different'
    with pytest.raises(ValueError,match='exact parity'):summarize(r,reference=reference)
    r['status']='GENERATING';r['cases']=r['cases'][:1]
    assert summarize(r,partial=True)['status']=='PARTIAL_REPLAY_NO_QUALITY_DECISION'
    with pytest.raises(ValueError):summarize(r)


def test_full_rgb_difference_and_temporal_variation_are_exact_and_not_quality():
    def frames(values):
        return [(np.full((2,2,3),value,dtype=np.uint8),i,'1/16') for i,value in enumerate(values)]
    s=score_frames(frames([0,10,20]),frames([2,12,22]),expected_frames=3)
    assert s['rgb_mse']==4 and s['rgb_mae']==2 and s['rgb_max_abs_difference']==2
    assert s['reference_temporal_rgb_mae']==s['candidate_temporal_rgb_mae']==10
    same=score_frames(frames([0,0,0]),frames([0,0,0]),expected_frames=3)
    assert same['identical_rgb'] and same['psnr_db'] is None
    with pytest.raises(ValueError,match='frame counts'):score_frames(frames([0,1]),frames([0]),expected_frames=2)
    altered=frames([0,1]);altered[1]=(altered[1][0],4,'1/16')
    with pytest.raises(ValueError,match='PTS'):score_frames(frames([0,1]),altered,expected_frames=2)
