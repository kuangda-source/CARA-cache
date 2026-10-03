"""Check independent native-window auditing on the immutable historical GPU receipt."""
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


def run(receipt_path):
    source = Path(__file__).parents[1] / 'scripts/audit_wc_timing_factorial_receipts.py'
    spec = importlib.util.spec_from_file_location('timing_auditor', source)
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    raw = gzip.decompress(Path(receipt_path).read_bytes())
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == 'a752a19587552ca4842a3dec0683bbf42891a3a774c4987ca104c58cc0364265'
    r = json.loads(raw); phase = r['measurement']['phases'][3]; context = r['reference_context']
    proof = audit.provenance_audit(phase, context, sparse_allowed=True)
    assert proof['sparse_CFG_calls'] == [23,24,41,42,47,50,51,54,55,59,60]
    assert proof['S_per_CFG'] == [6,5] and proof['sparse_attention_operators'] == 253
    assert len(proof['cache_calls_reading_approximate']) == 26
    assert proof['approximate_source_reads'] == 26 and proof['maximum_same_CFG_approximate_age'] == 8
    checks = ['actual_historical_legacy_SD_native_last_two_source_windows_quota_kernel_count']
    for label in ('reordered_two_sources', 'stale_dense_substitution', 'cross_CFG_source',
                  'sparse_as_true_dense', 'wrong_cadence', 'wrong_kernel_layer',
                  'nonfinite_density', 'wrong_final_window', 'missing_native_reset'):
        q = deepcopy(phase); report = q['refresh_provenance']; rows = report['events']
        if label == 'reordered_two_sources': rows[24]['references_read'].reverse()
        elif label == 'stale_dense_substitution': rows[24]['references_read'][1] = deepcopy(rows[10]['source'])
        elif label == 'cross_CFG_source': rows[24]['references_read'][0] = deepcopy(rows[11]['source'])
        elif label == 'sparse_as_true_dense': rows[22]['inserted_into_true_dense_history'] = True
        elif label == 'wrong_cadence': report['selection_policy']['every'] = 1
        elif label == 'wrong_kernel_layer': rows[22]['operator_metadata'][0]['layer'] = 6
        elif label == 'nonfinite_density': rows[22]['operator_metadata'][0]['selected_fraction'] = float('nan')
        elif label == 'wrong_final_window': report['windows'][0] = deepcopy(report['windows'][1])
        elif label == 'missing_native_reset': rows[69]['native_cycle_reset'] = False
        try: audit.provenance_audit(q, context, sparse_allowed=True)
        except (AssertionError, ValueError): checks.append('reject_' + label)
        else: raise AssertionError('Corrupt native provenance accepted: ' + label)
    with tempfile.TemporaryDirectory() as temporary:
        # Load can fail before policy/mask metadata exists. This is a failure
        # fixture, never a fabricated completed video or source receipt.
        failed = {'run_card': 'WC-TIMING-FACTORIAL-HUMAN-R1-20261004-A',
                  'scope': {'run_id': 'wc-timing-factorial-human-r1'},
                  'planned_total_phases': 6, 'planned_output_files': 6,
                  'status': 'TECH_BLOCKED', 'error': 'CPU failure fixture before core metadata'}
        result = audit.audit(failed, Path(temporary))
        assert result['planned_outputs'] == 6 and not result['quality_acceptance'] and not result['files']
        assert result['status'] == 'INCOMPLETE_TIMING_FACTORIAL_SIX_CARD_NOT_ACCEPTED'
        checks.append('pre_core_failure_retains_six_denominator_without_fake_binding')
        failed['planned_output_files'] = 4
        try: audit.audit(failed, Path(temporary))
        except AssertionError: checks.append('reject_failed_card_reduced_denominator')
        else: raise AssertionError('Reduced failed-card denominator accepted')
    return {'status': 'TIMING_INDEPENDENT_NATIVE_WINDOW_AUDITOR_HISTORICAL_SOURCE_CPU_CONTROLS_PASS_NOT_NEW_VIDEO',
            'CPU_only': True, 'GPU_submitted_by_test': False, 'source_raw_sha256': digest,
            'audit_code_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'test_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'checks': checks, 'legacy_provenance': proof, 'new_placement_full_video_audit_pending': True}
