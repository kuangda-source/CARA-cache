#!/usr/bin/env python3
"""Descriptive complete-card diagnostics; never fit, select or dispatch."""
import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.policy_generator_r1.cost112_terminal import accept


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correlation(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys))/den if den else None


def analyze(capture, accepted):
    v = json.loads(capture.read_text())
    a = json.loads(accepted.read_text())
    replay = accept(v)
    assert a['capture_sha256'] == digest(capture)
    assert replay == {k: val for k, val in a.items() if k not in ('capture_ref', 'capture_sha256')}
    t = a['scientific']['timing']
    monitor = [json.loads(line) for line in v['monitor_raw_utf8'].splitlines()]
    thermal = {r['thermal']['observed_unix']: r['thermal'] for r in monitor if r.get('thermal')}
    thermal = [thermal[k] for k in sorted(thermal)]

    def window(identifier):
        r = v['requests'][identifier]['result']
        samples = [x for x in thermal if r['started_unix'] <= x['observed_unix'] <= r['ended_unix']]
        assert samples, 'Missing temperature observations: '+identifier
        return dict(samples=len(samples), thermal_active_fraction=statistics.mean(
            x['SW_thermal_slowdown'] == 'Active' for x in samples),
            power_cap_active_fraction=statistics.mean(x['SW_power_cap'] == 'Active' for x in samples),
            mean_temperature_C=statistics.mean(x['temperature_C'] for x in samples),
            mean_SM_MHz=statistics.mean(x['SM_MHz'] for x in samples))

    rows = []
    for row in t['validation']:
        r = v['requests'][row['id']]['result']
        anchor = v['requests'][row['anchor_id']]['result']
        expected_saving = row['anchor_seconds']-row['predicted_seconds']
        actual_core_saving = anchor['core_seconds']-r['core_seconds']
        core_saving_shortfall = expected_saving-actual_core_saving
        outside_core_delta = (r['full_request_seconds']-r['core_seconds'])-(anchor['full_request_seconds']-anchor['core_seconds'])
        assert abs(core_saving_shortfall+outside_core_delta-row['underestimate_seconds']) < 1e-9
        same_block = next(q for q in t['validation'] if q['role'] == 'PG_ALL_D'
                          and q['member'] == row['member'] and q['repeat'] == row['repeat'])
        rows.append(dict(**row, anchor_to_target_start_seconds=r['started_unix']-anchor['started_unix'],
            expected_total_saving_seconds=expected_saving, actual_core_saving_seconds=actual_core_saving,
            core_saving_shortfall_seconds=core_saving_shortfall, outside_core_delta_seconds=outside_core_delta,
            video_write_delta_seconds=r['video_write_seconds']-anchor['video_write_seconds'],
            independent_fullD_control_drift_seconds=same_block['underestimate_seconds'],
            target_thermal=window(row['id']), anchor_thermal=window(row['anchor_id'])))
    xs = [r['underestimate_seconds'] for r in rows]
    associations = {}
    for key in ('thermal_active_fraction', 'mean_temperature_C', 'mean_SM_MHz'):
        associations[key+'_target_minus_anchor_Pearson_r'] = correlation(xs, [r['target_thermal'][key]-r['anchor_thermal'][key] for r in rows])
    associations['anchor_age_Pearson_r'] = correlation(xs, [r['anchor_to_target_start_seconds'] for r in rows])
    role_summary = []
    for role, q in a['scientific']['quality'].items():
        time_rows = [r for r in t['per_role'] if r['role'] == role]
        role_summary.append(dict(role=role, paired_LPIPS_mean=statistics.mean(x['LPIPS'] for x in q),
            complete_request_mean_seconds=statistics.mean(x['observed_mean_seconds'] for x in time_rows),
            both_rounds_measured_feasible=all(x['measured_feasible'] for x in time_rows),
            both_rounds_prediction_plus6_feasible=all(x['predicted_feasible'] for x in time_rows)))
    bill = json.loads(v['files']['billing']['raw_utf8'])
    post = json.loads(v['files']['post_exit']['raw_utf8'])
    return dict(status='COST112_COMPLETE_ACCEPTED_TIMING_GATE_DIAGNOSTIC', capture_ref=str(capture),
        capture_sha256=digest(capture), acceptance_ref=str(accepted), acceptance_sha256=digest(accepted),
        full_protocol_accepted=True, timing_model_validated=t['timing_model_validated'],
        thresholds_unchanged=True, validation_refit=False, GPU_submissions=0, selection_performed=False,
        gates=dict(mean_absolute_relative_error=t['mean_absolute_relative_error'],
            mean_error_pass=t['mean_absolute_relative_error'] <= .01,
            maximum_underestimate_seconds=t['maximum_underestimate_seconds'],
            maximum_underestimate_pass=t['maximum_underestimate_seconds'] <= 2,
            underestimate_over2_count=sum(x > 2 for x in xs), no_false_feasible=t['no_false_feasible'],
            predicted_feasible_role_round_count=sum(x['predicted_feasible'] for x in t['per_role']),
            budget_seconds=t['budget_seconds'], margin_seconds=6),
        actual_GPUh=a['actual_GPUh'], GPU_ended_unix=bill['ended_unix'], CPU_ended_unix=post['ended_unix'],
        ledger={k:v['pool'][k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},
        worst=max(rows,key=lambda r:r['underestimate_seconds']), validation=rows,
        thermal=dict(unique_samples=len(thermal), active_samples=sum(x['SW_thermal_slowdown']=='Active' for x in thermal),
            max_temperature_C=max(x['temperature_C'] for x in thermal), exploratory_associations=associations),
        descriptive_CAL_role_summary=role_summary,
        interpretation_limits=[
            'Core saving shortfall assigns the frozen total-cost decrement to core only for an algebraic decomposition; not an identified hardware cause.',
            'Thermal samples cover whole requests, not exact core phases; sparse observations, workload composition, shared anchors and four reused prompts confound correlations.',
            'No false feasibility is limited to registered role-round means and four predicted-feasible role-rounds; it does not clear the failed maximum-error gate.',
            'Endpoint summaries are old CAL descriptive evidence, not policy selection or new-input superiority.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('capture', 'accepted', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    result = analyze(args.capture, args.accepted)
    with args.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','gates','actual_GPUh','thermal')}, ensure_ascii=False))
