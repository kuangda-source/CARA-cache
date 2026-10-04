#!/usr/bin/env python3
"""All eight C/D full-video losses to matched Native; signed diagnostics only."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'receipt', 'terminal-audit', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve existing scoring identity; no overwrite')
    os.environ.update(CUDA_VISIBLE_DEVICES='', TORCH_HOME='/home/gaokuangda/.cache/torch',
                      OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(args.stage/'src'))
    from wcomr.rv0_execution import sha, validate_config, validate_preparation_audits
    from wcomr.rv0_evaluation_plan import evaluation_plan
    from wcomr.rv0_video_reader import decoded_video, probe_video
    config = json.loads((args.stage/'causal-config.json').read_text())
    validate_config(config, selected=True)
    terminal = json.loads(args.terminal_audit.read_text())
    if (terminal['status'] != 'FULL_CAUSAL_SOURCE_FULL_COST_RELEASE_AND18_VIDEO_AUDIT_PASS_NOT_QUALITY'
            or terminal['run_id'] != config['run_id']
            or terminal['runner_receipt_sha256'] != sha(args.receipt)
            or terminal['config_sha256'] != sha(args.stage/'causal-config.json')
            or terminal['original_pids_absent'] is not True or terminal['global_lock_free'] is not True
            or terminal['budget'] != json.loads((args.project/'reports/budget.json').read_text())):
        raise ValueError('Independent full terminal/source/cost/release audit required')
    records = validate_preparation_audits(args.project, config)
    resource = records['lpips_resource_original']
    receipt = json.loads(args.receipt.read_text())
    plan = evaluation_plan(receipt, config)
    def verify_files():
        for item in plan['files']:
            path = Path(item['path'])
            if not path.is_file() or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
                raise ValueError('Original complete encoded artifact changed')
    verify_files()
    site = args.project/config['lpips_resource_stage']/'site'
    sys.path.insert(0, str(site))
    import torch
    if torch.cuda.is_initialized():
        raise ValueError('CPU evaluation unexpectedly initialized CUDA')
    def forbidden(*a, **k): raise RuntimeError('No CUDA or model downloads in full-video CPU scoring')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    import lpips
    package = Path(lpips.__file__).parent
    if (importlib.metadata.version('lpips') != '0.1.4'
            or package.resolve() != (site/'lpips').resolve()
            or sha(package/'weights/v0.1/alex.pth') != resource['LPIPS_linear_weight_sha256']
            or sha(Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')) != resource['AlexNet_sha256']):
        raise ValueError('Frozen isolated LPIPS package/backbone differs')
    for name, digest in resource['installed_source_sha256'].items():
        if sha(package/name) != digest:
            raise ValueError('Isolated metric code changed')
    from wcomr.rv0_lpips import PROTOCOL, score_pair, signed_diagnostic
    if PROTOCOL != resource['protocol'] or sha(args.stage/'src/wcomr/rv0_lpips.py') != resource['source_sha256']:
        raise ValueError('Actual frozen full-frame LPIPS protocol differs')
    started = time.perf_counter()
    result = {'status': 'CPU_SCORING_STARTED', 'protocol': PROTOCOL, 'pairs': [], 'bridges': [],
              'planned_outputs': 18, 'planned_C_D_pairs_to_Native': 8, 'planned_signed_diagnostics': 4,
              'runner_receipt_sha256': sha(args.receipt), 'terminal_audit_sha256': sha(args.terminal_audit),
              'formal_RV_training_labels': False, 'budget_matched': False,
              'physics_or_quality_noninferiority': False, 'GPU_submissions': 0}
    def save():
        temporary = args.output.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n'); temporary.replace(args.output)
    save()
    try:
        model = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
        for parameter in model.parameters(): parameter.requires_grad_(False)
        result['videos'] = [{**item, 'probe': probe_video(item['path'])} for item in plan['files']]
        for bridge in plan['bridges']:
            if bridge['reference']['sha256'] != bridge['candidate']['sha256']:
                raise ValueError('OFF decode bridge changed')
            result['bridges'].append({'scene': bridge['scene'], 'encoded_SHA_identical': True,
                'source_pts_identical': probe_video(bridge['reference']['path']) == probe_video(bridge['candidate']['path'])})
            if result['bridges'][-1]['source_pts_identical'] is not True:
                raise ValueError('OFF bridge source timestamps differ')
        for pair in plan['pairs']:
            reference, candidate = pair['reference'], pair['candidate']
            with decoded_video(reference['path']) as left, decoded_video(candidate['path']) as right:
                score = score_pair(left, right, model, reference_sha256=reference['sha256'],
                                   candidate_sha256=candidate['sha256'])
            result['pairs'].append({**pair, 'score': score}); save()
        by = {(p['scene'], p['CFG_slot'], p['action']): p['score'] for p in result['pairs']}
        result['signed_diagnostics'] = [{'scene': name, 'CFG_slot': slot,
            **signed_diagnostic(by[name, slot, 'C'], by[name, slot, 'D'])}
            for name in config['sample_names'] for slot in (0, 1)]
        verify_files()
        if torch.cuda.is_initialized() or len(result['pairs']) != 8 or len(result['signed_diagnostics']) != 4:
            raise ValueError('Complete CPU evaluation/C-D denominator differs')
        result['status'] = 'FULL93_FRAME_EIGHT_NATIVE_RELATIVE_LPIPS_AND4_SIGNED_DIAGNOSTICS_NOT_RV_LABELS'
    except BaseException as error:
        result.update(status='TECH_BLOCKED_COMPLETE_LPIPS_DENOMINATORS_PRESERVED',
                      error_type=type(error).__name__, error=str(error)); raise
    finally:
        result['CPU_wall_seconds'] = time.perf_counter()-started
        result['CUDA_initialized'] = torch.cuda.is_initialized()
        result['metric_packages'] = {n: importlib.metadata.version(n) for n in ['torch', 'numpy', 'lpips']}
        for program in ['ffmpeg', 'ffprobe']:
            try:
                result[program+'_version'] = subprocess.check_output([program, '-version'], text=True, timeout=5).splitlines()[0]
            except Exception as error:
                result[program+'_version'] = {'status': 'UNKNOWN', 'error': str(error)}
        result['analysis_code_sha256'] = sha(Path(__file__))
        result['reader_code_sha256'] = sha(args.stage/'src/wcomr/rv0_video_reader.py')
        save()
    print(json.dumps({'status': result['status'], 'pairs': len(result['pairs']),
                      'signed_diagnostics': len(result['signed_diagnostics'])}))


if __name__ == '__main__': main()
