"""Request-boundary collection only; within-request execution is immutable.

Python cycles in request owners/compiled closures can retain CUDA tensors after
close(). Collect unreachable objects after the complete guarded request returns,
then return unused allocator blocks. Never clear live algorithm cache tensors.
"""
import gc
import time
import weakref
import json
from pathlib import Path
import torch
from . import simple26d_r1 as legacy
from . import clean_speed20_r1 as clean
from .simple26d_r1 import METHODS,COUNTS,MODE_REF,STRATEGY,plans,matrix,audit_row,sha,write

CONFIG='configs/wc_simple26d_memory_full36_r2_20261015.json'
RUN='wc-simple26d-memory-cal4-full36-r2'
CARD='WC-SIMPLE26D-MEMORY-CAL4-SIXMETHOD-FULL36-R2-20261015-A'
CPU_STATUS='SIMPLE26D_MEMORY_FULL144_CPU_PARITY_PASS_NOT_GPU'
PRODUCTION_CPU_STATUS='SIMPLE26D_MEMORY_FULL36_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'

def collect_boundary():
    before=memory()
    start=time.perf_counter()
    unreachable=gc.collect()
    # This returns free allocator blocks, not algorithm-owned tensor storage.
    if torch.cuda.is_initialized(): torch.cuda.empty_cache()
    return dict(before=before,after=memory(),unreachable_collected=unreachable,
                seconds=time.perf_counter()-start)

def memory():
    if not torch.cuda.is_initialized():return dict(CUDA_initialized=False)
    return dict(CUDA_initialized=True,allocated_bytes=torch.cuda.memory_allocated(),
                reserved_bytes=torch.cuda.memory_reserved(),peak_allocated_bytes=torch.cuda.max_memory_allocated())

def execute(*args,**kwargs):
    before=collect_boundary()
    references=[]
    old=clean.install
    def observed_install(*a,**kw):
        result=old(*a,**kw)
        if result[1] is not None:references.append(weakref.ref(result[1]))
        return result
    try:
        with clean.patched(clean,'install',observed_install):
            result=legacy.execute(*args,**kwargs)
    finally:
        after=collect_boundary()
    alive=sum(ref() is not None for ref in references)
    if alive:raise ValueError('Completed request owner remains reachable after collection')
    result['request_memory_lifecycle']=dict(version='BOUNDARY_GC_ONLY_R2',
        before=before,after=after,observed_owners=len(references),owners_alive_after=alive,
        within_request_algorithm_or_guardrails_changed=False,
        cleanup_excluded_from_core_seconds=True)
    return result

def validate_contract(c):
    old=dict(c,card=legacy.CARD,run_id=legacy.RUN)
    legacy.validate_contract(old)
    if (c['card']!=CARD or c['run_id']!=RUN or c['memory_policy']!='BOUNDARY_GC_ONLY_R2'
        or c['old28_reference_count']!=28 or c['old28_reference']['sha256']!=sha(Path(__file__).resolve().parents[2]/c['old28_reference']['ref'])):
        raise ValueError('Memory-only full36 scope or all28 old references changed')

def validate(project,stage):
    _old,reg,old,inputs,tables,previous=legacy.validate(project,stage)
    c=json.loads((Path(stage)/CONFIG).read_text());validate_contract(c)
    assert c['requests']==_old['requests'] and c['plans']==_old['plans']
    proof=json.loads((Path(stage)/'simple26d-memory-sampling-CPU-result.json').read_text())
    assert proof['status']==CPU_STATUS and proof['actual_CPU_paths']==144
    assert proof['legacy_complete_paths']==48 and proof['repair_complete_paths']==96
    assert proof['GPU_submissions']==0 and not proof['CUDA_initialized']
    assert all(reg['payload_sha256'].get(n)==h for n,h in proof['payload_sha256'].items())
    return c,reg,old,inputs,tables,previous
