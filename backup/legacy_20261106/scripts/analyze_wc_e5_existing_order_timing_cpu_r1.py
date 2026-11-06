"""Reconstruct E5 order/cost diagnostics from accepted original receipts only."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    capture_ref = 'reports/wc_e5_head_complete24_terminal_r1_20261011_capture.json'
    capture_path = root / capture_ref
    capture = json.loads(capture_path.read_text())
    assert capture['whole24_equivalence_accepted'] is True
    assert capture['source_revision'] == 'eff2b71bbd888f4576a2c1c159c394d72ba62fe9'
    per_arm = []
    all_pairs = []
    originals = {}
    for arm in ('AV_R1', 'HUMAN_R1', 'AV_R2', 'HUMAN_R2'):
        item = capture['originals'][arm+'_receipt']
        path = Path(item['local_path'])
        packed = path.read_bytes()
        plain = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == item['local_gzip_sha256']
        assert len(plain) == item['bytes'] and hashlib.sha256(plain).hexdigest() == item['sha256']
        receipt = json.loads(plain)
        assert receipt['source_revision'] == capture['source_revision']
        assert receipt['arm']['id'] == arm and len(receipt['batch']['requests']) == 1
        rows = receipt['batch']['requests'][0]['paths']
        assert len(rows) == 6 and [x['collect'] for x in rows] == receipt['arm']['methods']
        by_method = {row['collect']:row for row in rows}
        leaf = receipt['batch']['actual_native_leaf_profile_counts']
        pairs = []
        for mode in ('OFF', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE'):
            old, fast = [by_method[prefix+mode] for prefix in ('LEGACY_', 'FAST_')]
            assert old['status'] == fast['status'] == 'COMPLETE_PARENT_PATH'
            assert old['guided_sha256'] == fast['guided_sha256'] and old['final_latent_sha256'] == fast['final_latent_sha256']
            positions = [rows.index(row) for row in (old, fast)]
            assert abs(positions[0]-positions[1]) == 1
            walls = [row['instrumented_parent_pipeline_wall_seconds'] for row in (old, fast)]
            heads = [leaf[row['collect']] for row in (old, fast)]
            assert all(heads[i] == len(row['collection_complete']['actual_original_plus_candidate_heads'])
                       for i,row in enumerate((old, fast)))
            first = 0 if positions[0] < positions[1] else 1
            record = {'arm':arm, 'mode':mode, 'old_then_fast_positions_zero_based':positions,
                'old_then_fast_instrumented_seconds':walls, 'old_then_fast_actual_heads':heads,
                'saved_heads':heads[0]-heads[1], 'fast_minus_old_seconds':walls[1]-walls[0],
                'first_then_second_methods':[rows[min(positions)]['collect'], rows[max(positions)]['collect']],
                'first_minus_second_seconds':walls[first]-walls[1-first],
                'pair_contains_first_path_in_model_process':min(positions)==0,
                'all_guided_and_final_hashes_equal':True, 'clean_speed_claim':False}
            pairs.append(record)
            all_pairs.append(record)
        first_pair = next(x for x in pairs if x['pair_contains_first_path_in_model_process'])
        per_arm.append({'arm':arm, 'actual_method_order':receipt['arm']['methods'],
            'load_seconds':receipt['load_seconds'], 'first_adjacent_same_mode_pair':first_pair})
        originals[arm] = {'original_receipt_sha256':item['sha256'], 'local_gzip_sha256':item['local_gzip_sha256']}
    off = [x for x in all_pairs if x['mode']=='OFF']
    assert len(all_pairs)==12 and len(off)==4 and all(x['saved_heads']==0 for x in off)
    summary = {'independent_model_processes':4, 'full_paths':24, 'all_adjacent_same_mode_pairs':12,
        'first_pair_first_path_slower_cases':sum(x['first_adjacent_same_mode_pair']['first_minus_second_seconds']>0 for x in per_arm),
        'OFF_no_head_savings_pairs':4, 'OFF_earlier_path_slower_cases':sum(x['first_minus_second_seconds']>0 for x in off),
        'AV_W1_fast_minus_old_seconds':[x['fast_minus_old_seconds'] for x in all_pairs if x['mode']=='W1_ONE_PHASE' and x['arm'].startswith('AV_')],
        'Human_W1_fast_minus_old_seconds':[x['fast_minus_old_seconds'] for x in all_pairs if x['mode']=='W1_ONE_PHASE' and x['arm'].startswith('HUMAN_')],
        'startup_or_order_association_is_not_causal_attribution':True,
        'native_head_device_time_not_recorded':True, 'no_warmup_removed_or_timing_adjusted':True,
        'no_posthoc_samples_excluded':True, 'not_independent_confirmation':True,
        'source_specific_configuration_not_direction_rejection':True}
    result = {'status':'E5_EXISTING_WHOLE24_ORDER_TIMING_CPU_DIAGNOSTIC_NOT_NEW_GPU',
        'source_capture_ref':capture_ref, 'source_capture_sha256':hashlib.sha256(capture_path.read_bytes()).hexdigest(),
        'original_receipt_identities':originals, 'per_arm':per_arm, 'all12_pairs':all_pairs,
        'summary':summary, 'new_GPU_submissions':0, 'ledger_written':False,
        'new_quality_metric_generated':False, 'clean_speed_or_root_cause_claim':False}
    output = root / 'reports/wc_e5_existing_order_timing_cpu_r1_20261011.json'
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
