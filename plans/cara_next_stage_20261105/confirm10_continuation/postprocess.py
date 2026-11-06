"""Released CPU scoring for the 25 new requests and the prewritten 9-input endpoint.

Scoring reads inherited hashes and refuses unless the continuation itself has
been uniquely settled and the GPU/CPU processes have been released. It does not
rescore C01-C04, retry a refusal, or rewrite the original collection.
"""
import argparse
import hashlib
import json
import math
import os
import random
import statistics
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
RUNNER = ROOT / 'plans/cara_next_stage_20261104/sensitivity/runner.py'


def runner_functions():
    import importlib.util
    spec = importlib.util.spec_from_file_location('confirm10_continuation_sensitivity_runner', RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interval(values, bootstrap):
    rng = random.Random(bootstrap['seed'])
    n = len(values)
    means = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(bootstrap['replicates']))
    def quantile(p):
        x = p * (len(means) - 1)
        lo, hi = math.floor(x), math.ceil(x)
        return means[lo] + (x - lo) * (means[hi] - means[lo])
    return [quantile(.025), quantile(.975)]


def require_original_settlement(card):
    settlement = card['inherited_outputs']['settlement']
    if (settlement['status'] != 'SETTLED'
            or settlement['launch_id'] != 'fe91fe0468944be18b8c0950c33e092b'
            or settlement['billing_sha256'] != '471f3b73d840cb841f7148fa77617d10f1491e62a276961a2825984f73ae4e42'
            or settlement['actual_GPUh'] != 1.3313886947699616):
        raise ValueError('Original confirm10 unique settlement identity differs')
    receipt = ROOT / settlement['source_receipt']
    raw = json.loads(receipt.read_text())
    job = raw['central_after']['jobs'][card['inherited_outputs']['source_run_id']]
    if (job['status'] != settlement['status'] or job['launch_id'] != settlement['launch_id']
            or job['actual_GPUh'] != settlement['actual_GPUh']
            or job['billing_sha256'] != settlement['billing_sha256']):
        raise ValueError('Original settlement receipt differs from the frozen identity')


def require_inherited_scores(card):
    spec = card['inherited_scores_receipt']
    path = ROOT / spec['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256'] or spec['pairs'] != 16:
        raise ValueError('Inherited partial-score receipt changed')
    rows = card['inherited_score_rows']
    if len(rows) != 16:
        raise ValueError('Nine-input analysis needs the 16 inherited C01-C04 pairs')
    videos = {row['slot']['id']: row['video_artifact']['sha256']
              for row in card['inherited_outputs']['rows'] if row['slot']['section'] != 'warm'}
    for row in rows:
        if (row['slot']['member'] == card['excluded_cohort']['member'] or not row['mask_matches']
                or videos[row['slot']['id']] != row['video_sha256']):
            raise ValueError('Inherited score is not a hash-matched C01-C04 pair')


def require_score_release(card, release, collection):
    require_original_settlement(card)
    runner_functions().assert_inherited_hashes(card)
    require_inherited_scores(card)
    for key in ('GPU_released', 'mode_restored', 'cost_settled', 'original_processes_ended', 'container_exit_success'):
        if not release[key]:
            raise ValueError('Score only after the continuation final settlement and GPU/CPU release')
    if release.get('hard_limit_exceeded'):
        raise ValueError('Continuation hard limit exceeded')
    if (collection['status'] != 'COMPLETE_PENDING_RELEASE_SCORING'
            or collection['run_id'] != card['run_id'] or collection['scope_sha256'] != card['scope_sha256']
            or collection.get('claims_completion')):
        raise ValueError('Continuation collection is not a complete unreleased-score run')
    if [row['slot']['id'] for row in collection['rows']] != [slot['id'] for slot in card['matrix']]:
        raise ValueError('Continuation rows differ from the frozen matrix')
    if any(row['status'] != 'COMPLETE' for row in collection['rows']):
        raise ValueError('Incomplete continuation request')
    if any(row['slot']['member'] == card['excluded_cohort']['member'] for row in collection['rows']):
        raise ValueError('Excluded C05 entered the continuation')


def summarize(card, rows, native_timings):
    if any(row['slot']['member'] == card['excluded_cohort']['member'] for row in rows):
        raise ValueError('C05 is outside the pairing denominator')
    members = [card['inputs_by_alias'][alias] for alias in card['inputs_by_alias']]
    if members != [card['inputs_by_alias'][alias] for alias in (
            'C01', 'C02', 'C03', 'C04', 'C06', 'C07', 'C08', 'C09', 'C10')]:
        raise ValueError('Scientific cohort is not the registered nine inputs')
    if card['excluded_cohort']['member'] in members or card['excluded_cohort']['in_pairing_denominator']:
        raise ValueError('C05 is outside the pairing denominator')
    indexed = {(row['slot']['member'], row['slot']['role']): row for row in rows}
    if len(rows) != 36 or len(indexed) != 36:
        return dict(status='NOT_COMPLETE', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
            scientific_endpoint='NOT_RUN', pairs=len(rows), planned_pairs=36, claims_completion=False,
            original_ten_input_endpoint='NOT_EVALUABLE')
    means = {role: dict(Alex=statistics.mean(indexed[member, role]['Alex'] for member in members),
                        T_DD=statistics.mean(indexed[member, role]['T_DD'] for member in members))
             for role in card['roles'] if role != 'NATIVE35'}
    means['NATIVE35'] = dict(Alex=0.0, T_DD=statistics.mean(native_timings[member] for member in members))
    predictions = {}
    for role, prediction in card['frozen_predictions_vs_F17'].items():
        ratios = [indexed[member, role]['Alex'] / indexed[member, 'F17_A2_LIGHT_C']['Alex'] for member in members]
        predictions[role] = dict(frozen_prediction=prediction, measured_mean_ratio=statistics.mean(ratios),
            absolute_error_of_mean=abs(statistics.mean(ratios) - prediction),
            mean_prompt_absolute_error=statistics.mean(abs(value - prediction) for value in ratios),
            per_input=[dict(member=member, measured_ratio=ratio) for member, ratio in zip(members, ratios)])
    effects = []
    for contrast in card['contrasts']:
        pairs = [dict(member=member,
            delta_Alex=indexed[member, contrast['candidate']]['Alex'] - indexed[member, contrast['reference']]['Alex'],
            delta_T_DD=indexed[member, contrast['candidate']]['T_DD'] - indexed[member, contrast['reference']]['T_DD'])
            for member in members]
        values = [pair['delta_Alex'] for pair in pairs]
        effects.append(dict(**contrast, mean_delta=statistics.mean(values), CI95=interval(values, card['bootstrap']),
            improved=sum(value < 0 for value in values), equal=sum(value == 0 for value in values), per_input=pairs,
            mean_delta_T_DD=statistics.mean(pair['delta_T_DD'] for pair in pairs)))
    primary = effects[0]
    matched = all(row['mask_matches'] for row in rows)
    better = matched and primary['mean_delta'] < 0 and primary['CI95'][1] < 0
    noninferior = matched and not better and primary['CI95'][1] < card['primary']['secondary_noninferiority_margin']
    verdict = ('TECHNICAL_FAILURE' if not matched else
               ('BETTER' if better else ('SECONDARY_NONINFERIOR' if noninferior else 'INCONCLUSIVE')))
    return dict(status='COMPLETE_NINE_INPUT_ENDPOINT', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
        frozen_prediction_comparison=predictions, contrasts=effects, mean_metrics=means, verdict=verdict,
        primary_success=better, secondary_noninferiority=noninferior,
        monotonic_mean_LPIPS=means['R16C']['Alex'] >= means['R18C']['Alex'] >= means['R21C']['Alex'],
        all_fixed_masks_matched=matched, formal_scores=len(rows), scientific_inputs=9,
        claims_completion=True, original_ten_input_endpoint='NOT_EVALUABLE',
        excluded_from_denominator=card['excluded_cohort']['alias'], CI_method=card['bootstrap'],
        per_input_T_DD={member: {role: native_timings[member] if role == 'NATIVE35' else indexed[member, role]['T_DD']
            for role in card['roles']} for member in members},
        deferred_supplements=card['deferred_supplements'],
        timing_note='Nine inputs with five 36-update arms. C05 is not in the denominator. k18 remains deferred.')


def write_results(output, result):
    from wcomr.gpu_budget_pool_v2 import atomic_json
    atomic_json(output, result)
    if result['status'] != 'COMPLETE_NINE_INPUT_ENDPOINT':
        (output.parent / 'COMPLETE_RESULTS.md').write_text(
            '# confirm10 continuation results\n\nScientific endpoint: NOT_RUN. C05 remains outside the denominator.\n')
        return
    lines = ['# confirm10 continuation nine-input results', '',
             'Frozen prediction comparison first. The original ten-input endpoint stays NOT_EVALUABLE.', '',
             '|arm|frozen LPIPS/F17|measured mean ratio|absolute error of mean|prompt MAE|',
             '|---|---:|---:|---:|---:|']
    for role, row in result['frozen_prediction_comparison'].items():
        lines.append(f"|{role}|{row['frozen_prediction']}|{row['measured_mean_ratio']:.6f}|{row['absolute_error_of_mean']:.6f}|{row['mean_prompt_absolute_error']:.6f}|")
    lines += ['', f"Verdict: {result['verdict']}; prompt bootstrap: {result['CI_method']}", '',
              '|contrast|mean delta Alex|95% CI|improved/9|mean delta T_DD(s)|', '|---|---:|---|---:|---:|']
    for contrast in result['contrasts']:
        lines.append(f"|{contrast['candidate']} - {contrast['reference']}|{contrast['mean_delta']:+.6f}|{contrast['CI95']}|{contrast['improved']}|{contrast['mean_delta_T_DD']:+.4f}|")
    lines += ['', '|arm|mean Alex|mean T_DD(s)|', '|---|---:|---:|']
    for role, row in result['mean_metrics'].items():
        lines.append(f"|{role}|{row['Alex']:.6f}|{row['T_DD']:.4f}|")
    lines += ['', '|prompt|primary delta Alex|direction|primary delta T_DD(s)|', '|---|---:|---|---:|']
    for pair in result['contrasts'][0]['per_input']:
        direction = 'better' if pair['delta_Alex'] < 0 else ('worse' if pair['delta_Alex'] > 0 else 'equal')
        lines.append(f"|{pair['member']}|{pair['delta_Alex']:+.6f}|{direction}|{pair['delta_T_DD']:+.4f}|")
    lines += ['', f"Monotonic mean LPIPS: {result['monotonic_mean_LPIPS']}", result['timing_note'],
              'C05 / av_snowy_1_0 is not in this denominator. k18 is still deferred.']
    (output.parent / 'COMPLETE_RESULTS.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('verify-inherited', 'score', 'analyze'))
    parser.add_argument('--manifest', type=Path, required=True)
    for name in ('output', 'collection', 'capture', 'settlement', 'scores'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    card = json.loads(args.manifest.read_text())
    if args.action == 'verify-inherited':
        require_original_settlement(card)
        runner_functions().assert_inherited_hashes(card)
        require_inherited_scores(card)
        print(json.dumps(dict(status='INHERITED_HASHES_MATCH', count=21, GPU_submissions=0, ledger_written=False)))
        return
    if args.output.exists():
        raise ValueError('Recover the existing continuation score/analysis; no replay')
    if args.action == 'analyze':
        scores = json.loads(args.scores.read_text())
        if scores['status'] != 'COMPLETE_PENDING_ANALYSIS' or scores['scope_sha256'] != card['scope_sha256']:
            raise ValueError('Continuation scores are not ready for the nine-input analysis')
        inherited = card['inherited_score_rows']
        rows = inherited + scores['rows']
        timings = dict(scores['native_T_DD'])
        timings.update({row['slot']['member']: row['T_DD'] for row in card['inherited_outputs']['rows']
            if row['slot']['role'] == 'NATIVE35' and row['slot']['section'] != 'warm'})
        write_results(args.output, summarize(card, rows, timings))
        return
    from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
    capture = json.loads(args.capture.read_text())
    settlement = json.loads(args.settlement.read_text())
    release = released_lifecycle(capture, capture['files']['launch']['sha256'], settlement)
    collection = json.loads(args.collection.read_text())
    launch = json.loads(capture['files']['launch']['raw_utf8'])
    if launch['run_id'] != card['run_id'] or launch['scope_sha256'] != card['scope_sha256']:
        raise ValueError('Score capture is not this continuation')
    require_score_release(card, release, collection)
    if os.environ['CUDA_VISIBLE_DEVICES'] != '' or os.environ['NVIDIA_VISIBLE_DEVICES'] != 'void':
        raise ValueError('CPU scorer forbids a visible GPU')
    import torch
    import lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    from wcomr.gpu_budget_pool_v2 import atomic_json
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    def forbidden(*_args, **_kwargs):
        raise RuntimeError('CPU scorer forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval()
    references = {row['slot']['member']: row for row in collection['rows'] if row['slot']['role'] == 'NATIVE35'}
    state = dict(status='SCORING', scope_sha256=card['scope_sha256'], rows=[], release=release,
        native_T_DD={member: row['result']['T_DD'] for member, row in references.items()}, claims_completion=False)
    atomic_json(args.output, state)
    for row in collection['rows']:
        slot = row['slot']
        if slot['role'] == 'NATIVE35':
            continue
        fidelity = score_video_pair(row['result']['video_artifact'], references[slot['member']]['result']['video_artifact'], alex)
        actual = ''.join(step['actual'] for step in row['result']['semantic_history'])
        matched = actual == ''.join(card['roles'][slot['role']]['policy']['actions'])
        state['rows'].append(dict(slot=slot, Alex=fidelity['Alex'], T_DD=row['result']['T_DD'],
            fidelity=fidelity, mask_matches=matched))
        atomic_json(args.output, state)
    if len(state['rows']) != 20:
        raise ValueError('Continuation scoring must add exactly 20 new pairs')
    state.update(status='COMPLETE_PENDING_ANALYSIS', CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(args.output, state)


if __name__ == '__main__':
    main()
