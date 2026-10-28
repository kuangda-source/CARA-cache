"""Accept the complete corrected Q1 CPU card without claiming CUDA results."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_q1_control_cpu_r1 import FILES
from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL,SCOPE

ROOT=Path(__file__).resolve().parents[1]
CPU_SCOPE='plans/cara_next_stage_20261028/sq/Q1_ALLOCATION_CPU_R5.json'


def accept(capture,host,revision,attempt='r5'):
    state,launch,result=capture['container_state'],capture['launch'],capture['result']
    name='cara-sq-q1-control-cpu-'+host.replace('_','-')+'-'+attempt+'-20261028'
    wrapper_tests=14 if attempt=='r4' else 15
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Error']
        and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
        and capture['original_CLI_live'] is False,'Original corrected Q1 CPU handles are not cleanly terminal')
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and launch['source_revision']==revision
        and launch['stage'].endswith('/'+name) and launch['container']==name+'-cpu'
        and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
        'Original corrected Q1 CPU source or handle differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
            Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Corrected Q1 CPU runtime/resource boundary differs')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256']
        and result['status']=='SQ_Q1_CONTROL_CPU_PASS_BOUND_WRAPPERS_NOT_REAL_CUDA',
        'Original corrected Q1 CPU result bytes differ')
    core=result['core_result'];controls=result['wrapper_checks']
    require(result_sha(core)==result['core_result_sha256']
        and core['status']=='SQ_Q1_EXECUTION_CPU_PASS_FIXTURES_NOT_REAL_CUDA'
        and core['profile']==host and core['tests']==51
        and core['errors']==core['failures']==core['skipped']==0
        and controls['tests']==wrapper_tests and controls['errors']==controls['failures']==controls['skipped']==0
        and controls['real_Linux_stub_handoff_and_post_CLI'] is True
        and controls['actual_GPU_guardian_started'] is False,
        'Complete Linux affected Q1 core and wrapper controls required')
    require(all(core[k] is True for k in ('real_Linux_subprocess_control','host_allocation_integrated',
        'host_clock_includes_admission_startup_release','supervisor_interval_diagnostic_only',
        'unknown_or_restoration_failure_retains_envelope','allocation_bill_clock_tests_synthetic',
        'allocation_CPU_children_exited'))
        and core['enumerated_allocation_CPU_children']==14
        and len(core['allocation_CPU_child_exit_codes'])==14
        and all(v is not None for v in core['allocation_CPU_child_exit_codes'])
        and core['pre_worker_financial_cases']==['credential','admission','spawn','child_failure','never_created','timeout'],
        'Complete host allocation, failure capture and once-only settlement controls required')
    require(core['subprocess_scenarios']==['complete','numeric_failure','runner_failure','thermal','timeout']
        and core['fixture_head_calls']=={k:dict(started=n,completed=n) for k,n in (
            ('warm',4),('controls',26),('formal',192))},'Frozen Q1 controls or 222-head denominator differs')
    require(all(core[k] is False for k in ('fixture_is_GPU_evidence','actual_B1_replay','actual_model_weights',
        'CUDA_initialized','original_C_CUDA_parity_accepted','GPU_ready','actual_GPU_runner_entry_accepted',
        'actual_financial_settlement_performed')) and result['CUDA_initialized'] is False
        and core['temporary_fixture_ledger_only'] is True and core['synthetic_authority_only'] is True
        and all(v[k]==0 for v in (core,result) for k in ('GPU_submissions','new_GPUh','ledger_writes'))
        and capture['new_GPU_submissions']==capture['ledger_writes']==0,
        'CPU correction controls exceeded their fixture/GPU-free boundary')
    names=[name for name in FILES if attempt!='r4' or not name.endswith('/Q1_ALLOCATION_CPU_R5.json')]
    hashes={name:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest()
            for name in names}
    require(core['critical_source_sha256']=={name:hashes[name] for name in EXECUTION_CRITICAL}
        and core['scope']==json.loads(subprocess.check_output(['git','show',revision+':'+SCOPE],cwd=ROOT)),
        'Original published affected Q1 source or scientific scope differs')
    require(core['actual_platform']['system']=='Linux' and core['actual_platform']['machine']=='x86_64'
        and core['torch_version']=='2.7.1+cu128' and core['raw_ru_maxrss_unit']=='KiB'
        and 1<=core['torch_threads']<=2,'Actual registered Linux CPU runtime required')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<result['wall_seconds']<=wall<=1810 and 0<result['total_process_CPU_seconds']<3600
        and 0<result['peak_RSS_KiB']<8*2**20,'Corrected Q1 CPU resource accounting differs')
    return dict(status='Q1_FULL_HOST_ALLOCATION_AND_WRAPPERS_CPU_ACCEPTED_NOT_CUDA',passed=True,
        host=host,source_revision=revision,critical_source_sha256=hashes,tests=51+wrapper_tests,core_tests=51,wrapper_tests=wrapper_tests,
        enumerated_allocation_CPU_children=14,allocation_CPU_children_exited=True,
        host_allocation_integrated=True,supervisor_time_diagnostic_only=True,
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=result['wall_seconds'],
            worker_CPU_seconds=result['CPU_seconds'],reaped_child_CPU_seconds=result['child_CPU_seconds'],
            parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,allocated_vCPU_seconds_upper_bound=2*wall,
            staging_transport_git_CPU_unmetered=True),GPU_submissions=0,new_GPUh=0,ledger_writes=0,
        GPU_ready=False,original_C_CUDA_parity_accepted=False,actual_financial_settlement_performed=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r4','r5'),default='r5')
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Preserve original corrected Q1 CPU acceptance')
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    capture=json.loads(args.capture.read_text());accepted=accept(capture,args.host,revision,args.attempt)
    cases=dict(live_container=lambda c:c['container_state'].update(Running=True),
        live_CLI=lambda c:c.update(original_CLI_live=True),
        GPU_exposed=lambda c:c['host_config'].update(DeviceRequests=[{}]),
        stale_source=lambda c:c.update(source_hashes_equal=False),
        core_skip=lambda c:c['result']['core_result'].update(skipped=1),
        wrapper_skip=lambda c:c['result']['wrapper_checks'].update(skipped=1),
        inner_only=lambda c:c['result']['core_result'].update(host_allocation_integrated=False),
        lost_failed_cost=lambda c:c['result']['core_result'].update(pre_worker_financial_cases=[]),
        live_CPU_child=lambda c:c['result']['core_result'].update(allocation_CPU_children_exited=False),
        real_CUDA_claim=lambda c:c['result']['core_result'].update(original_C_CUDA_parity_accepted=True))
    rejected={}
    for name,mutate in cases.items():
        forged=copy.deepcopy(capture);mutate(forged)
        forged['result']['core_result_sha256']=result_sha(forged['result']['core_result'])
        forged['result_sha256']=result_sha(forged['result'])
        try:accept(forged,args.host,revision,args.attempt)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged corrected Q1 CPU receipt accepted: '+name)
    accepted.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        CPU_scope_sha256=hashlib.sha256((ROOT/(CPU_SCOPE if args.attempt=='r5' else CPU_SCOPE.replace('R5','R4'))).read_bytes()).hexdigest(),
        rejection_controls=rejected)
    with args.output.open('x') as stream:json.dump(accepted,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:accepted[key] for key in ('status','host','tests','resources')}))


if __name__=='__main__':main()
