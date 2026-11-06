"""All64 new numerical paths and24 original-arm controls; not real GPU video."""
import inspect
from pathlib import Path
from textwrap import dedent
import torch

from wcomr.drop1_correction_window24_r1 import METHODS, OLD_METHODS, plans, execute, CPU_STATUS
from wcomr.drop1_full18_r1 import execute as old_execute
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_phase_absolute_h1_control_r1 import VERSION, fingerprint


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stable(x):
    if isinstance(x, dict): return {k: stable(v) for k, v in x.items() if k != 'owner'}
    if isinstance(x, list): return [stable(v) for v in x]
    return x


def equivalent(a, b, *, all_guided):
    assert torch.equal(a['final_latent'], b['final_latent'])
    assert a['actions'] == b['actions'] and a['A_history'] == b['A_history']
    assert stable(a['source_history']) == stable(b['source_history'])
    assert Path(a['video_path']).read_bytes() == Path(b['video_path']).read_bytes()
    if all_guided:
        assert len(a['guided']) == len(b['guided']) == 36
        assert all(torch.equal(x, y) for x, y in zip(a['guided'], b['guided']))


def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root):
    net = inference.pipe.model.net
    scheduler = inference.pipe.model.sample_scheduler
    cal = Calibration('SYNTHETIC_AGE6',
        {(a, n): .99 for a in range(1, 36) for n in range(a+1, min(a+6, 36)+1)},
        {n: 1. for n in range(1, 37)})
    spec = dict(threshold=2., costs=Costs('SYNTHETIC', 1., 4., 3.5),
        partial_prior=CreationPhasePrior('SYNTHETIC', .005, .3, early_creation_floor=.005, late_creation_floor=.02),
        working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs = {'SOURCE_RA': spec, 'A_CPD_BETA1_ONE_PHASE': spec}
    old = {'fingerprint': 'SYNTHETIC_PRIOR_UNCHANGED', 'gamma': .5}
    parameters = dict(version=VERSION, gamma=.5,
        table_model=dict(grouping='SOURCE_PHASE', target='absolute_guided_MSE',
            current_teacher_energy_is_online_feature=False,
            cells={s+'_'+p: dict(status='FIT', C_scale=100., A_ratios={'FUSION_A': .02}, actual_NEW_P_birth_mean=.0001)
                   for s in ('D', 'P') for p in ('EARLY', 'LATE')}),
        cost_seconds={'C': 1., 'A': 1.3, 'P': 3.5, 'D': 4.},
        source_A_cost_seconds={'D': 1.1, 'P': 1.3}, lambda_seconds_per_weighted_absolute_MSE=100.)
    parameters['fingerprint'] = fingerprint(parameters)
    tables = {'SOURCE_PHASE': parameters}
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    origin = initial.fingerprint()
    checks = []

    def run(sample, method, executor, audit, out):
        initial.restore()
        assert initial.fingerprint() == origin
        return executor(inference, sample, method, table_parameters=tables, previous_parameters=old,
            runtime=runtime, wc=wc, rf=rf, settings=settings, calibration=cal, specs=specs,
            inference_module=inference_module, expected_shape=config['expected_shape'], output=out, audit=audit)

    try:
        for i, sample in enumerate(selected):
            directory = Path(artifact_root) / str(flow) / str(i)
            legacy = {m: run(sample, old_method, old_execute, True, directory / 'original' / m)
                      for m, old_method in OLD_METHODS.items()}
            audited = {}
            for method in METHODS:
                values = []
                plan = plans()[method]
                for mode, audit in (('audit', True), ('lean', False)):
                    row = run(sample, method, execute, audit, directory / (method + mode))
                    assert row['status'] == 'COMPLETE' and row['solver_steps'] == row['guided_pairs'] == 36
                    assert row['semantic_plan'] == list(plan) and row['online_teacher_calls'] == 0
                    assert row['actions'] == ['DD' if a == 'D' else 'CC' for a in plan]
                    assert [h['A_readout']['readout_action'] for h in row['source_history']] == list(plan)
                    for a, h in zip(plan, row['source_history']):
                        readout = h['A_readout']
                        assert h['teacher_calls'] == readout['teacher_calls'] == readout['extra_deep_blocks'] == 0
                        if a != 'D': assert h['true_D_before'] == h['true_D_after']
                        if a == 'C': assert readout['shared_alpha'] == readout['extra_heads'] == 0
                        if a == 'A': assert readout['shared_alpha'] == 1
                    assert row['request_memory_lifecycle']['observed_owners'] == 1
                    assert row['request_memory_lifecycle']['owners_alive_after'] == 0
                    if not audit:
                        assert row['in_timing_guided_copies'] == row['in_timing_hashes'] == row['research_checkpoints'] == 0
                    values.append(row)
                a, b = values
                equivalent(a, b, all_guided=False)
                assert len(a['guided']) == 36
                audited[method] = a
                if method in legacy: equivalent(a, legacy[method], all_guided=True)
                checks.append(dict(scene=sample.name, method=method, DD=plan.count('D'), A=plan.count('A'), C=plan.count('C'),
                    all36_actual_readout_and_paid_source_checks=True,
                    audit_lean_endpoint_actions_history_CPU_video_payload_equal=True,
                    original_all36_guided_control=method in legacy))
            # A1/A3 differ only from update22; the original input/solver state is restored.
            assert all(torch.equal(a, b) for a, b in zip(audited['S25-A1']['guided'][:21], audited['S25-A3']['guided'][:21]))
        assert len(checks) == 16
        return [dict(flow=flow, status='PASS', checks=checks, complete_CPU_paths=44,
            new_complete_paths=32, old_control_paths=12, all36_audit_guided_controls=True,
            common_A1_A3_first21_guided_equal=True, ordinary_initial_state_restored=True,
            CPU_video_payload_is_not_real_93frame_video=True)]
    finally:
        initial.restore()
        assert initial.fingerprint() == origin


def run(runtime, tensor_loader, artifact_root):
    original = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(original.exercise))
    marker = '    results=[]\n    try:'
    assert source.count(marker) == 1
    start = source.index(marker)
    end = source.index('\n    finally:\n', start) + 1
    changed = source[:start] + '    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n' + source[end:]
    namespace = {**vars(original), '_body': body}
    exec(compile(changed, __file__ + '#unchanged-Toy-setup', 'exec'), namespace)
    value = load('check_full_sampling').run(runtime,
        exercise=lambda **kw: namespace['exercise'](runtime=Path(runtime), tensor_loader=tensor_loader,
                                                    artifact_root=artifact_root, **kw))
    assert {r['flow'] for r in value['checks']} == {False, True}
    assert sum(r['complete_CPU_paths'] for r in value['checks']) == 88
    value.update(status=CPU_STATUS, actual_CPU_paths=88, new_complete_paths=64, old_control_paths=24,
                 actual_GPU_or_real_video_claim=False)
    return value
