"""Explicit bounded pair manifest -> one streaming Fidelity-v2 CPU receipt.

Never discovers videos or launches a background task. The caller supplies
scope-bound descriptors and an already admitted CPU container/resource bound.
"""
import argparse
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    from wcomr.cara_fast_spec_r1 import digest
    from wcomr.cara_fast_fidelity_r1 import file_sha,score_video_pair
    from wcomr.cara_fast_scoring_manifest_r2 import validate_pair_identities
    cfg=json.loads(a.manifest.read_text());bound=cfg['CPU_bound']
    if (cfg['protocol_sha256']!=digest(json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json').read_text()))
            or not 1<=bound['cpus']<=2 or not 0<bound['wall_hours']<=6
            or not 0<len(cfg['pairs'])<=bound['max_pairs']<=44
            or bound['memory_GiB']!=8 or cfg.get('GPU_released') is not True):
        raise ValueError('Frozen protocol and explicit post-release CPU resource bound required')
    ids=validate_pair_identities(cfg)
    signal.alarm(int(bound['wall_hours']*3600));start=time.time();cpu=time.process_time()
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',TORCH_HOME=cfg['torch_home'],
                      HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,cfg['piq_site'])
    import torch
    import lpips
    import piq
    if piq.__version__!='0.8.0':raise ValueError('Frozen PIQ 0.8.0 implementation required')
    torch.set_num_threads(bound['cpus']);torch.set_num_interop_threads(1)
    if torch.cuda.is_initialized():raise ValueError('CPU-only scoring process required')
    def forbidden(*args,**kwargs):raise RuntimeError('No CUDA/download allowed')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    for path,expected in cfg['weights_sha256'].items():
        if file_sha(path)!=expected:raise ValueError('Bound scorer weight differs')
    checkpoint=Path(cfg['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
    linear=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
    if (file_sha(checkpoint)!='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
            or file_sha(linear)!='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'):
        raise ValueError('Original Alex weights required')
    # Container memory/cpu boundaries are checked by the existing lifecycle.
    # This worker independently enforces wall time and thread count.
    result=dict(status='RUNNING',scope_sha256=cfg['scope_sha256'],protocol_sha256=cfg['protocol_sha256'],
                manifest_sha256=file_sha(a.manifest),worker_sha256=file_sha(__file__),rows=[],
                registered_pairs=ids,GPU_submissions=0,started_unix=start)
    def save():
        temp=a.output.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');temp.replace(a.output)
    save()
    try:
        alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
        for pair in cfg['pairs']:
            row=score_video_pair(pair['candidate'],pair['reference'],alex)
            result['rows'].append(dict(id=pair['id'],member=pair['candidate']['member'],
                                      role=pair['candidate']['role'],**row));save()
        result['status']='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
    except BaseException as error:
        result.update(status='FAILED_DENOMINATOR_RETAINED',error=repr(error));raise
    finally:
        result.update(ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu,
                      CUDA_initialized=torch.cuda.is_initialized());save()


if __name__=='__main__':main()
