"""Identity-bound final video quality inputs and prompt-grouped summaries.

This module loads no metric model and submits no work. An evaluator's actual
code, weights and sampling observations must be supplied by the scoring run.
Only per-video results are aggregated; upstream grand averages are not used.
"""
from collections import Counter
import hashlib
import json
import math
import random
import re
from statistics import mean

from .frozen_shared_statistics_r1 import interval

DIMENSIONS = (
    'subject_consistency', 'motion_smoothness', 'overall_consistency',
    'dynamic_degree', 'MUSIQ_LONGER512', 'temporal_flickering',
)
GENERATION_STATES = {'COMPLETE', 'TEXT_REJECTED', 'VIDEO_REJECTED', 'TECH_FAILED', 'NOT_REACHED'}
SCORER_STATES = {'SCORED', 'RESOURCE_UNAVAILABLE', 'METRIC_FAILED', 'NOT_REACHED'}
VBENCH_COMMIT = 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'


def fingerprint(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def text_sha(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()


def is_sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def sampling_spec(dimension):
    """Expected source-index policy for the fixed 93-frame/16fps final clips.

    Compared separately with the author's source in a no-model CPU check. This
    is a declared expectation, not a claim that a real evaluator has run.
    """
    if dimension not in DIMENSIONS:
        raise ValueError('Explicit supported dimension required')
    all_frames = list(range(93))
    result = dict(source_frames=93, source_fps=16, frame_indices=all_frames,
                  target_indices=[], policy='ALL93')
    if dimension == 'overall_consistency':
        edges = [(i * 93) // 8 for i in range(9)]
        result.update(frame_indices=[(edges[i] + edges[i + 1] - 1) // 2 for i in range(8)],
                      policy='VBENCH_MIDDLE8')
    elif dimension == 'dynamic_degree':
        result.update(frame_indices=all_frames[::2], policy='VBENCH_MAX1_ROUND_FPS_OVER8')
    elif dimension == 'motion_smoothness':
        result.update(frame_indices=all_frames[::2], target_indices=all_frames[1::2],
                      policy='AMT_EVEN47_INTERPOLATE_ODD46_ONE_ITERATION')
    elif dimension == 'MUSIQ_LONGER512':
        result.update(policy='ALL93_LONGER512_BILINEAR_NO_ANTIALIAS')
    return result


def dimension_role(dimension):
    if dimension == 'dynamic_degree':
        return 'DESCRIPTIVE_ACTIVITY_NOT_MONOTONIC_QUALITY'
    if dimension == 'temporal_flickering':
        return 'QUALITY_ONLY_ON_PREREGISTERED_STATIC_INPUTS'
    return 'SEPARATE_QUALITY_DIMENSION_NO_WEIGHTED_TOTAL'


def build_inputs(cases, methods, generation_rows, dimensions, evaluator_identity):
    """Keep every final 16-case x 10-method x selected-dimension position."""
    if (len(cases) != 16 or len({c['id'] for c in cases}) != 16
            or len(methods) != 10 or len(set(methods)) != 10
            or not dimensions or len(set(dimensions)) != len(dimensions)
            or not set(dimensions).issubset(DIMENSIONS) or not evaluator_identity
            or evaluator_identity.get('vbench_commit') != VBENCH_COMMIT):
        raise ValueError('Complete final matrix and explicitly frozen dimension/evaluator identities required')
    if ('motion_smoothness' in dimensions or 'subject_consistency' in dimensions) and 'dynamic_degree' not in dimensions:
        raise ValueError('Report activity alongside consistency/smoothness')
    prompts = sorted({c['prompt_id'] for c in cases})
    if len(prompts) != 8:
        raise ValueError('Eight original prompt groups required')
    for prompt_id in prompts:
        group = [c for c in cases if c['prompt_id'] == prompt_id]
        if sorted(c['seed'] for c in group) != [17, 43] or any(type(c['seed']) is not int for c in group):
            raise ValueError('Both preregistered seeds per prompt required')
        if len({c['prompt'] for c in group}) != 1:
            raise ValueError('Seeds cannot change the source inference prompt')
        for case in group:
            if not isinstance(case['prompt'], str) or not case['prompt'].strip() or case['prompt_sha256'] != text_sha(case['prompt']):
                raise ValueError('Use exact original inference text and its SHA, never filename-derived text')
        if 'temporal_flickering' in dimensions:
            if (any(type(c.get('static_eligible')) is not bool for c in group)
                    or len({c['static_eligible'] for c in group}) != 1):
                raise ValueError('Static eligibility must be frozen for the whole prompt, before scoring')
    expected = {(c['id'], m) for c in cases for m in methods}
    generation = {(r['case_id'], r['method']): r for r in generation_rows}
    if len(generation_rows) != len(generation) or set(generation) != expected:
        raise ValueError('Preserve all 160 generation positions, including failures and rejections')
    scorer = fingerprint(evaluator_identity)
    rows, path_identities = [], {}
    for case in cases:
        for method in methods:
            original = generation[(case['id'], method)]
            if original['status'] not in GENERATION_STATES:
                raise ValueError('Explicit original generation status required')
            usable = original['status'] == 'COMPLETE' and original.get('endpoint_audit') == 'PASS'
            artifact = original.get('video_artifact') if usable else None
            if usable:
                if (not artifact or not is_sha(artifact.get('sha256'))
                        or not isinstance(artifact.get('path'), str) or not artifact['path']
                        or artifact.get('frames') != 93 or artifact.get('fps') != 16
                        or [artifact.get('width'), artifact.get('height')] != [768, 432]
                        or len(artifact.get('decoded_rgb_sha256', [])) != 93
                        or any(not is_sha(h) for h in artifact['decoded_rgb_sha256'])):
                    raise ValueError('Scored video needs its original SHA and complete93 geometry/FPS/RGB audit')
                identity = (case['id'], artifact['sha256'])
                if artifact['path'] in path_identities and path_identities[artifact['path']] != identity:
                    raise ValueError('A video path cannot silently alias another input or seed')
                path_identities[artifact['path']] = identity
            for dimension in dimensions:
                eligible = dimension != 'temporal_flickering' or case['static_eligible']
                status = 'READY_TO_SCORE' if usable and eligible else (
                    'NOT_APPLICABLE_STATIC_SCOPE' if not eligible else 'VIDEO_UNAVAILABLE')
                rows.append(dict(case_id=case['id'], prompt_id=case['prompt_id'], seed=case['seed'],
                    method=method, dimension=dimension, input_status=status,
                    original_generation_status=original['status'],
                    generation_record_fingerprint=fingerprint(original),
                    prompt=case['prompt'], prompt_sha256=case['prompt_sha256'],
                    video_path=artifact['path'] if artifact else None,
                    video_sha256=artifact['sha256'] if artifact else None,
                    scorer_fingerprint=scorer, expected_sampling=sampling_spec(dimension),
                    role=dimension_role(dimension)))
    bundle = dict(cases=cases, methods=methods, dimensions=dimensions, rows=rows,
                  evaluator_identity=evaluator_identity, scorer_fingerprint=scorer,
                  registered_generation_positions=160, registered_metric_positions=len(rows),
                  full_official_VBench_total=False, physics_correctness_claim=False)
    bundle['fingerprint'] = fingerprint(bundle)
    return bundle


def vbench_metadata(bundle, dimension):
    """Explicit original prompts and exact paths; no name-based text inference."""
    if bundle['fingerprint'] != fingerprint({k: v for k, v in bundle.items() if k != 'fingerprint'}):
        raise ValueError('Frozen video/metric input bundle changed before scoring')
    if dimension not in bundle['dimensions'] or dimension == 'MUSIQ_LONGER512':
        raise ValueError('One frozen VBench dimension required; project MUSIQ has a separate scorer')
    groups = {}
    for row in bundle['rows']:
        if row['dimension'] != dimension or row['input_status'] != 'READY_TO_SCORE':
            continue
        group = groups.setdefault(row['prompt_id'], dict(prompt_en=row['prompt'],
                                    dimension=[dimension], video_list=[]))
        if row['video_path'] not in group['video_list']:
            group['video_list'].append(row['video_path'])
    return list(groups.values())


def summarize(bundle, score_rows, comparisons, *, bootstrap_repetitions=4096, bootstrap_seed=20261016):
    """Video scalar -> both seeds -> prompt equal. Missing values stay missing."""
    if bundle['fingerprint'] != fingerprint({k: v for k, v in bundle.items() if k != 'fingerprint'}):
        raise ValueError('Frozen video/metric input bundle changed')
    expected = {(r['case_id'], r['method'], r['dimension']): r for r in bundle['rows']}
    observed = {(r['case_id'], r['method'], r['dimension']): r for r in score_rows}
    if len(score_rows) != len(observed) or set(expected) != set(observed):
        raise ValueError('Keep the full registered metric matrix, not only successful scores')
    if (type(bootstrap_repetitions) is not int or bootstrap_repetitions < 1
            or len({tuple(p) for p in comparisons}) != len(comparisons)
            or any(len(p) != 2 or p[0] == p[1] or any(m not in bundle['methods'] for m in p) for p in comparisons)):
        raise ValueError('Explicit paired method comparisons and positive bootstrap count required')
    values, statuses = {}, []
    for key, planned in expected.items():
        actual = observed[key]
        status = actual['status']
        score = actual.get('value')
        if planned['input_status'] != 'READY_TO_SCORE':
            if status != planned['input_status'] or score is not None:
                raise ValueError('Unavailable or static-ineligible positions cannot become quality scores')
        elif status not in SCORER_STATES:
            raise ValueError('Explicit scorer failure/resource/not-reached state required')
        elif status == 'SCORED':
            for field in ('video_sha256', 'prompt_sha256', 'scorer_fingerprint'):
                if actual.get(field) != planned[field]:
                    raise ValueError('Metric score belongs to different video, prompt or evaluator')
            if actual.get('observed_sampling') != planned['expected_sampling']:
                raise ValueError('Metric frame selection must match the pinned source policy')
            if (not isinstance(score, (int, float)) or not math.isfinite(score)
                    or (isinstance(score, bool) and planned['dimension'] != 'dynamic_degree')):
                raise ValueError('Finite per-video raw metric scalar required')
            if planned['dimension'] == 'dynamic_degree' and score not in (0, 1):
                raise ValueError('Pinned dynamic-degree per-video output is a binary activity result')
            if planned['dimension'] == 'MUSIQ_LONGER512':
                frames = actual.get('frame_scores', [])
                if (len(frames) != 93 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                        or not math.isfinite(v) for v in frames)
                        or not math.isclose(mean(frames), score, rel_tol=1e-11, abs_tol=1e-12)):
                    raise ValueError('MUSIQ raw video mean must come from all93 original frame scores')
        elif score is not None:
            raise ValueError('Missing metric evidence cannot be zero-filled')
        values[key] = float(score) if status == 'SCORED' else None
        statuses.append(dict(case_id=key[0], method=key[1], dimension=key[2],
                             original_generation_status=planned['original_generation_status'], metric_status=status))
    cases = bundle['cases']
    prompts = sorted({c['prompt_id'] for c in cases})

    def eligible(prompt, dimension):
        return dimension != 'temporal_flickering' or next(c for c in cases if c['prompt_id'] == prompt)['static_eligible']

    def prompt_value(prompt, method, dimension):
        scores = [values[(c['id'], method, dimension)] for c in cases if c['prompt_id'] == prompt]
        return mean(scores) if all(v is not None for v in scores) else None

    methods, contrasts = [], []
    for dimension in bundle['dimensions']:
        cohort = [p for p in prompts if eligible(p, dimension)]
        for method in bundle['methods']:
            prompt_rows = [dict(prompt_id=p, eligible=eligible(p, dimension),
                value=prompt_value(p, method, dimension)) for p in prompts]
            complete = [r['value'] for r in prompt_rows if r['eligible'] and r['value'] is not None]
            methods.append(dict(method=method, dimension=dimension, role=dimension_role(dimension),
                registered_prompts=8, registered_seed_cases=16, eligible_prompts=len(cohort),
                complete_two_seed_prompts=len(complete), prompt_rows=prompt_rows,
                full_eligible_prompt_mean=mean(complete) if cohort and len(complete) == len(cohort) else None,
                available_complete_prompt_mean=mean(complete) if complete else None))
        for candidate, baseline in comparisons:
            pairs = []
            for prompt in cohort:
                a, b = prompt_value(prompt, candidate, dimension), prompt_value(prompt, baseline, dimension)
                if a is not None and b is not None:
                    pairs.append(dict(prompt_id=prompt, candidate=a, baseline=b, delta=a - b))
            rng = random.Random(bootstrap_seed)
            resamples = [mean(pairs[rng.randrange(len(pairs))]['delta'] for _ in pairs)
                         for _ in range(bootstrap_repetitions)] if pairs else []
            delta = mean(p['delta'] for p in pairs) if pairs else None
            contrasts.append(dict(candidate=candidate, baseline=baseline, dimension=dimension,
                role=dimension_role(dimension), registered_prompt_denominator=8,
                eligible_prompt_denominator=len(cohort), complete_paired_prompt_ids=[p['prompt_id'] for p in pairs],
                missing_eligible_prompt_ids=[p for p in cohort if p not in {v['prompt_id'] for v in pairs}],
                full_eligible_prompt_mean_delta=delta if cohort and len(pairs) == len(cohort) else None,
                available_cohort_mean_delta=delta,
                available_cohort_prompt_bootstrap95=interval(resamples) if resamples else None,
                cross_dimension_weighted_score=None,
                positive_delta_is_better_on_this_dimension=dimension != 'dynamic_degree'))
    return dict(status='IDENTITY_BOUND_DIMENSIONWISE_PROMPT_GROUPED_SUMMARY',
        input_bundle_fingerprint=bundle['fingerprint'], registered_generation_positions=160,
        registered_metric_positions=len(expected), metric_status_counts=dict(Counter(r['metric_status'] for r in statuses)),
        statuses=statuses, methods=methods, comparisons=contrasts,
        statistics=dict(unit='PROMPT_GROUP_AFTER_BOTH_SEEDS', bootstrap_repetitions=bootstrap_repetitions,
                        bootstrap_seed=bootstrap_seed),
        no_cross_dimension_total=True, not_full_official_VBench=True,
        no_physics_or_human_review_claim=True, scoring_cost_is_generation_latency=False)
