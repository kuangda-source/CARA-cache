#!/usr/bin/env python3
"""Inventory all old64 positions; do not select reuse, execution, or new scoring."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    capture_ref = 'reports/wc_full64_partial_recovery_cpu_r1_terminal_20261011_capture.json'
    capture = json.loads((root / capture_ref).read_text())
    item = capture['files']['result.json']
    raw = gzip.decompress((root / item['local_ref']).read_bytes())
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    old = json.loads(raw)
    config_ref = 'configs/wc_current_birth_full64_selected_r1_20261010.json'
    config = json.loads((root / config_ref).read_text())
    prereg = config['preregistration']
    expected = [(strategy, request['name'], method)
                for strategy in prereg['strategies']
                for request in prereg['requests']
                for method in prereg['methods']]
    assert len(expected) == len(set(expected)) == 64
    scores = {(row['strategy'], row['sample_name'], row['method']): row
              for row in old['pairs']}
    assert len(scores) == 8
    rows = []
    counts = {}
    for index, (key, original) in enumerate(zip(expected, old['all64_slots'])):
        assert key == (original['strategy'], original['sample_name'], original['method'])
        row = dict(slot=index, strategy=key[0], sample_name=key[1], method=key[2],
                   old_path_status=original['path_status'], E3_reuse_selected=False)
        if original['written_complete']:
            assert original['path_status'] == 'PATH_VALIDATED'
            paired = original['pairing']['compatible']
            assert paired == (key in scores)
            classification = ('VALID_REFERENCE_COMPATIBLE_SCORED_REUSE_CANDIDATE_PENDING_E1'
                              if paired else 'VALID_FILES_MISSING_PREPARE_NOT_REFERENCE_ELIGIBLE')
            row.update(vector_artifact=original['vector_artifact'],
                       video_artifact=original['video_artifact'],
                       prepared_evidence_available=original['pairing']['prepared_evidence_available'],
                       numerical_pairing_compatible=paired,
                       strict_original_pairing_compatible=original['pairing']['strict_original_verdict']['compatible'],
                       old_instrumented_pipeline_seconds=original['recorded_instrumented_pipeline_seconds'])
            if paired:
                row['existing_mean_LPIPS'] = scores[key]['score']['mean_LPIPS']
            else:
                assert key[1] == 'human_199' and not row['prepared_evidence_available']
                row['next_evidence_need'] = 'Preserve missing prepare; separately establish legitimate evidence or preregister matched regeneration. Never synthesize old metadata.'
        elif original['path_status'] == 'PARTIAL_FAILED_NOT_ELIGIBLE':
            classification = 'PARTIAL_FAILED_ORIGINAL_RETAINED_NEW_RESULT_NEEDED'
            row.update(original_error=original['original_error'], original_status=original['original_status'])
        else:
            assert original['path_status'] == 'NOT_WRITTEN'
            classification = 'NOT_WRITTEN_NEW_RESULT_NEEDED'
        row['classification'] = classification
        rows.append(row)
        counts[classification] = counts.get(classification, 0) + 1
    assert list(counts.values()) == [8, 6, 1, 49]
    result = dict(status='E3_COMPLETE64_READONLY_INVENTORY_NOT_EXECUTION_OR_REUSE_SELECTION',
                  planned_scientific_positions=64, all64_slots=rows, counts=counts,
                  original_failed_full64_status_unchanged=True,
                  old_written_complete_files=14, old_reference_eligible_scored_paths=8,
                  nominal_unwritten_or_partial_positions=50,
                  additional_valid_files_with_missing_prepare=6,
                  potential_fresh_paths_if_all_six_must_regenerate=56,
                  full_E1_terminal_numeric_and_memory_proof_pending=True,
                  E3_source_equivalence_and_artifact_rehash_required=True,
                  forecast_not_yet_registered=True, GPU_execution_selected=False,
                  old_authorization_not_reused=True, old_repeats_not_independent_confirmation=True,
                  Native_fidelity_not_physics=True, CUDA_initialized=False,
                  GPU_submissions=0, ledger_written=False,
                  source_sha256={capture_ref: hashlib.sha256((root / capture_ref).read_bytes()).hexdigest(),
                                 item['local_ref']: hashlib.sha256((root / item['local_ref']).read_bytes()).hexdigest(),
                                 config_ref: hashlib.sha256((root / config_ref).read_bytes()).hexdigest(),
                                 'scripts/build_wc_e3_full64_inventory_cpu_r1.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    target = root / 'reports/wc_e3_complete64_readonly_inventory_cpu_r1_20261011.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'planned_scientific_positions', 'counts', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
