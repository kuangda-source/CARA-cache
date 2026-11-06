#!/usr/bin/env python3
"""Import the original W3 bill without changing its code, files or CPU audit."""
import argparse,json,os,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage','binding'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.stage/'src'))
    from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,sha,atomic_json,process_identity,same_live_process
    b=json.loads(a.binding.read_text());old_stage=a.project/b['legacy_stage']
    path=a.project/'outputs'/b['legacy_run']/'supervisor.json'
    s=json.loads(path.read_text());before=s['budget_before']
    assert (s['source_revision'],s['pid'],s['launch_id'],s['admission']['uuid']) == (
        b['legacy_source'],b['supervisor_pid'],b['launch_id'],b['gpu_uuid'])
    assert before['cap_gpu_hours']==b['cumulative_cap_GPUh'] and before['used_gpu_hours']==b['origin_used_GPUh']
    assert before['gpu_jobs_launched']==b['origin_jobs'] and s['authorized_billed_GPUh_limit']==12
    assert sha(old_stage/'scripts/supervise_wc_w3_label64_full864_r1.py')==b['legacy_supervisor_sha256']
    ident=process_identity(s['pid'])
    if s['status']=='W3_LABEL64_GPU_RUNNING':
        assert ident['state'] not in (None,'Z','X') and 'supervise_wc_w3_label64_full864_r1.py' in ident['command']
    start_ticks=b['supervisor_start_ticks']
    if ident['state'] not in (None,'Z','X'):assert ident['start_ticks']==start_ticks
    legacy=dict(job_id=b['legacy_run'],kind='LEGACY_W3',status='RESERVED_OR_RUNNING',
        billed_limit_GPUh=12,source_revision=b['legacy_source'],launch_id=b['launch_id'],
        gpu_uuid=b['gpu_uuid'],supervisor_pid=s['pid'],supervisor_start_ticks=start_ticks,stage=str(old_stage))
    pool=BudgetPool(a.project);lease=DeviceLease(a.project,b['gpu_uuid']).acquire()
    state=dict(status='LEGACY_W3_BRIDGE_RUNNING_ORIGINAL_UNCHANGED',pid=os.getpid(),binding_sha256=sha(a.binding),
        original_supervisor_pid=s['pid'],legacy_run=b['legacy_run'],old_ledger_written=False,started_unix=time.time())
    dest=a.stage/'legacy-bridge.json'
    try:
        value=pool.initialize(cap=b['cumulative_cap_GPUh'],origin_used=b['origin_used_GPUh'],origin_jobs=b['origin_jobs'],
            authorization=b['authority'],legacy_job=legacy)
        state['pool_after_import']=value;atomic_json(dest,state)
        while True:
            s=json.loads(path.read_text())
            if s['status']=='W3_LABEL64_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT':break
            assert s['pid']==b['supervisor_pid'] and s['source_revision']==b['legacy_source']
            if not same_live_process(dict(pid=b['supervisor_pid'],start_ticks=start_ticks)):
                raise RuntimeError('Original W3 died without a terminal bill; retain its full reservation')
            time.sleep(20)
        assert not same_live_process(dict(pid=b['supervisor_pid'],start_ticks=start_ticks)) or s['ended_unix']<=time.time()
        actual=s['wall_seconds']/3600
        assert actual>=0 and abs(s['budget_after']['used_gpu_hours']-(b['origin_used_GPUh']+actual))<1e-9
        assert s['budget_after']['gpu_jobs_launched']==b['origin_jobs']+1
        billing=dict(status='ORIGINAL_LEGACY_W3_ACTUAL_BILL_IMPORTED',source_revision=b['legacy_source'],
            supervisor_pid=b['supervisor_pid'],launch_id=b['launch_id'],supervisor_sha256=sha(path),
            wall_seconds=s['wall_seconds'],actual_GPUh=actual,original_receipt=str(path))
        bill=a.stage/'legacy-W3-billing.json';atomic_json(bill,billing)
        value=pool.settle(b['legacy_run'],actual,sha(bill));lease.close()
        state.update(status='LEGACY_W3_GPU_SETTLED_WAITING_ORIGINAL_CPU_POST',billing=billing,pool_after_settle=value)
        atomic_json(dest,state)
        post=old_stage/'post-CPU-exit.json'
        while not post.exists():time.sleep(20)
        state['mirror_status']=pool.mirror_after_legacy_post(post_exit=post,expected_legacy_pid=b['supervisor_pid'])
        state.update(status='LEGACY_W3_BRIDGE_TERMINAL',ended_unix=time.time(),old_ledger_written=state['mirror_status'].startswith('OLD_LEDGER_MIRRORED'))
        atomic_json(dest,state)
    except BaseException as e:
        state.update(status='LEGACY_W3_BRIDGE_TECHNICAL_STOP_RESERVATION_PRESERVED',error_type=type(e).__name__,error=str(e))
        atomic_json(dest,state);raise
    finally:lease.close()

if __name__=='__main__':main()
