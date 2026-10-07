#!/usr/bin/env python3
"""One-parent/ten-suffix/six-output native-tail diagnostic; scoring runs after release."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate(project, stage, runtime, output):
    sys.path.insert(0, str(stage/'src'))
    from wcomr.rv0_native_onset_execution import validate_stage
    config = json.loads((stage/'onset-config.json').read_text())
    if output.parent.name != config['run_id']:
        raise ValueError('Independent placement output identity differs')
    result = validate_stage(project, stage, runtime, config, selected=config['GPU_execution_selected'])
    mode = json.loads((stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
    load(stage/'src/wcomr/h0_eval_scope.py', 'causal_mode_sources').validate_mode_sources(runtime, mode, config)
    # Reuse its asset/source validator, never the old profile's GPU entrypoint.
    assets = load(stage/'scripts/run_wc_s0_profile.py', 'causal_asset_validator')
    assets.validate(project, stage, runtime)
    return config, mode, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'runtime', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--source-revision')
    parser.add_argument('--draft-check', action='store_true')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--cpu-import-check', action='store_true')
    args = parser.parse_args()
    if args.draft_check:
        source = args.stage/'src'
        if not source.is_dir(): source = args.project/'src'
        sys.path.insert(0, str(source))
        from wcomr.rv0_native_onset_execution import validate_config
        config = json.loads((args.stage/'onset-config.json').read_text())
        print(json.dumps(validate_config(config))); return
    config, mode, validation = validate(args.project, args.stage, args.runtime, args.output)
    if args.validate_only:
        print(json.dumps(validation)); return
    if args.cpu_import_check:
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
                           TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                           PYTHONPATH=str(args.stage/'src'))
        imported = subprocess.run([sys.executable, str(args.stage/'scripts/check_wc_rv0_video_condition_import.py'),
            '--runtime', str(args.runtime), '--stage', str(args.stage)], env=environment,
            capture_output=True, text=True, cwd=args.runtime, check=True, timeout=90)
        print(imported.stdout.strip())
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('CPU check created CUDA context')
        def forbidden(*a, **k): raise RuntimeError('CUDA initialization forbidden in causal CPU imports')
        torch.cuda._lazy_init = forbidden
        from wcomr import (rv0_native_onset_causal, rv0_fork, rv0_actions, rv0_native_onset_execution,
                           rv0_native_onset_evaluation, rv0_native_onset_scores, rv0_video_reader, rv0_lpips)
        for module in [rv0_native_onset_causal, rv0_fork, rv0_actions, rv0_native_onset_execution,
                       rv0_native_onset_evaluation, rv0_native_onset_scores, rv0_video_reader, rv0_lpips]:
            if not Path(module.__file__).resolve().is_relative_to((args.stage/'src').resolve()):
                raise ValueError('Causal core import origin differs')
        print(json.dumps({'status': 'NATIVE_RESPONSE_ONSET_ACTUAL_CPU_IMPORT_PASS_NO_MODEL_OR_CUDA',
                          'cuda_initialized': False, 'GPU_submissions': 0})); return
    from wcomr.rv0_native_onset_execution import validate_config
    validate_config(config, selected=True)
    if (args.gpu_uuid != config['gpu_uuid'] or os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid
            or Path.cwd().resolve() != args.runtime.resolve()
            or type(args.source_revision) is not str or len(args.source_revision) != 40
            or any(c not in '0123456789abcdef' for c in args.source_revision)):
        raise ValueError('Frozen source revision and independently supervised selected GPU required')
    if (os.environ.get('WC_SUPERVISOR_PID') != str(os.getppid())
            or not os.environ.get('WC_LOCK_FD', '').isdigit()):
        raise ValueError('Runner must inherit the direct live supervisor and project lock')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    sys.path[:0] = [str(args.stage/'src'), str(args.runtime), str(args.runtime/'packages/cosmos-oss'),
                   str(args.runtime/'packages/cosmos-cuda')]
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.update(HF_HUB_CACHE=str(args.project/'hfhub'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    state = {'run_card': config['card'], 'scope': config, 'source_revision': args.source_revision,
             'status': 'INITIALIZING', 'pid': os.getpid(), 'started_unix': time.time(),
             'gpu_uuid': args.gpu_uuid, 'requests': [], 'RV_labels': 0,
             'planned_parent_phases': 1, 'planned_suffix_controls': 10, 'planned_encoded_outputs': 6,
             'complete_RV0_acceptance': False, 'clean_speed_measurement': False,
             'complete_video': False, 'CUDA_initialized': False, 'toy_fixture': False,
             'scoring_after_GPU_release': True}
    def save():
        temporary = args.output/'receipt.tmp'
        temporary.write_text(json.dumps(state, indent=2, allow_nan=False)+'\n')
        temporary.replace(args.output/'receipt.json')
    save(); cleanup = None
    try:
        import torch
        from cosmos_oss.init import init_environment, init_output_dir, cleanup_environment
        init_environment(); init_output_dir(args.output, profile=False); cleanup = cleanup_environment
        from cosmos_predict2.config import SetupArguments, InferenceArguments
        import cosmos_predict2.inference as inference_module
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.h0_mode import establish_shared_eval, verify_shared_eval
        from wcomr.mid_coverage import tree_digest
        from wcomr.rv0_native_onset_causal import run_native_onset_causal_batch
        from wcomr.rv0_restore import cuda_memory_observation
        if torch.__version__ != '2.7.1+cu128' or torch.cuda.get_device_capability() != (8, 6):
            raise ValueError('Actual Torch/sm86 differs')
        params = json.loads((args.project/'configs/f1_setup.json').read_text())
        if params['disable_guardrails'] or params['use_torch_compile'] or params['offload_diffusion_model']:
            raise ValueError('Frozen guarded/eager/no diffusion offload scope differs')
        params.update(keep_going=False, worldcache_enabled=True, output_dir=str(args.output))
        setup = SetupArguments(**params)
        state['registration'] = install_core_inference_registration(setup.model, setup.experiment)
        available = InferenceArguments.from_files([args.project/'configs/cal_w1d8.jsonl'])
        samples = [available[i] for i in config['sample_indices']]
        if [s.name for s in samples] != config['sample_names'] or any(s.seed != 0 or s.num_steps != 35 for s in samples):
            raise ValueError('Frozen Human CAL identity differs')
        started = time.perf_counter(); inference = inference_module.Inference(setup); torch.cuda.synchronize()
        state['load_seconds'] = time.perf_counter()-started
        state['CUDA_initialized'] = torch.cuda.is_initialized()
        state['memory_after_load'] = cuda_memory_observation()
        model, net = inference.pipe.model, inference.pipe.model.net
        state['mode_setup'] = establish_shared_eval(net, mode['module_types'])
        verify_shared_eval(net, state['mode_setup'])
        state['network_class'] = type(net).__module__+'.'+type(net).__name__
        if len(net.blocks) != 28 or model.config.use_torch_compile:
            raise ValueError('Actual dense model structure differs')
        for block in net.blocks:
            attention = block.self_attn
            if (attention.backend, attention.n_heads, attention.head_dim, type(attention.attn_op).__name__) != ('minimal_a2a', 16, 128, 'MinimalA2AAttnOp'):
                raise ValueError('Original dense attention binding differs')
        fields = ['worldcache_num_steps', 'worldcache_rel_l1_thresh', 'worldcache_ret_ratio', 'probe_depth',
                  'worldcache_motion_sensitivity', 'worldcache_flow_enabled', 'worldcache_flow_scale',
                  'worldcache_saliency_enabled', 'worldcache_saliency_weight', 'worldcache_osi_enabled', 'worldcache_dynamic_decay']
        settings = {name: getattr(net, name) for name in fields}
        if (settings['worldcache_num_steps'], settings['probe_depth'], settings['worldcache_rel_l1_thresh']) != (35, 2, .06):
            raise ValueError('Frozen WC settings differ')
        state['wc_settings'] = settings
        contexts = [(config['run_id']+':'+s.name, 'Cosmos-Predict2.5-2B:'+config['f1_setup_sha256'],
                     tree_digest(s.model_dump(mode='json'))) for s in samples]
        state['reference_contexts'] = [list(v) for v in contexts]; save()
        run_native_onset_causal_batch(inference, samples, wc, settings, state=state, save=save, output=args.output,
                         inference_module=inference_module, contexts=contexts, mode_setup=state['mode_setup'],
                         runtime=args.runtime, config=config, require_historical_bridge=True)
        state['complete_video'] = True; state['memory_after_all_controls'] = cuda_memory_observation()
    except BaseException as error:
        state.update(status='TECH_BLOCKED_NATIVE_RESPONSE_ONSET_1_PARENT_10_SUFFIX_6_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__, error=str(error))
        traceback.print_exc(); raise
    finally:
        if cleanup is not None:
            try: cleanup()
            except Exception as error:
                state['cleanup_error'] = str(error)
                state['complete_video'] = False
                state['status'] = 'TECH_BLOCKED_PLACEMENT_CLEANUP'
        state['ended_unix'] = time.time()
        state['process_wall_seconds'] = state['ended_unix']-state['started_unix']; save()


if __name__ == '__main__': main()
