"""One original CPU scoring process; a persistent intent prevents retries."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cpu-validation',action='store_true')
    args=parser.parse_args()
    from wcomr.cara_s_endpoint_scores_r1 import validate_config,SCORER_SOURCES
    from wcomr.cara_fast_fidelity_r1 import file_sha,score_video_pair
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.cara_budget_search_journal_r1 import create_record
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.policy_price_terminal_r1 import require
    cfg=json.loads(args.manifest.read_text());ids=validate_config(cfg,cpu_validation=args.cpu_validation)
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void',
            'Original GPU-hidden CPU environment required')
    require(not args.output.exists(),'Recover the original score output; never rescore')
    intent=args.output.with_name(args.output.stem+'-intent.json')
    identity=bind_original_process(os.getpid())
    manifest_sha=file_sha(args.manifest)
    create_record(intent,dict(manifest_sha256=manifest_sha,original_identity=identity,
        registered_pairs=ids,worker_sha256=file_sha(__file__),CPU_fixture_only=args.cpu_validation,no_replay=True))
    start=time.time();cpu=time.process_time();torch=None
    result=dict(status='RUNNING',analysis_scope_sha256=cfg['analysis_scope_sha256'],protocol_sha256=cfg['protocol_sha256'],
        manifest_sha256=manifest_sha,worker_sha256=file_sha(__file__),source_actual_sha256={p:file_sha(ROOT/p) for p in SCORER_SOURCES},
        original_identity=identity,rows=[],registered_pairs=ids,CPU_fixture_only=args.cpu_validation,GPU_submissions=0,started_unix=start)
    def interrupted(signum,frame):raise TimeoutError('Original CPU scorer stopped by signal '+str(signum))
    signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted)
    signal.alarm(int(cfg['CPU_bound']['wall_hours']*3600))
    atomic_json(args.output,result)
    try:
        os.environ.update(TORCH_HOME=cfg['torch_home'],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        sys.path.insert(0,cfg['piq_site'])
        import torch
        import lpips
        import piq
        require(piq.__version__=='0.8.0','Frozen PIQ0.8.0 required')
        torch.set_num_threads(cfg['CPU_bound']['cpus']);torch.set_num_interop_threads(1)
        require(not torch.cuda.is_initialized(),'CPU-only scoring required')
        def forbidden(*positional,**keywords):raise RuntimeError('No CUDA/download allowed')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        require(all(file_sha(p)==h for p,h in cfg['weights_sha256'].items()),'Bound scorer weights differ')
        checkpoint=Path(cfg['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
        linear=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
        require(file_sha(checkpoint)=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
                and file_sha(linear)=='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0',
                'Original Alex weights required')
        alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
        for pair in cfg['pairs']:
            row=score_video_pair(pair['candidate'],pair['reference'],alex,expected_shape=tuple(cfg['score_shape']))
            result['rows'].append(dict(id=pair['id'],member=pair['candidate']['member'],role=pair['candidate']['role'],**row))
            atomic_json(args.output,result)
        result['status']='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
    except BaseException as error:
        result.update(status='FAILED_DENOMINATOR_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        result.update(ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu,
            CUDA_initialized=False if torch is None else torch.cuda.is_initialized())
        atomic_json(args.output,result)


if __name__=='__main__':main()
