"""Read-only pretrained LPIPS identity, independent of historical GPU budgets."""
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(resource, expected_metric_sha):
    resource=Path(resource)
    raw=(resource/'receipt.json').read_bytes();r=json.loads(raw);cpu=r['CPU']
    if (r['status']!='LPIPS_ISOLATED_RESOURCE_AND_CPU_RUNTIME_PASS_NOT_VIDEO_SCORE'
            or r['exit_code']!=0 or not r['GPU_budget_unchanged'] or r['shared_environment_changed']
            or r['GPU_submissions']!=0 or cpu['CUDA_initialized'] or cpu['GPU_submissions']!=0
            or cpu['status']!='ACTUAL_LPIPS_PRETRAINED_CPU_RUNTIME_NORMALIZATION_REPEAT_REFUSALS_PASS_NOT_VIDEO_SCORE'
            or r['source_sha256']!=cpu['source_sha256'] or r['source_sha256']!=expected_metric_sha
            or sha(resource/'rv0_lpips.py')!=expected_metric_sha):
        raise ValueError('Original isolated CPU metric receipt/source differs')
    wheel=r['wheel'];published=json.loads((resource/'pypi-release.json').read_text())
    if (wheel['filename']!='lpips-0.1.4-py3-none-any.whl' or wheel['bytes']!=53763
            or wheel['sha256']!='fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e'
            or sha(resource/wheel['filename'])!=wheel['sha256']
            or (resource/wheel['filename']).stat().st_size!=wheel['bytes']
            or published['info']['version']!='0.1.4'
            or 'richzhang/PerceptualSimilarity' not in published['info']['home_page']):
        raise ValueError('Original LPIPS wheel/published identity differs')
    hits=[w for w in published['urls'] if w['filename']==wheel['filename']]
    if len(hits)!=1 or hits[0]['digests']['sha256']!=wheel['sha256']:
        raise ValueError('Original published wheel checksum differs')
    package=resource/'site/lpips'
    if (Path(cpu['package_origin']).resolve()!=(package/'__init__.py').resolve()
            or cpu['package_version']!='0.1.4'
            or set(cpu['installed_source_sha256'])!={'__init__.py','lpips.py','pretrained_networks.py','trainer.py'}):
        raise ValueError('Actual isolated LPIPS package origin differs')
    for n,v in cpu['installed_source_sha256'].items():
        if sha(package/n)!=v:raise ValueError('Actual isolated LPIPS source changed: '+n)
    backbone=Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')
    if (cpu['LPIPS_linear_weight_sha256']!=sha(package/'weights/v0.1/alex.pth')
            or cpu['LPIPS_linear_weight_sha256']!='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
            or cpu['AlexNet_sha256']!=sha(backbone)
            or cpu['AlexNet_sha256']!='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'):
        raise ValueError('Actual pretrained metric/backbone weights differ')
    p=cpu['protocol'];s=cpu['synthetic_checks']
    if (p['package_version']!='0.1.4' or p['metric_version']!='0.1' or p['backbone']!='alex'
            or p['device']!='cpu' or p['precision']!='torch.float32' or p['spatial']
            or p['expected_frames']!=93 or p['expected_HWC']!=[432,768,3]
            or p['resize_crop_subsample'] or p['formal_RV_training_labels'] or p['physics_or_quality_noninferiority']
            or s['frames']!=4 or s['HWC']!=[64,64,3] or s['self']!=0 or not s['repeat_exact']
            or s['refusals']!=4 or not math.isfinite(s['different']) or s['different']<=0
            or s['negative_retained']!=-s['different']):
        raise ValueError('Original metric protocol/actual CPU controls differ')
    # Budget stability described resource creation; it is not a requirement that
    # every later experiment retain the old number of submissions or cap.
    return {'status':'ACTUAL_LPIPS_PRETRAINED_RESOURCE_IDENTITY_PASS_NO_HISTORY_BUDGET_GATE',
        'server_receipt_sha256':hashlib.sha256(raw).hexdigest(),'source_sha256':expected_metric_sha,
        'installed_source_sha256':cpu['installed_source_sha256'],'protocol':p,
        'wheel_sha256':wheel['sha256'],'LPIPS_linear_weight_sha256':cpu['LPIPS_linear_weight_sha256'],
        'AlexNet_sha256':cpu['AlexNet_sha256'],'historical_CPU_controls_reused':s,
        'GPU_submissions':0,'current_GPU_ledger_read_or_written':False}
