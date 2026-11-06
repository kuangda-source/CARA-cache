"""Complete B36 tiny paths, frozen candidates and collector failure boundaries."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_b36_r1 import bind_handoff,make_requests,execute_B36,formal_sources
from wcomr.full_sampling import CompleteStateRoundtrip
from test_cara_fast_b36_r1 import metadata_fixture

ROOT = Path(__file__).resolve().parents[1]


def body(inference,selected,wc,rf,common,unused_initial,profile,root,
         native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as fixture
    model,net = inference.pipe.model,inference.pipe.model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    origin = initial.fingerprint()
    # The two existing flow exercises cover opposite ends of each finite grid.
    card,package,_ = metadata_fixture(root/'synthetic-A',host,int(flow))
    binding = bind_handoff(card,package,host=host,gpu_uuid='GPU-CPU-CONTROL')
    kwargs = dict(inference=inference,samples=samples,card=card,common=common,
        ra_binding=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text()),
        host=host,cpu_validation=True)
    originals = (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    last_RGB = [None]
    current_slot = [None]
    writer_fault = [None]
    original_writer = inference_module.save_img_or_video
    def writer(video,path,fps):
        if current_slot[0] == writer_fault[0] and writer_fault[0] is not None:
            raise OSError('DECLARED_B36_WRITER_FAILURE')
        last_RGB[0] = np.array(video,copy=True)
        return original_writer(video,path,fps)
    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)
    visited = []
    def before(slot):
        restored();initial.restore();assert initial.fingerprint()==origin
        current_slot[0] = slot['id'];visited.append(slot['id'])
    def make():
        return make_requests(binding,**kwargs)
    saved = []
    def save(state):
        # The real collector must return serializable, complete producer rows.
        saved.append(json.loads(json.dumps(state,allow_nan=False)))
    observations = {}
    repeat_checks = []
    class Observed:
        def __init__(self,inner):self.inner=inner
        def __getattr__(self,name):return getattr(self.inner,name)
        def __call__(self,slot,output):
            result = self.inner(slot,output)
            restored()
            assert result['CPU_fixture'] is True and result['status']=='COMPLETE'
            assert result['audit_enabled'] is False and 'guided' not in result
            assert all(result[key]==0 for key in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
            concrete = card['roles'][result['concrete_role']]
            if concrete['kind']=='policy':
                assert [row['actual'] for row in result['semantic_history']]==concrete['policy']['actions']
            key=(slot['member'],slot['role'])
            observed=dict(latent=result['final_latent'].clone(),RGB=last_RGB[0].copy(),RNG=torch.get_rng_state().clone())
            if slot['section']=='B_QUALITY':observations[key]=observed
            elif slot['section']=='B_REPEAT' and key in observations:
                reference=observations[key]
                assert torch.equal(reference['latent'],observed['latent'])
                assert np.array_equal(reference['RGB'],observed['RGB'])
                assert torch.equal(reference['RNG'],observed['RNG'])
                repeat_checks.append(slot['id'])
            return result
    with clean.patched(inference_module,'save_img_or_video',writer):
        entry=make()
        A_slot=next(slot for slot in card['physical_matrix'] if slot['phase']=='A')
        try:entry(A_slot,root/'A-slot-forbidden')
        except ValueError:pass
        else:raise AssertionError('B36 adapter accepted an A slot')
        assert not entry.seen
        try:make_requests(binding,**{**kwargs,'cpu_validation':False})
        except ValueError:pass
        else:raise AssertionError('Synthetic A handoff gained GPU authority')
        result=execute_B36(Observed(entry),binding,root/'complete-B',before_request=before,save=save)
        expected=[slot for slot in card['physical_matrix'] if slot['phase']=='B']
        assert visited==[slot['id'] for slot in expected] and len(entry.seen)==36
        assert len(formal_sources(card,binding,result,cpu_validation=True))==32
        for slot in expected:
            concrete=card['roles'][slot['role']]
            if concrete['kind']=='selection':
                row=next(row for row in result['rows'] if row['slot']['id']==slot['id'])
                assert row['result']['concrete_role']==binding['frozen']['selected'][concrete['family']]['candidate']
        before_replay=len(visited)
        try:execute_B36(make(),binding,root/'complete-B',before_request=before,save=save)
        except FileExistsError:pass
        else:raise AssertionError('Existing B36 output was replayed')
        assert len(visited)==before_replay
        # A real writer exception consumes the slot; the collector saves the
        # complete36 denominator and preserves all not-reached positions.
        visited.clear();saved.clear();failure_entry=make();writer_fault[0]=expected[8]['id']
        try:execute_B36(failure_entry,binding,root/'failed-B',before_request=before,save=save)
        except OSError as error:assert 'DECLARED_B36_WRITER_FAILURE' in str(error)
        else:raise AssertionError('Writer exception swallowed')
        restored();failed=saved[-1]
        assert failed['status']=='FAILED_NO_REPLAY' and len(failed['rows'])==36
        assert failed['rows'][8]['status']=='TECH_FAILED'
        assert all(row['status']=='NOT_REACHED' for row in failed['rows'][9:])
        assert writer_fault[0] in failure_entry.seen and len(failure_entry.seen)==9
        try:failure_entry(expected[8],root/'failed-slot-retry')
        except ValueError:pass
        else:raise AssertionError('Failed B slot was replayed')
    initial.restore();assert initial.fingerprint()==origin;restored()
    return [dict(flow=flow,status='PASS_COMPLETE_B36_CPU_HANDOFF',
        complete_B_paths=36,sections=dict(warm=6,quality=24,repeat=6),
        selected={family:row['candidate'] for family,row in binding['frozen']['selected'].items()},
        formal_logical_sources=32,reused_A_sources=8,
        repeated_B_quality_latent_RGB_RNG_equal=repeat_checks,
        clean_research_counters_zero=True,all_policy_actions_equal=True,
        original_methods_and_state_restored=True,A_slot_refused=True,CPU_fixture_GPU_refused=True,
        existing_output_refused_before_execution=True,
        failure_scope=dict(attempted=9,total=36,failed=1,not_reached=27,no_replay=True),
        synthetic_A_only=True,actual_A32_outputs_read=False,Cosmos_weights_loaded=False,
        metric_model_executed=False,GPU_submissions=0)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    fixture.body=body
    return fixture.run(runtime,artifact_root,host,samples)
