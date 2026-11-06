"""Bind stopped dual-host B post controls and reuse the unchanged outer execution acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_b36_r1 import COMMON_SOURCES
from wcomr.cara_fast_b36_execution_r1 import EXECUTION_SOURCES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    names=set(COMMON_SOURCES)|set(EXECUTION_SOURCES)|{
        'src/wcomr/cara_fast_b36_r1.py','src/wcomr/gpu_budget_pool_v2.py',
        'src/wcomr/wc73_execution_r1.py','src/wcomr/wc73_exclusive_r1.py',
        'src/wcomr/policy_price_mode_guard_r1.py','src/wcomr/policy_asset_price_review_r1.py',
        'src/wcomr/history104_storage_r2.py','src/wcomr/runtime_config.py','src/wcomr/h0_mode.py',
        'scripts/cara_fast_worker_r2.py','scripts/cara_fast_host_guardian_r2.py',
        'scripts/four_card_bank24_execution_tools_r1.py','scripts/four_card_policy_assets_port_r1.py',
        'scripts/check_cara_fast_b36_execution_cpu_r1.py','tests/test_cara_fast_b36_execution_r1.py',
        'src/wcomr/cara_fast_b36_terminal_r1.py','src/wcomr/cara_fast_b36_capture_r1.py',
        'src/wcomr/cara_fast_b36_post_r1.py','scripts/capture_cara_fast_b36_terminal_r1.py',
        'scripts/postprocess_cara_fast_b36_r1.py','scripts/score_cara_fast_b36_fidelity_r1.py',
        'scripts/score_cara_fast_fidelity_r1.py','scripts/check_cara_fast_b36_post_cpu_r1.py',
        'tests/test_cara_fast_b36_post_r1.py',
        'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
        'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
        'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json'}
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    expected={name:sha(ROOT/name) for name in sorted(names)}
    receipts={}
    for host in ('four_card','two_card'):
        name='reports/cara_fast_B36_post_'+host+'_CPU_capture_r18_20261029.json'
        captured=json.loads((ROOT/name).read_text())
        state,config,proof=(captured[key] for key in ('container_state','host_config','CPU_proof'))
        assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0
        assert not state['Running'] and not state['OOMKilled']
        assert captured['payload_intact'] and captured['runtime_intact']
        assert config==dict(NanoCpus=10**9,Memory=4*1024**3,MemorySwap=4*1024**3,CpusetCpus='27',
                            DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        assert proof['status']=='FAST_B36_POST_CPU_COMPLETE_NOT_GPU' and proof['host']==host
        assert proof['tests_run']==8 and proof['tests_skipped']==0 and proof['actual_CPU_affinity']==[27]
        assert proof['real_complete_A32_metadata_verified'] and proof['original_A32_frozen_file_changed'] is False
        assert proof['terminal_capture_recovery_failure_settlement_and_score_assembly_verified']
        assert proof['registered_scoring_positions']==32 and proof['new_metric_computations']==26
        assert proof['reused_accepted_A_metric_pairs']==6 and proof['metric_model_executed'] is False
        assert proof['unchanged_original_scorer_entry_tested_with_metadata_child']
        assert proof['external_GPU_observations_simulated'] and proof['temporary_CPU_ledger_mutations_only']
        assert proof['GPU_submissions']==proof['real_mode_changes']==0
        assert proof['central_ledger_written'] is proof['torch_imported'] is proof['model_weights_loaded'] is False
        assert proof['actual_Docker_GPU_command_executed'] is proof['real_GPU_driver_called'] is False
        assert proof['registration_sha256']==captured['registration_sha256']
        assert all(proof['payload_sha256'].get(name)==value for name,value in expected.items())
        receipts[host]=dict(path=name,sha256=sha(ROOT/name),launch=captured['launch'],container_state=state,
                            runtime_source_sha256=proof['runtime_source_sha256'])
    assert receipts['four_card']['runtime_source_sha256']==receipts['two_card']['runtime_source_sha256']
    core=json.loads((ROOT/'reports/cara_fast_B36_CPU_acceptance_r1_20261029.json').read_text())
    assert receipts['two_card']['runtime_source_sha256']==core['receipts']['two_card']['runtime_source_sha256']
    outer=json.loads((ROOT/'reports/cara_fast_B36_outer_CPU_acceptance_r1_20261029.json').read_text())
    assert outer['passed'] and all(expected.get(name)==value for name,value in outer['critical_source_sha256'].items())
    assert receipts['two_card']['runtime_source_sha256']==outer['receipts']['two_card']['runtime_source_sha256']
    result=dict(status='ACCEPTED_B36_DUAL_HOST_EXECUTION_AND_POST_CPU_ONLY',passed=True,
        critical_source_sha256=expected,receipts=receipts,post_tests_per_host=8,reused_outer_tests_per_host=7,supervisor_scenarios_per_host=6,
        resource_bound_per_host=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[27],work_seconds=180,exit_seconds=30),
        real_A32_metadata_handoff_verified=True,original_A32_freeze_modified=False,
        hardware_observations_simulated=True,model_weights_loaded=False,new_GPU_submissions=0,
        real_ledger_written=False,original_16point5_liability_preserved_in_temporary_ledger_controls=True,
        reused_core_CPU_ref='reports/cara_fast_B36_CPU_acceptance_r1_20261029.json',
        GPU_authorized=False,GPU_dispatch_ready=False,B36_terminal_postprocessing_CPU_accepted=True,
        registered_scoring_positions=32,new_metric_computations=26,reused_accepted_A_metric_pairs=6,
        actual_metric_models_executed=False,
        reused_unchanged_outer_ref='reports/cara_fast_B36_outer_CPU_acceptance_r1_20261029.json',
        single_dispatch_entry_implemented_and_accepted=False)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=result['status'],post_tests_per_host=8,new_GPU_submissions=0)))


if __name__=='__main__':
    main()
