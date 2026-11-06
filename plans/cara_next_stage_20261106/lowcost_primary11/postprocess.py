"""Fixed queue delivery counts and explicitly conditional fidelity; no GPU work."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
TERMINAL = {'COMPLETE', 'TEXT_REJECTED', 'VIDEO_REJECTED'}
ROLES = ('NATIVE35', 'F17_A2_LIGHT_C', 'R18C')
IDS = [33, 36, 37, 40, 41, 44, 45, 46, 48, 49, 50]


def validate_queue(card, collection):
    expected = [f'CONFIRM10_{i:03d}' for i in IDS]
    if ([s['id'] for s in card['matrix']] != expected
            or [r['slot'] for r in collection['rows']] != card['matrix']
            or collection['run_id'] != card['run_id']
            or collection['scope_sha256'] != card['scope_sha256']):
        raise ValueError('Exact eleven never-attempted requests required')
    if any(r['status'] not in TERMINAL | {'NOT_REACHED', 'RUNNING'} for r in collection['rows']):
        raise ValueError('Unknown request status')


def interval(values, seed=20261105, count=100000):
    rng = random.Random(seed)
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(count))
    def q(p):
        x = p * (len(means) - 1)
        lo = int(x)
        hi = min(lo + 1, len(means) - 1)
        return means[lo] + (x - lo) * (means[hi] - means[lo])
    return [q(.025), q(.975)]


def analyze(card, collection, scores):
    validate_queue(card, collection)
    members = list(card['inputs_by_alias'].values())
    rows = card['prior_primary_rows'] + collection['rows']
    index = {(r['slot']['member'], r['slot']['role']): r for r in rows}
    if len(index) != 27 or len(rows) != 27:
        raise ValueError('Fixed nine-input / three-arm accounting required')
    score_rows = card['prior_primary_scores'] + scores['rows']
    si = {(r['slot']['member'], r['slot']['role']): r for r in score_rows}
    coverage = {}
    for role in ROLES:
        statuses = [index[m, role]['status'] for m in members]
        coverage[role] = dict(denominator=9, COMPLETE=statuses.count('COMPLETE'),
            TEXT_REJECTED=statuses.count('TEXT_REJECTED'), VIDEO_REJECTED=statuses.count('VIDEO_REJECTED'),
            NOT_REACHED=statuses.count('NOT_REACHED'), RUNNING=statuses.count('RUNNING'))
    per_input = []
    for alias, member in card['inputs_by_alias'].items():
        row = dict(alias=alias, member=member, methods={})
        for role in ROLES:
            record = index[member, role]
            result = record.get('result', {})
            row['methods'][role] = dict(status=record['status'], refusal=record.get('refusal'),
                Alex=0.0 if role == 'NATIVE35' and record['status'] == 'COMPLETE' else si.get((member, role), {}).get('Alex'),
                T_DD=result.get('T_DD'), T_request=result.get('T_request'))
        joint = all(row['methods'][r]['status'] == 'COMPLETE' for r in ROLES)
        joint = joint and all(row['methods'][r]['Alex'] is not None for r in ROLES)
        row['joint_quality_evaluable'] = joint
        row['delta_Alex_R18_minus_F17'] = (row['methods']['R18C']['Alex'] - row['methods']['F17_A2_LIGHT_C']['Alex']) if joint else None
        per_input.append(row)
    matched = [r for r in per_input if r['joint_quality_evaluable']]
    conditional = dict(inputs=len(matched), aliases=[r['alias'] for r in matched], descriptive_only=True)
    if matched:
        delta = [r['delta_Alex_R18_minus_F17'] for r in matched]
        means = {role: dict(Alex=statistics.mean(r['methods'][role]['Alex'] for r in matched),
            T_DD=statistics.mean(r['methods'][role]['T_DD'] for r in matched),
            T_request=statistics.mean(r['methods'][role]['T_request'] for r in matched)) for role in ROLES}
        for role in ('F17_A2_LIGHT_C', 'R18C'):
            means[role]['T_DD_speedup_ratio_of_matched_means'] = means['NATIVE35']['T_DD'] / means[role]['T_DD']
            means[role]['T_request_speedup_ratio_of_matched_means'] = means['NATIVE35']['T_request'] / means[role]['T_request']
        ratios = [r['methods']['R18C']['Alex'] / r['methods']['F17_A2_LIGHT_C']['Alex'] for r in matched]
        conditional.update(mean_delta_Alex=statistics.mean(delta), descriptive_prompt_bootstrap_CI95=interval(delta),
            improved=sum(d < 0 for d in delta), means=means, measured_mean_ratio=statistics.mean(ratios),
            frozen_prediction=0.825, prediction_refitted=False)
    return dict(status='FIXED_QUEUE_ANALYZED', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
        fixed_queue_complete=all(r['status'] in TERMINAL for r in collection['rows']),
        coverage=coverage, conditional_quality=conditional, per_input=per_input,
        original_ten_input_endpoint='NOT_EVALUABLE', original_nine_input_LPIPS_endpoint='NOT_EVALUABLE',
        scientific_success_test=False, noninferiority_test=False, whole_original_run_success=False,
        score_pairs_new=len(scores['rows']), score_pairs_reused=len(card['prior_primary_scores']),
        limitation='Guardrail-accepted common inputs only; no rejected-value imputation or denominator substitution. F17 C07 was already rejected. Auxiliary arms are not completed by this run.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('score', 'analyze'))
    for name in ('manifest', 'collection', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('capture', 'settlement', 'scores'):
        p.add_argument('--' + name, type=Path)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text())
    card, collection = read(a.manifest), read(a.collection)
    validate_queue(card, collection)
    if a.output.exists():
        raise ValueError('Recover the existing scorer or analysis; no replay')
    from wcomr.gpu_budget_pool_v2 import atomic_json
    if a.action == 'analyze':
        atomic_json(a.output, analyze(card, collection, read(a.scores)))
        return
    from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
    capture, settlement = read(a.capture), read(a.settlement)
    release = released_lifecycle(capture, capture['files']['launch']['sha256'], settlement)
    if not all(release[k] for k in ('GPU_released', 'mode_restored', 'cost_settled', 'original_processes_ended')):
        raise ValueError('Scoring requires original resource and financial closure')
    if os.environ['CUDA_VISIBLE_DEVICES'] != '' or os.environ['NVIDIA_VISIBLE_DEVICES'] != 'void':
        raise ValueError('CPU-only scoring required')
    for receipt in card['prior_score_receipts']:
        if hashlib.sha256((ROOT / receipt['path']).read_bytes()).hexdigest() != receipt['sha256']:
            raise ValueError('A reused accepted score receipt changed')
    for row in card['prior_primary_rows']:
        if row['status'] == 'COMPLETE':
            for key in ('latent_artifact', 'video_artifact'):
                art = row['result'][key]
                if hashlib.sha256(Path(art['path']).read_bytes()).hexdigest() != art['sha256']:
                    raise ValueError('A retained original artifact changed')
    complete = [r for r in collection['rows'] if r['status'] == 'COMPLETE']
    natives = {r['slot']['member']: r for r in complete if r['slot']['role'] == 'NATIVE35'}
    candidates = [r for r in complete if r['slot']['role'] != 'NATIVE35' and r['slot']['member'] in natives]
    import torch
    import lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    def forbidden(*args, **kwargs):
        raise RuntimeError('CPU scoring forbids CUDA and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval() if candidates else None
    state = dict(status='SCORING', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
        rows=[], release=release, GPU_submissions=0, original_nine_input_endpoint='NOT_EVALUABLE')
    atomic_json(a.output, state)
    for row in candidates:
        slot = row['slot']
        fidelity = score_video_pair(row['result']['video_artifact'], natives[slot['member']]['result']['video_artifact'], alex)
        actual = ''.join(r['actual'] for r in row['result']['semantic_history'])
        if actual != ''.join(card['roles'][slot['role']]['policy']['actions']):
            raise ValueError('Executed policy differs from the frozen policy')
        state['rows'].append(dict(slot=slot, Alex=fidelity['Alex'], T_DD=row['result']['T_DD'],
            T_request=row['result']['T_request'], fidelity=fidelity, mask_matches=True))
        atomic_json(a.output, state)
    state.update(status='ACCEPTED_OUTPUT_SCORES_COMPLETE', CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(a.output, state)


if __name__ == '__main__':
    main()
