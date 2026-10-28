"""Accept the full Q1 controls and real journals only after original CPU exit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_control_journal_cpu_r1 import FILES,CONTROL_SCOPE
from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL,SCOPE

ROOT=Path(__file__).resolve().parents[1]


def source(revision):
    return {n:subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT) for n in FILES}


def accept(capture,host,revision,files):
    state,launch,result=capture['container_state'],capture['launch'],capture['result']
    name='cara-sq-control-journal-cpu-'+host.replace('_','-')+'-r1-20261029'
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Error']
        and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
        and capture['original_CLI_live'] is False,'Original journal CPU handles must be terminal')
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and launch['source_revision']==revision
        and launch['stage'].endswith('/'+name) and launch['container']==name+'-cpu'
        and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
        'Original journal CPU handle, source or runtime differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
            Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Journal CPU runtime/resource boundary differs')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256']
        and result['status']=='SQ_REAL_CONTROL_JOURNAL_FULL_Q1_CPU_PASS_NOT_GPU_AUTHORITY'
        and result['control_scope']==json.loads(files[CONTROL_SCOPE]),'Original journal CPU result or scope differs')
    original=result['prior_control_result'];core=original['core_result'];wrapper=original['wrapper_checks']
    require(result_sha(original)==result['prior_control_result_sha256']
        and original['status']=='SQ_Q1_CONTROL_CPU_PASS_BOUND_WRAPPERS_NOT_REAL_CUDA'
        and result_sha(core)==original['core_result_sha256']
        and core['status']=='SQ_Q1_EXECUTION_CPU_PASS_FIXTURES_NOT_REAL_CUDA'
        and core['profile']==host and core['tests']==51
        and core['errors']==core['failures']==core['skipped']==0
        and wrapper['tests']==15 and wrapper['errors']==wrapper['failures']==wrapper['skipped']==0
        and wrapper['real_Linux_stub_handoff_and_post_CLI'] is True
        and wrapper['actual_GPU_guardian_started'] is False,'Original complete51+15 Linux controls required')
    require(all(core[k] is True for k in ('real_Linux_subprocess_control','host_allocation_integrated',
        'host_clock_includes_admission_startup_release','supervisor_interval_diagnostic_only',
        'unknown_or_restoration_failure_retains_envelope','allocation_bill_clock_tests_synthetic',
        'allocation_CPU_children_exited')) and core['enumerated_allocation_CPU_children']==14
        and len(core['allocation_CPU_child_exit_codes'])==14
        and all(v is not None for v in core['allocation_CPU_child_exit_codes'])
        and core['pre_worker_financial_cases']==['credential','admission','spawn','child_failure','never_created','timeout'],
        'Original allocation clock, failure and terminal cohort differs')
    require(core['subprocess_scenarios']==['complete','numeric_failure','runner_failure','thermal','timeout']
        and core['fixture_head_calls']=={k:dict(started=n,completed=n) for k,n in (
            ('warm',4),('controls',26),('formal',192))},'Frozen Q1 222-head denominator differs')
    require((result['original_core_controls'],result['original_wrapper_controls'],result['real_journal_controls'],
        result['real_actor_journal_controls'],result['total_controls'])==(51,15,12,4,82)
        and result['errors']==result['failures']==result['skipped']==0
        and result['actual_48MiB_production_journals'] is True
        and result['actual_production_actor_persist_calls'] is True
        and result['actual_concurrent_journal_processes']==2
        and result['enumerated_allocation_CPU_children']==16
        and result['enumerated_journal_CPU_children']==2
        and result['all_enumerated_CPU_children_exited'] is True
        and len(result['child_exit_codes'])==18 and all(v is not None for v in result['child_exit_codes']),
        'Complete real journals, production actors and eighteen terminal CPU children required')
    hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}
    critical={n:hashes[n] for n in EXECUTION_CRITICAL}
    require(result['critical_source_sha256']==core['critical_source_sha256']==critical
        and core['scope']==json.loads(files[SCOPE]),'Published journal/numerical source or science scope differs')
    require(all(core[k] is False for k in ('fixture_is_GPU_evidence','actual_B1_replay','actual_model_weights',
        'CUDA_initialized','original_C_CUDA_parity_accepted','GPU_ready','actual_GPU_runner_entry_accepted',
        'actual_financial_settlement_performed'))
        and all(result[k] is False for k in ('actual_B1_replay','actual_Cosmos_weights','CUDA_initialized',
            'original_C_CUDA_parity_accepted','actual_GPU_or_SSD_scope_accepted'))
        and original['CUDA_initialized'] is False and result['Q1_numerical_scope_unchanged'] is True
        and result['GPU_mode_container_and_mount_observations_synthetic'] is True
        and result['temporary_fixture_ledgers_only'] is True
        and core['temporary_fixture_ledger_only'] is True and core['synthetic_authority_only'] is True
        and all(v[k]==0 for v in (core,original,result) for k in ('GPU_submissions','new_GPUh','ledger_writes'))
        and capture['new_GPU_submissions']==capture['ledger_writes']==0,'Journal CPU controls exceeded their evidence boundary')
    require(core['actual_platform']['system']==result['actual_platform']['system']=='Linux'
        and core['actual_platform']['machine']==result['actual_platform']['machine']=='x86_64'
        and core['torch_version']==result['torch_version']=='2.7.1+cu128'
        and core['raw_ru_maxrss_unit']=='KiB' and 1<=core['torch_threads']<=2,
        'Actual registered Linux CPU runtime required')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<result['CPU_wall_seconds']<=wall<=1810
        and 0<result['CPU_seconds']+result['reaped_child_CPU_seconds']<3600
        and 0<result['peak_RSS_KiB']<8*2**20,'Journal CPU resource accounting differs')
    return dict(status='Q1_FULL_REAL_CONTROL_JOURNAL_CPU_ACCEPTED_NOT_CUDA',passed=True,
        host=host,source_revision=revision,critical_source_sha256=hashes,tests=82,
        original_core_controls=51,original_wrapper_controls=15,real_journal_controls=12,real_actor_journal_controls=4,
        actual_48MiB_production_journals=True,actual_production_actor_persist_calls=True,
        enumerated_allocation_CPU_children=16,enumerated_journal_CPU_children=2,all_enumerated_CPU_children_exited=True,
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=result['CPU_wall_seconds'],
            worker_CPU_seconds=result['CPU_seconds'],reaped_child_CPU_seconds=result['reaped_child_CPU_seconds'],
            parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,allocated_vCPU_seconds_upper_bound=2*wall,
            staging_transport_git_CPU_unmetered=True),GPU_submissions=0,new_GPUh=0,ledger_writes=0,
        GPU_ready=False,original_C_CUDA_parity_accepted=False,actual_financial_settlement_performed=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Preserve original real-journal CPU acceptance')
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    files=source(revision);capture=json.loads(args.capture.read_text());accepted=accept(capture,args.host,revision,files)
    cases=dict(live_container=lambda c:c['container_state'].update(Running=True),
        live_CLI=lambda c:c.update(original_CLI_live=True),
        GPU_exposed=lambda c:c['host_config'].update(DeviceRequests=[{}]),
        stale_source=lambda c:c.update(source_hashes_equal=False),
        core_skip=lambda c:c['result']['prior_control_result']['core_result'].update(skipped=1),
        wrapper_skip=lambda c:c['result']['prior_control_result']['wrapper_checks'].update(skipped=1),
        lost_failed_cost=lambda c:c['result']['prior_control_result']['core_result'].update(pre_worker_financial_cases=[]),
        fixture_journal=lambda c:c['result'].update(actual_48MiB_production_journals=False),
        mocked_actor=lambda c:c['result'].update(actual_production_actor_persist_calls=False),
        missing_controls=lambda c:c['result'].update(real_actor_journal_controls=3),
        live_CPU_child=lambda c:c['result'].update(all_enumerated_CPU_children_exited=False),
        CUDA_claim=lambda c:c['result'].update(original_C_CUDA_parity_accepted=True))
    rejected={}
    for name,mutate in cases.items():
        forged=copy.deepcopy(capture);mutate(forged);original=forged['result']['prior_control_result']
        original['core_result_sha256']=result_sha(original['core_result'])
        forged['result']['prior_control_result_sha256']=result_sha(original)
        forged['result_sha256']=result_sha(forged['result'])
        try:accept(forged,args.host,revision,files)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged real-journal CPU receipt accepted: '+name)
    accepted.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        CPU_scope_sha256=hashlib.sha256(files[CONTROL_SCOPE]).hexdigest(),rejection_controls=rejected)
    with args.output.open('x') as f:json.dump(accepted,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:accepted[k] for k in ('status','host','tests','resources')}))


if __name__=='__main__':main()
