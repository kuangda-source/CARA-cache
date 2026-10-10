#!/usr/bin/env python3
"""Bind complete real C/P measurements to a fixed creation-phase proxy prior.

No future P drift is fitted. No policy, model, GPU job or budget is changed.
All six actions, eight origins and 144 timings remain in the source proof.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.action_cost_ranking import MODES, ORIGINS
from wcomr.source_aware_proxy_mapping import map_creation_error
from build_wc_action_cost_ranking_real_r1 import PROOF, DEST, read_native

REG = Path('manifests/wc_real_cost_creation_phase_prior_r1_preregistration_20261010.json')


def proposed_mse(record):
    e, b, q = [record[k] for k in ('base_guided_MSE',
        'guided_error_update_mean_dot', 'guided_update_mean_square')]
    if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (e, b, q))
            or e < 0 or q < 0 or b*b > e*q + 1e-12*max(1., e*q)):
        raise ValueError('Finite actual CFG reduced moments required')
    value = math.fsum((e, 2*b, q))
    if value < -1e-12*max(1., e, q):
        raise ValueError('Negative candidate squared error outside FP64 tolerance')
    return max(0., value)


def main():
    reg = json.loads(REG.read_text())
    for name, digest in reg['source_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise ValueError('Registered phase-prior source changed: ' + name)
    if not PROOF.exists() or not DEST.exists():
        print(json.dumps({'status': 'WAITING_COMPLETE_REAL_COST_NO_PRIOR_OR_INSTALL',
            'GPU_submissions': 0, 'ledger_written': False}))
        return 2
    proof, bound = [json.loads(p.read_text()) for p in (PROOF, DEST)]
    if (proof['GPU_exit_code'] != 0 or proof['CPU_exit_code'] != 0
            or not proof['independent_checks']['success']
            or not proof['independent_checks']['complete_8_parent_8_origin_6_mode_reconstruction']
            or bound['source_proof_sha256'] != hashlib.sha256(PROOF.read_bytes()).hexdigest()
            or bound['registered_cost_rows'] != 48 or bound['timed_values'] != 144):
        raise ValueError('Complete independent real source and cost binding required')
    table, runner, config = [read_native(proof, k) for k in ('calibration_table', 'runner', 'config')]
    if (proof['source_revision'] != reg['expected_cost_source_revision']
            or proof['config_sha256'] != reg['expected_cost_config_sha256']
            or table['context_sha256'] != hashlib.sha256(table['fingerprint_context'].encode()).hexdigest()
            or bound['source_table_sha256'] != proof['files']['calibration_table']['sha256']
            or table['teacher_updates_deployment_anchor'] is not False
            or table['strictly_past_actual_D_only_history'] is not True):
        raise ValueError('Original complete cost context or teacher role differs')
    ra_raw = gzip.decompress(Path(reg['RA_calibration_table_ref']).read_bytes())
    ra = json.loads(ra_raw); base = dict(ra); fingerprint = base.pop('fingerprint')
    if (hashlib.sha256(json.dumps(base, sort_keys=True, allow_nan=False).encode()).hexdigest() != fingerprint
            or fingerprint != reg['RA_calibration_fingerprint']
            or ra['paid_proxy_definition'] != 'WC_PAID_DELTA_Y'
            or ra['guided_weights'] != [8, -7] or ra['toy_only_not_Cosmos_calibration']):
        raise ValueError('Actual RA calibration identity or proxy coordinates differ')
    rho = {(r['anchor'], r['step']): r['rho'] for r in ra['rho_at']}
    histories = {}
    for request in runner['batch']['requests']:
        on = [p for p in request['paths'] if p['collect'] is True]
        if len(on) != 1 or on[0]['status'] != 'COMPLETE_PARENT_PATH' or len(on[0]['own_history']) != 36:
            raise ValueError('One complete actual ON parent required per scene')
        for step in reg['steps']:
            history = on[0]['own_history'][step-1]
            key = (request['sample_name'], step)
            if (key in histories or history['step'] != step
                    or history['anchor_before'] != reg['true_D_anchors'][str(step)]):
                raise ValueError('Repeated, missing or foreign true-D origin')
            histories[key] = history
    if set(histories) != set(ORIGINS):
        raise ValueError('Every registered origin must be retained')
    mapped = []
    for mode in MODES:
        records = table['all_modes_direct_guided_moments'][mode]
        if len(records) != 8:
            raise ValueError('All eight moment records required for every mode')
        seen = set()
        for record in records:
            origin = (record['scene'], int(record['state'].removeprefix('step')))
            if origin not in histories or origin in seen or record['diagnostics']['actual_CFG_coefficients'] != [8, -7]:
                raise ValueError('Unique same-state combined CFG origin required')
            seen.add(origin); history = histories[origin]
            row = map_creation_error(scene=origin[0], step=origin[1], anchor=history['anchor_before'],
                packets=history['paid_probes'], rho=rho[(history['anchor_before'], origin[1])],
                C_guided_MSE=record['base_guided_MSE'], P_guided_MSE=proposed_mse(record), mode=mode)
            mapped.append(row)
    if len(mapped) != 48:
        raise ValueError('Full six-mode denominator required')
    selected = [r for r in mapped if r['mode'] == reg['fixed_P_mode']]
    phase = {}
    for step in reg['steps']:
        rows = [r for r in selected if r['step'] == step]
        values = [r['empirically_mapped_creation_floor_proxy'] for r in rows if r['defined']]
        complete = len(rows) == len(values) == 4
        phase[str(step)] = {'all_four_origins': rows, 'complete_defined_denominator': complete,
            'median_creation_floor_proxy': median(values) if complete else None}
    values = [r['empirically_mapped_creation_floor_proxy'] for r in selected if r['defined']]
    usable = (len(values) == 8 and all(phase[str(t)]['median_creation_floor_proxy'] > 0 for t in reg['steps']))
    result = {'status': 'REAL_COMPLETE_CREATION_PHASE_PRIOR_BOUND_NOT_INSTALLED_OR_FUTURE_DRIFT',
        'registration_ref': str(REG), 'registration_sha256': hashlib.sha256(REG.read_bytes()).hexdigest(),
        'source_proof_sha256': bound['source_proof_sha256'],
        'source_table_sha256': bound['source_table_sha256'],
        'RA_calibration_fingerprint': fingerprint, 'all_six_mode_mapping_rows': mapped,
        'complete_registered_origins': 8, 'complete_registered_mode_rows': 48, 'original_timed_values': 144,
        'fixed_P_mode': reg['fixed_P_mode'], 'creation_phase_boundary': 25,
        'all_eight_origin_global_floor_control': median(values) if len(values) == 8 else None,
        'phase_priors': phase, 'positive_complete_phase_prior_available': usable,
        'borrowed_D_drift_ratio_assumption': 1., 'maximum_consecutive_P': 2,
        'propagation_gain_not_folded_into_creation_floor': True,
        'actual_RF_to_hidden_error_bound': False, 'P_future_drift_empirically_calibrated': False,
        'phase_samples_step12_step30_not_full_time_calibration': True,
        'GPU_submissions': 0, 'ledger_written': False, 'model_or_controller_installed': False,
        'endpoint_video_or_generalization_or_clean_latency_claim': False}
    dest = Path(reg['output'])
    if dest.exists():
        raise ValueError('Preserve original binding; register subsequent revisions separately')
    dest.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'positive_complete_phase_prior_available': usable,
        'creation_floors': {t: p['median_creation_floor_proxy'] for t, p in phase.items()},
        'GPU_submissions': 0}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
