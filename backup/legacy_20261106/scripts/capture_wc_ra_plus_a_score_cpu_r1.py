#!/usr/bin/env python3
"""Preserve original all93 CPU evidence and independently reconstruct its summary.

Read-only SSH; no dispatch, GPU access, ledger write or partial-success scoring.
The original whole-comparison capture must precede successful score acceptance.
"""
import base64
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess


LAUNCH = Path('reports/wc_ra_plus_a_score_cpu_r1_launch_20261010.json')
PRIMARY = Path('reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json')
PREFIX = 'reports/wc_ra_plus_a_score_cpu_r1_terminal_20261010_'
NAMES = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199', 'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191']
METHODS = ['WC', 'JOINT_NATIVE', 'RA', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE']


def same(actual, expected):
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys()
        for key in expected:
            same(actual[key], expected[key])
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected)
        for a, b in zip(actual, expected):
            same(a, b)
    elif isinstance(expected, float):
        assert type(actual) in (int, float) and math.isfinite(actual)
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    else:
        assert actual == expected


def check_complete(launch, objects, proof):
    reg, receipt = objects['registration'], objects['receipt']
    assert objects['launch'] == launch and reg['scope_counts'] == launch['planned_scope']
    assert receipt['pid'] == launch['supervisor_pid']
    assert receipt['source_revision'] == launch['source_revision']
    assert receipt['original_launch'] == reg['original_launch']
    assert receipt['planned_scope'] == reg['scope_counts']
    assert receipt['GPU_submissions'] == 0 and not receipt['ledger_written']
    assert receipt['payload_after_sha256'] == reg['payload_sha256'] == proof['actual_payload_sha256']
    assert len(reg['payload_sha256']) == launch['payload_files'] == 10
    original_reg = subprocess.check_output([
        'git', 'show', launch['source_revision'] + ':manifests/wc_ra_plus_a_score_cpu_r1_preregistration_20261010.json'])
    assert hashlib.sha256(original_reg).hexdigest() == launch['registration_sha256']
    assert json.loads(original_reg) == reg
    capture_source=subprocess.check_output(['git','show',launch['source_revision']+':'+reg['independent_capture_source_ref']])
    assert hashlib.sha256(capture_source).hexdigest()==reg['independent_capture_source_sha256']
    for name, digest in reg['payload_sha256'].items():
        raw = subprocess.check_output(['git', 'show', launch['source_revision'] + ':' + name])
        assert hashlib.sha256(raw).hexdigest() == digest
    if receipt.get('exit_code') != 0:
        return {'original_complete_scope_and_source_verified': True, 'success': False,
                'partial_pairs_not_accepted_as_success': True}
    assert receipt['child_exit_code'] == 0
    assert receipt['status'] == 'RA_PLUS_A_COMPLETE_ALL93_CPU_SCORING_EXIT0_NOT_METHOD_ACCEPTANCE'
    primary = json.loads(PRIMARY.read_text())
    assert primary['independent_checks']['success']
    assert primary['run_id'] == reg['original_launch']['run_id']
    originals = {}
    for name in ('runner', 'CPU_result', 'supervisor', 'CPU_receipt', 'config'):
        item = primary['files'][name]
        raw = gzip.decompress(Path(item['local_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == item['sha256'] == proof['original_evidence_sha256'][name]
        originals[name] = json.loads(raw)
    result, runner, audit = objects['result'], originals['runner'], originals['CPU_result']
    assert result['status'] == 'RA_PLUS_A_FULL_COMPARISON_COMPLETE_AVAILABLE_ALL93_FIDELITY_AND_COST_NOT_CLEAN_SPEED'
    assert result['original_launch'] == reg['original_launch']
    assert result['original_runner_receipt_sha256'] == primary['files']['runner']['sha256']
    assert result['original_raw_audit_sha256'] == primary['files']['CPU_result']['sha256']
    assert result['original_scope'] == reg['original_launch']['planned_scope']
    assert not any(result[k] for k in ('CUDA_initialized', 'GPU_submissions', 'ledger_written',
        'new_generation', 'clean_speed_claim', 'physics_or_semantics_or_independent_confirmation_claim'))
    assert result['budget_before_sha256'] == result['budget_after_sha256'] == receipt['budget_before_scoring_sha256']
    assert receipt['budget_after_sha256'] == result['budget_after_sha256']
    assert result['payload_sha256'] == reg['payload_sha256']
    refs = runner['comparison']['references']
    assert result['references'] == refs and [r['sample_name'] for r in refs] == NAMES
    costs = []
    for request, ref in zip(runner['comparison']['batch']['requests'], refs):
        assert request['sample_name'] == ref['sample_name']
        for row in request['paths']:
            costs.append({'sample_name': request['sample_name'], 'method': row['method'],
                'actions': row['actions'], 'complete_branch_calls': sum(a.count('D') for a in row['actions']),
                'instrumented_pipeline_wall_seconds': row['instrumented_pipeline_wall_seconds'],
                'extra_candidate_heads':row['A_readout']['extra_candidate_heads'] if row['A_readout'] else 0,
                'A_teacher_calls':row['A_readout']['teacher_calls'] if row['A_readout'] else 0,
                'A_extra_deep_blocks':row['A_readout']['extra_candidate_deep_blocks'] if row['A_readout'] else 0})
        costs.append({'sample_name': request['sample_name'], 'method': 'NATIVE', 'outcome': ref['outcome'],
            'complete_branch_calls': ref['block_counts']['full_calls'],
            'instrumented_pipeline_wall_seconds': ref['pipeline_wall_seconds']})
    assert result['original_method_actions_and_costs'] == audit['actual_method_actions_and_costs'] == costs
    assert [(c['sample_name'], c['method']) for c in costs] == [(n, m) for n in NAMES for m in METHODS + ['NATIVE']]
    resource = objects['metric_resource_receipt']
    identity = result['actual_resource_identity']
    assert resource['status'] == 'LPIPS_ISOLATED_RESOURCE_AND_CPU_RUNTIME_PASS_NOT_VIDEO_SCORE'
    assert resource['exit_code'] == resource['GPU_submissions'] == 0 and resource['GPU_budget_unchanged']
    cpu = resource['CPU']
    assert not cpu['CUDA_initialized'] and cpu['GPU_submissions'] == 0
    assert identity['server_receipt_sha256'] == proof['files']['metric_resource_receipt']['sha256']
    assert identity['source_sha256'] == resource['source_sha256'] == reg['payload_sha256']['src/wcomr/rv0_lpips.py']
    assert identity['protocol'] == cpu['protocol']
    assert result['metric_protocol'] == {k: v for k, v in cpu['protocol'].items() if k not in ('benefit', 'policy')}
    bindings = proof['metric_asset_sha256']
    assert bindings['metric_source'] == resource['source_sha256']
    assert bindings['wheel'] == identity['wheel_sha256'] == 'fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e'
    assert bindings['linear_weights'] == identity['LPIPS_linear_weight_sha256'] == 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
    assert bindings['backbone'] == identity['AlexNet_sha256'] == '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
    assert bindings['installed_source'] == identity['installed_source_sha256'] == cpu['installed_source_sha256']
    assert proof['original_video_bindings'] == [{k: v[k] for k in ('path', 'bytes', 'sha256')} for v in audit['videos']]
    available = [r['sample_name'] for r in refs if r['outcome'] == 'ACCEPTED']
    pairs = result['pairs']
    assert [(p['sample_name'], p['method']) for p in pairs] == [(n, m) for n in available for m in METHODS]
    assert len(pairs) == result['available_planned_pairs'] == 7 * len(available)
    assert result['maximum_pairs'] == 28
    assert [set(p) for p in pairs] == [set(q) | {'score', 'CPU_wall_seconds'} for q in audit['matched_fidelity_pairs']]
    rows = []
    actual_distances = 0
    for name in available:
        group = [p for p in pairs if p['sample_name'] == name]
        base = group[0]['score']
        for pair in group:
            original = next(q for q in audit['matched_fidelity_pairs'] if (q['sample_name'], q['method']) == (name, pair['method']))
            assert {k: pair[k] for k in original} == original
            score = pair['score']; values = score['frame_distances']
            assert score['frames'] == len(values) == len(score['pts']) == 93
            assert score['pts'] == base['pts'] and score['reference_sha256'] == pair['reference']['sha256']
            assert score['candidate_sha256'] == pair['candidate']['sha256']
            assert all(type(v) in (int, float) and math.isfinite(v) for v in values)
            pts = [Fraction(v) * Fraction(t) for v, t in score['pts']]
            assert all(b > a for a, b in zip(pts, pts[1:]))
            same(score['mean_LPIPS'], math.fsum(values) / 93)
            actual_distances += len(values)
            delta = [a - b for a, b in zip(base['frame_distances'], values)]
            ordered = sorted(delta)
            quantiles = {}
            for q in (0, .1, .25, .5, .75, .9, 1):
                position = 92 * q; lower = int(position); upper = math.ceil(position)
                quantiles[str(q)] = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
            bc = next(c for c in costs if (c['sample_name'], c['method']) == (name, 'WC'))
            c = next(c for c in costs if (c['sample_name'], c['method']) == (name, pair['method']))
            difference = base['mean_LPIPS'] - score['mean_LPIPS']
            time_difference = bc['instrumented_pipeline_wall_seconds'] - c['instrumented_pipeline_wall_seconds']
            rows.append({'sample_name': name, 'method': pair['method'], 'mean_LPIPS': score['mean_LPIPS'],
                'WC_minus_method_LPIPS': difference,
                'relative_fidelity_improvement_percent': 100 * difference / base['mean_LPIPS'] if base['mean_LPIPS'] > 0 else None,
                'improved_frames': sum(x > 0 for x in delta), 'degraded_frames': sum(x < 0 for x in delta),
                'tied_frames': sum(x == 0 for x in delta), 'frame_count': 93,
                'paired_difference_quantiles_type7': quantiles,
                'contiguous_frame_bin_means': [{'frames_0_based': [a, b], 'mean_WC_minus_method': math.fsum(delta[a:b + 1]) / 31}
                    for a, b in ((0, 30), (31, 61), (62, 92))],
                'complete_branch_calls': c['complete_branch_calls'],
                'instrumented_pipeline_wall_seconds': c['instrumented_pipeline_wall_seconds'],
                'WC_minus_method_instrumented_wall_seconds': time_difference,
                'descriptive_same_run_fidelity_and_instrumented_time_both_improve': difference > 0 and time_difference > 0,
                'clean_speed_claim': False, 'frames_are_independent_samples': False})
    aggregate = []
    for method in METHODS:
        own = [r for r in rows if r['method'] == method]
        delta = [r['WC_minus_method_LPIPS'] for r in own]
        aggregate.append({'method': method, 'matched_scenes': len(own),
            'scene_equal_mean_LPIPS': math.fsum(r['mean_LPIPS'] for r in own) / len(own) if own else None,
            'scene_equal_mean_WC_minus_method': math.fsum(delta) / len(delta) if delta else None,
            'scene_median_WC_minus_method': statistics.median(delta) if delta else None,
            'improved_scenes': sum(x > 0 for x in delta), 'degraded_scenes': sum(x < 0 for x in delta),
            'tied_scenes': sum(x == 0 for x in delta)})
    summary = {'per_scene_method': rows, 'scene_equal_aggregates': aggregate,
        'original_scenes': 4, 'original_method_paths': 28, 'original_reference_slots': 4,
        'accepted_reference_scenes': len(available), 'scored_pairs': len(pairs),
        'reference_gaps_or_rejections': [{'sample_name': r['sample_name'], 'outcome': r['outcome']} for r in refs if r['outcome'] != 'ACCEPTED'],
        'missing_scores_filled_with_zero': False, 'fidelity_not_semantic_physics_quality': True,
        'not_matched_time_or_call_count': True, 'clean_speed_claim': False,
        'development_exposure_not_independent_CONFIRMATION': True}
    # Independent reconstruction: do not call the production summary module.
    contrast_names = [('JOINT_NATIVE','WC'),('RA','WC')]
    contrast_names += [(m,'RA') for m in METHODS[3:]]
    contrast_names += [('W1_GLOBAL_1','BETA1_GLOBAL_1'),('W1_ONE_PHASE','BETA1_ONE_PHASE'),
                       ('W1_ONE_PHASE','W1_GLOBAL_1'),('BETA1_ONE_PHASE','BETA1_GLOBAL_1')]
    summary['registered_contrasts'] = []
    for candidate, baseline in contrast_names:
        per_scene = []
        for name in available:
            left = next(p for p in pairs if (p['sample_name'],p['method']) == (name,baseline))
            right = next(p for p in pairs if (p['sample_name'],p['method']) == (name,candidate))
            delta = [a-b for a,b in zip(left['score']['frame_distances'],right['score']['frame_distances'])]
            lc = next(c for c in costs if (c['sample_name'],c['method']) == (name,baseline))
            rc = next(c for c in costs if (c['sample_name'],c['method']) == (name,candidate))
            per_scene.append({'sample_name':name,
                'baseline_minus_candidate_LPIPS':left['score']['mean_LPIPS']-right['score']['mean_LPIPS'],
                'improved_frames':sum(x>0 for x in delta),'degraded_frames':sum(x<0 for x in delta),
                'tied_frames':sum(x==0 for x in delta),
                'baseline_minus_candidate_instrumented_seconds':lc['instrumented_pipeline_wall_seconds']-rc['instrumented_pipeline_wall_seconds'],
                'frames_are_independent_samples':False,'clean_speed_claim':False})
        summary['registered_contrasts'].append({'candidate':candidate,'baseline':baseline,'per_scene':per_scene,
            'scene_equal_mean_baseline_minus_candidate':math.fsum(r['baseline_minus_candidate_LPIPS'] for r in per_scene)/len(per_scene) if per_scene else None,
            'matched_scenes':len(per_scene),'development_not_confirmation':True})
    assert len(summary['registered_contrasts']) == 10
    same(result['summary'], summary)
    return {'success': True, 'original_complete_scope_and_source_verified': True,
        'original_28_paths_four_reference_slots_and_32_costs_verified': True,
        'accepted_reference_scenes': len(available), 'all_available_pairs_reconstructed': len(pairs),
        'actual_all93_frame_distances_reconstructed': actual_distances,
        'scene_frame_signs_quantiles_bins_costs_and_gaps_independently_reconstructed': True,
        'all_ten_registered_contrasts_independently_reconstructed': True,
        'source_bound_pretrained_CPU_metric_resource_identity_verified': True,
        'GPU_submissions': 0, 'ledger_written': False, 'new_metric_execution': False,
        'physics_semantics_independent_confirmation_or_clean_speed_claim': False,
        'scene_equal_aggregates': aggregate}


def main():
    launch = json.loads(LAUNCH.read_text())
    remote = 'L=' + repr(launch) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
receipt=json.loads((stage/'receipt.json').read_text());pids=[L['supervisor_pid'],receipt.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_SCORE_HANDLES_STILL_LIVE_NO_TERMINAL_CAPTURE','original_live_PIDs':live,'CPU_status':receipt['status'],'GPU_submissions':0},'native':{}}));raise SystemExit(0)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'score-preregistration.json').read_text());original=reg['original_launch'];out=root/'outputs'/original['run_id'];post=pathlib.Path(original['post_CPU_stage'])
assert receipt['pid']==L['supervisor_pid'] and receipt['source_revision']==L['source_revision'] and receipt['original_launch']==original
assert sha(stage/'score-preregistration.json')==L['registration_sha256'] and json.loads((stage/'launch.json').read_text())==L
payload={n:sha(stage/n) for n in reg['payload_sha256']};assert payload==reg['payload_sha256']==receipt['payload_after_sha256'] and len(payload)==L['payload_files']
success=receipt.get('exit_code')==0
original_files={'runner':out/'diagnostic/receipt.json','CPU_result':post/'result.json','supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','config':pathlib.Path(original['stage'])/'ra-plus-a-config.json'}
original_sha={k:sha(p) for k,p in original_files.items() if p.exists()}
videos=[];assets={}
if success:
 assert receipt['child_exit_code']==0 and sha(stage/'result.json')==receipt['result_sha256']
 for key in ('supervisor','CPU_receipt'):
  obj=json.loads(original_files[key].read_text());assert obj['exit_code']==0 and not any(pathlib.Path('/proc/'+str(obj[k])).exists() for k in ('pid','child_pid'))
 audit=json.loads(original_files['CPU_result'].read_text())
 for v in audit['videos']:
  path=pathlib.Path(v['path']);assert path.resolve().is_relative_to((out/'diagnostic').resolve()) and path.stat().st_size==v['bytes'] and sha(path)==v['sha256']
  videos.append({k:v[k] for k in ('path','bytes','sha256')})
 resource=root/'.sync/wc-rv0-lpips-resource-v2';r=json.loads((resource/'receipt.json').read_text());cpu=r['CPU'];package=resource/'site/lpips'
 assets={'metric_source':sha(resource/'rv0_lpips.py'),'wheel':sha(resource/r['wheel']['filename']),
  'linear_weights':sha(package/'weights/v0.1/alex.pth'),
  'backbone':sha(pathlib.Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')),
  'installed_source':{n:sha(package/n) for n in cpu['installed_source_sha256']}}
files={'receipt':stage/'receipt.json','registration':stage/'score-preregistration.json','launch':stage/'launch.json','driver_log':stage/'driver.log'}
for key,path in [('result',stage/'result.json'),('score_log',stage/'score.log'),('metric_resource_receipt',root/'.sync/wc-rv0-lpips-resource-v2/receipt.json')]:
 if path.exists():files[key]=path
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
print(json.dumps({'capture':{'status':'RA_PLUS_A_ALL93_CPU_SCORE_ORIGINAL_TERMINAL_CAPTURE' if success else 'RA_PLUS_A_ALL93_CPU_SCORE_ORIGINAL_FAILURE_COMPLETE_SCOPE_RETAINED',
 'observed_unix':time.time(),'original_score_PIDs_absent':[p for p in pids if p],'source_revision':L['source_revision'],'exit_code':receipt.get('exit_code'),
 'actual_payload_sha256':payload,'original_evidence_sha256':original_sha,'original_video_bindings':videos,'metric_asset_sha256':assets,
 'GPU_submissions':0,'ledger_written':False},'native':native}))
'''
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=remote, text=True, capture_output=True, timeout=55)
    if process.returncode:
        raise RuntimeError(process.stderr[-5000:])
    value = json.loads(process.stdout)
    if not value['native']:
        print(json.dumps(value['capture']));return 2
    target = Path(PREFIX + 'capture_and_independent_audit.json');assert not target.exists()
    proof = value['capture'];proof['files'] = {};objects = {}
    # Preserve original bytes before a local assertion can fail. Never re-run
    # the completed metric just to repair a capture-side implementation error.
    for key, item in value['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True);raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        path = Path(PREFIX + key + '_native.gz');assert not path.exists();path.write_bytes(compressed)
        proof['files'][key] = {k: v for k, v in item.items() if k != 'gzip_base64'}
        proof['files'][key]['local_path'] = str(path)
        if item['path'].endswith('.json'):objects[key] = json.loads(raw)
    try:
        proof['independent_checks'] = check_complete(launch, objects, proof)
    except BaseException as error:
        proof['independent_check_failure'] = {'type': type(error).__name__, 'error': str(error)}
        target.write_text(json.dumps(proof, indent=2) + '\n');raise
    target.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({k: v for k, v in proof.items() if k not in ('files', 'actual_payload_sha256',
        'original_video_bindings', 'metric_asset_sha256', 'original_evidence_sha256')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
