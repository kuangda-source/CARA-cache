"""Actual pinned WC/RF/UniPC with explicit tiny CPU weights, no video claim."""
import copy
import inspect
import json
from pathlib import Path
from textwrap import dedent
import types

import torch

from wcomr.cara_fast_spec_r1 import profile_from, policy_from_mask, uniform_mask
from wcomr.cara_read_write_suffix_r1 import ReadWriteSuffixPilot
from wcomr.cfg_paired_probe_velocity import compile_velocity
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.production_sampling import PolicyOwner
from wcomr.rv0_fork import official_suffix


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location(name, ROOT / 'tests' / (name + '.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_modules(runtime, wc):
    """Original function bodies with declared CPU dependency namespaces.

    Local source extraction avoids importing the GPU-only Cosmos package. It
    does not certify target Linux imports; those remain a separate gate.
    """
    fixture = load('check_full_sampling')
    wc.__file__ = str(runtime / 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
    fixture.load_functions(Path(wc.__file__), ['compute_saliency_map'], vars(wc))
    rf = types.ModuleType('read_write_pinned_RF_CPU')
    vars(rf).update(vars(wc))
    rf.__file__ = str(runtime / 'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py')
    rf.NUM_CONDITIONAL_FRAMES_KEY = 'num_conditional_frames'
    rf.parallel_state = types.SimpleNamespace(is_initialized=lambda: False)
    fixture.load_functions(Path(rf.__file__), ['denoise', 'get_velocity_fn_from_batch'], vars(rf))
    rf.Video2WorldModelRectifiedFlow = types.SimpleNamespace(
        denoise=rf.denoise, get_velocity_fn_from_batch=rf.get_velocity_fn_from_batch)
    return wc, rf


@torch.no_grad()
def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root):
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
    card = json.loads((ROOT / 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    profile = profile_from(card['profile'])
    mask, _ = uniform_mask(card['schedule'], profile, 19)
    policy = policy_from_mask(profile, mask)
    suffix = official_suffix(runtime / 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    noise = torch.randn((1, 8, 2, 8, 8), generator=torch.Generator().manual_seed(0))
    batch = dict(fps=torch.tensor([24.]), num_conditional_frames=0)
    owners = []
    def prepare(chosen):
        initial.restore()
        full_settings = {**settings, 'worldcache_num_steps': 70}
        wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in full_settings.items()})
        scheduler.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
        owner = PolicyOwner(model, policy=chosen, profile=profile,
            context=('READ_WRITE_CPU', 'TINY_NOT_COSMOS_WEIGHTS', 'seed0'), runtime=runtime, wc=wc, rf=rf)
        owners.append(owner)
        factory, _ = compile_velocity(runtime, rf, owner, owner.choose)
        velocity = factory(model, batch, guidance=7, is_negative_prompt=True)
        return owner, velocity, torch.Generator().manual_seed(0)
    def prefix(velocity, generator):
        latent = noise.clone()
        for t in scheduler.timesteps[:7]:
            v = velocity(noise, latent, t.reshape(1, 1))
            latent = scheduler.step(v.unsqueeze(0), t, latent.unsqueeze(0),
                return_dict=False, generator=generator)[0].squeeze(0)
        return latent
    try:
        _, velocity, generator = prepare(policy)
        reference_C = suffix(model, noise, noise.clone(), velocity, generator, scheduler.timesteps).clone()
        dense_mask = sorted(mask + [8])
        # This is an independent endpoint-equivalence control for corner11;
        # it intentionally uses20D, not a proposed19D deployment candidate.
        dense_policy = policy_from_mask(profile, dense_mask)
        _, velocity, generator = prepare(dense_policy)
        reference_D = suffix(model, noise, noise.clone(), velocity, generator, scheduler.timesteps).clone()
        owner, velocity, generator = prepare(policy)
        latent = prefix(velocity, generator)
        pilot = ReadWriteSuffixPilot(owner, velocity, latent, noise, generator, runtime=runtime,
            target_update=8, logical_copy_cap_bytes=1 << 30, CPU_storage_cap_bytes=1 << 30)
        outputs = pilot.run()
        assert pilot.parent_restored and scheduler._step_index == owner.readout.completed == 7
        assert torch.equal(outputs['00'], reference_C)
        assert torch.equal(outputs['11'], reference_D)
        records = {r['corner']: r for r in pilot.records}
        assert records['00']['current_solver_state_sha256'] == records['01']['current_solver_state_sha256']
        assert records['10']['current_solver_state_sha256'] == records['11']['current_solver_state_sha256']
        assert records['00']['current_cache_state_sha256'] == records['10']['current_cache_state_sha256']
        assert records['01']['current_cache_state_sha256'] == records['11']['current_cache_state_sha256']
        assert records['00']['true_D_sources'] == records['10']['true_D_sources'] == [[6, 7], [6, 7]]
        assert records['01']['true_D_sources'] == records['11']['true_D_sources'] == [[7, 8], [7, 8]]
        assert all(r['status'] == 'COMPLETE_UNSCORED_SUFFIX' and r['future_updates'] == 28
                   and r['future_actual_actions'] == policy['actions'][8:] for r in records.values())
        try:
            pilot.run()
        except ValueError:
            pass
        else:
            raise AssertionError('Duplicate pilot execution accepted')
        resumed = suffix(model, noise, latent, velocity, generator, scheduler.timesteps[7:])
        assert torch.equal(resumed, reference_C)
        owner, velocity, generator = prepare(policy)
        latent = prefix(velocity, generator)
        failed = ReadWriteSuffixPilot(owner, velocity, latent, noise, generator, runtime=runtime,
            target_update=8, logical_copy_cap_bytes=1 << 30, CPU_storage_cap_bytes=1 << 30)
        def injected(*args, **kwargs):
            raise RuntimeError('Declared CPU suffix failure')
        failed.suffix = injected
        try:
            failed.run()
        except RuntimeError as error:
            assert str(error) == 'Declared CPU suffix failure'
        else:
            raise AssertionError('Injected suffix failure swallowed')
        assert failed.parent_restored and failed.records[0]['status'] == 'FAILED'
        assert scheduler._step_index == owner.readout.completed == 7
        return [dict(status='PINNED_CPU_SUFFIX_COMPONENT_PASS', flow=flow, target_update=8,
            complete_corners=4, future_updates_per_corner=28, records=pilot.records,
            corner00_equals_independent_Uniform19=True, corner11_equals_independent_D8_policy=True,
            all_cache_sources_and_sigmas_bundled=True, entire_UniPC_state_with_read=True,
            parent_resume_equals_original=True, failure_restores_parent_and_propagates=True,
            repeated_pilot_refused=True, CPU_snapshot_bytes=pilot.CPU_bytes,
            actual_Cosmos_weights=False, actual_model_VJP=False, real_video_or_scientific_score=False)]
    finally:
        for owner in owners:
            owner.close()
        initial.restore()


def run(runtime, artifact_root):
    # Reuse the accepted tiny actual-module setup. Only its test body is
    # replaced; original production code and the upstream sources are intact.
    old = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(old.exercise))
    imports = ('    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc\n'
               '    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf\n')
    assert source.count(imports) == 1
    source = source.replace(imports, "    wc, rf = _pinned_modules(runtime, unused['wc'])\n")
    start = source.index('    results=[]\n    try:')
    end = source.index('\n    finally:\n', start) + 1
    source = source[:start] + '    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n' + source[end:]
    namespace = {**vars(old), '_body': body, '_pinned_modules': pinned_modules}
    exec(compile(source, __file__ + '#existing-tiny-setup', 'exec'), namespace)
    return load('check_full_sampling').run(runtime, exercise=lambda **kwargs: namespace['exercise'](
        runtime=Path(runtime), tensor_loader=None, artifact_root=artifact_root, **kwargs))
