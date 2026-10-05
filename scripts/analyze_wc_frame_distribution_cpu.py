#!/usr/bin/env python3
"""Registered descriptive all-frame distributions from audited existing scores; no Torch."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

COMMON = 'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191'
HUMAN = 'human_199'
SCENES = [COMMON, HUMAN]
INPUTS = {
    'common': 'reports/wc_w3_small_cd_failed_card_lpips_cpu_20261005.json',
    'human': 'reports/wc_w3_small_human_lpips_cpu_20261005.json',
    'fair': 'reports/wc_existing_fair_w1_lpips_cpu_r1_20261004.json'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quantile(values, p):
    ordered = sorted(values); position = p*(len(ordered)-1)
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)


def validate_pair(pair):
    score = pair['score']; values = score['frame_distances']; pts = score['pts']
    if (score['frames'] != 93 or len(values) != 93 or len(pts) != 93
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or type(score['mean_LPIPS']) not in (int, float) or not math.isfinite(score['mean_LPIPS'])
            or not math.isclose(sum(values)/93, score['mean_LPIPS'], rel_tol=1e-12, abs_tol=1e-12)
            or score['reference_sha256'] != pair['reference']['sha256']
            or score['candidate_sha256'] != pair['candidate']['sha256']
            or len({tuple(p) for p in pts}) != 93):
        raise ValueError('Audited complete-frame loss, PTS, mean or artifact identity differs')
    return values


def compare(baseline, variant, *, bins):
    left, right = validate_pair(baseline), validate_pair(variant)
    if baseline['reference'] != variant['reference'] or baseline['score']['pts'] != variant['score']['pts']:
        raise ValueError('Paired Native artifact and complete timestamps must match')
    if bins != [[0, 30], [31, 61], [62, 92]]:
        raise ValueError('Preserve registered three contiguous31 frame bins')
    difference = [a-b for a, b in zip(left, right)]
    segments = []
    for lo, hi in bins:
        a, b, d = left[lo:hi+1], right[lo:hi+1], difference[lo:hi+1]
        segments.append({'frames_0_based': [lo, hi], 'frames': 31,
            'baseline_mean_LPIPS': sum(a)/31, 'variant_mean_LPIPS': sum(b)/31,
            'mean_baseline_minus_variant': sum(d)/31,
            'positive_frames': sum(v > 0 for v in d), 'negative_frames': sum(v < 0 for v in d)})
    return {'frames': 93, 'original_baseline_mean_LPIPS': baseline['score']['mean_LPIPS'],
        'original_variant_mean_LPIPS': variant['score']['mean_LPIPS'],
        'original_mean_baseline_minus_variant': baseline['score']['mean_LPIPS']-variant['score']['mean_LPIPS'],
        'mean_paired_difference': sum(difference)/93, 'bin_means': segments,
        'paired_difference_quantiles_type7': {str(p): quantile(difference, p) for p in [0, .1, .25, .5, .75, .9, 1]},
        'descriptive_positive_frame_fraction': sum(v > 0 for v in difference)/93,
        'positive_frames': sum(v > 0 for v in difference), 'negative_frames': sum(v < 0 for v in difference),
        'zero_frames': sum(v == 0 for v in difference),
        'baseline_mean_largest10_distances': sum(sorted(left, reverse=True)[:10])/10,
        'variant_mean_largest10_distances': sum(sorted(right, reverse=True)[:10])/10,
        'largest10_separately_selected_not_paired_frames': True,
        'baseline_artifact': baseline['candidate'], 'variant_artifact': variant['candidate'],
        'Native_reference': baseline['reference'], 'independent_unit': 'SCENE_NOT_FRAME_OR_REPEAT'}


def analyze(root, manifest):
    read = lambda n: json.loads((root/n).read_text())
    for name, digest in manifest['input_sha256'].items():
        if sha(root/name) != digest: raise ValueError('Frozen analysis input changed: '+name)
    registration = read(manifest['hypothesis_registry'])
    if sha(root/manifest['hypothesis_registry']) != manifest['hypothesis_registry_sha256']:
        raise ValueError('Original hypothesis registration changed')
    hypothesis = next(h for h in registration['hypotheses'] if h['id'] == manifest['hypothesis_id'])
    if (hypothesis['analysis']['contiguous_frame_bins_0_based'] != manifest['frame_bins_0_based']
            or manifest['quantile_definition'] != 'SORT_ASCENDING_TYPE7_LINEAR_INTERPOLATION_AT_P_TIMES_N_MINUS_1'
            or manifest['distribution_quantiles'] != [0, .1, .25, .5, .75, .9, 1]
            or manifest['new_GPU_seconds'] != 0 or manifest['new_generation'] is not False):
        raise ValueError('Registered descriptive analysis or CPU-only scope differs')
    common, human, wrapped = [read(INPUTS[k]) for k in ('common', 'human', 'fair')]
    fair = wrapped['result']
    common_audit = read('reports/wc_w3_small_cd_failed_card_lpips_cpu_audit_20261005.json')
    human_audit = read('reports/wc_w3_small_human_lpips_cpu_audit_20261005.json')
    fair_audit = read('reports/wc_existing_fair_w1_lpips_cpu_r1_audit_20261004.json')
    if (common['status'] != 'FAILED_CARD_COMPLETED_ROW_ALL93_FRAME_DIAGNOSTICS_OTHER_SCENE_UNFINISHED_NOT_FULL_CARD'
            or common['full_card_accepted'] is not False or len(common['pairs']) != 2
            or human['status'] != 'HUMAN_FULL93_FRAME_TWO_NATIVE_RELATIVE_LPIPS_AND1_SIGNED_DIAGNOSTIC_NOT_RV_LABELS'
            or len(human['pairs']) != 2 or wrapped['exit_code'] != 0
            or fair['status'] != 'EXISTING_FAIR_TEN_FULL93_LPIPS_CPU_PASS_NOT_METHOD_ACCEPTANCE'
            or len(fair['pairs']) != 10 or len(fair['W1_pairs']) != 2
            or any(x['GPU_submissions'] != 0 or x['CUDA_initialized'] is not False for x in (common, human, fair))
            or common_audit['score_original_sha256'] != manifest['input_sha256'][INPUTS['common']]
            or human_audit['score_original_sha256'] != manifest['input_sha256'][INPUTS['human']]
            or common_audit['status'] != 'FAILED_CARD_COMPLETED_ROW_FULL93_CPU_SCORE_ORIGINAL_AUDIT_PASS_NOT_FULL_CARD_OR_METHOD_GAIN'
            or human_audit['status'] != 'HUMAN_SCORE_ORIGINAL_NATIVE_SHA_PASS_NOT_METHOD_GAIN'
            or fair_audit['status'] != 'INDEPENDENT_EXISTING_FAIR_W1_LPIPS_CPU_FILE_AND_AGGREGATION_AUDIT_PASS'
            or hashlib.sha256((json.dumps(fair, indent=2)+'\n').encode()).hexdigest() != wrapped['result_sha256']
            or fair_audit['checked_server_file_sha256'].get(wrapped['directory']+'/result.json') != wrapped['result_sha256']
            or fair_audit['compatible_W1_pairs'] != 2 or fair_audit['frames_per_pair'] != 93):
        raise ValueError('Only the original accepted score rows and source audits can be analyzed')
    scope = read('configs/wc_w3_placement_scope_r1_draft.json'); rows = []
    for name, record, call, slot in [(COMMON, common, 45, 0), (HUMAN, human, 46, 1)]:
        pairs = record['pairs']; left, right = pairs
        if ([(p['scene'], p['action'], p['target_call'], p['CFG_slot']) for p in pairs]
                != [(name, 'C', call, slot), (name, 'D', call, slot)]
                or any(left['reference'][k] != scope['references'][name]['Native35'][k] for k in ('path', 'sha256'))):
            raise ValueError('Original C/D diagnostic identity differs')
        rows.append({'scene': name, 'comparison': 'W3_ONE_ACTION_ADAPTIVE_C_MINUS_D',
            'target_call': call, 'CFG_slot': slot, 'same_CFG_quota': False,
            **compare(left, right, bins=manifest['frame_bins_0_based'])})
    for name in SCENES:
        left = next(p for p in fair['pairs'] if p['sample'] == name and p['variant'] == 'wc006')
        right = next(p for p in fair['W1_pairs'] if p['sample'] == name)
        if (right['variant'] != 'W1_scalar' or right['matching_official_WC_sha256'] != left['candidate']['sha256']
                or any(left['reference'][k] != scope['references'][name]['Native35'][k] for k in ('path', 'sha256'))):
            raise ValueError('Existing reference-compatible W1/WC identity differs')
        rows.append({'scene': name, 'comparison': 'W1_WC006_MINUS_SCALAR',
                     **compare(left, right, bins=manifest['frame_bins_0_based'])})
    return {'status': 'REGISTERED_EXPLORATORY_FOUR_EXISTING_FULL93_DISTRIBUTIONS_COMPLETE',
        'hypothesis_id': manifest['hypothesis_id'], 'rows': rows, 'existing_comparisons': 4,
        'unique_exposed_scenes': 2, 'original_W1_denominator': manifest['original_W1_denominator'],
        'original_A_card_denominator_and_failure': common['original_denominator'], 'original_A_full_card_accepted': False,
        'B_new_comparisons': 0, 'B_four_pair_scope_changed': False,
        'old_means_or_criteria_modified': False, 'frame_level_pvalues_or_independence_claim': False,
        'new_GPU_seconds': 0, 'new_generation': False, 'new_human_review': False,
        'budget_sha256_before': manifest['input_sha256']['reports/budget.json'],
        'input_sha256': manifest['input_sha256'], 'registry_sha256': manifest['hypothesis_registry_sha256'],
        'metric': 'REUSE_AUDITED_CPU_FP32_FULL93_NATIVE_RELATIVE_LPIPS_ARRAYS_NO_RESCORE',
        'physics_or_semantic_or_speed_or_CONF_acceptance': False,
        'outcome_exposure': 'EXPLORATORY_AFTER_KNOWN_A_HUMAN_W1_MEANS'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'manifest', 'output']: parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise ValueError('Preserve prior analysis identity')
    start = time.perf_counter(); result = analyze(args.root, json.loads(args.manifest.read_text()))
    result.update(CPU_wall_seconds=time.perf_counter()-start, analysis_code_sha256=sha(__file__),
                  execution_manifest_sha256=sha(args.manifest))
    if sha(args.root/'reports/budget.json') != result['budget_sha256_before']:
        raise ValueError('CPU-only analysis cannot modify the budget')
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': result['status'], 'existing_comparisons': 4, 'new_GPU_seconds': 0}))
