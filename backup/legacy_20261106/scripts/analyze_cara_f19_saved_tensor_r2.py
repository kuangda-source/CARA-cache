#!/usr/bin/env python3
"""One bounded CPU worker; original B1 input mount is read-only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--progress',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--base-src',type=Path,required=True)
    parser.add_argument('--overlay-src',type=Path,required=True)
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or Path('/dev/nvidia0').exists():
        raise RuntimeError('GPU-hidden CPU-only worker required')
    sys.path.insert(0,str(args.base_src))
    import wcomr
    wcomr.__path__.insert(0,str(args.overlay_src/'wcomr'))
    import torch
    def forbid(*a,**kw):
        raise RuntimeError('Saved-tensor worker forbids CUDA initialization')
    torch.cuda._lazy_init = forbid
    torch.set_num_threads(2)
    from wcomr.cara_f19_saved_tensor_r2 import analyze

    started = time.time()
    def progress(value):
        value.update(observed_unix=time.time(),started_unix=started,GPU_submissions=0)
        temporary=args.progress.with_suffix('.tmp')
        temporary.write_text(json.dumps(value)+'\n')
        temporary.replace(args.progress)
        print(json.dumps(value),flush=True)
    progress(dict(phase='STARTED'))
    result=analyze(args.assets,args.manifest_sha256,progress=progress)
    result.update(started_unix=started,ended_unix=time.time(),wall_seconds=time.time()-started,
        cuda_initialized=torch.cuda.is_initialized(),torch_version=torch.__version__,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            Path(__file__),args.overlay_src/'wcomr/cara_f19_saved_tensor_r2.py',
            args.overlay_src/'wcomr/cara_f19_zero_gpu_r1.py')})
    with args.output.open('x') as stream:
        stream.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    progress(dict(phase='COMPLETE',states=12,lag_pairs=len(result['delta_hold_rows'])))


if __name__=='__main__':
    main()
