#!/usr/bin/env python3
"""One model-resident full40 timing run from a separately frozen config."""
import argparse
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def metric_processes(project, own_pid):
    """Observe project CPU metric entrypoints outside every core timer."""
    aliases = {str(Path(project)), str(Path(project).resolve()), '/home/gaokuangda/data/gkd/worldcache_omr'}
    raw = subprocess.check_output(['ps', '-eo', 'pid=,args='], text=True, timeout=10)
    found = []
    for line in raw.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or not fields[0].isdigit() or int(fields[0]) == own_pid: continue
        if (any(root in fields[1] for root in aliases)
                and any(name in fields[1] for name in ('postprocess_wc_', 'score_wc_', 'evaluate_wc_'))):
            found.append(dict(pid=int(fields[0]), kind='PROJECT_METRIC_ENTRYPOINT'))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--cpu-check', action='store_true')
    parser.add_argument('--source-revision'); parser.add_argument('--gpu-uuid')
    args = parser.parse_args()
    os.environ.update(HF_HUB_CACHE=str(args.project / 'hfhub'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path[:0] = [str(args.stage / 'src'), str(args.project / 'runtime'),
        str(args.project / 'runtime/packages/cosmos-oss'), str(args.project / 'runtime/packages/cosmos-cuda')]
    import torch
    if args.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        def forbidden(*a, **kw): raise RuntimeError('N08 CPU forbids CUDA, external weights and downloads')
        torch.cuda._lazy_init = forbidden; torch.load = forbidden; torch.hub.download_url_to_file = forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self): return forbidden
            def __getattr__(self, name): raise RuntimeError('N08 CPU denies Triton execution: ' + name)
        triton.runtime.driver.active = ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        prior = hu.is_flash_attn_2_available, iu.is_flash_attn_2_available, torch.cuda.current_device
        hu.is_flash_attn_2_available = iu.is_flash_attn_2_available = lambda: True
        torch.cuda.current_device = lambda: 0
    from cosmos_predict2.config import SetupArguments, InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
    from wcomr.balanced_repeat_production_r1 import (
        CONFIG, RUN, CPU_RESULT, CPU_STATUS, STRATEGY, validate, validate_launch_authority,
        clean_registered_jobs, archive_output,
    )
    from wcomr.balanced_repeat_execution_r1 import COUNTS, prepare_samples, execute_one, run_registered_batch
    from wcomr.frozen_shared_production_r1 import sha, write, fingerprint
    from wcomr.w1_native_reference_sampling import NATIVE_FORWARD
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval, verify_shared_eval
    if args.cpu_check:
        hu.is_flash_attn_2_available, iu.is_flash_attn_2_available, torch.cuda.current_device = prior
    config, registration, old, inputs, tables, previous, bound, source_reuse = validate(args.project, args.stage)
    calibration, specs, _, evidence = inputs
    samples = prepare_samples(bound, InferenceArguments)
    setup_data = json.loads((args.project / 'configs/f1_setup.json').read_text())
    setup = SetupArguments(**{**setup_data, 'keep_going': True, 'worldcache_enabled': True,
                              'output_dir': str(args.project / 'outputs' / RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    native = MinimalV1LVGDiT.forward
    assert native.__module__ + '.' + native.__qualname__ == NATIVE_FORWARD
    native_path = Path(inspect.getfile(native)).resolve()
    native_identity = dict(qualified_name=NATIVE_FORWARD, path=str(native_path), sha256=sha(native_path))
    if args.cpu_check:
        from types import SimpleNamespace
        from wcomr.frozen_shared_execution_r1 import execute
        dummy = SimpleNamespace(rank0=True, text_guardrail_runner=None, video_guardrail_runner=None)
        checks = []
        for request in bound['requests']:
            sample = samples[(request['name'], 'FULL_NATIVE')]
            try:
                execute(dummy, sample, 'NATIVE35', table_parameters=tables, previous_parameters=previous,
                    settings=old['historical_wc_settings'], specs=specs[STRATEGY], runtime=args.project / 'runtime',
                    wc=wc, rf=rf, calibration=calibration, inference_module=im,
                    output=args.stage / 'NEVER_CREATED_N08', expected_shape=old['expected_real_shape'])
            except ValueError as error: assert str(error) == 'Ordinary guardrails required'
            else: raise AssertionError('Unguarded Native timing request accepted')
            checks.append(dict(scene=request['name'], seed=0, method='NATIVE35', unguarded_execution_refused=True))
        assert len(checks) == 2 and not torch.cuda.is_initialized() and not (args.stage / 'NEVER_CREATED_N08').exists()
        write(args.stage / CPU_RESULT, dict(status=CPU_STATUS, exit_code=0,
            source_revision=registration['source_revision'], registration_sha256=sha(args.stage / 'registration.json'),
            config_sha256=sha(args.stage / CONFIG), runner_source_sha256=sha(Path(__file__)),
            bound_timing_fingerprint=fingerprint(bound), scope_counts=COUNTS,
            matrix=bound['execution_plan'], actual_sample_argument_variants=len(samples),
            native_forward_identity=native_identity, guardrail_checks=checks,
            unchanged_numeric_CPU_reuse=source_reuse, old_physical_input_evidence=evidence,
            CUDA_initialized=False, GPU_submissions=0, model_weights_loaded=0, ledger_written=False))
        print(CPU_STATUS); return
    proof_path = args.stage / CPU_RESULT
    proof = json.loads(proof_path.read_text())
    authority = json.loads((args.stage / 'N08-launch-authorization.json').read_text())
    validate_launch_authority(config, bound, registration, proof, authority,
        revision=args.source_revision, gpu_uuid=args.gpu_uuid, config_sha256=sha(args.stage / CONFIG),
        proof_sha256=sha(proof_path), registration_sha256=sha(args.stage / 'registration.json'))
    assert proof['native_forward_identity'] == native_identity and proof['runner_source_sha256'] == sha(Path(__file__))
    assert os.environ['CUDA_VISIBLE_DEVICES'] == args.gpu_uuid
    assert os.environ['WC_SUPERVISOR_PID'] == str(os.getppid())
    lease = (args.project / '.sync/gpu-locks' / (args.gpu_uuid + '.lock')).resolve()
    assert Path('/proc/self/fd/' + os.environ['WC_LOCK_FD']).resolve() == lease
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from wcomr.gpu_budget_pool_v2 import BudgetPool
    def resources():
        with BudgetPool(args.project).transaction() as pool:
            job = pool['jobs'][RUN]
            assert job['status'] == 'RESERVED_OR_RUNNING' and job['gpu_uuid'] == args.gpu_uuid
            assert job['source_revision'] == args.source_revision and job['launch_id'] == authority['launch_id']
            assert job['config_sha256'] == sha(args.stage / CONFIG)
            assert job['billed_limit_GPUh'] == config['billed_limit_GPUh']
            assert pool['cap_gpu_hours'] == config['cumulative_cap_GPUh']
            assert pool['origin_used_gpu_hours'] == config['budget_origin_used_GPUh']
            if config['billed_limit_GPUh'] >= 12: assert job['kind'] == 'V2_SPECIFIC_WHOLE_CARD_APPROVAL'
            observed = clean_registered_jobs(pool, RUN)
        metrics = metric_processes(args.project, os.getpid())
        if metrics: raise ValueError('A project metric process overlaps clean timing: ' + json.dumps(metrics))
        return dict(observed, project_CPU_metric_entrypoints=metrics, unix=time.time())
    from cosmos_oss.init import init_environment, init_output_dir, cleanup_environment
    output = (args.project / 'outputs' / RUN).resolve()
    assert output.is_dir() and not (output / 'runner.json').exists()
    state = dict(status='N08_FULL40_INITIALIZING_ONE_RESIDENT_MODEL', pid=os.getpid(),
        source_revision=args.source_revision, config_sha256=sha(args.stage / CONFIG), scope_counts=COUNTS,
        bound_timing_fingerprint=fingerprint(bound), matrix=bound['execution_plan'], bindings=bound['bindings'],
        started_unix=time.time(), model_load_calls=0, model_loads_completed=0, runs=[],
        native_forward_identity=native_identity, resource_observations=[],
        timing_claim='PENDING_FULL40_RAW_RGB_PARITY_AND_RESOURCE_ACCEPTANCE')
    def save(): write(output / 'runner.json', state)
    save(); init_environment(); init_output_dir(output, profile=False)
    try:
        state['resource_observations'].append(dict(section='BEFORE_LOAD', **resources())); save()
        install_core_inference_registration(setup.model, setup.experiment)
        start = time.perf_counter(); state['model_load_calls'] += 1; save()
        inference = im.Inference(setup); torch.cuda.synchronize()
        state['model_loads_completed'] += 1; state['load_seconds'] = time.perf_counter() - start
        model, net = inference.pipe.model, inference.pipe.model.net
        scheduler = model.sample_scheduler
        mode_contract = json.loads((args.stage / 'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        mode = establish_shared_eval(net, mode_contract['module_types']); verify_shared_eval(net, mode)
        assert type(net).forward is MinimalV1LVGDiT.forward and torch.__version__ == '2.7.1+cu128'
        assert torch.cuda.get_device_capability() == (8, 6) and len(net.blocks) == 28
        assert all(b.self_attn.backend == 'minimal_a2a' and type(b.self_attn.attn_op).__name__ == 'MinimalA2AAttnOp'
                   for b in net.blocks)
        settings = old['historical_wc_settings']
        wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
        initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)); origin = initial.fingerprint()
        versions = [(p, p._version) for p in net.parameters()]
        def restore():
            initial.restore(); verify_shared_eval(net, mode)
            return dict(original_state_sha256=origin, restored_state_sha256=initial.fingerprint(), shared_eval_verified=True)
        def run_one(planned, sample):
            state['resource_observations'].append(dict(id=planned['id'], section='BEFORE_PATH', **resources()))
            result = execute_one(inference, sample, planned, bound, restore_request_state=restore,
                table_parameters=tables, previous_parameters=previous, runtime=args.project / 'runtime', wc=wc, rf=rf,
                settings=settings, calibration=calibration, specs=specs[STRATEGY], inference_module=im,
                output=output / planned['id'], expected_shape=old['expected_real_shape'])
            state['resource_observations'].append(dict(id=planned['id'], section='AFTER_PATH', **resources()))
            row = archive_output(result, planned, output / planned['id'], output,
                                 expected_shape=old['expected_real_shape'])
            assert all(p._version == version for p, version in versions)
            return row
        def progress(value): state.update(value); save()
        run_registered_batch(bound, samples, run_one, save=progress)
        initial.restore(); assert initial.fingerprint() == origin and len(state['runs']) == 40
        state['resource_observations'].append(dict(section='AFTER_ALL', **resources()))
    except BaseException as error:
        state.update(status='N08_FULL40_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',
                     error_type=type(error).__name__, error=str(error))
        save(); raise
    finally:
        cleanup_environment(); state['ended_unix'] = time.time(); save()


if __name__ == '__main__': main()
