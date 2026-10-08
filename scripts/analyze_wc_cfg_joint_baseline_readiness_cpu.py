#!/usr/bin/env python3
"""Export every existing paid-probe event and check joint-baseline readiness.

Standard library only. No teacher scores/tensors, routing, fitting, or GPU calls.
"""
import argparse
import ast
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time


REG = Path('manifests/wc_cfg_joint_baseline_readiness_cpu_r1_preregistration_20261009.json')
CAP = Path('reports/wc_cfg_guided_teacher_r1_terminal_20261009_capture.json')
RAW = Path('reports/wc_cfg_guided_teacher_r1_terminal_20261009_runner_native.gz')
FRAGMENTS = Path('research/sources/wc_joint_baseline_cpu_20261009/actual_runtime_source_fragments.json')
SIGNALS = ('paid_input_drift', 'paid_probe_drift', 'dynamic_threshold', 'accumulator_before_action')
MODES = ('CC', 'DC', 'CD', 'DD')
ORIGINS = ('S22', 'S23_after_CC', 'S23_after_DC', 'S23_after_CD', 'S23_after_DD')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    started = time.perf_counter()
    assert not a.output.exists()
    reg = json.loads(REG.read_text())
    for name, expected in reg['input_sha256'].items():
        assert sha(Path(name)) == expected, name
    cap = json.loads(CAP.read_text())
    assert cap['status'] == 'TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS'
    raw = gzip.decompress(RAW.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == cap['files']['runner']['sha256']
    assert len(raw) == cap['files']['runner']['bytes']
    r = json.loads(raw)
    assert r['run_id'] == reg['input_native_run']
    parents = r['teacher']['parents']
    assert len(parents) == 2 and [x['phase'] for x in parents] == ['OFF', 'ON']
    assert all(x['status'] == 'COMPLETE_PARENT' for x in parents)
    origins = parents[1]['origins']
    assert [x['label'] for x in origins] == list(ORIGINS)
    records, cell_rows = [], 0
    for origin in origins:
        assert origin['status'] == 'COMPLETE_LOCAL_ORIGIN' and len(origin['pairs']) == 8
        groups = {mode: [] for mode in MODES}
        for pair in origin['pairs']:
            assert pair['status'] == 'LOCAL_TEACHER_PAIR_COMPLETE' and pair['parent_restored']
            assert pair['mode'] in groups and not pair['formal_RV_label'] and not pair['endpoint_label']
            events = pair['action_report']['events']
            assert len(events) == 2 and [e['cfg_slot'] for e in events] == [0, 1]
            assert [e['actual_action'] for e in events] == list(pair['mode'])
            for slot, event in enumerate(events):
                assert event['paid_probe'] and not event['current_deep_truth_used']
                assert event['solver_step'] == pair['origin_completed_updates'] + 1
                assert event['call'] == 2 * pair['origin_completed_updates'] + slot + 1
                for field in SIGNALS:
                    v = event[field]
                    assert type(v) in (int, float) and math.isfinite(v) and v >= 0
                assert event['age_solver_steps'] == event['solver_step'] - pair['origin_own_history'][slot][-1]
            groups[pair['mode']].append(pair)
            cell_rows += 1
        assert all(len(rows) == 2 for rows in groups.values())
        for repetition in range(2):
            chosen = {mode: groups[mode][repetition] for mode in MODES}
            first = chosen['CC']
            assert all(x['origin_fingerprint'] == first['origin_fingerprint'] for x in chosen.values())
            assert all(x['origin_own_history'] == first['origin_own_history'] for x in chosen.values())
            rows = {mode: [{field: e[field] for field in (*SIGNALS, 'cfg_slot', 'solver_step', 'call',
                    'age_solver_steps', 'native_skip', 'actual_action')} for e in x['action_report']['events']]
                    for mode, x in chosen.items()}
            signal_values = lambda mode: [(e['paid_input_drift'], e['paid_probe_drift']) for e in rows[mode]]
            records.append({'origin': origin['label'], 'repetition': repetition + 1,
                'origin_fingerprint': first['origin_fingerprint'],
                'completed_updates': first['origin_completed_updates'],
                'target_step_one_based': first['origin_completed_updates'] + 1,
                'RA_target_index_zero_based': first['origin_completed_updates'],
                'own_true_full_history': first['origin_own_history'],
                'branch_anchor_indices_zero_based': [h[-1] - 1 for h in first['origin_own_history']],
                'shared_latest_full_anchor': first['origin_own_history'][0][-1] == first['origin_own_history'][1][-1],
                'solver_configuration_sha256': hashlib.sha256(json.dumps(first['origin_solver_configuration'],
                    sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                'cells': rows,
                'paid_drift_values_equal_across_four_actions': all(signal_values(m) == signal_values('CC') for m in MODES)})
    assert len(records) == 10 and cell_rows == 40

    fragments = json.loads(FRAGMENTS.read_text())
    source = {f['name']: f['source'] for item in fragments for f in item['functions']}
    for item in fragments:
        suffix = item['runtime_path'].split('/runtime/', 1)[1]
        assert item['file_sha256'] == r['config']['runtime_source_sha256'][suffix]
    closure = ast.parse(source['velocity_fn']).body[0]
    assert [n.value.func.attr for n in closure.body[:2]] == ['denoise', 'denoise']
    assert [n.value.args[-1].id for n in closure.body[:2]] == ['condition', 'uncondition']
    assert ast.dump(closure.body[2].value) == ast.dump(ast.parse('cond_v + guidance * (cond_v - uncond_v)', mode='eval').body)
    wc = ast.parse(source['worldcache_mini_train_dit_forward'])
    delta_y = [n for n in ast.walk(wc) if isinstance(n, ast.Assign)
               and any(isinstance(x, ast.Name) and x.id == 'delta_y' for x in n.targets)]
    assert len(delta_y) == 2 and any(isinstance(n.value, ast.Name) and n.value.id == 'weighted_rel_drift' for n in delta_y)
    assert r['config']['historical_wc_settings']['worldcache_saliency_enabled'] is True
    di = ast.parse(Path('research/sources/ra_cfgcache_20261009/wan-di_proxy.py.readonly.txt').read_text())
    extract = next(n for n in ast.walk(di) if isinstance(n, ast.FunctionDef) and n.name == '_extract_branch_error')
    assert any(isinstance(n, ast.Return) and ast.dump(n.value) == ast.dump(ast.parse('float(dy)', mode='eval').body)
               for n in ast.walk(extract))
    router = Path('src/wcomr/rv0_actions.py').read_text()
    assert "('ori_x', 'test_x', 'delta_x', 'delta_y', 'dynamic_thresh')" in router
    guidance = r['config']['preregistration'].get('guidance', 7)
    assert guidance == 7
    result = {'status': 'COMPLETE_CPU_PROXY_INPUT_EXPORT_AND_CALL_ORDER_CHECK_NOT_BASELINE_DEPLOYMENT',
        'preregistration_sha256': sha(REG), 'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'script_sha256': sha(Path(__file__)), 'input_sha256': reg['input_sha256'],
        'scope': reg['scope'], 'complete_parents_verified': 2, 'CFG_pair_rows_exported': cell_rows,
        'paid_probe_events_verified': 2 * cell_rows, 'same_origin_records': records,
        'shared_anchor_records': sum(x['shared_latest_full_anchor'] for x in records),
        'mixed_anchor_records': sum(not x['shared_latest_full_anchor'] for x in records),
        'four_action_drift_equality_records': sum(x['paid_drift_values_equal_across_four_actions'] for x in records),
        'Cosmos_guidance': guidance, 'RA_standard_s': 1 + guidance, 'branch_weights': [1 + guidance, -guidance],
        'actual_FP32_closure_not_rewritten': True,
        'actual_WC_proxy': 'SALIENCY_WEIGHTED_PREVIOUS_SHALLOW_STATE_RELATIVE_L1',
        'identical_official_Di_proxy_claim': False,
        'current_velocity_fn_conditional_completes_before_unconditional_probe': True,
        'paired_preprobe_before_first_deep_available': False,
        'Cosmos_rho_and_propagation_calibration_supplied_in_this_registration': False,
        'joint_baseline_GPU_ready': False, 'teacher_scores_or_tensors_read': False,
        'oracle_geometry_used_as_online_signal': False, 'policy_or_threshold_fitting': False,
        'new_quality_or_speed_claim': False, 'GPU_submissions': 0,
        'current_GPU_payload_modified': False, 'CPU_wall_seconds': time.perf_counter() - started}
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('same_origin_records', 'input_sha256')}))


if __name__ == '__main__':
    main()
