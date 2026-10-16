"""Real pinned inference refusals and full-path parity in the existing Toy setup.

All180 registered slots are refused through the original inference text
guard, rather than by faking a batch result. Accepted and video-refused
fixed-mask paths additionally compare every actual guided update to R1.
"""
import copy
import importlib.util
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import frozen_guardrail_boundary_r2 as repair
from wcomr import frozen_shared_execution_r1 as original
from wcomr.frozen_shared_production_r1 import run_registered_batch
from wcomr.full_sampling import CompleteStateRoundtrip

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = Path(__file__).with_name(name + '.py')
    spec = importlib.util.spec_from_file_location(name + '_refusal_r2', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def body_tail(inference, selected, common, flow, artifact_root):
    shared = load('check_frozen_shared_execution_sampling_cpu_r1')
    methods = ('FRONT_DENSE_C', 'FRONT_DENSE_A')
    state = CompleteStateRoundtrip(inference.pipe.model.net,
        inference.pipe.model.sample_scheduler, torch.zeros(1))
    origin = state.fingerprint()
    guards = common['inference_module'].guardrail_presets
    old_text, old_video = guards.run_text_guardrail, guards.run_video_guardrail
    fixed, proof = repair.compile_fixed_boundary()
    assert proof['inverse_bytes_and_AST_equal'] and proof['complete_and_video_rejected_masks_still_checked']
    root = Path(artifact_root) / str(flow)
    checks, reproduced, video_checks = [], [], []
    full_paths = 0

    def run(function, sample, method, audit, label):
        nonlocal full_paths
        state.restore(); assert state.fingerprint() == origin
        result = function(inference, sample, method, audit=audit,
            output=root / label, **common)
        full_paths += bool(result['solver_steps'])
        assert result['frozen_request_cleanup']['components_alive_after'] == 0
        return result

    def compare(a, b, method, status, audit):
        assert a['status'] == b['status'] == status
        assert a['solver_steps'] == b['solver_steps'] == a['guided_pairs'] == b['guided_pairs'] == 36
        assert a['semantic_plan'] == b['semantic_plan']
        assert len(b['source_history']) == 36
        assert a['actions'] == b['actions'] and a['A_history'] == b['A_history']
        assert shared.stable(a['source_history']) == shared.stable(b['source_history'])
        assert torch.equal(a['final_latent'], b['final_latent'])
        if audit: assert all(torch.equal(x, y) for x, y in zip(a['guided'], b['guided'])) and len(b['guided']) == 36
        else: assert b['in_timing_guided_copies'] == b['in_timing_hashes'] == b['research_checkpoints'] == 0
        if status == 'COMPLETE':
            assert Path(a['video_path']).read_bytes() == Path(b['video_path']).read_bytes()
        else: assert a['video_path'] is b['video_path'] is None
        assert b['guardrail_request_boundary']['actual_zero_step_text_refusal'] is False
        return dict(method=method, audit=audit, status=status, actual_guided=36,
            all_guided_when_audit_final_actions_Ahistory_sourcehistory_and_Toy_RGB_equal=True,
            components_alive_after=0)

    try:
        # Exercise both registered seeds, all four existing Toy inputs, both
        # semantic masks and audit/lean; neither executor selects any new data.
        for i, sample in enumerate(selected):
            for seed in (17, 43):
                request = copy.copy(sample); request.seed = seed
                for method in methods:
                    request.num_steps = original.point(method)['requested_steps']
                    for audit in (True, False):
                        label = f'complete/{i}/{seed}/{method}/{audit}'
                        a = run(original.execute, request, method, audit, label + '/old')
                        b = run(repair.execute, request, method, audit, label + '/repaired')
                        checks.append(dict(scene=sample.name, seed=seed, **compare(a, b, method, 'COMPLETE', audit)))
        guards.run_video_guardrail = lambda frames, runner: None
        for seed in (17, 43):
            request = copy.copy(selected[0]); request.seed = seed
            for method in methods:
                request.num_steps = 35
                for audit in (True, False):
                    label = f'video_refusal/{seed}/{method}/{audit}'
                    a = run(original.execute, request, method, audit, label + '/old')
                    b = run(repair.execute, request, method, audit, label + '/repaired')
                    video_checks.append(dict(seed=seed, **compare(a, b, method, 'VIDEO_REJECTED', audit)))
        guards.run_video_guardrail = old_video
        guards.run_text_guardrail = lambda *args: False
        # Preserve an actual reproduction of the admitted R1 failure.
        for method in methods:
            request = copy.copy(selected[0]); request.seed = 17; request.num_steps = 35
            state.restore()
            try:
                original.execute(inference, request, method, audit=False,
                    output=root / 'original_text_failure' / method, **common)
            except ValueError as error:
                assert str(error) == 'Actual semantic readouts do not equal full frozen mask'
                reproduced.append(dict(method=method, error_type='ValueError', error=str(error)))
            else: raise AssertionError('The original refusal bug was not reproduced')
        config = json.loads((ROOT / 'configs/wc_paper_N07_frozen_shared_production_r1_20261016.json').read_text())
        bound = json.loads((ROOT / config['references']['bound_inputs']['ref']).read_text())
        assert len(bound['cases']) == 16 and len(config['method_ids']) == 10
        samples = {}
        for case in bound['cases']:
            for method in config['method_ids']:
                sample = copy.copy(selected[0]); sample.name = case['id']; sample.seed = case['seed']
                sample.num_steps = original.point(method)['requested_steps']
                samples[(case['id'], method)] = sample
        def refused(planned, sample):
            value = run(repair.execute, sample, planned['method'], planned['section'] == 'WARMUP',
                'complete180_refused/' + planned['id'])
            assert value['status'] == 'TEXT_REJECTED'
            assert value['solver_steps'] == value['guided_pairs'] == 0
            assert not value.get('video_path') and not value.get('source_history')
            return value
        batch = run_registered_batch(config, bound, samples, refused)
        assert len(batch['runs']) == 180 and all(r['status'] == 'TEXT_REJECTED' for r in batch['runs'])
        assert batch['status'] == 'N07_SHARED180_GPU_COMPLETE_CPU_AUDIT_PENDING'
        assert sum(r['section'] == 'WARMUP' for r in batch['runs']) == 20
        assert len(checks) == 32 and len(video_checks) == 8 and len(reproduced) == 2 and full_paths == 80
        return [dict(flow=flow, status='PASS', complete_sampling_CPU_paths=80, ordinary_pairs=2880,
            accepted_path_parity=checks, video_refusal_parity=video_checks, original_failure_reproduced=reproduced,
            full_registered_refusal_paths=180, registered_formal_refusals=160, registered_warm_refusals=20,
            no_text_refusal_replacement_or_generation=True, full_mask_validation_not_weakened=True,
            guardrail_boundary_proof=proof, numerical_runtime_changed=False,
            Native_boundary='ORIGINAL_DECLARED_TOY_WC_DENSE_STANDIN_NOT_REAL_COSMOS')]
    finally:
        guards.run_text_guardrail, guards.run_video_guardrail = old_text, old_video
        state.restore(); assert state.fingerprint() == origin


def run(runtime, tensor_loader, artifact_root):
    shared = load('check_frozen_shared_execution_sampling_cpu_r1')
    prefix = dedent(inspect.getsource(shared.body)).split('    # Observe the seed and initial noise')[0]
    prefix += '    return _body_tail(inference, selected, common, flow, artifact_root)\n'
    namespace = {**vars(shared), '_body_tail': body_tail}
    exec(compile(prefix, __file__ + '#unchanged-shared-Toy-setup', 'exec'), namespace)
    setup = load('check_paper_baseline_grid_sampling_cpu_r1')
    source = dedent(inspect.getsource(setup.run))
    marker = "    assert {r['flow'] for r in value['checks']}=={False,True}\n"
    assert source.count(marker) == 1
    adapted = source[:source.index(marker)] + '    return value\n'
    harness = {**vars(setup), 'body': namespace['body']}
    exec(compile(adapted, __file__ + '#unchanged-pinned-pipeline-Toy-harness', 'exec'), harness)
    value = harness['run'](runtime, tensor_loader, artifact_root)
    assert {v['flow'] for v in value['checks']} == {False, True}
    assert sum(v['complete_sampling_CPU_paths'] for v in value['checks']) == 160
    assert sum(v['full_registered_refusal_paths'] for v in value['checks']) == 360
    value.update(status='N07_REFUSAL_BOUNDARY_TWO_FLOW_FULL520_CPU_PASS_NOT_PRODUCTION',
        complete_sampling_CPU_paths=160, zero_step_refusal_CPU_paths=360, original_reproduced_failures=4,
        ordinary_pairs=5760, CFG_calls=11520, actual_CPU_paths=520,
        actual_Cosmos_production_CPU=False, real_videos_generated=0, model_weights_loaded=0,
        actual_GPU_submissions=0, GPUh_used=0, final_test_quality_or_latency_read=False)
    return value
