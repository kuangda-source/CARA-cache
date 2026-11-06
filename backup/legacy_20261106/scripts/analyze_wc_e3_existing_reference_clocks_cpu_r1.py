"""Read all16 accepted E3 correction traces; do not run or alter a generator."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean


def main():
    root = Path(__file__).resolve().parents[1]
    ref = 'reports/wc_e3_complete64_terminal_r1_20261011_capture.json'
    content = (root / ref).read_bytes()
    capture = json.loads(content)
    assert capture['complete_scope_post_chain_verified'] and capture['whole64_all_scored']
    originals = {}
    for name, bound in capture['originals'].items():
        packed = (root / bound['local_ref']).read_bytes()
        plain = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == bound['local_gzip_sha256']
        assert hashlib.sha256(plain).hexdigest() == bound['sha256']
        originals[name] = json.loads(plain)
    scope = originals['scope']
    rows = {}
    for block in scope['blocks']:
        receipt = originals[block['id'] + '_receipt']
        assert receipt['block'] == block
        for request in receipt['batch']['requests']:
            for row in request['paths']:
                rows[(block['strategy'], request['sample_name'], row['collect'])] = row
    for declared in scope['all64_slots']:
        if declared['disposition'] != 'REUSE_QUALIFIED_DEV_OUTPUT':
            continue
        original = originals['ORIGINAL64_reuse_receipt'] if declared['reuse_binding']['origin'] == 'ORIGINAL_FAILED64_VALID_E0_PATH' else originals['E1_CPU_PREFIX_reuse_receipt']
        batch = original['batches'][declared['strategy']] if 'batches' in original else original['batch']
        matches = [row for request in batch['requests'] if request['sample_name'] == declared['sample_name']
                   for row in request['paths'] if row['collect'] == declared['method']]
        assert len(matches) == 1
        key = (declared['strategy'], declared['sample_name'], declared['method'])
        assert key not in rows
        rows[key] = matches[0]
    assert len(rows) == 64
    method_sources = {}
    for name in ('src/wcomr/partial_mlp_guided_readout.py', 'src/wcomr/cfg_guided_w1_deployment.py'):
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        assert actual == originals['selected_config']['payload_sha256'][name]
        method_sources[name] = actual
    traces = []
    for strategy in scope['strategies']:
        for sample in scope['sample_names']:
            for method in ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'):
                row = rows[(strategy, sample, method)]
                deployment = row['collection_complete']['deployment']
                history = deployment['history']
                a_history = deployment['A_readout']['history']
                assert deployment['working_epoch_strategy'] == strategy
                assert len(history) == len(a_history) == len(row['actions']) == 36
                reads = []
                for step, (h, a, action) in enumerate(zip(history, a_history, row['actions']), 1):
                    assert h['step'] == a['step'] == step
                    assert h['action'] == a['action'] == action and h['A_readout'] == a
                    assert not a['teacher_calls'] and not a['C_or_P_observation_updates_D_anchor']
                    if action != 'CC':
                        continue
                    assert h['true_D_before'] == h['true_D_after'] == a['past_D_steps']
                    kinds = [w['kind'] for w in h['working_sources']]
                    assert kinds == a['working_source_kind'] and kinds[0] == kinds[1]
                    branches = []
                    for branch in (0, 1):
                        d_steps = a['past_D_steps'][branch]
                        assert len(d_steps) == 2
                        source_step = h['working_sources'][branch]['created_step']
                        age = step - source_step
                        assert age == h['working_source_ages'][branch]
                        branches.append({'branch': branch, 'past_true_D_steps': d_steps,
                            'true_D_reference_age': step - d_steps[-1],
                            'working_source_kind': kinds[branch], 'working_source_created_step': source_step,
                            'working_source_age': age, 'reference_age_minus_working_age': source_step - d_steps[-1],
                            'branch_status': a['branch_status'][branch]})
                    assert branches[0]['reference_age_minus_working_age'] == branches[1]['reference_age_minus_working_age']
                    reads.append({'step': step, 'working_kind': kinds[0], 'shared_alpha': a['shared_alpha'],
                                  'extra_heads': a['extra_heads'], 'branches': branches})
                p = [x for x in reads if x['working_kind'] == 'P']
                ages = [x['branches'][0]['working_source_age'] for x in p]
                gaps = [x['branches'][0]['reference_age_minus_working_age'] for x in p]
                traces.append({'strategy': strategy, 'sample_name': sample, 'method': method,
                    'full_updates': 36, 'all_C_pairs': len(reads), 'C_from_P_pairs': len(p),
                    'P_source_age_counts': dict(Counter(ages)), 'D_reference_age_gap_counts': dict(Counter(gaps)),
                    'P_source_C_mean_age': mean(ages) if ages else None,
                    'mean_true_D_reference_age_gap': mean(gaps) if gaps else None,
                    'P_source_C_alpha_counts': dict(Counter(x['shared_alpha'] for x in p)), 'all_C_reads': reads})
    assert len(traces) == 16
    groups = []
    for strategy in scope['strategies']:
        for method in ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'):
            subset = [t for t in traces if t['strategy'] == strategy and t['method'] == method]
            p = [x for t in subset for x in t['all_C_reads'] if x['working_kind'] == 'P']
            ages = [x['branches'][0]['working_source_age'] for x in p]
            gaps = [x['branches'][0]['reference_age_minus_working_age'] for x in p]
            groups.append({'strategy': strategy, 'method': method, 'scenes': 4,
                'C_pairs': sum(t['all_C_pairs'] for t in subset), 'C_from_P_pairs': len(p),
                'P_source_age_counts': dict(Counter(ages)), 'reference_age_gap_counts': dict(Counter(gaps)),
                'mean_P_age': mean(ages) if ages else None, 'mean_D_reference_age_gap': mean(gaps) if gaps else None,
                'max_D_reference_age_gap': max(gaps) if gaps else None,
                'all_P_source_C_kept_true_D_only_history': all(g > 0 for g in gaps)})
    earlier = json.loads((root / 'reports/wc_e3_complete64_accepted_results_r1_20261012.json').read_text())
    for group in groups:
        accepted = next(x for x in earlier['groups'] if all(x[k] == group[k] for k in ('strategy', 'method')))
        assert group['C_from_P_pairs'] == accepted['CC_after_last_PP_before_next_DD']
    divergences = []
    for sample in scope['sample_names']:
        for method in ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'):
            a, b = [rows[(strategy, sample, method)] for strategy in scope['strategies']]
            action_step = next((i for i, (x, y) in enumerate(zip(a['actions'], b['actions']), 1) if x != y), None)
            output_step = next((i for i, (x, y) in enumerate(zip(a['guided_sha256'], b['guided_sha256']), 1) if x != y), None)
            divergences.append({'sample_name': sample, 'method': method,
                'first_action_difference_step': action_step, 'first_guided_record_difference_step': output_step,
                'all_prior_guided_record_hashes_equal': a['guided_sha256'][:output_step-1] == b['guided_sha256'][:output_step-1] if output_step else a['guided_sha256'] == b['guided_sha256'],
                'first_differing_actions_KEEP_then_NONZERO': [x['actions'][action_step-1] for x in (a, b)] if action_step else None,
                'metadata_prefix_equality_not_full_solver_snapshot_equivalence': True})
    p_scope = json.loads((root / 'manifests/wc_p_reference_same_state_complete_scope_r1_20261011.json').read_text())
    assert p_scope['working_epoch_strategy'] == scope['strategies'][0]
    assert p_scope['forced_following_actions'] == ['C'] * 4
    result = {'status': 'E3_EXISTING16_CORRECTION_TRACES_REFERENCE_CLOCKS_CPU_RECONSTRUCTED',
        'capture_ref': ref, 'capture_sha256': hashlib.sha256(content).hexdigest(),
        'method_source_SHA_bound_to_original_GPU': method_sources, 'registered_scope_positions': 64,
        'actual_correction_paths_read': 16, 'actual_correction_update_records_read': 576,
        'groups': groups, 'per_path_all16': traces,
        'all8_cross_rule_first_record_divergences': divergences,
        'planned_P_card_strategy': p_scope['working_epoch_strategy'],
        'planned_P_card_forced_C_not_natural_nonzero_trajectory': True,
        'five_readout_card_can_test_reference_mechanism_not_uniquely_attribute_E3_failure': True,
        'posthoc_metadata_diagnostic_not_same_state_error_measurement': True,
        'numeric_beta_and_per_step_error_not_inferred': True, 'new_GPU_submissions': 0,
        'ledger_written': False, 'CPU_reader_or_LPIPS_rerun': False, 'teacher_or_generator_calls': 0}
    target = root / 'reports/wc_e3_existing_reference_clocks_cpu_r1_20261012.json'
    assert not target.exists()
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'groups': groups}, ensure_ascii=False))


if __name__ == '__main__':
    main()
