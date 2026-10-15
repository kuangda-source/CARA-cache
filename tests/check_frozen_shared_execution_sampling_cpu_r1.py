"""Full existing-point registry x three seeds x two flows, with legacy parity.

Four Toy inputs, unchanged pinned UniPC/RF/pipeline bodies and declared Toy
attention/head/weights/writer. This is execution validation, not final N07
selection or actual Cosmos/video performance.
"""
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr import paper_baseline_grid_r1 as grid
from wcomr import simple26d_memory_r2 as old_simple
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.frozen_shared_execution_r1 import AVAILABLE_METHODS, SEEDS, execute, point
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = dict(paths=952, ordinary_pairs=32816, CFG_calls=65632,
                audit_lean_pairs=408, seed0_legacy_bridges=136)


def checksum(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k != 'owner'}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root):
    import json
    model = inference.pipe.model
    net = model.net
    params = json.loads((ROOT / 'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    old = json.loads((ROOT / 'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    calibration = Calibration('DECLARED_TOY_SHARED_AGE6',
        {(a, n): .99 for a in range(1, 36) for n in range(a + 1, min(a + 6, 36) + 1)},
        {n: 1. for n in range(1, 37)})
    prior = CreationPhasePrior('DECLARED_TOY_SHARED_ROOT', .005, .3,
                              early_creation_floor=.005, late_creation_floor=.02)
    spec = dict(threshold=grid.RA_THRESHOLD,
        costs=Costs('DECLARED_TOY_FROZEN_QUOTES', params['source_A_cost_seconds']['D'],
                    params['cost_seconds']['D'], params['cost_seconds']['P']),
        partial_prior=prior, working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs = {'SOURCE_RA': spec, 'A_CPD_BETA1_ONE_PHASE': spec}

    def native(self, *args, **kwargs):
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try:
            return wc.worldcache_mini_train_dit_forward(self, *args, **kwargs)
        finally:
            self.worldcache_rel_l1_thresh = threshold

    common = dict(runtime=runtime, wc=wc, rf=rf, settings=settings,
        calibration=calibration, specs=specs, inference_module=inference_module,
        expected_shape=config['expected_shape'], CPU_native=native,
        table_parameters={'SOURCE_PHASE': params}, previous_parameters=old)
    # Observe the seed and initial noise at the real pinned sampler boundary.
    # Keeping the CPU tensor reference avoids an extra in-timer clone/hash.
    sampler_body = inspect.unwrap(model.generate_samples_from_batch.__func__)
    sampler_path = Path(runtime) / 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py'
    assert Path(sampler_body.__code__.co_filename).resolve() == sampler_path.resolve()
    misc = sampler_body.__globals__['misc']
    original_noise = misc.arch_invariant_rand
    noise_events = []

    def observe_noise(*args, **kwargs):
        value = original_noise(*args, **kwargs)
        seed = kwargs.get('seed', args[3] if len(args) > 3 else None)
        noise_events.append((seed, value))
        return value

    misc.arch_invariant_rand = observe_noise
    state = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    original_fingerprint = state.fingerprint()
    checks, legacy, seed_hashes = [], [], {}
    total_pairs = 0
    total_paths = 0
    base_output = Path(artifact_root) / str(flow)

    def run_path(sample, method, audit, relative, previous=False):
        nonlocal total_pairs, total_paths
        state.restore()
        assert state.fingerprint() == original_fingerprint
        noise_events.clear()
        function = (grid.execute if method in grid.METHODS else old_simple.execute) if previous else execute
        result = function(inference, sample, method, audit=audit,
                          output=base_output / relative, **common)
        assert result['status'] == 'COMPLETE'
        assert len(noise_events) == 1 and noise_events[0][0] == sample.seed
        digest = checksum(noise_events[0][1])
        noise_events.clear()
        key = (sample.name, sample.seed)
        if key in seed_hashes:
            assert seed_hashes[key] == digest
        seed_hashes[key] = digest
        expected = point(method)['actual_updates']
        assert result['solver_steps'] == result['guided_pairs'] == expected
        assert len(result['scheduler_timesteps']) == expected
        if audit:
            assert len(result['guided']) == expected
        else:
            assert result['in_timing_guided_copies'] == result['in_timing_hashes'] == result['research_checkpoints'] == 0
        if not previous:
            assert result['frozen_input_identity']['actual_sample_seed'] == sample.seed
            assert result['frozen_request_cleanup']['components_alive_after'] == 0
            assert result['registered_seed_gate_proof']['inverse_bytes_and_AST_equal']
        total_pairs += expected
        total_paths += 1
        return result, digest

    try:
        assert len(selected) == 4
        for i, sample in enumerate(selected):
            for method in AVAILABLE_METHODS:
                for seed in SEEDS:
                    request = copy.copy(sample)
                    request.num_steps = point(method)['requested_steps']
                    request.seed = seed
                    prefix = f'{i}/{method}/seed{seed}'
                    audit, noise = run_path(request, method, True, prefix + '/audit')
                    lean, noise_lean = run_path(request, method, False, prefix + '/lean')
                    assert noise == noise_lean
                    assert torch.equal(audit['final_latent'], lean['final_latent'])
                    assert audit['actions'] == lean['actions'] and audit['A_history'] == lean['A_history']
                    assert stable(audit.get('source_history')) == stable(lean.get('source_history'))
                    assert Path(audit['video_path']).read_bytes() == Path(lean['video_path']).read_bytes()
                    if seed == 0:
                        original, noise_original = run_path(request, method, True, prefix + '/legacy', previous=True)
                        assert noise == noise_original
                        assert len(original['guided']) == len(audit['guided'])
                        assert all(torch.equal(a, b) for a, b in zip(original['guided'], audit['guided']))
                        assert torch.equal(original['final_latent'], audit['final_latent'])
                        assert original['actions'] == audit['actions']
                        assert original['A_history'] == audit['A_history']
                        assert stable(original.get('source_history')) == stable(audit.get('source_history'))
                        assert Path(original['video_path']).read_bytes() == Path(audit['video_path']).read_bytes()
                        legacy.append(dict(scene=sample.name, method=method, seed=0,
                            all_guided_final_actions_Ahistory_sourcehistory_mock_equal=True,
                            original_guided_count=len(original['guided']),
                            mock_video_path=original['video_path'], mock_video_sha256=checksum_bytes(original['video_path'])))
                        del original
                    checks.append(dict(scene=sample.name, method=method, seed=seed,
                        actual_updates=point(method)['actual_updates'], initial_noise_sha256=noise,
                        audit_lean_final_actions_Ahistory_sourcehistory_mock_equal=True,
                        actual_sampler_seed=seed, final_sha256=checksum(audit['final_latent']),
                        installed_contexts=audit['frozen_input_identity']['installed_contexts'],
                        components_released=True,
                        actual_threshold=point(method)['threshold'],
                        semantic_plan=audit.get('semantic_plan'),
                        native_block_CFG_counts=audit.get('native_block_CFG_counts'),
                        guided_sha256=[checksum(v) for v in audit['guided']],
                        audit_mock_video_path=audit['video_path'],
                        lean_mock_video_path=lean['video_path'],
                        mock_video_sha256=checksum_bytes(audit['video_path'])))
                    del audit, lean
        for sample in selected:
            assert len({seed_hashes[(sample.name, seed)] for seed in SEEDS}) == 3
        assert total_paths == 476 and total_pairs == 16408
        assert len(checks) == 204 and len(legacy) == 68
        return [dict(flow=flow, status='PASS', complete_CPU_paths=total_paths,
                     ordinary_pairs=total_pairs, CFG_calls=2 * total_pairs,
                     audit_lean_checks=checks, seed0_legacy_bridges=legacy,
                     seed_noise_hashes=[dict(scene=s, seed=k, sha256=h) for (s, k), h in seed_hashes.items()],
                     all_actual_sampler_seeds_verified=True,
                     initial_noise_distinct_across_seeds=True,
                     Native_boundary='DECLARED_CPU_DENSE_WC_STANDIN_NOT_REAL_NATIVE_MODEL',
                     CPU_noise_observer_not_installed_by_production_executor=True)]
    finally:
        noise_events.clear()
        misc.arch_invariant_rand = original_noise
        state.restore()
        assert state.fingerprint() == original_fingerprint


def checksum_bytes(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finish(value):
    assert {r['flow'] for r in value['checks']} == {False, True}
    for field in ('complete_CPU_paths', 'ordinary_pairs', 'CFG_calls'):
        wanted = EXPECTED['paths' if field == 'complete_CPU_paths' else field]
        assert sum(r[field] for r in value['checks']) == wanted
    assert sum(len(r['audit_lean_checks']) for r in value['checks']) == 408
    assert sum(len(r['seed0_legacy_bridges']) for r in value['checks']) == 136
    value.update(status='FROZEN_SHARED_FULL952_LOCAL_REGISTRY_CPU_PASS_NOT_PRODUCTION',
                 actual_CPU_paths=952, ordinary_pairs=32816, CFG_calls=65632,
                 audit_lean_pairs=408, seed0_legacy_bridges=136,
                 available_methods=list(AVAILABLE_METHODS), seeds=list(SEEDS),
                 final_inputs_selected=False, final_methods_selected=False,
                 production_CPU_accepted=False, real_video_quality_or_speed_claim=False,
                 real_videos_generated=0, weights_loaded=0)
    return value


def run(runtime, tensor_loader, artifact_root):
    from importlib.util import module_from_spec, spec_from_file_location
    path = Path(__file__).with_name('check_paper_baseline_grid_sampling_cpu_r1.py')
    spec = spec_from_file_location('accepted_N05_Toy_setup_for_shared_registry', path)
    accepted = module_from_spec(spec)
    spec.loader.exec_module(accepted)
    source = dedent(inspect.getsource(accepted.run))
    marker = "    assert {r['flow'] for r in value['checks']}=={False,True}\n"
    assert source.count(marker) == 1
    prefix = source[:source.index(marker)]
    changed = prefix + '    return _finish(value)\n'
    namespace = {**vars(accepted), 'body': body, '_finish': finish}
    exec(compile(changed, str(path) + '#shared-registry-test-harness-r1', 'exec'), namespace)
    return namespace['run'](runtime, tensor_loader, artifact_root)
