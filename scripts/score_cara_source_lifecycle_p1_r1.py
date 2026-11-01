"""One released P1 post-score CPU; full denominator retained on any failure."""
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
    from wcomr.cara_source_lifecycle_p1_scores_r1 import validate_config,SOURCES
    from wcomr.cara_fast_fidelity_r1 import file_sha,score_video_pair
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.cara_budget_search_journal_r1 import create_record
    from wcomr.cara_fast_spec_r1 import digest
    from wcomr.gpu_budget_pool_v2 import atomic_json
    cfg=json.loads(args.manifest.read_bytes());ids=validate_config(cfg,cpu_validation=args.cpu_validation)
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void' or args.output.exists():
        raise ValueError('Original GPU-hidden post-score CPU required; recover rather than rescore')
    identity=bind_original_process(os.getpid())
    create_record(args.output.with_name(args.output.stem+'-intent.json'),dict(config_sha256=digest(cfg),
        original_identity=identity,registered_pairs=ids,no_replay=True,CPU_fixture_only=args.cpu_validation))
    started=time.time();torch=None
    result=dict(status='P1_POST_SCORES_RUNNING',config_sha256=digest(cfg),source_sha256={n:file_sha(ROOT/n) for n in SOURCES},
        original_identity=identity,registered_pairs=ids,rows=[],CPU_fixture_only=args.cpu_validation,
        GPU_submissions=0,started_unix=started)
    def interrupted(signum,frame):raise TimeoutError('Original P1 released scorer interrupted by '+str(signum))
    signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted)
    signal.alarm(cfg['CPU_bound']['wall_seconds']);atomic_json(args.output,result)
    try:
        os.environ.update(TORCH_HOME=cfg['torch_home'],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        sys.path.insert(0,cfg['piq_site'])
        import torch
        import lpips
        import piq
        if piq.__version__!='0.8.0' or torch.cuda.is_initialized():raise ValueError('Original offline CPU PIQ0.8.0 required')
        torch.set_num_threads(cfg['CPU_bound']['cpus']);torch.set_num_interop_threads(1)
        def forbidden(*args,**kwargs):raise RuntimeError('P1 post-score CPU forbids CUDA and downloads')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        checkpoint=Path(cfg['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
        linear=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
        if (any(file_sha(p)!=h for p,h in cfg['weights_sha256'].items())
                or file_sha(checkpoint)!='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
                or file_sha(linear)!='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'):
            raise ValueError('Frozen original Alex weights required')
        alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
        for pair in cfg['manifest']['new_pairs']:
            row=score_video_pair(pair['candidate'],pair['reference'],alex,expected_shape=tuple(cfg['score_shape']))
            if row['decoded_RGB_sha256']!=pair['expected_decoded_RGB_sha256']:
                raise ValueError('Post-score decoded RGB differs from the full released reader')
            result['rows'].append(dict(id=pair['id'],member=pair['member'],**row));atomic_json(args.output,result)
        result['status']='P1_COMPLETE_NEW_PAIRS_PENDING_INDEPENDENT_ACCEPTANCE'
    except BaseException as error:
        result.update(status='P1_FAILED_NEW_PAIR_DENOMINATOR_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0)
        result.update(ended_unix=time.time(),wall_seconds=time.time()-started,
                      CUDA_initialized=False if torch is None else torch.cuda.is_initialized())
        atomic_json(args.output,result)


if __name__=='__main__':main()
