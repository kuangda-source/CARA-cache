#!/usr/bin/env python3
"""Bound old exposed adaptive-S versus current fixed-S; no causal attribution."""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('pair_metrics',
    Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def analyze(old, new, old_audit, new_audit, old_deploy, new_deploy):
    assert old_audit['status'] == 'TEN_LIGHT_OUTPUT_STRUCTURAL_DD_PROVENANCE_AND_TIMING_AUDIT_PASS_NOT_QUALITY'
    assert new_audit['status'] == 'FOUR_FIXED_OUTPUT_SOURCE_MASK_VIDEO_AND_COST_STRUCTURE_PASS_NOT_QUALITY'
    assert old_deploy['source_revision'] == '7bec5f84ac6eee1289780a574f86972d1d19f3af'
    assert new_deploy['source_revision'] == '4bd8951aa660cafe6f95a0173714134c6e386e52'
    keys = ('f1_setup_sha256', 'cal_config_sha256', 'upstream_source_sha256',
        'request_lifecycle_source_sha256', 'unipc_source_sha256', 'mode_policy',
        'policy', 'dense_fallback_layers', 'deployment_sparse', 'pv_skipping')
    for k in keys:
        assert old['scope'][k] == new['scope'][k], k
    shared = ('profile-config.json', 'configs/f1_setup.json', 'configs/cal_w1d8.jsonl',
        'manifests/wc_h0_eval_mode_contract_20261003.json', 'scripts/run_wc_s0_profile.py',
        'src/wcomr/decoder_policy.py', 'src/wcomr/light_sampling.py',
        'src/wcomr/h0_mode.py', 'src/wcomr/sparge_no_pv.py', 'src/wcomr/sparge_routed_no_pv.py')
    for k in shared:
        assert old_deploy['payload_sha256'][k] == new_deploy['payload_sha256'][k], k
    assert old['wc_settings'] == new['wc_settings']
    index = old['scope']['sample_names'].index('human_199')
    assert old['reference_contexts'][index][1:] == new['reference_context'][1:]
    request = old['measurements']['requests'][index]
    group = old_audit['measurement_groups'][index]
    assert group['sample_name'] == request['sample_name'] == 'human_199'
    old_d = [p for p in request['phases'] if p['kind'] == 'official']
    old_s = [p for p in request['phases'] if p['kind'] == 'candidate']
    assert len(old_d) == len(old_s) == 2
    assert old_d[0]['sampling'] == old_s[0]['sampling'] == new['measurement']['phases'][0]['sampling']
    assert old_d[0]['trace'] == old_d[1]['trace'] and old_s[0]['trace'] == old_s[1]['trace']
    assert [p['deep_executed'] for p in old_d[0]['trace']] == new['fixed_mask']['dense_calls']
    old_df = [p for p in group['files'] if p['kind'] == 'official']
    old_sf = [p for p in group['files'] if p['kind'] == 'candidate']
    new_d, new_s = new_audit['measurement_files']
    assert old_df[0]['sha256'] == old_df[1]['sha256'] == new_d['sha256']
    assert old_sf[0]['sha256'] == old_sf[1]['sha256']
    for f in old_df + old_sf + [new_d, new_s]:
        assert f['full93_decode'] and base.metrics.sha(Path(f['path'])) == f['sha256']
    pair = base.pair(old_sf[0], new_s, 'human_199')
    pair['comparison'] = 'exposed_adaptive_S_as_reference_vs_current_fixed_S'
    fixed_trace = new['measurement']['phases'][1]['trace']
    diffs = [i+1 for i,(a,b) in enumerate(zip(old_s[0]['trace'], fixed_trace))
        if a['deep_executed'] != b['deep_executed']]
    return {'status':'EXPOSED_ADAPTIVE_FIXED_PROTOCOL_AND_REFERENCE_BINDING_PASS_DESCRIPTIVE_ONLY',
        'shared_config_keys':list(keys), 'shared_payload_sha256':{k:new_deploy['payload_sha256'][k] for k in shared},
        'reference_D_SHA_equal':True, 'reference_D_sha256':new_d['sha256'],
        'adaptive_S_sha256':old_sf[0]['sha256'], 'fixed_S_sha256':new_s['sha256'],
        'adaptive_S_deep_CFG_calls':sum(p['deep_executed'] for p in old_s[0]['trace']),
        'fixed_S_deep_CFG_calls':sum(p['deep_executed'] for p in fixed_trace),
        'adaptive_vs_fixed_deep_decision_differences':diffs, 'pairs':[pair],
        'CPU_only':True, 'new_GPU_submission':False, 'quality_acceptance':False,
        'same_refresh_compute_budget':False, 'causal_additive_decomposition':False,
        'independent_confirmation':False,
        'limits':['Shared source/assets configuration and exact dense video reference permit exposed development comparison.',
            'Adaptive35 and fixed38 deep calls differ; this cross-run pair is not a matched compute budget or timing comparison.',
            'Nonlinear latent/cache feedback prevents an additive decomposition of sparse versus scheduling error.',
            'No Native full-compute, semantic/physics quality or CONF acceptance.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('old-receipt','new-receipt','old-audit','new-audit','old-deployment','new-deployment','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert base.metrics.sha(a.old_receipt) == '29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae'
    inputs={k:json.loads(getattr(a,k).read_text()) for k in ('old_receipt','new_receipt','old_audit','new_audit','old_deployment','new_deployment')}
    assert base.metrics.sha(a.new_receipt) == inputs['new_audit']['receipt_sha256']
    assert base.metrics.sha(a.old_receipt) == inputs['old_audit']['receipt_sha256']
    r=analyze(inputs['old_receipt'],inputs['new_receipt'],inputs['old_audit'],inputs['new_audit'],inputs['old_deployment'],inputs['new_deployment'])
    r.update(input_sha256={k:base.metrics.sha(getattr(a,k)) for k in inputs},analysis_code_sha256=base.metrics.sha(Path(__file__)),
        reused_pair_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py')),
        reused_metric_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'whole_video':r['pairs'][0]['whole_video']}))
