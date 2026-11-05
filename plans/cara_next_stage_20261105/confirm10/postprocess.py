"""Released CPU-only93-frame scoring and the prewritten paired confirmation."""
import argparse
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))


def interval(values, bootstrap):
    rng = random.Random(bootstrap['seed'])
    n = len(values)
    means = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(bootstrap['replicates']))
    def quantile(p):
        x = p * (len(means) - 1)
        lo, hi = math.floor(x), math.ceil(x)
        return means[lo] + (x - lo) * (means[hi] - means[lo])
    return [quantile(.025), quantile(.975)]


def summarize(card, rows, native_timings):
    indexed = {(r['slot']['member'], r['slot']['role']): r for r in rows}
    members = list(card['inputs_by_alias'].values())
    means = {role: dict(Alex=statistics.mean(indexed[m, role]['Alex'] for m in members),
                        T_DD=statistics.mean(indexed[m, role]['T_DD'] for m in members))
             for role in card['roles'] if role != 'NATIVE35'}
    means['NATIVE35'] = dict(Alex=0.0, T_DD=statistics.mean(native_timings.values()))
    # Transfer predictions are frozen old-four means, not refitted new-prompt values.
    predictions = {}
    for role, prediction in card['frozen_predictions_vs_F17'].items():
        pairs = [dict(member=m, measured_ratio=indexed[m, role]['Alex'] / indexed[m, 'F17_A2_LIGHT_C']['Alex']) for m in members]
        ratios = [p['measured_ratio'] for p in pairs]
        predictions[role] = dict(frozen_prediction=prediction, measured_mean_ratio=statistics.mean(ratios),
            absolute_error_of_mean=abs(statistics.mean(ratios) - prediction),
            mean_prompt_absolute_error=statistics.mean(abs(v - prediction) for v in ratios), per_input=pairs)
    effects = []
    for contrast in card['contrasts']:
        pairs = [dict(member=m, delta_Alex=indexed[m, contrast['candidate']]['Alex'] - indexed[m, contrast['reference']]['Alex'],
                      delta_T_DD=indexed[m, contrast['candidate']]['T_DD'] - indexed[m, contrast['reference']]['T_DD']) for m in members]
        values = [p['delta_Alex'] for p in pairs]
        effects.append(dict(**contrast, mean_delta=statistics.mean(values), CI95=interval(values, card['bootstrap']),
            improved=sum(v < 0 for v in values), equal=sum(v == 0 for v in values), per_input=pairs,
            mean_delta_T_DD=statistics.mean(p['delta_T_DD'] for p in pairs)))
    primary = effects[0]
    matched = all(r['mask_matches'] for r in rows)
    better = matched and primary['mean_delta'] < 0 and primary['CI95'][1] < 0
    noninferior = matched and not better and primary['CI95'][1] < card['primary']['secondary_noninferiority_margin']
    verdict = ('TECHNICAL_FAILURE' if not matched else
               ('BETTER' if better else ('SECONDARY_NONINFERIOR' if noninferior else 'INCONCLUSIVE')))
    return dict(status='COMPLETE', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
        frozen_prediction_comparison=predictions, contrasts=effects, mean_metrics=means,
        verdict=verdict, primary_success=better, secondary_noninferiority=noninferior,
        monotonic_mean_LPIPS=means['R16C']['Alex'] >= means['R18C']['Alex'] >= means['R21C']['Alex'],
        all_fixed_masks_matched=matched, formal_scores=len(rows),
        CI_method=card['bootstrap'], same_run_controls=True,
        per_input_T_DD={m: {role: native_timings[m] if role == 'NATIVE35' else indexed[m, role]['T_DD']
                           for role in card['roles']} for m in members},
        deferred_supplements=['NATIVE_K18; R18C-vs-k18 secondary comparison'],
        timing_note='All five arms have36 actual updates; report measured T_DD. k18 comparison is deferred.',
        position_overlap_gate=False)


def write_results(output, result):
    from wcomr.gpu_budget_pool_v2 import atomic_json
    atomic_json(output, result)
    atomic_json(output.parent / 'outcome_summary.json', {k: result[k] for k in
        ('run_id', 'verdict', 'primary_success', 'secondary_noninferiority', 'mean_metrics', 'formal_scores')})
    lines = ['# confirm10 complete results', '', 'Frozen prediction comparison first; no post-hoc tuning.', '',
             '|arm|frozen LPIPS/F17|measured mean ratio|absolute error of mean|prompt MAE|', '|---|---:|---:|---:|---:|']
    for role, r in result['frozen_prediction_comparison'].items():
        lines.append(f"|{role}|{r['frozen_prediction']}|{r['measured_mean_ratio']:.6f}|{r['absolute_error_of_mean']:.6f}|{r['mean_prompt_absolute_error']:.6f}|")
    lines += ['', f"Verdict: {result['verdict']}; prompt bootstrap: {result['CI_method']}", '',
              '|contrast|mean delta Alex|95% CI|improved/10|mean delta T_DD(s)|', '|---|---:|---|---:|---:|']
    for c in result['contrasts']:
        lines.append(f"|{c['candidate']} - {c['reference']}|{c['mean_delta']:+.6f}|{c['CI95']}|{c['improved']}|{c['mean_delta_T_DD']:+.4f}|")
    lines += ['', '|arm|mean Alex|mean T_DD(s)|', '|---|---:|---:|']
    for role, r in result['mean_metrics'].items():
        lines.append(f"|{role}|{r['Alex']:.6f}|{r['T_DD']:.4f}|")
    lines += ['', '|prompt|primary delta Alex|direction|primary delta T_DD(s)|', '|---|---:|---|---:|']
    for pair in result['contrasts'][0]['per_input']:
        direction = 'better' if pair['delta_Alex'] < 0 else ('worse' if pair['delta_Alex'] > 0 else 'equal')
        lines.append(f"|{pair['member']}|{pair['delta_Alex']:+.6f}|{direction}|{pair['delta_T_DD']:+.4f}|")
    lines += ['', f"Monotonic mean LPIPS: {result['monotonic_mean_LPIPS']}", result['timing_note'],
              'Per-input directions, times and frozen-prediction errors are in complete_analysis.json.']
    (output.parent / 'COMPLETE_RESULTS.md').write_text('\n'.join(lines) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('score', 'analyze'))
    for name in ('manifest', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('collection', 'capture', 'settlement', 'scores'):
        p.add_argument('--' + name, type=Path)
    args = p.parse_args()
    read = lambda path: json.loads(path.read_text())
    from wcomr.gpu_budget_pool_v2 import atomic_json
    card = read(args.manifest)
    assert not args.output.exists(), 'Recover the existing original score/analysis; no replay'
    if args.action == 'analyze':
        scores = read(args.scores)
        assert scores['status'] == 'COMPLETE_PENDING_ANALYSIS' and scores['scope_sha256'] == card['scope_sha256']
        write_results(args.output, summarize(card, scores['rows'], scores['native_T_DD']))
        return
    from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
    capture = read(args.capture)
    release = released_lifecycle(capture, capture['files']['launch']['sha256'], read(args.settlement))
    assert all(release[k] for k in ('GPU_released', 'mode_restored', 'cost_settled', 'original_processes_ended', 'container_exit_success'))
    collection = read(args.collection)
    launch = json.loads(capture['files']['launch']['raw_utf8'])
    assert launch['run_id'] == card['run_id'] and launch['scope_sha256'] == card['scope_sha256']
    assert collection['status'] == 'COMPLETE_PENDING_RELEASE_SCORING' and collection['scope_sha256'] == card['scope_sha256']
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    import torch
    import lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    def forbidden(*a, **kw):
        raise RuntimeError('CPU scorer forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval()
    references = {r['slot']['member']: r for r in collection['rows']
                  if r['slot']['section'] != 'warm' and r['slot']['role'] == 'NATIVE35'}
    state = dict(status='SCORING', scope_sha256=card['scope_sha256'], rows=[], release=release,
        native_T_DD={m: r['result']['T_DD'] for m, r in references.items()})
    atomic_json(args.output, state)
    for row in collection['rows']:
        slot = row['slot']
        if slot['section'] == 'warm' or slot['role'] == 'NATIVE35':
            continue
        fidelity = score_video_pair(row['result']['video_artifact'], references[slot['member']]['result']['video_artifact'], alex)
        actual = ''.join(h['actual'] for h in row['result']['semantic_history'])
        matched = actual == ''.join(card['roles'][slot['role']]['policy']['actions'])
        state['rows'].append(dict(slot=slot, Alex=fidelity['Alex'], T_DD=row['result']['T_DD'], fidelity=fidelity, mask_matches=matched))
        atomic_json(args.output, state)
    state.update(status='COMPLETE_PENDING_ANALYSIS', CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(args.output, state)


if __name__ == '__main__':
    main()
