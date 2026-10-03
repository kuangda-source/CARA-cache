#!/usr/bin/env python3
"""Predeclared fixed D/S encoded proxies; no Native or quality acceptance."""
import argparse
import importlib.util
import importlib.metadata
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('existing_pair_metrics',
    Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def analyze(audit, *, control_only=False):
    if control_only:
        assert audit['status'] == 'FIXED_DD_TWO_OUTPUT_AUDIT_PASS_FOUR_CARD_PENDING'
        assert len(audit['files']) == 2
        pairs = [base.pair(*audit['files'], 'human_199', diagnostic_control=True)]
    else:
        assert audit['status'] == 'FOUR_FIXED_OUTPUT_SOURCE_MASK_VIDEO_AND_COST_STRUCTURE_PASS_NOT_QUALITY'
        assert len(audit['files']) == 4 and audit['measurement_outputs'] == 2
        a, b = audit['measurement_files']
        assert a['kind'] == 'official' and b['kind'] == 'candidate'
        pairs = [base.pair(a, b, 'human_199')]
    return {'status':'FIXED_DD_ENCODED_CONTROL_PASS' if control_only else
        'EXPOSED_HUMAN_FIXED_DS_ENCODED_PROXIES_NOT_ACCEPTANCE',
        'CPU_only':True, 'planned_card_outputs':4, 'control_only':control_only,
        'metric_packages':{k:importlib.metadata.version(k) for k in ['numpy','scikit-image']},
        'pairs':pairs, 'quality_acceptance':False, 'semantic_or_physics_acceptance':False,
        'deployment_speed_claim':False, 'independent_confirmation':False,
        'limits':['One fixed offline38-deep mask on an exposed human/seed0 input.',
            'Encoded WC-relative fidelity and frame-change are descriptive, not Native/semantic/physical quality.',
            'Fixed schedule isolates the current common-action comparison; does not prove additive causal decomposition.',
            'Single light pair is descriptive timing, not a replicated speed result or quality-time frontier.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--control-only', action='store_true')
    args = p.parse_args()
    result = analyze(json.loads(args.audit.read_text()), control_only=args.control_only)
    result.update(input_audit_sha256=base.metrics.sha(args.audit),
        analysis_code_sha256=base.metrics.sha(Path(__file__)),
        reused_pair_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py')),
        reused_metric_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'], 'pairs':len(result['pairs']),
        'whole_video':[q['whole_video'] for q in result['pairs']]}))
