"""Accept exact stopped dual-host B36 CPU continuation controls only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_b36_r1 import COMMON_SOURCES
from wcomr.cara_fast_binding_r2 import load_card


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',type=int,default=16)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--four-card-capture')
    parser.add_argument('--two-card-capture')
    args=parser.parse_args()
    assert not args.output.exists()
    names=[*COMMON_SOURCES,'src/wcomr/cara_fast_b36_r1.py','tests/test_cara_fast_b36_r1.py',
        'tests/check_cara_fast_b36_routes_r1.py','scripts/check_cara_fast_b36_cpu_r1.py',
        'tests/check_wc_time_card_r1.py','tests/test_cara_fast_post_r2.py',
        'tests/test_cara_fast_execution_r2.py','tests/test_cara_fast_freeze_r2.py',
        'scripts/score_cara_fast_fidelity_r1.py',
        'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
        'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json',
        'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json',
        'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json']
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    expected={name:sha(ROOT/name) for name in names}
    card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    receipts={}
    for host in ('four_card','two_card'):
        name='reports/cara_fast_B36_'+host+'_CPU_complete_r'+str(args.revision)+'_20261029.json'
        name=getattr(args,host+'_capture') or name
        captured=json.loads((ROOT/name).read_text())
        state,config,proof=(captured[key] for key in ('container_state','host_config','CPU_proof'))
        assert state['Status']=='exited' and state['ExitCode']==0 and not state['Running']
        assert state['Pid']==0 and not state['OOMKilled']
        assert captured['payload_intact'] and captured['runtime_intact']
        assert config==dict(NanoCpus=10**9,Memory=4*1024**3,MemorySwap=4*1024**3,
            CpusetCpus='26',DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        assert proof['host']==host and proof['status']=='FAST_B36_COMPLETE_HANDOFF_CPU_ONLY'
        assert proof['scope_sha256']==card['scope_sha256'] and proof['spec_tests']==3
        assert proof['actual_CPU_affinity']==[26] and proof['actual_compile_threads']==1
        assert proof['compile_pools']==[] and proof['CUDA_initialized'] is False
        assert proof['Cosmos_model_weights_loaded'] is False
        assert proof['actual_A32_outputs_read'] is proof['actual_selection_frozen'] is False
        assert proof['GPU_submissions']==0 and proof['ledger_written'] is proof['authorizes_phase_B'] is False
        assert proof['registration_sha256']==captured['registration_sha256']
        assert all(proof['payload_sha256'].get(name)==value for name,value in expected.items())
        checks=proof['numeric']['checks']
        assert len(checks)==2 and {row['flow'] for row in checks}=={False,True}
        for row in checks:
            assert row['status']=='PASS_COMPLETE_B36_CPU_HANDOFF' and row['complete_B_paths']==36
            assert row['sections']==dict(warm=6,quality=24,repeat=6)
            assert row['formal_logical_sources']==32 and row['reused_A_sources']==8
            assert row['failure_scope']==dict(attempted=9,total=36,failed=1,not_reached=27,no_replay=True)
            assert row['clean_research_counters_zero'] and row['all_policy_actions_equal']
            assert row['original_methods_and_state_restored'] and row['A_slot_refused']
            assert row['CPU_fixture_GPU_refused'] and row['existing_output_refused_before_execution']
            assert row['synthetic_A_only'] and row['actual_A32_outputs_read'] is False
            assert row['Cosmos_weights_loaded'] is row['metric_model_executed'] is False
            assert row['GPU_submissions']==0 and len(row['repeated_B_quality_latent_RGB_RNG_equal'])==4
        for family,candidates in card['finite_grids'].items():
            assert {row['selected'][family] for row in checks}==set(candidates)
        receipts[host]=dict(path=name,sha256=sha(ROOT/name),launch=captured['launch'],
            runtime_source_sha256=proof['runtime_source_sha256'],container_state=state,
            successful_tiny_B_paths=sum(row['complete_B_paths'] for row in checks),
            failure_prefix_attempts=sum(row['failure_scope']['attempted'] for row in checks))
    assert receipts['four_card']['runtime_source_sha256']==receipts['two_card']['runtime_source_sha256']
    result=dict(status='ACCEPTED_DUAL_HOST_COMPLETE_B36_CPU_CONTINUATION_ONLY',passed=True,
        scope_sha256=card['scope_sha256'],critical_source_sha256=expected,receipts=receipts,
        successful_tiny_B_paths_per_host=72,declared_failed_prefix_attempts_per_host=18,
        exact_full_B36_per_flow=True,finite_candidates_covered=card['finite_grids'],
        metadata_unit_controls_per_host=3,logical_sources=32,reused_A_sources=8,
        reused_unchanged_A_sampler_and_metric_evidence='reports/cara_fast_scoped_CPU_acceptance_r2_20261028.json',
        reused_unchanged_A_terminal_chain='reports/cara_fast_post_CPU_acceptance_r2_20261028.json',
        resource_bound_per_host=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[26],work_seconds=600,exit_seconds=60),
        maximum_aggregate_vCPUh=2*660/3600,external_GPU_observations_simulated=True,
        temporary_CPU_ledgers_only=True,actual_A32_outputs_read=False,actual_baseline_selection_frozen=False,
        actual_GPU_B36_run_accepted=False,GPU_authorized=False,GPU_dispatch_ready=False,
        GPU_submissions=0,new_reserved_GPUh=0,real_ledger_written=False,authorizes_phase_B=False)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=result['status'],successful_tiny_paths_per_host=72,
        failed_prefix_attempts_per_host=18,GPU_submissions=0)))


if __name__=='__main__':
    main()
