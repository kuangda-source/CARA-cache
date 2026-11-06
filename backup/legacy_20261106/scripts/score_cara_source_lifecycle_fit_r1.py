"""Single bounded GPU-hidden complete P1 FIT scoring attempt; never retry."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu-validation', action='store_true')
    args = parser.parse_args()
    from wcomr.cara_source_lifecycle_fit_scores_r1 import validate_config, SOURCES
    from wcomr.cara_fast_fidelity_r1 import file_sha, score_video_pair
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.cara_budget_search_journal_r1 import create_record
    from wcomr.cara_fast_spec_r1 import digest
    from wcomr.gpu_budget_pool_v2 import atomic_json

    config = json.loads(args.manifest.read_bytes())
    validate_config(config, cpu_validation=args.cpu_validation)
    if (os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != 'void'
            or args.output.exists()):
        raise ValueError('GPU-hidden original score attempt required; recover an existing output')
    identity = bind_original_process(os.getpid())
    create_record(args.output.with_name(args.output.stem+'-intent.json'), dict(
        config_sha256=digest(config), manifest_sha256=file_sha(args.manifest),
        original_identity=identity, no_replay=True, CPU_fixture_only=args.cpu_validation))
    started, cpu = time.monotonic(), time.process_time()
    result = dict(status='RUNNING_INTERNAL_FIT', packet_sha256=config['packet_sha256'],
        config_sha256=digest(config), registered_FIT_members=config['packet']['FIT_members'],
        candidate_id=config['packet']['candidate_id'], query_id=config['packet']['query_id'],
        source_sha256={p: file_sha(ROOT/p) for p in SOURCES}, CPU_fixture_only=args.cpu_validation,
        original_identity=identity, rows=[], GPU_submissions=0, started_unix=time.time())
    torch = None

    def interrupted(signum, frame):
        raise TimeoutError('Original internal scorer stopped by signal '+str(signum))

    signal.signal(signal.SIGALRM, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    signal.alarm(config['CPU_bound']['wall_seconds'])
    atomic_json(args.output, result)
    try:
        os.environ.update(TORCH_HOME=config['torch_home'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        sys.path.insert(0, config['piq_site'])
        import torch
        import lpips
        import piq
        if piq.__version__ != '0.8.0' or torch.cuda.is_initialized():
            raise ValueError('Frozen offline CPU PIQ0.8.0 required')
        torch.set_num_threads(config['CPU_bound']['cpus'])
        torch.set_num_interop_threads(1)

        def forbidden(*positional, **keywords):
            raise RuntimeError('Internal calibration forbids CUDA and model downloads')

        torch.cuda._lazy_init = forbidden
        torch.hub.download_url_to_file = forbidden
        checkpoint = Path(config['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
        linear = Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
        if (not all(file_sha(p) == h for p, h in config['weights_sha256'].items())
                or file_sha(checkpoint) != '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
                or file_sha(linear) != 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'):
            raise ValueError('Original fixed Alex weights required')
        alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval()
        for pair in config['packet']['pairs']:
            row = score_video_pair(pair['candidate'], pair['reference'], alex,
                                   expected_shape=tuple(config['packet']['score_shape']))
            result['rows'].append(dict(member=pair['member'], **row))
            atomic_json(args.output, result)
        result['status'] = 'COMPLETE_INTERNAL_FIT_NOT_SCIENTIFIC_ACCEPTANCE'
    except BaseException as error:
        result.update(status='FAILED_INTERNAL_FIT_DENOMINATOR_RETAINED',
                      error_type=type(error).__name__, error=str(error))
        raise
    finally:
        signal.alarm(0)
        result.update(ended_unix=time.time(), wall_seconds=time.monotonic()-started,
            CPU_process_seconds=time.process_time()-cpu,
            CUDA_initialized=False if torch is None else torch.cuda.is_initialized())
        atomic_json(args.output, result)


if __name__ == '__main__':
    main()
