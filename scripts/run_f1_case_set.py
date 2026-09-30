"""One process per baseline arm. Run from the assembled Cosmos runtime.

Requires a supervisor wall-time limit and live GPU admission. Does not download
models. Eager technical smoke with identical offloading and retained guardrails;
not a reproduction of the paper's compiled throughput claim.
"""
import argparse
import hashlib
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--mode', choices=['native', 'worldcache'], required=True)
parser.add_argument('--gpu-uuid', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
project, output = args.project.resolve(), args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu_uuid
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
sys.path.insert(0, str(project / 'src'))
state = {'stage': 'F1_SMOKE', 'mode': args.mode, 'pid': os.getpid(),
         'started_unix': time.time(), 'status': 'INITIALIZING', 'samples': []}

def save():
    tmp = output / 'receipt.tmp'
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(output / 'receipt.json')

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()

save()
try:
    # Fail closed before model loading if the documented runtime differs.
    runtime = Path.cwd()
    lock = json.loads((project / 'manifests/upstream.json').read_text())
    module = runtime / 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    if sha(module) != lock['cache_module_sha256']:
        raise RuntimeError('WorldCache source differs from pinned module')
    completion = json.loads((project / 'manifests/runtime_completion.json').read_text())
    for relative, expected in completion['files'].items():
        if sha(runtime / relative) != expected:
            raise RuntimeError('Source-completion hash mismatch: ' + relative)
    state['source_completion_commit'] = completion['completion_commit']
    from cosmos_oss.init import init_environment, init_output_dir, cleanup_environment
    init_environment()
    init_output_dir(output, profile=False)
    import torch
    from cosmos_predict2.config import SetupArguments, InferenceArguments
    from cosmos_predict2.inference import Inference
    from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common import presets
    from wcomr.measurement import StageTimes, BlockCounts
    from wcomr.protocol import validate_schedule
    policy_path = project / 'manifests/f1_runtime_protocol.json'
    policy = json.loads(policy_path.read_text())
    scheduler_source = runtime / 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py'
    if sha(scheduler_source) != policy['scheduler_source_sha256']:
        raise RuntimeError('Scheduler source differs from approved protocol')
    state['sampling_protocol'] = policy
    state['sampling_protocol_sha256'] = sha(policy_path)

    params = json.loads((project / 'configs/f1_setup.json').read_text())
    if params['disable_guardrails'] or params['use_torch_compile']:
        raise ValueError('Unsupported change to frozen F1 execution profile')
    params.update(output_dir=str(output), worldcache_enabled=args.mode == 'worldcache')
    samples = InferenceArguments.from_files([project / 'configs/smoke.jsonl'])
    setup = SetupArguments(**params)
    from wcomr.runtime_config import install_core_inference_registration
    state['registration_adapter'] = install_core_inference_registration(setup.model, setup.experiment)
    state.update(setup=json.loads(setup.model_dump_json()),
                 input_sha256=sha(project / 'configs/smoke.jsonl'),
                 profile_sha256=sha(project / 'configs/f1_setup.json'),
                 torch=torch.__version__, cuda=torch.version.cuda,
                 measurement='Synchronized stage boundaries and two block hooks in both arms; first sample includes cold effects')
    save()
    torch.cuda.synchronize()
    start = time.perf_counter()
    inference = Inference(setup)
    torch.cuda.synchronize()
    state['model_load_seconds'] = time.perf_counter() - start
    state['status'] = 'GENERATING'
    model = inference.pipe.model
    if getattr(model.config, 'use_torch_compile', False):
        raise RuntimeError('Model config enabled compilation despite frozen eager profile')
    counts = BlockCounts(model.net.blocks, cache_model=model.net)
    timing = StageTimes(torch.cuda.synchronize)
    timing.wrap(model, 'generate_samples_from_batch', 'denoising')
    timing.wrap(model, 'decode', 'decode')
    timing.wrap(presets, 'run_text_guardrail', 'text_guardrail')
    timing.wrap(presets, 'run_video_guardrail', 'video_guardrail')
    if model.text_encoder is not None:
        timing.wrap(model.text_encoder, 'compute_text_embeddings_online', 'text_encoding')
    save()
    try:
        for index, sample in enumerate(samples):
            timing.reset(); counts.reset()
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize(); start = time.perf_counter()
            state['current_sample'] = sample.name; save()
            paths = inference.generate([sample], output_dir=output)
            torch.cuda.synchronize()
            total = time.perf_counter() - start
            if len(paths) != 1 or not Path(paths[0]).is_file():
                raise RuntimeError('Expected one accepted generated video')
            path = Path(paths[0])
            probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,nb_read_frames,r_frame_rate', '-of', 'json', str(path)],
                check=True, capture_output=True, text=True, timeout=60)
            stream = json.loads(probe.stdout)['streams'][0]
            h, w = map(int, sample.resolution.split(','))
            if (stream['width'], stream['height'], int(stream['nb_read_frames'])) != (w, h, sample.num_output_frames):
                raise RuntimeError('Generated output specification mismatch')
            if Fraction(stream['r_frame_rate']) != 16:
                raise RuntimeError('Unexpected output frame rate')
            block_counts = counts.result()
            # Preserve the observation before any protocol assertion can reject it.
            # A failed run must still explain actual scheduler/block behavior.
            scheduler = model.sample_scheduler
            state['pending_sample'] = {
                'name': sample.name, 'path': str(path), 'ffprobe': stream,
                'end_to_end_seconds': total, 'stages': timing.values,
                'block_counts': block_counts,
                'scheduler_class': type(scheduler).__name__,
                'scheduler_config': dict(scheduler.config),
                'requested_steps': sample.num_steps,
                'actual_schedule_steps': len(scheduler.timesteps),
                'timesteps': scheduler.timesteps.detach().cpu().tolist(),
                'use_kerras_sigma': model.config.use_kerras_sigma_at_inference,
                'worldcache_horizon': getattr(model.net, 'worldcache_num_steps', None),
                'denoiser_trace': counts.trace,
            }
            save()
            validate_schedule(state['pending_sample'], block_counts, policy, args.mode)
            state['samples'].append({'name': sample.name, 'index': index,
                'cold_first_sample': index == 0, 'end_to_end_seconds': total,
                'stages': timing.values, 'block_counts': block_counts,
                'sampling': state['pending_sample'],
                'peak_allocated_bytes_since_upstream_last_reset': torch.cuda.max_memory_allocated(),
                'peak_reserved_bytes_since_upstream_last_reset': torch.cuda.max_memory_reserved(),
                'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size, 'ffprobe': stream})
            save()
    finally:
        timing.close(); counts.close()
    state['status'] = 'TECHNICAL_PASS_AWAITING_VIDEO_REVIEW'
    cleanup_environment()
except BaseException as exc:
    state.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
    traceback.print_exc()
    raise
finally:
    state['ended_unix'] = time.time()
    state['process_wall_seconds'] = state['ended_unix'] - state['started_unix']
    save()
