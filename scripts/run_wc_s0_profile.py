#!/usr/bin/env python3
"""Bounded official WC profile and separately captured real QKV. No sparse edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def validate(project, stage, runtime):
    c = json.loads((stage / 'profile-config.json').read_text())
    if c['max_gpu_wall_seconds'] != 750 or c['phases'] != ['profile', 'capture']:
        raise ValueError('Frozen two-phase scope required')
    if c['capture_calls'] != [1, 2, 71, 72] or c['capture_layers'] != [2, 14, 27]:
        raise ValueError('Frozen diagnostic selection required')
    for relative, digest in c['project_files_sha256'].items():
        if sha(project / relative) != digest:
            raise RuntimeError('Project identity mismatch: ' + relative)
    for relative, digest in c['runtime_files_sha256'].items():
        if sha(runtime / relative) != digest:
            raise RuntimeError('Runtime identity mismatch: ' + relative)
    completion = json.loads((project / 'manifests/runtime_completion.json').read_text())
    for relative, digest in completion['files'].items():
        if sha(runtime / relative) != digest:
            raise RuntimeError('Source-completion mismatch: ' + relative)
    sampling = json.loads((project / 'manifests/f1_runtime_protocol.json').read_text())
    if sha(runtime / 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py') != sampling['scheduler_source_sha256']:
        raise RuntimeError('Scheduler mismatch')
    outcome = json.loads((project / 'manifests/f1_outcome_protocol.json').read_text())
    if sha(runtime / 'cosmos_predict2/inference.py') != outcome['inference_source_sha256']:
        raise RuntimeError('Outcome source mismatch')
    checkpoint = Path(c['checkpoint']['path'])
    if checkpoint.stat().st_size != c['checkpoint']['bytes'] or sha(checkpoint) != c['checkpoint_sha256']:
        raise RuntimeError('Actual checkpoint changed')
    samples = [json.loads(x) for x in (project / 'configs/cal_w1d8.jsonl').read_text().splitlines() if x]
    if samples[0]['name'] != c['sample_name'] or samples[0]['num_steps'] != 35 or samples[0]['seed'] != 0:
        raise ValueError('Frozen first CAL case mismatch')
    return c, sampling


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'runtime', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--gpu-uuid')
    p.add_argument('--validate-only', action='store_true')
    a = p.parse_args()
    c, sampling = validate(a.project, a.stage, a.runtime)
    if a.validate_only:
        print(json.dumps({'status': 'S0_IDENTITIES_CHECKPOINT_SCOPE_PASS_NO_TORCH_OR_GPU',
                          'config_sha256': sha(a.stage / 'profile-config.json'), 'sample': c['sample_name']}))
        return
    if not a.gpu_uuid or Path.cwd().resolve() != a.runtime.resolve():
        raise ValueError('Selected UUID and actual assembled runtime cwd required')
    a.output.mkdir(parents=True, exist_ok=False)
    os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0, str(a.project / 'src'))
    sys.path.insert(0, str(a.stage / 'src'))
    state = {'status': 'INITIALIZING', 'pid': os.getpid(), 'started_unix': time.time(),
             'scope': c, 'sampling_protocol': sampling, 'gpu_uuid': a.gpu_uuid, 'phases': []}
    def save():
        tmp = a.output / 'receipt.tmp'
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(a.output / 'receipt.json')
    save()
    try:
        from cosmos_oss.init import init_environment, init_output_dir, cleanup_environment
        init_environment()
        init_output_dir(a.output, profile=False)
        import torch
        from cosmos_predict2.config import SetupArguments, InferenceArguments
        from cosmos_predict2.inference import Inference
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common import presets
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.measurement import StageTimes, BlockCounts
        from wcomr.protocol import validate_schedule
        from wcomr.guardrail_observation import GuardrailObservation
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.decoder_policy import decode_policy, backend_flags
        from wcomr.stage_witness import StageWitness
        from wcomr.wc_cost_observer import WCCostObserver
        from wcomr.wc_qkv_snapshot import dump_qkv
        if torch.cuda.get_device_capability() != (8, 6):
            raise RuntimeError('Expected admitted sm86')
        params = json.loads((a.project / 'configs/f1_setup.json').read_text())
        if params['disable_guardrails'] or params['use_torch_compile']:
            raise ValueError('Frozen guardrail/eager settings required')
        params.update(keep_going=True, worldcache_enabled=True, output_dir=str(a.output))
        setup = SetupArguments(**params)
        state['registration'] = install_core_inference_registration(setup.model, setup.experiment)
        sample = InferenceArguments.from_files([a.project / 'configs/cal_w1d8.jsonl'])[0]
        state.update(setup=json.loads(setup.model_dump_json()), torch=torch.__version__, cuda=torch.version.cuda,
                     gpu_name=torch.cuda.get_device_name(), backend_flags=backend_flags())
        save()
        torch.cuda.synchronize()
        load_start = time.perf_counter()
        inference = Inference(setup)
        torch.cuda.synchronize()
        state['model_load_seconds'] = time.perf_counter() - load_start
        model, net = inference.pipe.model, inference.pipe.model.net
        if getattr(model.config, 'use_torch_compile', False) or len(net.blocks) != 28:
            raise RuntimeError('Actual model structure differs')
        for block in net.blocks:
            attn = block.self_attn
            if (attn.backend, attn.n_heads, attn.head_dim, type(attn.attn_op).__name__) != ('minimal_a2a', 16, 128, 'MinimalA2AAttnOp'):
                raise RuntimeError('Actual attention binding differs')
        state['actual_model'] = {'blocks': len(net.blocks), 'heads': 16, 'head_dim': 128,
                                 'backend': 'minimal_a2a', 'attention_op': type(net.blocks[0].self_attn.attn_op).__name__}
        save()
        for phase in c['phases']:
            phase_dir = a.output / phase
            phase_dir.mkdir()
            result = {'phase': phase, 'sample': sample.name, 'status': 'GENERATING', 'snapshots': []}
            state['phases'].append(result)
            state['status'] = 'GENERATING_' + phase.upper()
            save()
            counts = BlockCounts(net.blocks, cache_model=net)
            timing = StageTimes(torch.cuda.synchronize)
            timing.wrap(model, 'generate_samples_from_batch', 'denoising')
            timing.wrap(model, 'decode', 'decode')
            timing.wrap(presets, 'run_text_guardrail', 'text_guardrail')
            timing.wrap(presets, 'run_video_guardrail', 'video_guardrail')
            if model.text_encoder is not None:
                timing.wrap(model.text_encoder, 'compute_text_embeddings_online', 'text_encoding')
            witnesses = StageWitness()
            witnesses.wrap(model, 'generate_samples_from_batch', after=lambda x: witnesses.record('latent', x))
            witnesses.wrap(model, 'decode', call_context=lambda: decode_policy(True))
            guards = GuardrailObservation(presets)
            def capture(args, context):
                target = phase_dir / ('qkv-call%02d-layer%02d.pt' % (context['call'], context['layer']))
                if any(value.device.type != 'cuda' for value in args):
                    raise RuntimeError('Expected real CUDA QKV')
                entry = dump_qkv(args, target, c['expected_qkv_shape'], c['expected_qkv_dtype'])
                result['snapshots'].append(dict(context, **entry))
                save()
                return entry
            observer = WCCostObserver(net, event_factory=(lambda: torch.cuda.Event(enable_timing=True)) if phase == 'profile' else None,
                                      capture=capture if phase == 'capture' else None,
                                      calls=c['capture_calls'], layers=c['capture_layers'])
            if phase == 'profile':
                for layer, block in enumerate(net.blocks):
                    scope = 'probe' if layer < 2 else 'deep'
                    observer.wrap(block.self_attn.attn_op, 'forward', scope + '_self_core', layer)
                    observer.wrap(block.cross_attn.attn_op, 'forward', scope + '_cross_core', layer)
                    observer.wrap(block.mlp, 'forward', scope + '_mlp', layer)
                    for attr in ['q_proj', 'k_proj', 'v_proj', 'output_proj']:
                        observer.wrap(getattr(block.self_attn, attr), 'forward', scope + '_self_' + attr, layer)
                for attr in ['estimate_optical_flow', 'warp_feature', 'compute_saliency_map']:
                    observer.wrap(wc, attr, attr)
            else:
                for layer in c['capture_layers']:
                    observer.attach_capture(net.blocks[layer].self_attn.attn_op, layer)
            try:
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                start = time.perf_counter()
                paths = inference.generate([sample], output_dir=phase_dir)
                torch.cuda.synchronize()
                result.update(end_to_end_seconds=time.perf_counter() - start, stages=timing.values,
                              outcome=guards.classify(paths), guardrail_events=guards.events,
                              block_counts=counts.result(), denoiser_trace=counts.trace, witnesses=witnesses.events,
                              peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved())
                if phase == 'profile':
                    costs = observer.resolve()
                    cost_path = phase_dir / 'component-events.json'
                    cost_path.write_text(json.dumps(costs, indent=2) + '\n')
                    result['component_costs'] = {'totals': costs['totals'], 'rows': len(costs['rows']), 'path': str(cost_path), 'sha256': sha(cost_path), 'warning': costs['warning']}
                save()
                if result['outcome'] == 'TEXT_REJECTED':
                    raise RuntimeError('Frozen sample text rejected; no alternate sample substitution')
                scheduler = model.sample_scheduler
                observed = {'scheduler_class': type(scheduler).__name__, 'requested_steps': sample.num_steps,
                            'actual_schedule_steps': len(scheduler.timesteps), 'timesteps': scheduler.timesteps.detach().cpu().tolist(),
                            'use_kerras_sigma': model.config.use_kerras_sigma_at_inference, 'worldcache_horizon': net.worldcache_num_steps}
                result['sampling'] = observed
                validate_schedule(observed, counts.result(), sampling, 'worldcache')
                if phase == 'capture':
                    expected = {(call, layer) for call in c['capture_calls'] for layer in c['capture_layers']}
                    if {(x['call'], x['layer']) for x in result['snapshots']} != expected or len(result['snapshots']) != len(expected):
                        raise RuntimeError('Incomplete real-QKV coverage')
                    if any(not counts.trace[call - 1]['deep_executed'] for call in c['capture_calls']):
                        raise RuntimeError('Capture unexpectedly from cache-only call')
                result['paths'] = []
                for path in paths:
                    path = Path(path)
                    probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                                            'stream=width,height,nb_read_frames,r_frame_rate', '-of', 'json', str(path)], capture_output=True, text=True, check=True, timeout=30)
                    result['paths'].append({'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size, 'ffprobe': json.loads(probe.stdout)})
                result['status'] = 'DIAGNOSTIC_PHASE_COMPLETE_NOT_QUALITY_EVIDENCE'
                save()
            finally:
                observer.close()
                guards.close()
                witnesses.close()
                timing.close()
                counts.close()
        left, right = state['phases']
        state['phase_consistency'] = {k: left[k] == right[k] for k in ['block_counts', 'denoiser_trace', 'witnesses', 'sampling', 'outcome']}
        state['status'] = 'S0_PROFILE_AND_ACTUAL_QKV_COMPLETE_REQUIRES_AUDIT'
        cleanup_environment()
    except BaseException as exc:
        state.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
        traceback.print_exc()
        raise
    finally:
        state['ended_unix'] = time.time()
        state['process_wall_seconds'] = state['ended_unix'] - state['started_unix']
        save()


if __name__ == '__main__':
    main()
