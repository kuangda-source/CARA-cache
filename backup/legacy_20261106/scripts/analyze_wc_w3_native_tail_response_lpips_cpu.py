#!/usr/bin/env python3
"""Three reused and two new full93 Native losses;two signed native-tail policy effects."""
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
    from wcomr.rv0_native_tail_execution import sha, validate_config, validate_stage
    from wcomr.rv0_native_tail_evaluation import evaluation_plan, audit_trajectories
    from wcomr.rv0_video_reader import decoded_video, probe_video
    config = json.loads((args.stage/'tail-config.json').read_text())
    validate_config(config, selected=True)
    terminal = json.loads(args.terminal_audit.read_text())
    if (terminal['status'] != 'NATIVE_TAIL_SOURCE_COST_RELEASE_AND6_NEW_4_REFERENCE_VIDEO_AUDIT_PASS_NOT_QUALITY'
            or terminal['run_id'] != config['run_id']
            or terminal['runner_receipt_sha256'] != sha(args.receipt)
            or terminal['config_sha256'] != sha(args.stage/'tail-config.json')
            or terminal['original_pids_absent'] is not True or terminal['global_lock_free'] is not True
            or terminal['budget'] != json.loads((args.project/'reports/budget.json').read_text())):
        raise ValueError('Independent full terminal/source/cost/release audit required')
    validate_stage(args.project, args.stage, args.project/'runtime', config, selected=True)
    base = json.loads((args.stage/'placement-config.json').read_text())
    from wcomr.rv0_placement_v2_execution import validate_preparation
    resource = validate_preparation(args.stage, base)['lpips_resource']
    receipt = json.loads(args.receipt.read_text())
    plan = evaluation_plan(receipt, config)
    audit_trajectories(receipt, config, 26)
    def verify_files():
        for item in plan['files']+plan['references']:
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
    from wcomr.rv0_lpips import PROTOCOL, score_pair
    if PROTOCOL != resource['protocol'] or sha(args.stage/'src/wcomr/rv0_lpips.py') != resource['source_sha256']:
        raise ValueError('Actual frozen full-frame LPIPS protocol differs')
    from wcomr.rv0_native_tail_scores import POLICY, reused_losses, signed_tail_diagnostics
    started = time.perf_counter()
    result = {'status': 'CPU_SCORING_STARTED', 'metric_protocol': {k: v for k, v in PROTOCOL.items() if k not in {'benefit', 'policy', 'formal_RV_training_labels', 'physics_or_quality_noninferiority'}}, 'reused_resource_protocol_not_placement_policy': PROTOCOL, 'policy_protocol': POLICY, 'pairs': [], 'bridges': [],
              'planned_new_outputs': 6, 'planned_existing_references': 4, 'planned_Native_relative_losses': 5, 'planned_signed_diagnostics': 2,
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
        result['videos'] = [{**item, 'probe': probe_video(item['path'])} for item in plan['files']+plan['references']]
        for left_item, right_item in plan['bridges']:
            bridge = {'reference':left_item, 'candidate':right_item, 'scene':'human_199'}
            if bridge['reference']['sha256'] != bridge['candidate']['sha256']:
                raise ValueError('OFF decode bridge changed')
            result['bridges'].append({'scene': bridge['scene'], 'encoded_SHA_identical': True,
                'source_pts_identical': probe_video(bridge['reference']['path']) == probe_video(bridge['candidate']['path'])})
            if result['bridges'][-1]['source_pts_identical'] is not True:
                raise ValueError('OFF bridge source timestamps differ')
        prior_path = args.stage/config['prior_score_ref']
        if sha(prior_path) != config['prior_score_sha256']:
            raise ValueError('Frozen actual prior score changed')
        prior = json.loads(prior_path.read_text())
        result['pairs'] = reused_losses(prior, {'row':receipt['requests'][0]}, config, result['metric_protocol'])
        result['prior_score_sha256'] = sha(prior_path)
        result['reused_existing_loss_count'] = 3
        for pair in plan['pairs']:
            reference, candidate = pair['reference'], pair['candidate']
            with decoded_video(reference['path']) as left, decoded_video(candidate['path']) as right:
                score = score_pair(left, right, model, reference_sha256=reference['sha256'],
                                   candidate_sha256=candidate['sha256'])
            result['pairs'].append({**pair, 'score': score}); save()
        result['signed_diagnostics'] = signed_tail_diagnostics(result['pairs'], receipt, config)
        result['measured_branch_costs'] = [{'scene': row['sample_name'],
            'inclusive_parent_with_controls_wall_seconds': row['inclusive_parent_wall_seconds'],
            'snapshot_storage': row['snapshot_storage'],
            'suffixes': [{'label': child['label'], 'swap_calls': child['swap_calls'],
                'full_calls_per_CFG': [sum(v > 0 for v in child['deep'][slot::2]) for slot in (0, 1)],
                'control_inclusive_wall_seconds': child['record']['control_wall_seconds']}
                for child in row['children']],
            'decode_guardrail_encode': [{'label': child['label'],
                'wall_seconds': child['decode_guardrail_encode_wall_seconds']} for child in row['decoded_children']],
            'diagnostic_cost_not_clean_speed_or_same_seconds': True} for row in receipt['requests']]
        verify_files()
        if torch.cuda.is_initialized() or len(result['pairs']) != 5 or len(result['signed_diagnostics']) != 2:
            raise ValueError('Complete CPU placement evaluation denominator differs')
        result['status'] = 'NATIVE_TAIL_FULL93_FIVE_LOSSES_THREE_REUSED_TWO_NEW_AND2_SIGNED_POLICY_EFFECTS_NOT_RV_LABELS'
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
