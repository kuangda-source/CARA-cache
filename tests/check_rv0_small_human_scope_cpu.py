"""Refuse science-scope drift and non-cardinality edits to the proven pipeline."""
import argparse
import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys


def run(root):
    sys.path.insert(0, str(root/'src'))
    from wcomr.rv0_small_human_scope import proposal, validate_scope
    config = json.loads((root/'configs/wc_w3_small_human_complement_r1_draft.json').read_text())
    scope = config['scope']
    assert scope == proposal()
    validate_scope(scope)
    refusals = []
    for key, value in [('sample_names', ['human_199', 'human_199']),
                       ('sample_indices', [1]), ('target_calls', [45]),
                       ('selected_CFG_slots', [0]), ('parent_phases', 2),
                       ('complete_suffix_controls', 2), ('new_encoded_outputs', 2),
                       ('original_failed_card_denominator', [1, 6, 4, 1]),
                       ('suffix_policy', 'FIXED_MASK'), ('GPU_execution_selected', True),
                       ('timeout_seconds', 6900), ('cumulative_cap_gpu_hours', 13),
                       ('distinct_GPU_card_authorization_required', False),
                       ('prior_card_failure_reclassified_as_success', True)]:
        damaged = copy.deepcopy(scope); damaged[key] = value
        try:
            validate_scope(damaged)
        except ValueError:
            refusals.append(key)
        else:
            raise AssertionError('Invalid complement scope accepted: '+key)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for name, digest in config['prior_evidence_sha256'].items():
        assert sha(root/name) == digest, name
    prior = json.loads((root/'configs/wc_w3_small_cd_approved_r1_20261005.json').read_text())
    derivation = json.loads((root/'manifests/wc_w3_small_human_core_derivation_20261005.json').read_text())
    base_path = root/derivation['base_path']; derived_path = root/derivation['derived_path']
    assert derivation['base_sha256'] == prior['payload_sha256']['src/wcomr/rv0_small_causal.py'] == sha(base_path)
    assert sha(derived_path) == derivation['derived_sha256']
    changes = [
        ('run_small_causal_batch(', 'run_small_human_complement_batch('),
        ('len(samples) != 2', 'len(samples) != 1'),
        ('len(contexts) != 2', 'len(contexts) != 1'),
        ("config['target_calls'] != [45, 46]", "config['target_calls'] != [46]"),
        ("startswith('CPU_SMALL:')", "startswith('CPU_SMALL_HUMAN:')"),
        ('planned_parent_phases=2, planned_suffix_controls=12, planned_encoded_outputs=8',
         'planned_parent_phases=1, planned_suffix_controls=6, planned_encoded_outputs=4'),
        ("policy='TWO_ONE_ACTION_ADAPTIVE_DIAGNOSTICS_WITH_HISTORICAL_REFERENCE'",
         "policy='ONE_HUMAN_COMPLEMENT_ADAPTIVE_DIAGNOSTIC_WITH_HISTORICAL_REFERENCE'"),
        ("len(state['requests']) != 2", "len(state['requests']) != 1"),
        ("sum(len(r['children']) for r in state['requests']) != 12",
         "sum(len(r['children']) for r in state['requests']) != 6"),
        ("sum(1+len(r['decoded_children']) for r in state['requests']) != 8",
         "sum(1+len(r['decoded_children']) for r in state['requests']) != 4"),
        ('Small two-parent/twelve-suffix/eight-output coverage differs',
         'Human complement one-parent/six-suffix/four-output coverage differs'),
        ('SMALL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT',
         'HUMAN_COMPLEMENT_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT')]
    assert derivation['author_time_text_changes'] == [{'old': a, 'new': b} for a, b in changes]
    body = base_path.read_text().split('def run_small_causal_batch(', 1)[1]
    body = 'def run_small_causal_batch('+body
    for before, after in changes:
        assert body.count(before) == 1
        body = body.replace(before, after)
    expected = ast.dump(ast.parse(body).body[0], include_attributes=False)
    derived = ast.parse(derived_path.read_text())
    functions = [n for n in derived.body if isinstance(n, ast.FunctionDef)]
    assert len(functions) == 1 and ast.dump(functions[0], include_attributes=False) == expected
    imports = [n for n in derived.body if isinstance(n, ast.ImportFrom) and n.module == 'rv0_small_causal']
    assert len(imports) == 1 and [a.name for a in imports[0].names] == ['verify_small_children']
    runner = json.loads(gzip.decompress((root/'reports/wc_w3_small_cd_runner_20261005.json.gz').read_bytes()))
    first = runner['requests'][0]
    cost = config['cost']; budget = json.loads((root/'reports/budget.json').read_text())
    parent = first['inclusive_parent_wall_seconds']; load = runner['load_seconds']
    assert cost['nominal_complete_seconds'] == load+parent+60+30
    assert cost['stress_proxy_seconds'] == load+parent*1.3+60+30
    assert cost['stress_proxy_seconds'] < scope['timeout_seconds']
    assert cost['required_seconds_for_arithmetic_admission'] == scope['timeout_seconds']+15
    assert (budget['cap_gpu_hours']-budget['used_gpu_hours'])*3600 == cost['remaining_seconds_at_preparation']
    assert not config['production_entry_ready'] and not config['GPU_execution_selected'] and config['gpu_uuid'] is None
    return {'status': 'HUMAN_COMPLEMENT_SCOPE_COST_AST_CPU_PASS_NOT_PRODUCTION_OR_GPU',
            'refusal_count': len(refusals), 'refusals': refusals,
            'pipeline_AST_diff_only_declared_cardinality_and_identity': True,
            'original_GPU_core_source_unchanged': True, 'fake_second_scene': False,
            'original_denominator_retained': [2, 12, 8, 2], 'new_scope': [1, 6, 4, 1],
            'GPU_submissions': 0, 'new_GPU_authorization': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().root)))
