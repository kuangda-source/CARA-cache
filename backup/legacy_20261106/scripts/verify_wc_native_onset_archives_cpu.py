#!/usr/bin/env python3
"""Independently check archived R3 bytes and calculate signed endpoint results.

Standard library only. No server calls, video scoring, Torch or GPU submission.
Native tensor hashes and decoding evidence were produced by the separately
archived server audit; this checks their complete inventory and cross-binding.
"""
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
PREFIX = 'wc_w3_native_response_onset_r3_'
TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']


def raw(suffix):
    data = (REPORTS / (PREFIX + suffix)).read_bytes()
    return gzip.decompress(data) if suffix.endswith('.gz') else data


def load(suffix):
    return json.loads(raw(suffix))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def state_digest(components):
    h = hashlib.sha256()
    for key in sorted(components):
        h.update(key.encode())
        h.update(repr(components[key]).encode())
    return h.hexdigest()


def counts(actions):
    return [sum(a == 'D' for a in actions[s::2]) for s in (0, 1)]


def main():
    captured = {}
    for name in ('gpu_terminal_capture_20261007.json', 'cpu_terminal_capture_20261007.json'):
        capture = load(name)
        assert capture['source_revision'] == 'a8dd451e8f2a7b65d98a14fef4f6c75b7b222739'
        assert capture['GPU_submissions'] == 0
        for suffix, binding in capture['archives'].items():
            archive = (REPORTS / (PREFIX + suffix)).read_bytes()
            native = raw(suffix)
            assert digest(archive) == binding['archive_sha256']
            assert digest(native) == binding['original_sha256']
            assert len(native) == binding['original_bytes']
            captured[suffix] = {'native_sha256': digest(native), 'bytes': len(native)}
    gpu = load('gpu_terminal_capture_20261007.json')
    cpu = load('cpu_terminal_capture_20261007.json')
    runner = load('runner_terminal_native_20261007.json.gz')
    sup = load('supervisor_terminal_native_20261007.json.gz')
    audit = load('terminal_audit_native_20261007.json')
    score = load('lpips_score_native_20261007.json')
    budget = load('budget_after_native_20261007.json')
    assert sup['exit_code'] == 0 and not sup['cumulative_budget_exceeded']
    assert sup['release']['pids'] == [] and sup['release']['memory_used_mib'] == 24
    assert budget == sup['budget_after'] == audit['budget'] == gpu['budget_after']
    assert math.isclose(budget['used_gpu_hours'], sup['budget_before']['used_gpu_hours'] + sup['wall_seconds']/3600, abs_tol=1e-12)
    assert budget['gpu_jobs_launched'] == 55 and budget['cap_gpu_hours'] == 24
    assert budget['budget_authorization_history'] == sup['budget_before']['budget_authorization_history']
    assert len(cpu['original_GPU_and_CPU_pids_absent']) == 5
    assert all(s['exit_code'] == 0 for s in cpu['CPU_steps'])
    assert not cpu['CUDA_initialized'] and not score['CUDA_initialized']
    assert audit['global_lock_free'] and audit['original_pids_absent']
    assert len(audit['videos']) == 10 and all(v['full93_decode'] for v in audit['videos'])
    assert score['runner_receipt_sha256'] == digest(raw('runner_terminal_native_20261007.json.gz'))
    assert score['terminal_audit_sha256'] == digest(raw('terminal_audit_native_20261007.json'))
    assert [runner[k] for k in ('planned_parent_phases', 'planned_suffix_controls', 'planned_encoded_outputs')] == [1, 10, 6]
    q = runner['requests'][0]
    scope = runner['scope']['scope']
    mask = scope['scenes'][0]['parent_action_mask']
    fixed = mask.copy(); fixed[60], fixed[62] = fixed[62], fixed[60]
    by = {c['label']: c for c in q['children']}
    assert list(by) == scope['order'] and scope['scope_counts'] == [1, 10, 6, 2]
    assert all(len(q[k]) == (36 if k == 'solver_outputs' else 72) for k in TRACE)
    assert ['C' if n == 0 else 'D' for n in q['deep']] == mask
    inventory = set(q['final_components'])
    required = {'output', 'cpu_rng', 'python_rng', 'numpy_rng', 'cuda_rng', 'explicit_generators', 'net.cnt', 'solver._step_index'}
    assert required <= inventory and any(k.startswith('mode.') for k in inventory) and any(k.startswith('buffer.') for k in inventory)

    def components(c, output=None, fingerprint=None):
        assert set(c) == inventory and c
        assert all(type(v) is str and len(v) == 64 and all(x in '0123456789abcdef' for x in v) for v in c.values())
        if output is not None: assert c['output'] == output
        if fingerprint is not None: assert state_digest(c) == fingerprint

    components(q['final_components'], q['final_latent_sha256'])
    off = by['OFF1']
    assert all(off[k] == q[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)
    assert off['record']['final_state_components'] == q['final_components']
    assert off['final_latent_sha256'] == q['final_latent_sha256'] == q['sample_return_sha256']
    repeats = [('OFF1', 'OFF2')] + [(m+'_first', m+'_second') for m in ('FIXED61', 'LATE69', 'RESP65', 'RESP67')]
    repeat_checks = {}
    for a, b in repeats:
        x, y = by[a], by[b]
        checks = {k: x[k] == y[k] for k in TRACE + ['final_latent_sha256', 'response_boundaries']}
        checks.update(final_state_components=x['record']['final_state_components'] == y['record']['final_state_components'], action_report=x['record']['action_report'] == y['record']['action_report'])
        assert all(checks.values()); repeat_checks[a] = checks
    for label, c in by.items():
        rec = c['record']; ar = rec['action_report']; actions = ar['actual_actions']; events = ar['suffix_events']
        assert rec['parent_restored'] and rec['planned_remaining_updates'] == 14 and rec['completed_updates'] == 22
        assert all(len(c[k]) == (14 if k == 'solver_outputs' else 28) for k in TRACE)
        components(rec['final_state_components'], c['final_latent_sha256'], rec['final_state_sha256'])
        for boundary in c['response_boundaries'].values():
            components(boundary['components']); assert boundary['own_CFG_history']
        assert all(n in (0, 26) for n in c['deep'])
        assert ['C' if n == 0 else 'D' for n in c['deep']] == actions[44:]
        assert counts(actions) == ar['per_CFG_full_counts']
        assert [e['call'] for e in events] == list(range(45, 73))
        assert [e['actual_action'] for e in events] == actions[44:]
        assert events[-3]['native_cycle_reset'] and actions[-2:] == ['D', 'D']
        assert not any(e['current_deep_truth_used'] for e in events)
        if label.startswith('OFF'):
            assert actions == mask; continue
        calls = c['responsive_calls']
        expected_changes = [n+1 for n, (a, b) in enumerate(zip(fixed, actions)) if a != b]
        assert set(expected_changes) <= set(calls)
        if calls: assert expected_changes == ar['response_action_changes']
        for e in events:
            if e['actual_action'] == 'C' or e['call'] in (61, 63):
                assert e['paid_probe'] and 1 <= e['age_solver_steps'] <= 33
            if e['call'] in calls:
                assert e['native_response'] and e['paid_probe'] and not e['actual_native_override']
                assert e['actual_action'] == ('C' if e['native_skip'] else 'D')
            else:
                assert e.get('native_response') is not True and e['actual_action'] == fixed[e['call']-1]
    prefix_checks = {}
    for n, modes in [(65, ['FIXED61','LATE69','RESP65','RESP67']), (67, ['FIXED61','LATE69','RESP67']), (69, ['FIXED61','LATE69'])]:
        a = by[modes[0]+'_first']; prefix = n-45; comparisons = {}
        for mode in modes[1:]:
            b = by[mode+'_first']
            checks = {'complete_state_and_history': a['response_boundaries'][str(n)] == b['response_boundaries'][str(n)], 'inputs_through_first_variable_call': a['inputs'][:prefix+1] == b['inputs'][:prefix+1]}
            checks.update({k: a[k][:prefix//2 if k == 'solver_outputs' else prefix] == b[k][:prefix//2 if k == 'solver_outputs' else prefix] for k in TRACE if k != 'inputs'})
            assert all(checks.values()); comparisons[mode] = checks
        prefix_checks[str(n)] = comparisons
    decoded = {c['label']: c for c in q['decoded_children']}
    assert len(decoded) == 5 and all(c['flags_before'] == c['flags_after'] for c in decoded.values())
    refs = runner['scope']['references']['human_199']
    assert q['artifact']['sha256'] == decoded['OFF1']['artifact']['sha256'] == refs['official_WC']['sha256']
    assert all(decoded[m+'_first']['artifact']['sha256'] == refs[m]['sha256'] for m in ('FIXED61','LATE69'))
    old_path = REPORTS / 'wc_w3_native_tail_response_lpips_score_native_20261007.json'
    old = json.loads(old_path.read_bytes()); assert digest(old_path.read_bytes()) == score['prior_score_sha256']
    old_by = {p['label']: p for p in old['pairs']}
    pair_by = {p['label']: p for p in score['pairs']}
    assert len(pair_by) == 5 and score['reused_existing_loss_count'] == 3
    for p in pair_by.values():
        s = p['score']; assert s['frames'] == len(s['frame_distances']) == len(s['pts']) == 93
        assert s['pts'] == [[1024*n, '1/16384'] for n in range(93)]
        assert math.isclose(math.fsum(s['frame_distances'])/93, s['mean_LPIPS'], abs_tol=1e-14)
        assert s['reference_sha256'] == p['reference']['sha256'] and s['candidate_sha256'] == p['candidate']['sha256']
        if p.get('reused_identical_SHA_protocol_loss'):
            op = old_by[p['reused_original_pair_label']]
            assert s == op['score'] and p['reference']['sha256'] == op['reference']['sha256'] and p['candidate']['sha256'] == op['candidate']['sha256']
    L = {k: p['score']['mean_LPIPS'] for k, p in pair_by.items()}
    signed = []
    def cost(mode):
        cs = [by[mode+'_'+x] for x in ('first','second')]
        walls = [c['record']['control_wall_seconds'] for c in cs]
        return {'whole_CFG_full_counts': cs[0]['record']['action_report']['per_CFG_full_counts'], 'repeats_seconds': walls, 'mean_seconds': math.fsum(walls)/2}
    for n in (65, 67):
        label = 'RESP'+str(n)+'_first'; late = 'LATE69_first'
        result = {'response_start': n, 'LPIPS': L[label], 'improvement_vs_LATE69_percent': 100*(L[late]-L[label])/L[late], 'improvement_vs_FIXED61_percent': 100*(L['FIXED61_first']-L[label])/L['FIXED61_first'], 'worse_vs_original_WC_percent': 100*(L[label]-L['BASE'])/L['BASE'], 'fraction_FIXED_excess_repaired_percent': 100*(L['FIXED61_first']-L[label])/(L['FIXED61_first']-L['BASE'])}
        result['frame_distribution'] = {base: {'better': sum(a<b for a,b in zip(pair_by[label]['score']['frame_distances'], pair_by[base]['score']['frame_distances'])), 'worse': sum(a>b for a,b in zip(pair_by[label]['score']['frame_distances'], pair_by[base]['score']['frame_distances']))} for base in ('BASE','FIXED61_first','LATE69_first')}
        result['response_cost'] = cost('RESP'+str(n)); result['late69_cost'] = cost('LATE69')
        dt = result['response_cost']['mean_seconds']-result['late69_cost']['mean_seconds']
        result['extra_diagnostic_seconds'] = dt
        result['extra_diagnostic_percent'] = 100*dt/result['late69_cost']['mean_seconds']
        result['actual_counts_equal_to_LATE69'] = result['response_cost']['whole_CFG_full_counts'] == result['late69_cost']['whole_CFG_full_counts']
        result['actual_action_changes_from_fixed'] = by[label]['record']['action_report']['response_action_changes']
        original = next(d for d in score['signed_diagnostics'] if d['response_start'] == n)
        assert math.isclose(result['improvement_vs_LATE69_percent']/100, original['relative_fidelity_improvement'], abs_tol=1e-14)
        assert math.isclose(dt, -original['mean_control_wall_LATE69_minus_RESPONSE'], abs_tol=1e-12)
        signed.append(result)
    out = {'status': 'ARCHIVED_NATIVE_BYTES_COMPLETE_RAW_REPEAT_PREFIX_COST_SCORE_CROSS_BINDINGS_AND_SIGNED_RECALCULATION_PASS', 'source_revision': runner['source_revision'], 'scope_counts': [1,10,6,2], 'archived_bytes': captured, 'state_inventory_components': len(inventory), 'five_repeat_pairs_nine_checks': repeat_checks, 'registered_prefix_checks': prefix_checks, 'LPIPS_five_losses': L, 'signed_recalculated': signed, 'gpu_wall_seconds': sup['wall_seconds'], 'gpu_hours': sup['wall_seconds']/3600, 'used_gpu_hours': budget['used_gpu_hours'], 'remaining_gpu_hours': 24-budget['used_gpu_hours'], 'jobs': 55, 'server_actual_CPU_exit0_no_CUDA': True, 'GPU_submissions': 0, 'score_runs': 0, 'independent_CONF': False, 'clean_speed_measurement': False, 'single_action_RV_labels': False, 'physics_or_semantic_acceptance': False}
    path = REPORTS / 'wc_w3_native_response_onset_r3_independent_results_20261008.json'
    if path.exists():
        assert json.loads(path.read_bytes()) == out
    else:
        path.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'status': out['status'], 'signed': signed, 'budget': [out['used_gpu_hours'], out['remaining_gpu_hours']], 'file': str(path)}, indent=2))


if __name__ == '__main__':
    main()
