"""Affected exit cleanup only; reuse the immutable, completed Ada R1 components."""
import argparse
import hashlib
import json
import multiprocessing
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--host',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert a.host=='four_card' and not a.output.exists();signal.alarm(300);start=time.time();cpu=time.process_time()
    reg=json.loads((a.stage/'registration.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    old=a.stage.parent/'cara-fast-CPU-ada-r1-20261028';previous=json.loads((old/'CPU-proof.json').read_text())
    capture=json.loads((a.stage/'reports/cara_fast_four_card_CPU_terminal_r1_20261028.json').read_text())
    assert sha(old/'CPU-proof.json')==capture['CPU_proof_sha256'] and capture['container_state']['ExitCode']==142
    assert previous==capture['CPU_proof'] and previous['status']=='FAST_AFFECTED_PRODUCTION_AND_FIDELITY_CPU_PASS_NOT_GPU'
    # Every numerical/scoring source remains byte-identical. Only the worker's
    # explicit teardown guard differs; no layout, alpha, sampler or score change.
    reused=[n for n in previous['payload_sha256'] if n.startswith(('src/wcomr/cara_fast_',
            'tests/test_cara_fast_', 'tests/check_cara_fast_', 'plans/cara_next_stage_20261028/mainline/'))]
    for n in reused:assert sha(a.stage/n)==previous['payload_sha256'][n]
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests'),str(a.runtime),
                  str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    def forbidden(*args,**kwargs):raise RuntimeError('No CUDA/download in CPU exit check')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('No Triton: '+n)
    triton.runtime.driver.active=Driver()
    import transformers.utils as hu
    from transformers.utils import import_utils as iu
    saved=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
    hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
    # Exercise imported process logging, a spawned child, real scorer startup,
    # and the new exit guard. No new generation or numerical matrix is run.
    from loguru import logger
    sink=logger.add(sys.stdout,enqueue=True);logger.info('CPU cleanup control')
    with multiprocessing.get_context('spawn').Pool(1) as pool:assert pool.map(abs,[-1,2])==[1,2]
    from check_cara_fast_cpu_r1 import closing_guard,scoring_controls
    scorer=scoring_controls(a.stage,a.host)
    negative=subprocess.run([sys.executable,'-c','import signal,time; signal.alarm(1); time.sleep(2)'],timeout=5)
    assert negative.returncode==-signal.SIGALRM
    closing_guard()
    assert not torch.cuda.is_initialized() and not multiprocessing.active_children()
    proof=dict(status='FAST_EXIT_REPAIR_CPU_PASS_NOT_NEW_NUMERICAL_MATRIX',host=a.host,started_unix=start,ended_unix=time.time(),
               CPU_process_seconds=time.process_time()-cpu,registration_sha256=sha(a.stage/'registration.json'),
               scope_sha256=previous['scope_sha256'],reused_component_CPU_proof_sha256=capture['CPU_proof_sha256'],
               original_failed_container_exit_code=142,original_failure_preserved=True,reused_numeric_and_fidelity_source_sha256={n:previous['payload_sha256'][n] for n in reused},
               close_guard_source_sha256=sha(a.stage/'scripts/check_cara_fast_cpu_r1.py'),
               old_alarm_failure_control=True,new_log_queue_and_child_cleanup=True,active_children_after_cleanup=0,
               fidelity=scorer,CUDA_initialized=False,GPU_submissions=0,new_GPUh=0,
               new_numerical_matrix_paths=0,resource_bound=dict(work_seconds=300,teardown_seconds=30,cpus=1,memory_GiB=4),
               payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'])
    with a.output.open('x') as handle:json.dump(proof,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-start)))


if __name__=='__main__':main()
