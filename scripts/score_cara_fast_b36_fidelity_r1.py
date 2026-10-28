"""Run the unchanged scorer on26 fresh pairs; assemble32 with six accepted A rows."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from wcomr.cara_fast_b36_post_r1 import new_pairs_manifest,assemble_scores,SCORER_SOURCES
    from wcomr.cara_fast_capture_r2 import file_sha
    from wcomr.cara_fast_execution_r2 import require,read
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from cara_fast_worker_r2 import stop
    require(not args.output.exists(), 'Existing B score result; recover original CPU handle')
    started=time.monotonic()
    manifest=read(args.manifest)
    require(manifest['CPU_bound']==dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=32)
            and manifest['GPU_released'] is True, 'Original B post-release CPU scope required')
    require(os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void', 'GPU-hidden scorer required')
    require(all(file_sha(ROOT/name)==manifest['scorer_source_sha256'][name] for name in SCORER_SOURCES),
            'Original scorer/assembly source changed')
    inner_path=args.output.parent/'new-pairs-manifest.json'
    inner_output=args.output.parent/'new-scores.json'
    inner=new_pairs_manifest(manifest)
    with inner_path.open('x') as handle:
        json.dump(inner,handle,indent=2,allow_nan=False);handle.write('\n')
        handle.flush();os.fsync(handle.fileno())
    child=None
    try:
        child=subprocess.Popen([sys.executable,'-u',str(ROOT/SCORER_SOURCES[0]),
            '--manifest',str(inner_path),'--output',str(inner_output)],start_new_session=True)
        require(child.wait(timeout=14340-(time.monotonic()-started))==0, 'Original B scorer failed; no retry')
    finally:
        stop(child)
    result=assemble_scores(manifest,file_sha(args.manifest),inner,file_sha(inner_path),
                           read(inner_output),file_sha(inner_output))
    atomic_json(args.output,result)


if __name__=='__main__':
    main()
