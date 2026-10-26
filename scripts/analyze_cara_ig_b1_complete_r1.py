"""Analyze only a terminal, released, centrally settled B1 result.

Descriptive two-prompt readout evidence. No video-quality or automatic
mainline decision, and no partial-run coefficient or candidate selection.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


def analyze(capture, settlement, prior):
    assert capture['terminal'] and capture['UUID_lock_free']
    assert not any(capture['live_handles'].values()) and not capture['GPU']['compute_apps']
    files = capture['files']
    auth, bill = (files[k]['value'] for k in ('auth', 'billing'))
    result = files['B1-results.json']['value']
    post = files['post-results.json']['value']
    assert files['release']['value']['accepted']
    supervisor, guardian = (files[k]['value'] for k in ('supervisor', 'guardian'))
    assert supervisor['child_exit_code'] == supervisor['post_exit_code'] == 0
    assert supervisor['exclusive_monitor_accepted'] and not supervisor.get('release_error')
    assert guardian['status'] == 'IG_B1_HOST_GUARDIAN_TERMINAL' and guardian['container_exit_code'] == 0
    assert all(supervisor[k] == auth[k] for k in ('launch_id', 'source_revision', 'gpu_uuid'))
    assert result['status'] == 'B1_LOCAL_READOUT_COMPLETE_PENDING_VIDEO_VALIDATION'
    assert post['status'] == 'B1_LOCAL_READOUT_ACCEPTED_PENDING_CENTRAL_SETTLEMENT_AND_VIDEO'
    assert post['result_sha256'] == files['B1-results.json']['sha256']
    assert post['billing_sha256'] == files['billing']['sha256']
    job = settlement['job']
    assert settlement['status'] == 'IG_B1_CENTRAL_SETTLED' and job['status'] == 'SETTLED'
    assert all(job[k] == auth[k] == bill[k] for k in
               ('run_id', 'launch_id', 'source_revision', 'gpu_uuid', 'scope_counts', 'billed_limit_GPUh'))
    assert job['billing_sha256'] == files['billing']['sha256']
    assert job['actual_GPUh'] == bill['actual_GPUh'] == post['actual_GPUh']
    assert prior['status'] == 'IG_B1_CENTRAL_SETTLED' and prior['job']['status'] == 'SETTLED'
    assert prior['job']['launch_id'] != auth['launch_id']
    assert prior['job']['round_id'] == job['round_id']
    assert len(result['rows']) == 4 and all(r['status'] == 'COMPLETE' for r in result['rows'])
    assert len(result['controls']) == 2 and all(all(c[k] for k in
               ('all36_guided_equal', 'final_latent_equal', 'video_bytes_equal')) for c in result['controls'])
    cal = result['calibration']
    prompts, steps = cal['expected_prompts'], cal['expected_steps']
    assert len(set(prompts)) == 2 and steps == [22, 23, 25, 33, 34, 35]
    assert {f['held_out_prompt'] for f in cal['folds']} == set(prompts)
    for f in cal['folds']:
        assert f['training_prompts'] == [p for p in prompts if p != f['held_out_prompt']]
    replays = result['replays']
    endpoints = [r for r in replays if r['kind'] == 'ENDPOINT']
    assert len(replays) == 72 and len(endpoints) == 24 and all(r['exact'] for r in endpoints)
    assert {(r['prompt'], r['step'], r['role']) for r in endpoints} == set(
        itertools.product(prompts, steps, ('FULL', 'R4_GLOBAL')))
    reports = {}
    def ratio(new, base):
        return 100 * (1 - new / base) if base > 0 else None
    for kind in ('LOPO', 'FINAL'):
        rows = [r for r in replays if r['kind'] == kind]
        assert len(rows) == 24 and {(r['prompt'], r['step'], r['role']) for r in rows} == set(
            itertools.product(prompts, steps, ('IG_SCALAR', 'IG_BAND')))
        groups = {}
        for prompt in prompts:
            group = {}
            coef = cal['final'] if kind == 'FINAL' else next(
                f['coefficients'] for f in cal['folds'] if f['held_out_prompt'] == prompt)
            for role in ('IG_SCALAR', 'IG_BAND'):
                selected = [r for r in rows if r['prompt'] == prompt and r['role'] == role]
                assert all(r['gains'] == coef[role] for r in selected)
                means = {k: math.fsum(r[k] for r in selected) / 6 for k in
                         ('actual_guided_MSE', 'baseline_FULL_MSE', 'baseline_DEEP_MSE')}
                assert all(math.isfinite(x) and x >= 0 for x in means.values())
                group[role] = dict(means, gains=coef[role],
                    improvement_vs_FULL_percent=ratio(means['actual_guided_MSE'], means['baseline_FULL_MSE']),
                    improvement_vs_DEEP_percent=ratio(means['actual_guided_MSE'], means['baseline_DEEP_MSE']),
                    states_better_than_FULL=sum(r['actual_guided_MSE'] < r['baseline_FULL_MSE'] for r in selected),
                    states_better_than_DEEP=sum(r['actual_guided_MSE'] < r['baseline_DEEP_MSE'] for r in selected))
            group['band_improvement_vs_scalar_percent'] = ratio(
                group['IG_BAND']['actual_guided_MSE'], group['IG_SCALAR']['actual_guided_MSE'])
            groups[prompt] = group
        pooled = {}
        for role in ('IG_SCALAR', 'IG_BAND'):
            means = {k: math.fsum(groups[p][role][k] for p in prompts) / 2 for k in
                     ('actual_guided_MSE', 'baseline_FULL_MSE', 'baseline_DEEP_MSE')}
            pooled[role] = dict(means,
                improvement_vs_FULL_percent=ratio(means['actual_guided_MSE'], means['baseline_FULL_MSE']),
                improvement_vs_DEEP_percent=ratio(means['actual_guided_MSE'], means['baseline_DEEP_MSE']))
        pooled['band_improvement_vs_scalar_percent'] = ratio(
            pooled['IG_BAND']['actual_guided_MSE'], pooled['IG_SCALAR']['actual_guided_MSE'])
        reports[kind] = dict(by_prompt=groups, equal_prompt_mean=pooled)
    return dict(status='B1_COMPLETE_LOCAL_READOUT_ANALYSIS_NOT_VIDEO_VALIDATION',
                launch_id=auth['launch_id'], source_revision=auth['source_revision'],
                controls=result['controls'], summary=reports,
                deployment_coefficients=result['deployment_coefficients'],
                training_folds=cal['folds'],
                actual_GPUh=bill['actual_GPUh'], prior_engineering_GPUh=prior['job']['actual_GPUh'],
                round_actual_GPUh=bill['actual_GPUh'] + prior['job']['actual_GPUh'],
                round_remaining_GPUh=7 - bill['actual_GPUh'] - prior['job']['actual_GPUh'],
                independent_prompts=2, states=12, uncertainty='Descriptive development LOPO only; no independent TEST',
                mainline_admitted=False, video_quality_measured=False,
                deployment_speed_measured=False, scientific_continuation_requires_review=True)


def main():
    p = argparse.ArgumentParser()
    for key in ('capture', 'settlement', 'prior', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    inputs = {key: getattr(a, key) for key in ('capture', 'settlement', 'prior')}
    result = analyze(**{k: json.loads(path.read_text()) for k, path in inputs.items()})
    result['evidence'] = {k: dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                          for k, path in inputs.items()}
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(result['status'])


if __name__ == '__main__':
    main()
