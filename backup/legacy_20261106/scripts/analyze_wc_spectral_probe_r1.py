#!/usr/bin/env python3
"""CPU-only F16 module screen: prompt-held-out C/A prediction and regret.

Old teacher tensors are checked against frozen same-state hashes. No fitting
uses new-input confirmation, video endpoints, current teacher energy, or held
prompt normalization. This is an offline C/A screen, not a deployed controller.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.source_phase_table_fit_r1 import fit, predict, validate_complete
from wcomr.spectral_probe_r1 import VERSION, FIT_ADDITIONS, ProbeIdentity

RIDGE_MEAN_LOSS = 1.0
RATIO_CLIP = 100.0
RAW_ALLOW = {'delta_x_c', 'delta_y_c', 'delta_x_u', 'delta_y_u',
             'local_proxy', 'gain', 'birth_floor'}
METHODS = ('SOURCE_PHASE_LOPO', 'RAW_CLOCK', 'RAW_SUB', 'HAAR', 'FFT')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def key(point):
    return point['selection']['scene'], point['selection']['chosen']['step']


def _raw_features(point, row):
    f = row['feature_row']
    if f['version'] != VERSION or f.get('teacher_features') is not False:
        raise ValueError('Bound causal F implementation required')
    raw = dict(f['raw_full_paid_proxies'])
    if not raw or set(raw) - RAW_ALLOW:
        raise ValueError('Unknown or potentially noncausal raw predictor')
    # Exact-state old values are themselves pre-action; labels stay separate.
    paid = point['actual_C_paid_proxy']
    required = {'local_proxy': paid['local_proxy'], 'gain': paid['gain'],
                'birth_floor': point['parent_pre_action'][3]}
    for name, value in required.items():
        if name in raw and not math.isclose(raw[name], value, rel_tol=1e-6, abs_tol=1e-9):
            raise ValueError('New paid proxy is not the old bound state')
        raw[name] = value
    metadata = f['metadata']
    allowed_meta = {'source_is_P', 'step', 'source_age', 'true_D_age',
                    'tau', 'source_tau_span', 'D_tau_span'}
    if set(metadata) != allowed_meta:
        raise ValueError('Exact causal source/noise-time clock metadata required')
    result = {'raw:' + n: float(v) for n, v in raw.items()}
    result.update({'clock:' + n: float(v) for n, v in metadata.items()})
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError('Nonfinite causal input')
    return result


def join_and_verify(capture, labels, project):
    import torch
    from wcomr.mid_coverage import tree_digest
    if torch.cuda.is_initialized():
        raise ValueError('Only CPU analysis allowed')
    points = copy.deepcopy(labels['final']['points'])
    validate_complete(points)
    if len(capture['points']) != 16:
        raise ValueError('Full16 F observations required; no partial analysis')
    observed = {(p['scene'], p['step']): p for p in capture['points']}
    if len(observed) != 16 or set(observed) != {key(p) for p in points}:
        raise ValueError('F observations changed fixed16 scene/state scope')
    records = []
    for p in points:
        r = observed[key(p)]
        if r.get('parent_control_pass') is not True or r['input_sha256'] != p['input_sha256']:
            raise ValueError('Feature parent or same-state input parity missing')
        old, new = p['raw_artifact'], r['raw_label_artifact']
        if Path(old['path']).resolve() != Path(new['path']).resolve() or old['sha256'] != new['sha256']:
            raise ValueError('Old actual teacher binding changed')
        path = Path(new['path']).resolve()
        if not path.is_relative_to((Path(project) / 'outputs').resolve()) or sha(path) != old['sha256']:
            raise ValueError('Old tensor path/hash mismatch')
        raw = torch.load(path, weights_only=True, map_location='cpu')
        if tree_digest(raw) != old['tensor_sha256']:
            raise ValueError('Old semantic tensor digest mismatch')
        if set(raw) != {'DENSE_SAME_STATE', 'C', 'D_REFERENCE_A', 'FUSION_A', 'NEW_P', 'actual_latent', 'timestep'}:
            raise ValueError('Old teacher file schema mismatch')
        teacher = raw['DENSE_SAME_STATE']; actual = {}
        for action, label in (('C', 'C'), ('A', 'FUSION_A')):
            values = raw[label]
            if not all(t.shape == teacher[b].shape and torch.isfinite(t).all() for b, t in enumerate(values)):
                raise ValueError('Teacher/candidate geometry or finiteness changed')
            ec, eu = (values[b].double() - teacher[b].double() for b in (0, 1))
            loss = (8 * ec - 7 * eu).square().mean().item()
            if not math.isclose(loss, p['losses'][label]['absolute_guided_MSE'], rel_tol=1e-9, abs_tol=1e-11):
                raise ValueError('Independent absolute guided target reconstruction differs')
            actual[action] = loss
        ident = r['feature_row']['identity']; s = p['selection']; chosen = s['chosen']
        ProbeIdentity(**ident).validate()
        if not math.isclose(ident['current_tau'], p['sigma'], rel_tol=1e-7, abs_tol=1e-9):
            raise ValueError('Actual current sigma changed')
        meta = r['feature_row']['metadata']
        expected_meta = {'source_is_P': int(ident['source_kind'] == 'P'), 'step': ident['step'],
            'source_age': ident['step'] - ident['source_birth'], 'true_D_age': ident['step'] - ident['true_D_birth'],
            'tau': ident['current_tau'], 'source_tau_span': ident['current_tau'] - ident['source_tau'],
            'D_tau_span': ident['current_tau'] - ident['true_D_tau']}
        if meta != expected_meta:
            raise ValueError('Feature clocks not derived from bound source identity')
        if (ident['request_id'] != s['scene'] or ident['step'] != chosen['step']
                or ident['source_kind'] != s['source'] or ident['source_birth'] != chosen['source_birth']
                or ident['true_D_birth'] != chosen['true_D_anchor']):
            raise ValueError('Causal feature identity/source does not match fixed old state')
        for group in ('F_RAW_SUB', 'F_HAAR', 'F_FFT'):
            for name in FIT_ADDITIONS[group]:
                if not math.isfinite(r['feature_row']['features'][name]):
                    raise ValueError('Missing or nonfinite frozen F feature')
        for mode in ('RAW', 'HAAR', 'FFT'):
            t = r['feature_timing'][mode]
            if (t['warmups'] != 10 or t['repeats'] != 30 or len(t['seconds']) != 30
                    or any(not math.isfinite(v) or v <= 0 for v in t['seconds'])
                    or not math.isfinite(t['median_seconds']) or t['median_seconds'] <= 0):
                raise ValueError('Complete actual whole-feature timing required')
        records.append({'point': p, 'observation': r, 'actual': actual, 'raw': _raw_features(p, r)})
        del raw, teacher, ec, eu
    return records


def _standardize(train, test):
    import numpy as np
    center = train.mean(axis=0); scale = train.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.)
    return (train - center) / scale, (test - center) / scale, center, scale


def _raw_basis(train, test):
    """Two train-input-only PCA axes; labels do not select axes or dimension."""
    import numpy as np
    a, b, mean, scale = _standardize(train, test)
    _, singular, vt = np.linalg.svd(a, full_matrices=False)
    basis = vt[:2].copy()
    for row in basis:
        if row[np.argmax(np.abs(row))] < 0:
            row *= -1
    pa, pb = a @ basis.T, b @ basis.T
    pscale = np.where(pa.std(axis=0) > 1e-12, pa.std(axis=0), 1.)
    return pa / pscale, pb / pscale, {'mean': mean.tolist(), 'scale': scale.tolist(),
        'PCA_axes': basis.tolist(), 'PCA_coordinate_scale': pscale.tolist(),
        'singular_values': singular.tolist(), 'labels_used_for_preprocessing': False}


def _residual_predict(xtrain, xtest, qtrain, prior_train, prior_test):
    import numpy as np
    # Source-phase moment prior supplies the intercept; fit no extra intercept.
    target = np.log(np.maximum(qtrain, 1e-12) / np.maximum(prior_train, 1e-12))
    coef = np.linalg.solve(xtrain.T @ xtrain + len(xtrain) * RIDGE_MEAN_LOSS * np.eye(xtrain.shape[1]), xtrain.T @ target)
    residual = xtest @ coef
    clipped = np.clip(residual, -math.log(RATIO_CLIP), math.log(RATIO_CLIP))
    return prior_test * np.exp(clipped), {'coefficients': coef.tolist(),
        'supervised_coefficients_per_output': xtrain.shape[1],
        'clipped_prediction_count': int(np.sum(residual != clipped))}


def analyze(records, parameters):
    import numpy as np
    scenes = validate_complete([r['point'] for r in records])
    names = sorted(records[0]['raw'])
    if any(sorted(r['raw']) != names for r in records):
        raise ValueError('Raw inputs must be identical in definition for every point')
    lam = parameters['lambda_seconds_per_weighted_absolute_MSE']
    curve = parameters['curve_lambdas']
    if lam not in curve or any(not math.isfinite(v) or v < 0 for v in curve):
        raise ValueError('Frozen H1 complete shared lambda curve required')
    folds = []
    for scene in scenes:
        train = [r for r in records if key(r['point'])[0] != scene]
        test = [r for r in records if key(r['point'])[0] == scene]
        model = fit([r['point'] for r in train], 'SOURCE_PHASE')
        def prior(rows):
            values = [predict(model, r['point']) for r in rows]
            if any(v is None for v in values):
                raise ValueError('Missing source/phase prior; no held-label fallback')
            return np.asarray([[v['C'], v['FUSION_A']] for v in values])
        ptr, pte = prior(train), prior(test)
        atr = np.asarray([[r['actual']['C'], r['actual']['A']] for r in train])
        rawtr = np.asarray([[r['raw'][n] for n in names] for r in train])
        rawte = np.asarray([[r['raw'][n] for n in names] for r in test])
        xtr, xte, pre = _raw_basis(rawtr, rawte)
        candidates = {'SOURCE_PHASE_LOPO': (pte, {}),
                      'RAW_CLOCK': _residual_predict(xtr, xte, atr, ptr, pte)}
        prep = {'raw_clock': pre}
        for method, family in (('RAW_SUB', 'F_RAW_SUB'), ('HAAR', 'F_HAAR'), ('FFT', 'F_FFT')):
            cols = FIT_ADDITIONS[family]
            tr = np.asarray([[r['observation']['feature_row']['features'][n] for n in cols] for r in train])
            te = np.asarray([[r['observation']['feature_row']['features'][n] for n in cols] for r in test])
            tr, te, center, scale = _standardize(tr, te)
            candidates[method] = _residual_predict(np.concatenate((xtr, tr), axis=1),
                                                  np.concatenate((xte, te), axis=1), atr, ptr, pte)
            prep[method] = {'columns': cols, 'train_mean': center.tolist(), 'train_scale': scale.tolist()}
        held = []
        for j, r in enumerate(test):
            p = r['point']; prices = {'C': parameters['cost_seconds']['C'],
                'A': parameters['source_A_cost_seconds'][p['selection']['source']]}
            gain2 = p['actual_C_paid_proxy']['gain'] ** 2
            scores = []
            for method in METHODS:
                prediction = {a: float(candidates[method][0][j, k]) for k, a in enumerate(('C', 'A'))}
                # Measurement includes gather/difference/transform. Already-paid
                # raw-clock baseline increment is unavailable, conservatively0;
                # do not call this a full controller/E2E latency measurement.
                mode = {'RAW_SUB': 'RAW', 'HAAR': 'HAAR', 'FFT': 'FFT'}.get(method)
                overhead = r['observation']['feature_timing'][mode]['median_seconds'] if mode else 0.
                decisions = []
                for l in curve:
                    truth = {a: prices[a] + l * gain2 * r['actual'][a] for a in prices}
                    selected = min(prices, key=lambda a: (prices[a] + l * gain2 * prediction[a], a))
                    oracle = min(prices, key=lambda a: (truth[a], a))
                    regret = max(0., truth[selected] - truth[oracle])
                    decisions.append({'lambda': l, 'primary_lambda': l == lam, 'chosen': selected,
                        'local_CA_oracle': oracle, 'regret_seconds_plus_weighted_MSE': regret,
                        'observed_feature_seconds': overhead,
                        'regret_plus_observed_feature_seconds': regret + overhead,
                        'chosen_true_objective_plus_observed_feature': truth[selected] + overhead,
                        'selected_C_true_objective': truth['C'], 'selected_A_true_objective': truth['A'],
                        'locally_harmful_choice': regret > 1e-12})
                scores.append({'method': method, 'prediction': prediction,
                    'squared_prediction_error': {a: (prediction[a] - r['actual'][a]) ** 2 for a in prices},
                    'decisions': decisions})
            held.append({'scene': scene, 'step': key(p)[1], 'source': p['selection']['source'],
                'phase': p['selection']['phase'], 'parent_continues': p['parent_continues'],
                'actual_absolute_guided_MSE': r['actual'], 'actual_CA_improvement': r['actual']['C'] - r['actual']['A'],
                'source_prices': prices, 'gain_squared': gain2, 'scores': scores})
        folds.append({'held_prompt': scene, 'training_prompts': sorted({key(r['point'])[0] for r in train}),
            'training_states': len(train), 'held_states': len(test), 'train_only_source_phase_prior': model,
            'train_only_preprocessing': prep,
            'regression': {m: candidates[m][1] for m in METHODS}, 'held_rows': held})
    summaries = []
    for subset in ('ALL16', 'NATURAL_C_ONLY'):
        for method in METHODS:
            for l in curve:
                groups = []; harmful = count = 0
                for fold in folds:
                    values = []
                    for row in fold['held_rows']:
                        if subset == 'NATURAL_C_ONLY' and row['parent_continues'] != 'CC':
                            continue
                        score = next(s for s in row['scores'] if s['method'] == method)
                        d = next(d for d in score['decisions'] if d['lambda'] == l)
                        values.append(d); harmful += int(d['locally_harmful_choice']); count += 1
                    if values:
                        groups.append({'prompt': fold['held_prompt'], 'states': len(values),
                            'mean_regret': sum(v['regret_seconds_plus_weighted_MSE'] for v in values) / len(values),
                            'mean_regret_plus_observed_feature': sum(v['regret_plus_observed_feature_seconds'] for v in values) / len(values)})
                summaries.append({'subset': subset, 'method': method, 'lambda': l,
                    'primary_lambda': l == lam, 'states': count, 'prompt_groups': groups,
                    'locally_harmful_states': harmful,
                    'prompt_equal_mean_regret': sum(g['mean_regret'] for g in groups) / len(groups),
                    'prompt_equal_mean_regret_plus_observed_feature': sum(g['mean_regret_plus_observed_feature'] for g in groups) / len(groups)})
    return {'status': 'F16_CPU_RAW_VERIFIED_PROMPT_LOPO_CA_SCREEN_NOT_DEPLOYMENT',
        'raw_columns': names, 'folds': folds, 'summaries': summaries,
        'fixed_ridge_mean_loss': RIDGE_MEAN_LOSS, 'fixed_log_residual_ratio_clip': RATIO_CLIP,
        'primary_lambda': lam, 'shared_frozen_curve_lambdas': curve,
        'source_price_provenance': parameters['prices_scope'],
        'scope': {'states': 16, 'prompt_groups': 4, 'natural_C_states': sum(r['point']['parent_continues'] == 'CC' for r in records)},
        'limitations': ['Only C/A counterfactual choice: no reconstructed full legal C/A/P/D policy or deployment.',
            'Four CAL prompts; frozen gamma and lambda previously used all CAL; this is module LOPO, not independent whole-method generalization.',
            'Raw-clock PCA uses training inputs only; two supervised raw coefficients and two additional coefficients per output for each matched spectral/raw extension.',
            'Old prices are post-paid-probe CFG quotes; observed feature timing excludes regression/controller and source-state taxes not explicitly inside caller timing.',
            'RAW_CLOCK and no-F increment assigned zero, favoring their cost baseline; controller and final E2E speed are unmeasured.',
            'Current teacher energy, losses and post-action outputs are targets only; no endpoint quality claim.',
            'All16 has two parent-P states; their offline C/A choice does not mean original P_OFF permits P-source A online.']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--labels', type=Path, default=ROOT / 'reports/wc_source_phase16_live_or_terminal_capture_20261012.json')
    p.add_argument('--parameters', type=Path, default=ROOT / 'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json')
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import torch
    torch.set_num_threads(2)
    if a.output.exists():
        raise ValueError('Preserve prior results; output already exists')
    parameters = json.loads(a.parameters.read_text()); labels = json.loads(a.labels.read_text())
    if parameters['sources']['reports/wc_source_phase16_live_or_terminal_capture_20261012.json'] != sha(a.labels):
        raise ValueError('H1 frozen parameters bind a different old label receipt')
    capture = json.loads(a.capture.read_text())
    records = join_and_verify(capture, labels, a.project)
    result = analyze(records, parameters)
    result.update(inputs={str(x): sha(x) for x in (a.capture, a.labels, a.parameters)},
                  parameter_fingerprint=parameters['fingerprint'], GPU_submissions=0, CUDA_initialized=torch.cuda.is_initialized())
    if result['CUDA_initialized']:
        raise ValueError('CPU analysis initialized CUDA')
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(a.output), 'scope': result['scope']}))


if __name__ == '__main__':
    main()
