import copy
import types
import pytest
import torch
from wcomr.w1d import select_pairs,grouped_error,validate_geometry,validate_pair
from wcomr.same_state import SameStateProbe
from test_same_state import same_model
from test_integration import model,run


def trace(count=20):
    return [{'call':i+1,'cache_counter_before':i,'deep_executed':i<6} for i in range(count)]


def test_selection_uses_only_earlier_full_anchors_and_covers_eligible_ranks():
    t=trace();result=select_pairs(t)
    assert result['calls']==[7,8,11,12,15,16,19,20]
    assert all(pair['anchor_steps']==[[2,4],[3,5]] for pair in result['selected_pairs'])
    assert result['coverage']=='FULL_FOUR_PAIR_SCREEN'
    small=select_pairs(trace(8));assert small['calls']==[7,8] and small['coverage']=='INSUFFICIENT_SKIP_COVERAGE'
    restarted=t+[{'call':21+i,'cache_counter_before':i,'deep_executed':False} for i in range(4)]
    assert select_pairs(restarted)==result  # Reset destroys both histories.
    assert select_pairs([])['calls']==[]
    with pytest.raises(ValueError):select_pairs(t[:-1])
    malformed=copy.deepcopy(t);malformed[1]['cache_counter_before']=0
    with pytest.raises(ValueError):select_pairs(malformed)


@pytest.mark.parametrize('kind,shape',[('residual',(1,5,3,7,9)),('velocity',(1,9,5,3,7))])
def test_group_partitions_cover_tensor_and_preserve_weighted_error_rng(kind,shape):
    x=torch.ones(shape);p=x.clone();p.flatten()[::7]+=2
    rng=torch.random.get_rng_state().clone();version=x._version;score=grouped_error(p,x,kind)
    assert torch.equal(rng,torch.random.get_rng_state()) and x._version==version
    for groups in score['partitions'].values():
        assert sum(g['elements'] for g in groups)==x.numel()
        weighted=sum(g['metrics']['mse']*g['elements'] for g in groups)/x.numel()
        assert weighted==pytest.approx(score['mse'])
    assert grouped_error(torch.ones(1,1,1,1,1),torch.zeros(1,1,1,1,1),kind)['relative_mse'] is None
    with pytest.raises(ValueError):grouped_error(torch.ones(2),torch.ones(2),kind)


def test_velocity_geometry_is_explicit_and_wrong_mapping_fails():
    net=types.SimpleNamespace(patch_temporal=1,patch_spatial=2)
    validate_geometry(net,torch.ones(1,3,4,5,8),torch.ones(1,2,3,8,10))
    with pytest.raises(ValueError):validate_geometry(net,torch.ones(1,3,4,5,8),torch.ones(1,3,8,10,2))


def test_grouped_same_state_probe_preserves_deployment_and_global_scores():
    probe=SameStateProbe([8,9,10,11,12],{'decay':0},grouped=True);probe.begin_request('grouped')
    scored=same_model(probe);plain=model('official').eval()
    for net in [scored,plain]:
        net.patch_spatial=net.patch_temporal=1
        net.unpatchify=lambda x:x.permute(0,4,1,2,3)
    rng=torch.random.get_rng_state().clone();a,b=run(plain,12),run(scored,12)
    assert torch.equal(rng,torch.random.get_rng_state())
    assert all(torch.equal(x,y) for x,y in zip(a,b))
    assert len(probe.records)==5
    for record in probe.records:
        for m in ['official','scalar','shrink']:
            for k in ['prewarp_residual','postwarp_residual','velocity']:
                assert set(record['candidates'][m][k]['partitions'])=={'time','channel','spatial'}


def test_rejections_are_preserved_and_pair_validator_rejects_changed_raw_decode():
    a={k:[] for k in ['guardrail_events','forward_output_sha256','trace','pipeline_events','decoder_calls','decoded_rgb']}
    a.update(outcome='TEXT_REJECTED',block_counts={},cache_end_sha256='old',sampling=None,video_sha256=None,
             flags_before={},flags_after={},shadow_records=[])
    assert all(validate_pair(a,copy.deepcopy(a),{'calls':[]}).values())
    b=copy.deepcopy(a);b['pipeline_events']=[{'stage':'decode_output','value':'changed'}]
    with pytest.raises(ValueError):validate_pair(a,b,{'calls':[]})


def test_partial_summary_does_not_decide_and_retains_rejection_denominator():
    from wcomr.w1d_summary import summarize
    a={k:[] for k in ['guardrail_events','forward_output_sha256','trace','pipeline_events','decoder_calls','decoded_rgb']}
    a.update(outcome='TEXT_REJECTED',block_counts={},cache_end_sha256='old',sampling=None,video_sha256=None,
             flags_before={},flags_after={},shadow_records=[])
    case={'name':'rejected','status':'PAIR_PARITY_PASS','off':a,'on':copy.deepcopy(a),'selection':{'calls':[]},'coverage':'INSUFFICIENT_SKIP_COVERAGE'}
    r={'status':'GENERATING','protocol':{'samples':['rejected']+[str(i) for i in range(7)]},'cases':[case]}
    s=summarize(r,partial=True)
    assert s['status']=='LIVE_PARTIAL_NO_DECISION' and s['text_rejected']==1 and s['completed_pair_samples']==1
    assert s['candidate_signals']==[] and s['aggregate']['scalar']['mean_sample_velocity_mse_ratio'] is None
    with pytest.raises(AssertionError):summarize(r)


def test_zero_reference_sample_prevents_false_aggregate_signal():
    from wcomr.w1d_summary import summarize
    cases=[]
    for i in range(8):
        points=[]
        for call in range(1,9):
            scores={}
            for mode in ['official','scalar','shrink']:
                value=0.0 if i==7 else (1.0 if mode=='official' else .5)
                metric={'status':'OK','mse':value,'partitions':{'time':[{'metrics':{'status':'OK'}}]}}
                scores[mode]={k:copy.deepcopy(metric) for k in ['prewarp_residual','postwarp_residual','velocity']}
                scores[mode].update(reason=mode,history={'anchor_steps':[0,2]})
            points.append({'call':call,'cache_counter':call+4,'cfg_branch':(call-1)%2,'candidates':scores,
                           'truth_tail_seconds':0,'diagnostic_seconds':0})
        off={k:[] for k in ['guardrail_events','forward_output_sha256','trace','pipeline_events','decoder_calls','decoded_rgb']}
        off.update(outcome='ACCEPTED',block_counts={},cache_end_sha256='x',sampling=None,video_sha256='v',flags_before={},flags_after={},shadow_records=[])
        on=copy.deepcopy(off);on['shadow_records']=points
        cases.append({'name':str(i),'status':'PAIR_PARITY_PASS','off':off,'on':on,'selection':{'calls':list(range(1,9))},'coverage':'FULL_FOUR_PAIR_SCREEN'})
    r={'status':'W1D_CAL8_ATTEMPTED_ALL_PARITY_PASS','protocol':{'samples':[str(i) for i in range(8)]},'cases':cases}
    s=summarize(r);assert s['status']=='INCONCLUSIVE_CAL8' and s['candidate_signals']==[]
    assert s['aggregate']['scalar']['mean_sample_velocity_mse_ratio'] is None
