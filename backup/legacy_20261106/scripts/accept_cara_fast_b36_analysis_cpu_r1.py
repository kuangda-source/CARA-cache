"""Accept only exited, source-bound dual-host aggregation CPU controls."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', type=int, default=25)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    names = ('src/wcomr/cara_fast_b36_analysis_r1.py', 'scripts/analyze_cara_fast_b36_complete_r1.py',
             'scripts/check_cara_fast_b36_analysis_cpu_r1.py', 'tests/test_cara_fast_b36_analysis_r1.py')
    expected = {name: sha(ROOT/name) for name in names}
    execution_ref = 'reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json'
    execution = json.loads((ROOT/execution_ref).read_bytes())
    assert execution['passed'] and all(sha(ROOT/name) == value for name, value in execution['critical_source_sha256'].items())
    receipts = {}
    for host in ('four_card', 'two_card'):
        name = 'reports/cara_fast_B36_analysis_'+host+'_CPU_capture1_r'+str(args.revision)+'_20261029.json'
        captured = json.loads((ROOT/name).read_bytes())
        state, config, proof = (captured[key] for key in ('container_state', 'host_config', 'CPU_proof'))
        assert state['Status'] == 'exited' and state['ExitCode'] == 0 and state['Pid'] == 0
        assert not state['Running'] and not state['OOMKilled']
        assert config == dict(NanoCpus=10**9, Memory=4*1024**3, MemorySwap=4*1024**3,
                              CpusetCpus='27', DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)
        assert captured['payload_intact'] and captured['runtime_intact']
        assert proof['status'] == 'FAST_B36_ANALYSIS_CPU_COMPLETE_NOT_SCIENCE' and proof['host'] == host
        assert proof['tests_run'] == 6 and proof['tests_skipped'] == 0 and proof['actual_CPU_affinity'] == [27]
        assert 0 < proof['ended_unix']-proof['started_unix'] < 180
        for key in ('prompt_equal_formal_plus_six_clean_repeats_verified',
                    'separate_dual_clocks_and_A_only_FIT_sensitivity_verified',
                    'all32_curves_PSNR_and_undefined_gradient_states_preserved',
                    'WC_RA_UNMATCHED_preserved', 'partial_mixed_unaccepted_live_and_UNKNOWN_refused',
                    'production_fixture_and_output_overwrite_refused', 'CPU_metadata_fixture_only'):
            assert proof[key] is True
        for key in ('immutable_A32_freeze_changed', 'actual_B36_results_accessed', 'metric_model_executed',
                    'torch_imported', 'model_weights_loaded', 'ledger_written', 'GPU_authorized', 'GPU_dispatch_ready'):
            assert proof[key] is False
        assert proof['GPU_submissions'] == proof['new_metric_computations'] == 0
        assert proof['registered_scoring_positions'] == 32 and proof['reused_A_metric_pairs'] == 6
        assert proof['registration_sha256'] == captured['registration_sha256'] == captured['launch']['registration_sha256']
        assert proof['payload_sha256'] == captured['registration']['payload_sha256']
        assert all(proof['payload_sha256'].get(name) == value for name, value in expected.items())
        assert proof['runtime_source_sha256'] == execution['receipts'][host]['runtime_source_sha256']
        receipts[host] = dict(path=name, sha256=sha(ROOT/name), launch=captured['launch'],
            container_state=state, tests_run=6, runtime_source_sha256=proof['runtime_source_sha256'])
    assert receipts['four_card']['runtime_source_sha256'] == receipts['two_card']['runtime_source_sha256']
    frozen_ref = 'plans/cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json'
    assert sha(ROOT/frozen_ref) == '56e1eb84fed0a459ae8fdeb6598680009226dced9529052cabc57cf11cef2be8'
    result = dict(status='ACCEPTED_B36_COMPLETE_ANALYSIS_DUAL_HOST_CPU_R1', passed=True,
        observed_unix=time.time(), critical_source_sha256=expected,
        CPU_operator_sha256=sha(ROOT/'scripts/cara_fast_b36_execution_cpu_r1.py'),
        acceptor_sha256=sha(Path(__file__)), execution_CPU_ref=execution_ref,
        execution_CPU_sha256=sha(ROOT/execution_ref), admitted_execution_sources_unchanged=len(execution['critical_source_sha256']),
        receipts=receipts, tests_per_host=6, CPU_metadata_fixture_only=True,
        frozen_file_ref=frozen_ref, frozen_file_sha256=sha(ROOT/frozen_ref),
        original_A32_freeze_changed=False, formal_logical_positions=32, reused_A_sources=8,
        reused_A_metric_pairs=6, new_metric_computations=0, new_GPU_submissions=0,
        real_ledger_written=False, actual_B36_results_accessed=False,
        scientific_result_accepted=False, GPU_dispatch_ready=False, explicit_B36_approval_received=False,
        failed_CPU_history_refs=['reports/cara_fast_B36_analysis_'+host+'_CPU_capture1_r24_20261029.json'
                                 for host in receipts],
        scope_note='Only aggregation metadata controls; original22 execution controls remain a separate unchanged acceptance')
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], tests_per_host=6,
                          admitted_execution_sources_unchanged=result['admitted_execution_sources_unchanged'])))


if __name__ == '__main__':
    main()
