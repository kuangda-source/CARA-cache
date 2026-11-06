"""Affected wrapper controls on top of the complete accepted 34-case CPU entry."""
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

import check_cara_sq_q1_execution_cpu_r1 as core


def main():
    index=sys.argv.index('--output')+1;output=Path(sys.argv[index]);core_output=output.with_suffix('.core.json')
    if output.exists() or core_output.exists():raise FileExistsError('Preserve the original control CPU attempt')
    started,cpu=time.monotonic(),time.process_time();children_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    sys.argv[index]=str(core_output)
    try:core.main()
    finally:sys.argv[index]=str(output)
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromName('test_sq_q1_control_r1')
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not tests.wasSuccessful():raise RuntimeError(stream.getvalue())
    from wcomr.gpu_budget_pool_v2 import sha
    import torch
    if torch.cuda.is_initialized():raise RuntimeError('Wrapper CPU tests initialized CUDA')
    result=json.loads(core_output.read_text())
    raw_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children=resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu=children.ru_utime+children.ru_stime-children_before.ru_utime-children_before.ru_stime
    result=dict(status='SQ_Q1_CONTROL_CPU_PASS_BOUND_WRAPPERS_NOT_REAL_CUDA',
        core_result=result,core_result_sha256=sha(core_output),
        wrapper_checks=dict(tests=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),
            skipped=len(tests.skipped),log=stream.getvalue(),actual_GPU_guardian_started=False,
            real_Linux_stub_handoff_and_post_CLI=platform.system()=='Linux' and not tests.skipped),
        wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,child_CPU_seconds=child_cpu,
        total_process_CPU_seconds=time.process_time()-cpu+child_cpu,
        peak_RSS_KiB=raw_rss/1024 if platform.system()=='Darwin' else raw_rss,
        CUDA_initialized=False,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'])


if __name__=='__main__':main()
