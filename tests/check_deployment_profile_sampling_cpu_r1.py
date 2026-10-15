"""All seventeen existing configurations, both flows, one Toy request/seed17.

Each configuration runs original audit, profiled audit and profiled lean. This
tests the new observer, not another parameter search or final paper evaluation.
"""
import copy
import hashlib
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import paper_baseline_grid_r1 as grid
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.deployment_profile_r1 import profile_execution
from wcomr.frozen_shared_execution_r1 import AVAILABLE_METHODS, execute, point
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior

ROOT = Path(__file__).resolve().parents[1]
COUNTS = dict(paths=102, pairs=3516, CFG_calls=7032,
              profile_paths=68, full_guided_parities=34, profile_audit_lean_parities=34)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest(tensor):
    return sha_bytes(tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k != 'owner'}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root):
    model, net = inference.pipe.model, inference.pipe.model.net
    parameters = json.loads((ROOT / 'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    previous = json.loads((ROOT / 'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    calibration = Calibration('DECLARED_TOY_SHARED_AGE6',
        {(a, n): .99 for a in range(1, 36) for n in range(a + 1, min(a + 6, 36) + 1)},
        {n: 1. for n in range(1, 37)})
    prior = CreationPhasePrior('DECLARED_TOY_SHARED_ROOT', .005, .3,
                              early_creation_floor=.005, late_creation_floor=.02)
    spec = dict(threshold=grid.RA_THRESHOLD,
        costs=Costs('DECLARED_TOY_FROZEN_QUOTES', parameters['source_A_cost_seconds']['D'],
                    parameters['cost_seconds']['D'], parameters['cost_seconds']['P']),
        partial_prior=prior, working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')

    def native(self, *args, **kwargs):
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try:
            return wc.worldcache_mini_train_dit_forward(self, *args, **kwargs)
        finally:
            self.worldcache_rel_l1_thresh = threshold

    common = dict(runtime=runtime, wc=wc, rf=rf, settings=settings,
        calibration=calibration, specs={'SOURCE_RA': spec, 'A_CPD_BETA1_ONE_PHASE': spec},
        inference_module=inference_module, expected_shape=config['expected_shape'],
        CPU_native=native, table_parameters={'SOURCE_PHASE': parameters}, previous_parameters=previous)
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    origin = initial.fingerprint()
    checks, profiles = [], []
    sample = copy.copy(selected[0])
    sample.seed = 17
    base = Path(artifact_root) / str(flow)
    paths = pairs = 0
    try:
        for method in AVAILABLE_METHODS:
            sample.num_steps = point(method)['requested_steps']
            outputs = []
            for mode, audit in (('original', True), ('profile_audit', True), ('profile_lean', False)):
                initial.restore()
                assert initial.fingerprint() == origin
                destination = base / method / mode
                if mode == 'original':
                    result = execute(inference, sample, method, output=destination, audit=audit, **common)
                else:
                    with profile_execution(inference, inference_module=inference_module,
                                           probe_depth=settings['probe_depth'], device='cpu') as profiler:
                        result = execute(inference, sample, method, output=destination, audit=audit, **common)
                    summary = profiler.summary
                    assert summary['status'] == 'PROFILE_COMPLETE'
                    assert summary['memory_before']['available'] is False
                    assert summary['memory_after']['peak_allocated_bytes'] is None
                    assert not summary['peak_reset_before_request']
                    assert not profiler.rows and not profiler._patches
                    components = summary['components']
                    updates = point(method)['actual_updates']
                    assert components['shallow_block']['calls'] == 2 * updates * settings['probe_depth']
                    assert components['solver_update']['calls'] == updates
                    assert components['VAE_decode']['calls'] == components['video_write']['calls'] == 1
                    assert components['output_head']['calls'] >= 2 * updates
                    assert components['method_install_inclusive']['calls'] == 1
                    assert all(r['outcome'] == 'RETURNED' and r['CUDA_elapsed_ms'] is None for r in summary['intervals'])
                    # Full scalar interval records stay isolated, and are hashed after timing.
                    profile_path = destination / 'profile-scalar-records.json'
                    data = (json.dumps(summary, indent=2, allow_nan=False) + '\n').encode()
                    profile_path.write_bytes(data)
                    profiles.append(dict(flow=flow, method=method, mode=mode,
                        ref=str(profile_path), sha256=sha_bytes(data), intervals=len(summary['intervals']),
                        components=components, device='cpu', unavailable_CUDA_memory_not_zero=True))
                assert result['status'] == 'COMPLETE'
                assert result['solver_steps'] == result['guided_pairs'] == point(method)['actual_updates']
                assert result['frozen_request_cleanup']['components_alive_after'] == 0
                if not audit:
                    assert result['in_timing_guided_copies'] == result['in_timing_hashes'] == result['research_checkpoints'] == 0
                outputs.append(result)
                paths += 1
                pairs += result['guided_pairs']
            original, measured, lean = outputs
            assert len(original['guided']) == len(measured['guided'])
            assert all(torch.equal(a, b) for a, b in zip(original['guided'], measured['guided']))
            for other in (measured, lean):
                assert torch.equal(original['final_latent'], other['final_latent'])
                assert original['actions'] == other['actions'] and original['A_history'] == other['A_history']
                assert stable(original.get('source_history')) == stable(other.get('source_history'))
                assert Path(original['video_path']).read_bytes() == Path(other['video_path']).read_bytes()
            checks.append(dict(flow=flow, method=method, seed=17, actual_updates=original['guided_pairs'],
                original_profile_all_guided_equal=True, audit_profile_lean_final_actions_history_mock_equal=True,
                all_components_released=True, final_sha256=digest(original['final_latent']),
                original_guided_sha256=[digest(v) for v in original['guided']],
                profile_guided_sha256=[digest(v) for v in measured['guided']],
                mock_paths=[v['video_path'] for v in outputs],
                mock_sha256=sha_bytes(Path(original['video_path']).read_bytes())))
            del outputs, original, measured, lean, result
        assert paths == 51 and pairs == 1758 and len(checks) == 17 and len(profiles) == 34
        return [dict(flow=flow, complete_CPU_paths=paths, ordinary_pairs=pairs,
                     CFG_calls=2 * pairs, checks=checks, profiles=profiles)]
    finally:
        initial.restore()
        assert initial.fingerprint() == origin


def finish(value):
    assert {r['flow'] for r in value['checks']} == {False, True}
    assert sum(r['complete_CPU_paths'] for r in value['checks']) == COUNTS['paths']
    assert sum(r['ordinary_pairs'] for r in value['checks']) == COUNTS['pairs']
    value.update(status='DEPLOYMENT_PROFILE_FULL102_TOY_CPU_PARITY_PASS_NOT_GPU_PROFILE',
        scope_counts=COUNTS, actual_CPU_paths=102, production_CPU_accepted=False,
        real_video_quality_or_speed_claim=False, CUDA_profile_or_memory_measured=False,
        all_existing_seventeen_methods_unchanged=True, actual_GPU_or_real_video_claim=False,
        weights_loaded=0, GPU_submissions=0, SSH_queries=0, ledger_written=False)
    return value


def run(runtime, tensor_loader, artifact_root):
    from importlib.util import module_from_spec, spec_from_file_location
    path = Path(__file__).with_name('check_paper_baseline_grid_sampling_cpu_r1.py')
    spec = spec_from_file_location('accepted_Toy_setup_for_deployment_profile', path)
    accepted = module_from_spec(spec)
    spec.loader.exec_module(accepted)
    source = dedent(inspect.getsource(accepted.run))
    marker = "    assert {r['flow'] for r in value['checks']}=={False,True}\n"
    assert source.count(marker) == 1
    changed = source[:source.index(marker)] + '    return _finish(value)\n'
    namespace = {**vars(accepted), 'body': body, '_finish': finish}
    exec(compile(changed, str(path) + '#deployment-profile-harness-r1', 'exec'), namespace)
    return namespace['run'](runtime, tensor_loader, artifact_root)
