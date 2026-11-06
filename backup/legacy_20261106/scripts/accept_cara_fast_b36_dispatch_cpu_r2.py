"""Independently bind stopped dual-host B dispatch/billing controls to current sources."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_b36_r1 import COMMON_SOURCES
from wcomr.cara_fast_b36_execution_r1 import EXECUTION_SOURCES
from wcomr.cara_fast_post_r2 import SCORER_SOURCES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',type=int,default=23)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    core=json.loads((ROOT/'reports/cara_fast_B36_CPU_acceptance_r1_20261029.json').read_text())
    names=set(COMMON_SOURCES)|set(EXECUTION_SOURCES)|set(SCORER_SOURCES)|{
        'src/wcomr/cara_fast_b36_r1.py','src/wcomr/cara_fast_b36_terminal_r1.py',
        'src/wcomr/cara_fast_b36_capture_r1.py','src/wcomr/cara_fast_b36_post_r1.py',
        'src/wcomr/gpu_budget_pool_v2.py','src/wcomr/wc73_execution_r1.py','src/wcomr/wc73_exclusive_r1.py',
        'src/wcomr/policy_price_mode_guard_r1.py','src/wcomr/policy_asset_price_review_r1.py',
        'src/wcomr/history104_storage_r2.py','src/wcomr/runtime_config.py','src/wcomr/h0_mode.py',
        'scripts/cara_fast_worker_r2.py','scripts/cara_fast_host_guardian_r2.py',
        'scripts/four_card_bank24_execution_tools_r1.py','scripts/four_card_policy_assets_port_r1.py',
        'scripts/postprocess_cara_fast_b36_r1.py','scripts/capture_cara_fast_b36_terminal_r1.py',
        'scripts/score_cara_fast_b36_fidelity_r1.py','scripts/check_cara_fast_b36_dispatch_cpu_r2.py',
        'tests/test_cara_fast_b36_execution_r1.py','tests/test_cara_fast_b36_post_r1.py',
        'tests/test_cara_fast_b36_startup_r2.py','tests/test_cara_fast_b36_dispatch_r2.py',
        'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
        'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
        'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
        'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'}
    expected={name:sha(ROOT/name) for name in sorted(names)}
    receipts={}
    for host in ('four_card','two_card'):
        name='reports/cara_fast_B36_dispatch_'+host+'_CPU_capture_r'+str(args.revision)+'_20261029.json'
        captured=json.loads((ROOT/name).read_text())
        state,config,proof=(captured[key] for key in ('container_state','host_config','CPU_proof'))
        assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0
        assert not state['Running'] and not state['OOMKilled']
        assert captured['payload_intact'] and captured['runtime_intact']
        assert config==dict(NanoCpus=10**9,Memory=4*1024**3,MemorySwap=4*1024**3,CpusetCpus='27',
            DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        assert proof['status']=='FAST_B36_DISPATCH_AND_BILLING_CPU_R2_COMPLETE_NOT_GPU' and proof['host']==host
        assert proof['tests_run']==22 and proof['tests_skipped']==0 and proof['actual_CPU_affinity']==[27]
        assert proof['billing_clock_owner']=='HOST_GUARDIAN'
        assert proof['unique_measured_allocation_bill_verified'] and proof['missing_or_unknown_is_never_zero_cost']
        assert proof['pre_worker_failure_scenarios']==['container_failure','busy','spawn_failure','budget','unknown','missing_credential']
        assert proof['normal_supervisor_controls']==6 and proof['post_controls']==8 and proof['dispatch_controls']==5
        assert proof['GPU_once_intent_and_no_relaunch_verified']
        assert proof['CPU_once_dispatch_and_exact_receipt_recovery_verified']
        assert proof['asset_digest_and_changed_stamp_refusal_verified']
        assert proof['isolated_source_preparation_with_actual_pinned_runtime_verified']
        assert proof['real_complete_A32_metadata_verified'] and proof['original_A32_frozen_file_changed'] is False
        assert proof['real_OS_child_PID_start_ticks_inherited_FD_and_process_groups']
        assert proof['external_GPU_and_Docker_observations_simulated'] and proof['temporary_CPU_ledger_mutations_only']
        assert proof['GPU_submissions']==proof['real_mode_changes']==0
        assert proof['central_ledger_written'] is proof['torch_imported'] is proof['model_weights_loaded'] is False
        assert proof['actual_Docker_GPU_command_executed'] is proof['real_GPU_driver_called'] is False
        assert proof['registration_sha256']==captured['registration_sha256']
        assert all(proof['payload_sha256'].get(name)==value for name,value in expected.items())
        assert proof['runtime_source_sha256']==core['receipts'][host]['runtime_source_sha256']
        receipts[host]=dict(path=name,sha256=sha(ROOT/name),launch=captured['launch'],container_state=state,
                            runtime_source_sha256=proof['runtime_source_sha256'])
    assert receipts['four_card']['runtime_source_sha256']==receipts['two_card']['runtime_source_sha256']
    original=json.loads((ROOT/'reports/cara_fast_A6000_terminal_20261029_0050.json').read_text())
    registration=json.loads(original['files']['registration']['raw_utf8'])
    assert all(expected[name]==registration['payload_sha256'][name] for name in (*COMMON_SOURCES,*SCORER_SOURCES))
    result=dict(status='ACCEPTED_B36_DISPATCH_DUAL_HOST_CPU_R2',passed=True,critical_source_sha256=expected,
        receipts=receipts,tests_per_host=22,pre_worker_scenarios=6,normal_supervisor_scenarios=6,
        billing_clock_owner='HOST_GUARDIAN',single_central_measured_wall_bill=True,
        single_dispatch_entry_implemented_and_CPU_accepted=True,CPU_once_score_dispatch_accepted=True,
        actual_B_GPU_card_executed=False,actual_metric_models_executed=False,
        reused_core_CPU_ref='reports/cara_fast_B36_CPU_acceptance_r1_20261029.json',
        shared_original_A_sources_unchanged=14,unchanged_metric_sources=3,
        registered_scoring_positions=32,new_metric_computations=26,reused_accepted_A_metric_pairs=6,
        resource_bound_per_host=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[27],work_seconds=180,exit_seconds=30),
        new_GPU_submissions=0,real_ledger_written=False,GPU_authorized=False,GPU_dispatch_ready=False,
        remaining='Explicit B36 approval and fresh actual same-UUID/assets/resources/central-ledger admission; no replay or automatic restart')
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=result['status'],tests_per_host=22,critical_source_files=len(expected),new_GPU_submissions=0)))


if __name__=='__main__':
    main()
