#!/usr/bin/env python3
"""Judge returned CPU evidence locally against native remote hash observations.

This performs no remote operation, import of Torch, or file substitution. The
original files were hashed remotely by sha256sum; all reasoning stays local.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_wc_rv0_causal_cpu import audit_receipt

REMOTE = Path('/home/gaokuangda/data/gkd/worldcache_omr')
CAUSAL = REMOTE/'.sync/wc-rv0-causal-cpu-r3'
RESOURCE = REMOTE/'.sync/wc-rv0-lpips-resource-v2'
BACKBONE = Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def returned_original(path):
    body = json.loads(path.read_text())
    claimed = body.pop('server_receipt_sha256')
    assert sha((json.dumps(body, indent=2)+'\n').encode()) == claimed
    return body, claimed


def audit(project, native_path, metadata_path):
    proof = json.loads(native_path.read_text())
    assert proof['status'] == 'SERVER_NATIVE_READ_ONLY_HASHES_AND_PUBLIC_RELEASE_METADATA_PASS_NO_CODE_UPLOAD'
    assert proof['no_local_private_code_sent_or_executed_remotely'] is True
    assert proof['server_original_files_changed'] is proof['shared_environment_changed'] is False
    assert proof['GPU_submissions'] == 0 and math.isfinite(proof['observed_unix'])
    cpu_path = project/'reports/wc_rv0_causal_cpu_r3_20261004.json'
    cpu, cpu_sha = returned_original(cpu_path)
    resource, resource_sha = returned_original(project/'reports/wc_rv0_lpips_resource_cpu_v2_20261004.json')
    prior = json.loads((project/'reports/wc_rv0_frozen_restore_cpu_r4_20261004.json').read_text())
    budget_path = project/'reports/budget.json'
    budget = json.loads(budget_path.read_text())
    auth_path = project/budget['budget_authorization_ref']
    auth = json.loads(auth_path.read_text())
    assert budget['cap_gpu_hours'] == auth['cumulative_cap_gpu_hours'] == 13
    assert auth['source_user_text'] == '允许增加 GPUh'
    assert auth['user_message_id'] == 'Sentinel_861e63a87d8c819180ec9a8bcfa6dc92'
    assert auth['previous_cap_gpu_hours'] == 12 and auth['usage_reset'] is False
    assert not any(k.endswith('_inflight') for k in budget)
    lpips = resource['CPU']; wheel = resource['wheel']
    expected = {str(CAUSAL/'receipt.json'): cpu_sha,
        str(REMOTE/'.sync/wc-rv0-frozen-restore-cpu-r4/receipt.json'): prior['server_receipt_sha256'],
        str(RESOURCE/'receipt.json'): resource_sha,
        str(RESOURCE/'rv0_lpips.py'): sha((project/'src/wcomr/rv0_lpips.py').read_bytes()),
        str(RESOURCE/wheel['filename']): wheel['sha256'],
        str(RESOURCE/'site/lpips/weights/v0.1/alex.pth'): lpips['LPIPS_linear_weight_sha256'],
        str(BACKBONE): lpips['AlexNet_sha256'],
        str(REMOTE/'reports/budget.json'): sha(budget_path.read_bytes()),
        str(REMOTE/budget['budget_authorization_ref']): sha(auth_path.read_bytes())}
    expected.update({str(CAUSAL/n): h for n, h in cpu['payload_sha256'].items()})
    expected.update({str(REMOTE/'runtime'/n): h for n, h in cpu['upstream_sha256'].items()})
    expected.update({str(RESOURCE/'site/lpips'/n): h for n, h in lpips['installed_source_sha256'].items()})
    assert len(expected) == proof['verified_files'] == 62
    assert proof['expected_file_sha256'] == proof['observed_file_sha256'] == expected
    assert proof['GPU_budget_sha256'] == expected[str(REMOTE/'reports/budget.json')]
    metadata_bytes = metadata_path.read_bytes()
    assert sha(metadata_bytes) == proof['public_release_metadata_sha256']
    meta = json.loads(metadata_bytes)
    assert meta['info']['version'] == '0.1.4'
    assert 'richzhang/PerceptualSimilarity' in meta['info']['home_page']
    published = [w for w in meta['urls'] if w['filename'] == wheel['filename']]
    assert len(published) == 1
    assert wheel['filename'] == 'lpips-0.1.4-py3-none-any.whl'
    assert published[0]['digests']['sha256'] == wheel['sha256'] == 'fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e'
    assert published[0]['size'] == wheel['bytes'] == 53763
    assert resource['status'] == 'LPIPS_ISOLATED_RESOURCE_AND_CPU_RUNTIME_PASS_NOT_VIDEO_SCORE'
    assert resource['exit_code'] == 0 and resource['GPU_budget_unchanged'] is True
    assert resource['shared_environment_changed'] is False and resource['GPU_submissions'] == 0
    assert resource['source_sha256'] == lpips['source_sha256'] == expected[str(RESOURCE/'rv0_lpips.py')]
    assert resource['server_stage'] == str(RESOURCE)
    assert lpips['status'] == 'ACTUAL_LPIPS_PRETRAINED_CPU_RUNTIME_NORMALIZATION_REPEAT_REFUSALS_PASS_NOT_VIDEO_SCORE'
    assert lpips['package_origin'] == str(RESOURCE/'site/lpips/__init__.py')
    assert set(lpips['installed_source_sha256']) == {'__init__.py', 'lpips.py', 'pretrained_networks.py', 'trainer.py'}
    assert lpips['package_version'] == '0.1.4' and lpips['CUDA_initialized'] is False
    assert lpips['AlexNet_sha256'] == '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
    assert lpips['LPIPS_linear_weight_sha256'] == 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
    assert lpips['GPU_submissions'] == lpips['real_C_D_video_scores'] == lpips['formal_RV_training_labels'] == 0
    protocol = lpips['protocol']
    assert (protocol['package_version'], protocol['metric_version'], protocol['backbone'], protocol['device']) == ('0.1.4', '0.1', 'alex', 'cpu')
    assert protocol['precision'] == 'torch.float32' and protocol['spatial'] is False
    assert protocol['RGB_input'] == 'UINT8_HWC_TO_NCHW_MINUS1_TO_PLUS1'
    assert protocol['aggregation'] == 'ARITHMETIC_MEAN_ALL93_FRAME_DISTANCES'
    assert protocol['reference'] == 'MATCHED_NATIVE_FULL35_SAME_REQUEST_NOISE_DECODE'
    assert protocol['benefit'] == 'J_C_MINUS_J_D_NEGATIVE_VALUES_RETAINED'
    assert protocol['policy'] == 'ONE_ACTION_ADAPTIVE_DIAGNOSTIC_NOT_BUDGET_MATCHED'
    assert protocol['expected_frames'] == 93 and protocol['expected_HWC'] == [432, 768, 3]
    assert protocol['resize_crop_subsample'] is False
    assert protocol['formal_RV_training_labels'] is protocol['physics_or_quality_noninferiority'] is False
    checks = lpips['synthetic_checks']
    assert checks['frames'] == 4 and checks['HWC'] == [64, 64, 3]
    assert checks['self'] == 0 and checks['repeat_exact'] is True and checks['refusals'] == 4
    assert math.isfinite(checks['different']) and checks['different'] > 0
    assert checks['negative_retained'] == -checks['different']
    historical = resource['budget_before']
    assert historical['cap_gpu_hours'] == 12
    assert all(budget[k] == historical[k] for k in ['used_gpu_hours', 'gpu_jobs_launched'])
    assert math.isfinite(resource['CPU_and_resource_wall_seconds']) and resource['CPU_and_resource_wall_seconds'] > 0
    common = {'method': 'LOCAL_JUDGMENT_WITH_REMOTE_NATIVE_HASHES_NO_PRIVATE_CODE_UPLOAD',
        'native_hash_audit_ref': str(native_path.relative_to(project)),
        'native_hash_audit_sha256': sha(native_path.read_bytes()),
        'native_observed_unix': proof['observed_unix'], 'remote_original_and_stage_files_rechecked': True,
        'no_Torch_import_in_auditor': True, 'GPU_submissions': 0,
        'no_local_private_code_sent_or_executed_remotely': True,
        'production_actual_host_CPU_check_complete': False, 'budget': budget}
    causal = audit_receipt(project, cpu_path)
    causal.update(common)
    resource_audit = {'status': 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE',
        'server_receipt_sha256': resource_sha, 'source_sha256': resource['source_sha256'],
        'wheel_sha256': wheel['sha256'], 'installed_source_sha256': lpips['installed_source_sha256'],
        'AlexNet_sha256': lpips['AlexNet_sha256'], 'LPIPS_linear_weight_sha256': lpips['LPIPS_linear_weight_sha256'],
        'CPU_and_resource_wall_seconds': resource['CPU_and_resource_wall_seconds'],
        'synthetic_checks': checks, 'protocol': protocol, 'real_C_D_video_scores': 0,
        'formal_RV_training_labels': 0, 'public_release_metadata_sha256': sha(metadata_bytes),
        'published_wheel': {'filename': wheel['filename'], 'sha256': wheel['sha256'], 'bytes': wheel['bytes']},
        'wheel_size_evidence': 'PUBLISHED_SIZE_PLUS_IDENTICAL_REMOTE_WHEEL_SHA_NOT_NEW_REMOTE_STAT', **common}
    return causal, resource_audit


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--native-hashes', type=Path, required=True)
    p.add_argument('--public-metadata', type=Path, required=True)
    p.add_argument('--causal-output', type=Path, required=True)
    p.add_argument('--resource-output', type=Path, required=True)
    args = p.parse_args()
    assert not args.causal_output.exists() and not args.resource_output.exists()
    outputs = audit(args.project, args.native_hashes, args.public_metadata)
    for path, result in zip([args.causal_output, args.resource_output], outputs):
        path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': 'LOCAL_NATIVE_HASH_BOUND_CPU_AND_LPIPS_AUDITS_PASS',
        'verified_remote_files': 62, 'GPU_submissions': 0, 'private_code_uploads': 0}))
