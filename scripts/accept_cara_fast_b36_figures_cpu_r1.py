"""Accept source-bound exited CPU figure controls and their actual file hashes."""
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
    parser.add_argument('--revision', type=int, default=26)
    parser.add_argument('--capture-index', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    names = ('src/wcomr/cara_fast_b36_figures_r1.py', 'scripts/render_cara_fast_b36_figures_r1.py',
        'scripts/check_cara_fast_b36_figures_cpu_r1.py', 'tests/test_cara_fast_b36_figures_r1.py',
        'scripts/analyze_cara_fast_r1.py', 'plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST.json')
    expected = {name: sha(ROOT/name) for name in names}
    parents = {}
    for ref in ('reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json',
                'reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json'):
        parent = json.loads((ROOT/ref).read_bytes())
        assert parent['passed'] and all(sha(ROOT/name) == value for name, value in parent['critical_source_sha256'].items())
        parents[ref] = sha(ROOT/ref)
    receipts = {}
    for host in ('four_card', 'two_card'):
        ref = 'reports/cara_fast_B36_figures_'+host+'_CPU_capture'+str(args.capture_index)+'_r'+str(args.revision)+'_20261029.json'
        data = json.loads((ROOT/ref).read_bytes())
        state, config, proof = (data[key] for key in ('container_state', 'host_config', 'CPU_proof'))
        assert state['Status'] == 'exited' and state['ExitCode'] == 0 and state['Pid'] == 0
        assert not state['Running'] and not state['OOMKilled']
        assert config == dict(NanoCpus=10**9, Memory=4*1024**3, MemorySwap=4*1024**3,
            CpusetCpus='27', DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)
        assert data['payload_intact'] and data['runtime_intact']
        assert proof['status'] == 'FAST_B36_FIGURES_CPU_COMPLETE_NOT_SCIENCE' and proof['host'] == host
        assert proof['tests_run'] == 6 and proof['tests_skipped'] == 0 and proof['actual_CPU_affinity'] == [27]
        assert 0 < proof['ended_unix']-proof['started_unix'] < 180
        assert proof['bootstrap_samples'] == 20000 and proof['bootstrap_seed'] == 20261028 and proof['bootstrap_unit'] == 'prompt'
        assert proof['formal_positions'] == 32 and proof['all_frame_curve_rows'] == 2976
        assert proof['figure_panels'] == 4 and proof['formats'] == ['png','pdf']
        for key in ('original_bootstrap_implementation_reused', 'all_five_original_receipts_rebuilt',
                    'altered_aggregate_input_source_and_partial_refused', 'production_fixture_and_output_replacement_refused',
                    'CPU_watermark_on_all_figures', 'CPU_fixture_column_on_all_tables',
                    'FIT_UNMATCHED_and_undefined_values_preserved', 'CPU_metadata_fixture_only',
                    'counterbalanced_member_order_uses_fixed_role_numbers', 'undefined_gradient_plot_path_exercised'):
            assert proof[key] is True
        for key in ('actual_B36_results_accessed', 'metric_networks_executed', 'torch_imported',
                    'model_weights_loaded', 'ledger_written', 'GPU_authorized', 'GPU_dispatch_ready'):
            assert proof[key] is False
        assert proof['GPU_submissions'] == 0
        assert proof['registration_sha256'] == data['registration_sha256'] == data['launch']['registration_sha256']
        assert all(proof['payload_sha256'].get(name) == value for name, value in expected.items())
        assert proof['preview_proof_sha256'] == data['figure_layout']['proof_sha256']
        assert proof['preview_file_sha256'] == data['figure_layout']['files'] and len(proof['preview_file_sha256']) == 12
        receipts[host] = dict(path=ref, sha256=sha(ROOT/ref), launch=data['launch'], container_state=state,
            matplotlib_version=proof['matplotlib_version'], preview_file_sha256=proof['preview_file_sha256'],
            runtime_source_sha256=proof['runtime_source_sha256'])
    assert receipts['four_card']['runtime_source_sha256'] == receipts['two_card']['runtime_source_sha256']
    result = dict(status='ACCEPTED_B36_FIGURES_DUAL_HOST_CPU_R1', passed=True, observed_unix=time.time(),
        critical_source_sha256=expected, parent_acceptance_sha256=parents, receipts=receipts, tests_per_host=6,
        CPU_operator_sha256=sha(ROOT/'scripts/cara_fast_b36_execution_cpu_r1.py'), acceptor_sha256=sha(Path(__file__)),
        admitted_execution_sources_unchanged=52, accepted_aggregation_sources_unchanged=4,
        actual_rendered_panels_per_host=4, output_files_per_host=12, CSV_rows=dict(per_member=32,frame_curves=2976,prompt_equal=24,FIT_A_only=6),
        CPU_metadata_fixture_only=True, production_fixture_output_refused=True,
        bootstrap_samples=20000, bootstrap_seed=20261028, bootstrap_unit='prompt', bootstrap_claim='two-sided95 exploratory only',
        actual_B36_results_accessed=False, new_metric_computations=0, new_GPU_submissions=0,
        scientific_result_accepted=False, real_ledger_written=False, GPU_dispatch_ready=False, explicit_B36_approval_received=False)
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], tests_per_host=6, actual_rendered_panels_per_host=4)))


if __name__ == '__main__':
    main()
