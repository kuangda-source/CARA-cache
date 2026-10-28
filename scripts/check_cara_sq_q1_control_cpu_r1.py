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
    reuse={}
    if '--reuse-core' in sys.argv:
        from wcomr.gpu_budget_pool_v2 import sha
        from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL
        path=Path(sys.argv[sys.argv.index('--reuse-core')+1])
        expected=sys.argv[sys.argv.index('--reuse-core-sha256')+1]
        expected_reg=sys.argv[sys.argv.index('--reuse-core-registration-sha256')+1]
        if sha(path)!=expected or sha(path.parent/'registration.json')!=expected_reg:
            raise ValueError('Original core CPU byte identity changed')
        original=json.loads(path.read_text());registration=json.loads((path.parent/'registration.json').read_text())
        if (original['status']!='SQ_Q1_EXECUTION_CPU_PASS_FIXTURES_NOT_REAL_CUDA'
                or original['tests']!=34 or original['errors'] or original['failures'] or original['skipped']
                or set(original['critical_source_sha256'])!=set(EXECUTION_CRITICAL)
                or any(sha(core.ROOT/name)!=digest for name,digest in original['critical_source_sha256'].items())
                or any(sha(core.ROOT/'cache/runtime'/name)!=digest
                       for name,digest in registration['runtime_source_sha256'].items())):
            raise ValueError('Unchanged complete core CPU proof required for reuse')
        if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
            raise ValueError('GPU-hidden wrapper CPU entry required')
        import torch
        def forbidden(*args,**kwargs):raise RuntimeError('CPU wrapper cannot initialize CUDA or download')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        torch.set_num_threads(2);os.nice(10)
        core_output.write_bytes(path.read_bytes())
        reuse=dict(ref=str(path),sha256=expected,registration_sha256=expected_reg,
            source_revision=registration['source_revision'],unchanged_critical_source_verified=True,
            unchanged_runtime_verified=True,new_core_replays=0)
    else:
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
        reused_core_evidence=reuse,
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
