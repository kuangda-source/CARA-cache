#!/usr/bin/env python3
"""Read-only audit of isolated pretrained LPIPS CPU resources; no Torch."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def audit(root, stage, expected_source):
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    raw = (stage/'receipt.json').read_bytes()
    result = json.loads(raw)
    assert result['status'] == 'LPIPS_ISOLATED_RESOURCE_AND_CPU_RUNTIME_PASS_NOT_VIDEO_SCORE'
    assert result['exit_code'] == 0 and result['GPU_budget_unchanged'] is True
    assert result['shared_environment_changed'] is False and result['GPU_submissions'] == 0
    assert result['source_sha256'] == expected_source == sha(stage/'rv0_lpips.py')
    wheel = result['wheel']
    assert wheel['filename'] == 'lpips-0.1.4-py3-none-any.whl'
    assert wheel['sha256'] == 'fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e'
    assert sha(stage/wheel['filename']) == wheel['sha256']
    assert (stage/wheel['filename']).stat().st_size == wheel['bytes'] == 53763
    metadata = json.loads((stage/'pypi-release.json').read_text())
    assert metadata['info']['version'] == '0.1.4'
    assert 'richzhang/PerceptualSimilarity' in metadata['info']['home_page']
    published = [w for w in metadata['urls'] if w['filename'] == wheel['filename']]
    assert len(published) == 1 and published[0]['digests']['sha256'] == wheel['sha256']
    cpu = result['CPU']
    assert cpu['status'] == 'ACTUAL_LPIPS_PRETRAINED_CPU_RUNTIME_NORMALIZATION_REPEAT_REFUSALS_PASS_NOT_VIDEO_SCORE'
    assert cpu['source_sha256'] == expected_source and cpu['package_version'] == '0.1.4'
    package = stage/'site/lpips'
    assert Path(cpu['package_origin']).resolve() == (package/'__init__.py').resolve()
    assert set(cpu['installed_source_sha256']) == {'__init__.py', 'lpips.py', 'pretrained_networks.py', 'trainer.py'}
    for name, digest in cpu['installed_source_sha256'].items():
        assert sha(package/name) == digest
    assert cpu['LPIPS_linear_weight_sha256'] == sha(package/'weights/v0.1/alex.pth') == 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
    backbone = Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')
    assert cpu['AlexNet_sha256'] == sha(backbone) == '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
    assert cpu['CUDA_initialized'] is False
    assert cpu['GPU_submissions'] == cpu['real_C_D_video_scores'] == cpu['formal_RV_training_labels'] == 0
    protocol = cpu['protocol']
    assert (protocol['package_version'], protocol['metric_version'], protocol['backbone'], protocol['device']) == ('0.1.4', '0.1', 'alex', 'cpu')
    assert protocol['precision'] == 'torch.float32' and protocol['spatial'] is False
    assert protocol['expected_frames'] == 93 and protocol['expected_HWC'] == [432, 768, 3]
    assert protocol['resize_crop_subsample'] is False
    assert protocol['formal_RV_training_labels'] is protocol['physics_or_quality_noninferiority'] is False
    checks = cpu['synthetic_checks']
    assert checks['frames'] == 4 and checks['HWC'] == [64, 64, 3]
    assert checks['self'] == 0 and checks['repeat_exact'] is True and checks['refusals'] == 4
    assert math.isfinite(checks['different']) and checks['different'] > 0
    assert checks['negative_retained'] == -checks['different']
    budget = json.loads((root/'reports/budget.json').read_text())
    historical_budget = result['budget_before']
    assert historical_budget['cap_gpu_hours'] == 12
    assert all(budget[k] == historical_budget[k] for k in ['used_gpu_hours', 'gpu_jobs_launched'])
    if budget != historical_budget:
        authorization = json.loads((root/budget['budget_authorization_ref']).read_text())
        assert authorization['source_user_text'] == '允许增加 GPUh'
        assert authorization['user_message_id'] == 'Sentinel_861e63a87d8c819180ec9a8bcfa6dc92'
        assert authorization['cumulative_cap_gpu_hours'] == budget['cap_gpu_hours'] == 13
        assert authorization['previous_cap_gpu_hours'] == 12 and authorization['usage_reset'] is False
    assert not any(k.endswith('_inflight') for k in budget)
    return {'status': 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE',
            'server_receipt_sha256': hashlib.sha256(raw).hexdigest(),
            'source_sha256': expected_source, 'wheel_sha256': wheel['sha256'],
            'installed_source_sha256': cpu['installed_source_sha256'],
            'AlexNet_sha256': cpu['AlexNet_sha256'],
            'LPIPS_linear_weight_sha256': cpu['LPIPS_linear_weight_sha256'],
            'CPU_and_resource_wall_seconds': result['CPU_and_resource_wall_seconds'],
            'synthetic_checks': checks, 'protocol': protocol, 'budget': budget,
            'no_Torch_import_in_auditor': True, 'GPU_submissions': 0,
            'real_C_D_video_scores': 0, 'formal_RV_training_labels': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.project, args.stage, args.source_sha)))
