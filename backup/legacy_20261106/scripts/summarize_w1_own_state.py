"""Signed registered local diagnostics, after independent full terminal audit."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['project','stage','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.stage/'src'));os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    torch.cuda._lazy_init=lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError('CPU summary denies CUDA'))
    from wcomr.own_state_execution import read,sha
    from wcomr.own_state_summary import summarize
    sys.path.insert(0,str(a.stage/'scripts'))
    from audit_w1_own_state_terminal import audit
    terminal=audit(a.project,a.stage,a.output)
    result=summarize(read(a.output/'diagnostic/receipt.json'),read(a.stage/'own-state-config.json'))
    result.update(terminal=terminal,runner_sha256=sha(a.output/'diagnostic/receipt.json'),
        historical_endpoint_reused_only_after_exact_video_bridge=True,CUDA_initialized=torch.cuda.is_initialized())
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
