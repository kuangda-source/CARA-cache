#!/usr/bin/env python3
"""Fixed adjacent repeat pairs; encoded WC-relative proxies, not acceptance."""
import argparse
import importlib.metadata
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('existing_video_metrics',
    Path(__file__).with_name('analyze_wc_video_pairs_cpu.py'))
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def pair(left, right, sample, *, diagnostic_control=False):
    for file in (left, right):
        path = Path(file['path'])
        assert file['full93_decode'] and path.stat().st_size == file['bytes']
        assert metrics.sha(path) == file['sha256']
    with metrics.rgb_frames(left['path']) as l, metrics.rgb_frames(right['path']) as r:
        result = metrics.compare_frames(l, r, expected_frames=93)
    result.update(sample_name=sample, official_index=left['index'], candidate_index=right['index'],
        baseline_sha256=left['sha256'], candidate_sha256=right['sha256'], diagnostic_control=diagnostic_control)
    if diagnostic_control:
        whole = result['whole_video']
        assert left['sha256'] == right['sha256'] and whole['exact_RGB_equality']
        assert whole['mean_luma_SSIM_win7'] == 1 and whole['temporal_difference_MSE_0to1'] == 0
    return result


def analyze(audit, *, control_only=False):
    if control_only:
        assert audit['status'] == 'LIGHT_DD_TWO_OUTPUT_INDEPENDENT_AUDIT_PASS_TEN_CARD_PENDING'
        assert len(audit['files']) == 2
        a, b = audit['files']
        pairs = [pair(a, b, Path(a['path']).stem, diagnostic_control=True)]
    else:
        assert audit['status'] == 'TEN_LIGHT_OUTPUT_STRUCTURAL_DD_PROVENANCE_AND_TIMING_AUDIT_PASS_NOT_QUALITY'
        assert len(audit['files']) == 10 and audit['measurement_outputs'] == 8
        groups = audit['measurement_groups']
        assert len(groups) == 2
        pairs = []
        for group, sequence, indices in zip(groups,
                [['official', 'candidate', 'candidate', 'official'],
                 ['candidate', 'official', 'official', 'candidate']],
                [[(0, 1), (3, 2)], [(1, 0), (2, 3)]]):
            assert group['sequence'] == sequence and len(group['files']) == 4
            for left, right in indices:
                a, b = group['files'][left], group['files'][right]
                assert a['kind'] == 'official' and b['kind'] == 'candidate'
                pairs.append(pair(a, b, group['sample_name']))
    return {'status':'LIGHT_DD_ENCODED_METRIC_CONTROL_PASS' if control_only else
                'TWO_EXPOSED_CAL_FOUR_FIXED_REPEAT_PAIR_DIAGNOSTICS_NOT_ACCEPTANCE',
        'CPU_only':True, 'planned_card_outputs':10, 'control_only':control_only,
        'metric_packages':{k:importlib.metadata.version(k) for k in ['numpy','scikit-image']},
        'pairs':pairs, 'quality_acceptance':False, 'semantic_or_physics_acceptance':False,
        'deployment_speed_claim':False,
        'limits':['ABBA pairs0-1/3-2; BAAB pairs1-0/2-3 fixed by indices before this metric calculation; earlier CAL results were exposed, none selected by quality.',
            'Every successful measurement repeat included; same seed repetitions are not independent quality scenes.',
            'Encoded RGB reference is official WC, not native full computation.',
            'Frame-change proxy and SSIM/PSNR do not establish semantic or physical behavior.',
            'Exposed CAL inputs and first-use diagnostics cannot establish independent CONF.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--control-only', action='store_true')
    a = p.parse_args()
    result = analyze(json.loads(a.audit.read_text()), control_only=a.control_only)
    result.update(input_audit_sha256=metrics.sha(a.audit), analysis_code_sha256=metrics.sha(Path(__file__)),
        reused_metric_code_sha256=metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status':result['status'], 'pairs':len(result['pairs']),
        'whole_video':[q['whole_video'] for q in result['pairs']]}))
