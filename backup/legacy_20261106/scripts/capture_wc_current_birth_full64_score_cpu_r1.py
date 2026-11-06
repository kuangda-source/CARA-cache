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


LAUNCH = Path('reports/wc_current_birth_full64_score_cpu_r1_launch_20261010.json')
PRIMARY = Path('reports/wc_current_birth_full64_r1_terminal_20261010_capture_and_independent_audit.json')
PREFIX = 'reports/wc_current_birth_full64_score_cpu_r1_terminal_20261010_'
SOURCE_REG = Path('manifests/wc_current_birth_full64_capture_source_r1_preregistration_20261010.json')

def check_complete(launch, objects, proof):
    from wc_current_birth_full64_independent_r1 import COUNTS, STRATEGIES, NAMES, METHODS, same, costs_from_runner, slots_from_pairing, reconstruct_summary
    reg, receipt = objects['registration'], objects['receipt']
    assert objects['launch'] == launch and reg['scope_counts'] == launch['planned_scope'] == COUNTS
    assert receipt['pid'] == launch['supervisor_pid'] and receipt['source_revision'] == launch['source_revision']
    assert receipt['original_launch'] == reg['original_launch'] and receipt['planned_scope'] == COUNTS
    assert receipt['GPU_submissions'] == 0 and not receipt['ledger_written']
    assert receipt['payload_after_sha256'] == reg['payload_sha256'] == proof['actual_payload_sha256']
    assert len(reg['payload_sha256']) == launch['payload_files']
    original_reg = subprocess.check_output(['git','show',launch['source_revision']+':manifests/wc_current_birth_full64_score_cpu_r1_preregistration_20261010.json'])
    assert hashlib.sha256(original_reg).hexdigest() == launch['registration_sha256'] and json.loads(original_reg) == reg
    for name, digest in reg['payload_sha256'].items():
        raw = subprocess.check_output(['git','show',launch['source_revision']+':'+name])
        assert hashlib.sha256(raw).hexdigest() == digest
    assert reg['maximum_pairs'] == 64 and reg['frames_per_pair'] == 93
    assert reg['sample_names'] == list(NAMES) and reg['strategies'] == list(STRATEGIES)
    if receipt.get('exit_code') != 0:
        return {'original_complete_scope_and_source_verified':True,'success':False,'partial_pairs_not_accepted_as_success':True}
    assert receipt['child_exit_code'] == 0 and receipt['status'] == 'CURRENT_BIRTH_FULL64_COMPLETE_ALL93_CPU_SCORING_EXIT0_NOT_METHOD_ACCEPTANCE'
    primary = json.loads(PRIMARY.read_text()); assert primary['independent_checks']['success']
    assert primary['run_id'] == reg['original_launch']['run_id']
    originals = {}
    for name in ('runner','CPU_result','supervisor','CPU_receipt','config'):
        item = primary['files'][name];raw = gzip.decompress(Path(item['local_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == item['sha256'] == proof['original_evidence_sha256'][name]
        originals[name] = json.loads(raw)
    result, runner, audit = objects['result'], originals['runner'], originals['CPU_result']
    assert result['status'] == 'CURRENT_BIRTH_FULL64_COMPLETE_AVAILABLE_ALL93_FIDELITY_NOT_CLEAN_SPEED'
    assert result['original_launch'] == reg['original_launch'] and result['original_scope'] == COUNTS
    assert result['original_runner_receipt_sha256'] == primary['files']['runner']['sha256']
    assert result['original_raw_audit_sha256'] == primary['files']['CPU_result']['sha256']
    assert not any(result[k] for k in ('CUDA_initialized','GPU_submissions','ledger_written',
        'new_generation','clean_speed_claim','physics_or_semantics_or_independent_confirmation_claim'))
    assert result['budget_before_sha256'] == result['budget_after_sha256'] == receipt['budget_before_scoring_sha256'] == receipt['budget_after_sha256']
    assert result['payload_sha256'] == reg['payload_sha256'] and result['complete_pairing'] == audit['pairing']
    costs = costs_from_runner(runner);same(result['complete_actual_costs'], costs)
    slots = slots_from_pairing(audit['pairing'])
    assert result['maximum_pairs'] == 64 and result['available_planned_pairs'] == sum(s['compatible'] for s in slots)
    assert result['incompatible_slots_retained'] == [s for s in slots if not s['compatible']]
    actual_videos = [{'path':s['video_artifact']['path'],'bytes':s['video_artifact']['bytes'],'sha256':s['video_artifact']['sha256']} for s in slots]
    actual_videos += [{k:r['artifact'][k] for k in ('path','bytes','sha256')} for r in runner['matched_Native_metadata']]
    assert proof['original_video_bindings'] == actual_videos
    resource = objects['metric_resource_receipt'];identity = result['actual_resource_identity']
    assert resource['status'] == 'LPIPS_ISOLATED_RESOURCE_AND_CPU_RUNTIME_PASS_NOT_VIDEO_SCORE'
    assert resource['exit_code'] == resource['GPU_submissions'] == 0 and resource['GPU_budget_unchanged']
    cpu = resource['CPU'];assert not cpu['CUDA_initialized'] and cpu['GPU_submissions'] == 0
    assert identity['server_receipt_sha256'] == proof['files']['metric_resource_receipt']['sha256']
    assert identity['source_sha256'] == resource['source_sha256'] == reg['payload_sha256']['src/wcomr/rv0_lpips.py']
    assert identity['protocol'] == cpu['protocol'] and result['metric_protocol'] == {k:v for k,v in cpu['protocol'].items() if k not in ('benefit','policy')}
    bindings = proof['metric_asset_sha256']
    assert bindings['metric_source'] == resource['source_sha256']
    assert bindings['wheel'] == identity['wheel_sha256'] == 'fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e'
    assert bindings['linear_weights'] == identity['LPIPS_linear_weight_sha256'] == 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
    assert bindings['backbone'] == identity['AlexNet_sha256'] == '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
    assert bindings['installed_source'] == identity['installed_source_sha256'] == cpu['installed_source_sha256']
    legacy_proof = objects['legacy_score_proof'];legacy = objects['legacy_score_result']
    assert legacy_proof['independent_checks']['success'] and legacy_proof['files']['result']['sha256'] == result['legacy_score_native_sha256']
    assert result['legacy_score_proof_sha256'] == proof['files']['legacy_score_proof']['sha256']
    assert proof['files']['legacy_score_result']['sha256'] == result['legacy_score_native_sha256']
    assert legacy['actual_resource_identity'] == identity
    expected = reconstruct_summary(result['pairs'], audit['pairing'], costs, legacy)
    same(result['summary'], expected)
    assert len(expected['registered_same_card_contrasts']) == 24 and len(expected['legacy_quality_only_contrasts']) == 48
    return {'success':True,'original_complete_scope_and_source_verified':True,
        'original64_method_slots_and_four_reference_slots_verified':True,
        'all_available_pairs_reconstructed':expected['scored_pairs'],
        'actual_all93_frame_distances_reconstructed':expected['actual_frame_distances'],
        'incompatible_pairs_retained':expected['incompatible_pairs_retained'],
        'all64_actual_costs_independently_reconstructed':True,
        'all24_same_card_and48_legacy_quality_only_contrasts_independently_reconstructed':True,
        'source_bound_pretrained_CPU_metric_resource_identity_verified':True,
        'harmful_frames_scene_equal_denominators_and_all_gaps_retained':True,
        'GPU_submissions':0,'ledger_written':False,'new_metric_execution':False,
        'physics_semantics_independent_confirmation_or_clean_speed_claim':False,
        'scene_equal_aggregates':expected['scene_equal_aggregates']}


def main():
    if not LAUNCH.exists():
        print(json.dumps({'status':'WAIT_ORIGINAL_FULL64_SCORE_LAUNCH_NO_CAPTURE_WRITTEN','GPU_submissions':0}));return 2
    reg=json.loads(SOURCE_REG.read_text())
    assert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in reg['source_sha256']}==reg['source_sha256']
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
original_files={'runner':out/'diagnostic/receipt.json','CPU_result':post/'result.json','supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','config':pathlib.Path(original['stage'])/'current-birth-full64-config.json'}
original_sha={k:sha(p) for k,p in original_files.items() if p.exists()}
videos=[];assets={}
if success:
 assert receipt['child_exit_code']==0 and sha(stage/'result.json')==receipt['result_sha256']
 for key in ('supervisor','CPU_receipt'):
  obj=json.loads(original_files[key].read_text());assert obj['exit_code']==0 and not any(pathlib.Path('/proc/'+str(obj[k])).exists() for k in ('pid','child_pid'))
 audit=json.loads(original_files['CPU_result'].read_text())
 runner=json.loads(original_files['runner'].read_text())
 for strategy in runner['completed_strategies']:
  for request in runner['batches'][strategy]['requests']:
   for row in request['paths']:
    v=row['video_artifact'];path=pathlib.Path(v['path']).resolve()
    assert path.is_relative_to((out/'diagnostic'/strategy).resolve()) and path.stat().st_size==v['bytes'] and sha(path)==v['sha256']
    videos.append({k:v[k] for k in ('path','bytes','sha256')})
 for ref in runner['matched_Native_metadata']:
  v=ref['artifact'];path=pathlib.Path(v['path']).resolve()
  assert path.is_relative_to((root/'outputs').resolve()) and path.stat().st_size==v['bytes'] and sha(path)==v['sha256']
  videos.append({k:v[k] for k in ('path','bytes','sha256')})
 resource=root/'.sync/wc-rv0-lpips-resource-v2';r=json.loads((resource/'receipt.json').read_text());cpu=r['CPU'];package=resource/'site/lpips'
 assets={'metric_source':sha(resource/'rv0_lpips.py'),'wheel':sha(resource/r['wheel']['filename']),
  'linear_weights':sha(package/'weights/v0.1/alex.pth'),
  'backbone':sha(pathlib.Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')),
  'installed_source':{n:sha(package/n) for n in cpu['installed_source_sha256']}}
files={'receipt':stage/'receipt.json','registration':stage/'score-preregistration.json','launch':stage/'launch.json','driver_log':stage/'driver.log'}
for key,path in [('result',stage/'result.json'),('score_log',stage/'score.log'),('metric_resource_receipt',root/'.sync/wc-rv0-lpips-resource-v2/receipt.json')]:
 if path.exists():files[key]=path
if success:
 legacy_proof_path=stage/reg['legacy_score_proof_ref'];legacy_proof=json.loads(legacy_proof_path.read_text())
 files['legacy_score_proof']=legacy_proof_path
 # Preserve the exact decompressed legacy score as native bytes in this local capture.
 files['legacy_score_result']=stage/legacy_proof['files']['result']['local_path']
native={}
for key,path in files.items():
 raw=path.read_bytes()
 if key=='legacy_score_result':raw=gzip.decompress(raw)
 compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
print(json.dumps({'capture':{'status':'CURRENT_BIRTH_FULL64_ALL93_CPU_SCORE_ORIGINAL_TERMINAL_CAPTURE' if success else 'CURRENT_BIRTH_FULL64_ALL93_CPU_SCORE_ORIGINAL_FAILURE_COMPLETE_SCOPE_RETAINED',
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
    proof['independent_capture_source_preregistration_sha256']=hashlib.sha256(SOURCE_REG.read_bytes()).hexdigest()
    # Preserve original bytes before a local assertion can fail. Never re-run
    # the completed metric just to repair a capture-side implementation error.
    for key, item in value['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True);raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        path = Path(PREFIX + key + '_native.gz');assert not path.exists();path.write_bytes(compressed)
        proof['files'][key] = {k: v for k, v in item.items() if k != 'gzip_base64'}
        proof['files'][key]['local_path'] = str(path)
        if item['path'].endswith('.json') or key=='legacy_score_result':objects[key] = json.loads(raw)
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
