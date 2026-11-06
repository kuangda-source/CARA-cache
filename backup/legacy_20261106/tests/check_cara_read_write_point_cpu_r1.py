"""Complete guarded CPU requests for the paid read/write point adapter."""
import copy
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_spec_r1 import profile_from, policy_from_mask, uniform_mask
from wcomr.cara_read_write_point_r1 import execute
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.mid_coverage import tree_digest
from wcomr.policy_generator_r1.production_sampling import execute as ordinary
from wcomr.prepared_input import PreparedInputReplay
from wcomr.rv0_fork import object_state

from check_cara_read_write_suffix_cpu_r1 import ROOT, load, pinned_modules


@torch.no_grad()
def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root, *, target_update=8):
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    model.config.state_ch = 8
    class Head(torch.nn.Module):
        def forward(self, value, *args, **kwargs):
            return value + .01 * value.square()
    net.final_layer = Head().eval()
    net.unpatchify = lambda x: x[:, :, ::2, ::2, :].movedim(-1, 1).contiguous()
    cls, _ = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    model.conditioner.get_condition_with_negative_prompt = lambda batch: tuple(
        cls(crossattn_emb=torch.ones(1, 3, 4) * (1+b), fps=batch['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1, 8, 2, 8, 8), 0, 0, num_conditional_frames=0) for b in (0, 1))
    model.get_data_and_condition = lambda batch: (None, torch.zeros(1, 8, 2, 8, 8), None)
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    origin = initial.fingerprint()
    card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    profile = profile_from(card['profile'])
    mask, _ = uniform_mask(card['schedule'], profile, 19)
    policy = policy_from_mask(profile, mask)
    output = Path(artifact_root)/('point_flow_'+str(flow))
    common = dict(runtime=runtime, wc=wc, rf=rf, settings=settings, calibration=None, specs={},
        inference_module=inference_module, expected_shape=[1, 8, 2, 8, 8], audit=True)
    rows, post_y = {}, {}
    replay = PreparedInputReplay(inference.pipe._get_data_batch_input)
    original_step = scheduler.step
    def record_step(*args, **kwargs):
        result = original_step(*args, **kwargs)
        if scheduler._step_index == target_update:
            post_y['current'] = tree_digest(dict(latent=result[0], memory=object_state(scheduler)))
        return result
    try:
        with clean.patched(inference.pipe, '_get_data_batch_input', replay), clean.patched(scheduler, 'step', record_step):
            for corner in ('00', '10', '01', '11'):
                initial.restore()
                result = execute(inference, selected[0], profile=profile, policy=policy, corner=corner,
                    target_update=target_update,
                    logical_copy_cap_bytes=1 << 30, CPU_storage_cap_bytes=1 << 30,
                    output=output/corner, **common)
                assert result['status'] == 'COMPLETE' and result['physical_model_pairs'] == 37
                assert result['solver_steps'] == result['guided_pairs'] == 36
                assert result['diagnostic_timing_only'] and result['intervention']['actual_current_read'] == ('D' if corner[0]=='1' else 'C')
                rows[corner] = result
                post_y[corner] = post_y['current']
            for name, dense in [('C', mask), ('D_CONTROL', sorted(mask+[target_update]))]:
                initial.restore()
                rows[name] = ordinary(inference, selected[0], profile=profile,
                    policy=policy_from_mask(profile, dense), output=output/name, **common)
                assert rows[name]['status'] == 'COMPLETE'
        assert torch.equal(rows['00']['final_latent'], rows['C']['final_latent'])
        assert torch.equal(rows['11']['final_latent'], rows['D_CONTROL']['final_latent'])
        assert Path(rows['00']['video_path']).read_bytes() == Path(rows['C']['video_path']).read_bytes()
        assert Path(rows['11']['video_path']).read_bytes() == Path(rows['D_CONTROL']['video_path']).read_bytes()
        assert post_y['00'] == post_y['01'] and post_y['10'] == post_y['11']
        records = {k: rows[k]['intervention'] for k in ('00', '10', '01', '11')}
        assert len({r['parent_state_sha256'] for r in records.values()}) == 1
        assert records['00']['cache_after_sha256'] == records['10']['cache_after_sha256']
        assert records['01']['cache_after_sha256'] == records['11']['cache_after_sha256']
        before = [t for t in mask if t < target_update][-2:]
        after = [before[-1],target_update]
        assert records['00']['true_D_sources'] == records['10']['true_D_sources'] == [before,before]
        assert records['01']['true_D_sources'] == records['11']['true_D_sources'] == [after,after]
        assert len(replay.calls) == 6 and all(c['prepared']==replay.calls[0]['prepared'] for c in replay.calls)
        initial.restore()
        assert initial.fingerprint() == origin
        return [dict(status='FULL_GUARDED_POINT_FOUR_CORNER_CPU_PASS', flow=flow, complete_paths=6,
            four_corner_paths=4, independent_controls=2, logical_updates_per_path=36,
            physical_pairs_per_intervention=37, physical_pairs_per_control=36,
            original_inputs_and_prewrite_state_exact=True, all_solver_memory_with_read=True,
            entire_cache_and_sources_with_write=True, Native_pipeline_decode_and_writer_completed=True,
            **{('corner00_C_and_corner11_D8_latent_and_mock_RGB_exact' if target_update == 8
                 else 'corner00_C_and_corner11_D20_latent_and_mock_RGB_exact'):True}, caller_restored=True,
            records=records, actual_Cosmos_weights=False, real_encoded_video=False,
            target_update=target_update,
            real_scientific_scores=False, real_model_VJP=False)]
    finally:
        initial.restore()


def run(runtime, artifact_root, *, actual_modules=False, target_update=8):
    old = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(old.exercise))
    if not actual_modules:
        imports = ('    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc\n'
                   '    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf\n')
        assert source.count(imports) == 1
        source = source.replace(imports, "    wc, rf = _pinned_modules(runtime, unused['wc'])\n")
    start = source.index('    results=[]\n    try:')
    end = source.index('\n    finally:\n', start)+1
    source = source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    def target_body(*args):
        return body(*args,target_update=target_update)
    namespace = {**vars(old), '_body': target_body, '_pinned_modules': pinned_modules}
    exec(compile(source, __file__+'#accepted-tiny-setup', 'exec'), namespace)
    return load('check_full_sampling').run(runtime, exercise=lambda **kwargs: namespace['exercise'](
        runtime=Path(runtime), tensor_loader=None, artifact_root=artifact_root, **kwargs))
