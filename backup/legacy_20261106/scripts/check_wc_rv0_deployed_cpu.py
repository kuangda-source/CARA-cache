#!/usr/bin/env python3
"""Validate the approved frozen W3 deployment on CPU using existing videos."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'view', 'stage', 'runtime', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    if args.output.exists() or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('New receipt identity and explicit CPU-only environment required')
    sys.path.insert(0, str(args.stage/'src'))
    started = time.time()
    config = json.loads((args.stage/'causal-config.json').read_text())
    protected = [args.project/'reports/budget.json',
                 args.project/'manifests/budget_authorization_20261004_wc_13gpuh.json']
    video_manifest = json.loads((args.stage/'existing-videos.json').read_text())
    protected += [Path(v['path']) for v in video_manifest]
    before = {str(p): sha(p) for p in protected}
    result = {'status': 'APPROVED_W3_DEPLOYMENT_CPU_STARTED',
              'source_revision': args.source_revision, 'server_stage': str(args.stage),
              'project_view': str(args.view), 'GPU_submissions': 0,
              'new_C_D_videos': 0, 'formal_RV_training_labels': 0,
              'CUDA_initialized': False, 'checks': {}, 'existing_video_checks': [],
              'protected_file_sha256_before': before,
              'validation_harness_sha256': sha(Path(__file__)),
              'started_unix': started, 'exit_code': None}

    def save():
        temporary = args.output.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        temporary.replace(args.output)

    def command(label, argv, timeout=150):
        tick = time.perf_counter()
        child = subprocess.run([sys.executable]+argv, capture_output=True, text=True,
                               cwd=args.runtime, env=os.environ.copy(), timeout=timeout)
        (args.stage/(label+'.log')).write_text(child.stdout+'\n'+child.stderr)
        result['checks'][label] = {'exit_code': child.returncode,
                                  'CPU_wall_seconds': time.perf_counter()-tick}
        save()
        if child.returncode:
            raise RuntimeError(label+': '+child.stderr[-2500:])
        return child.stdout

    save()
    try:
        from wcomr.rv0_execution import validate_config, validate_stage
        result['checks']['frozen_stage'] = validate_stage(args.view, args.stage, args.runtime, config)
        try:
            validate_config(config, selected=True)
        except ValueError:
            result['checks']['unselected_GPU_launch_refused'] = True
        else:
            raise AssertionError('CPU draft unexpectedly permitted GPU execution')
        for relative in config['payload_sha256']:
            if relative.endswith('.py'):
                ast.parse((args.stage/relative).read_text(), filename=relative)
        result['checks']['frozen_Python_syntax'] = True
        for entry in ['run_wc_rv0_causal.py', 'supervise_wc_rv0_causal.py',
                      'audit_wc_rv0_causal_terminal.py', 'analyze_wc_rv0_causal_lpips_cpu.py']:
            command('CLI_'+entry.removesuffix('.py'), [str(args.stage/'scripts'/entry), '--help'], 30)
        raw = command('actual_production_CPU_import', [str(args.stage/'scripts/run_wc_rv0_causal.py'),
            '--project', str(args.view), '--stage', str(args.stage), '--runtime', str(args.runtime),
            '--output', str(args.stage/config['run_id']/'never-created-GPU-output'), '--cpu-import-check'])
        result['checks']['actual_import_receipts'] = [json.loads(line) for line in raw.splitlines()
                                                     if line.startswith('{')]
        assert len(result['checks']['actual_import_receipts']) == 2
        assert all(v.get('CUDA_initialized', v.get('cuda_initialized')) is False
                   for v in result['checks']['actual_import_receipts'])
        contract = load(args.stage/'tests/check_rv0_execution_cpu.py', 'deployed_execution_contract')
        result['checks']['execution_contract'] = contract.run(args.view)
        resource_auditor = load(args.stage/'scripts/audit_wc_rv0_lpips_resource.py', 'deployed_resource_auditor')
        resource = resource_auditor.audit(args.project, args.project/config['lpips_resource_stage'],
                                         config['payload_sha256']['src/wcomr/rv0_lpips.py'])
        result['checks']['existing_LPIPS_resource_audit'] = resource
        sys.path.insert(0, str(args.project/config['lpips_resource_stage']/'site'))
        import torch
        assert not torch.cuda.is_initialized()

        def forbidden(*a, **k):
            raise RuntimeError('CPU validation forbids CUDA initialization and downloads')

        torch.cuda._lazy_init = forbidden
        torch.hub.download_url_to_file = forbidden
        torch.set_num_threads(2)
        import lpips
        from wcomr.rv0_lpips import PROTOCOL, score_pair, signed_diagnostic
        from wcomr.rv0_video_reader import decoded_video, probe_video
        assert PROTOCOL == resource['protocol']
        assert Path(lpips.__file__).resolve() == (args.project/config['lpips_resource_stage']/'site/lpips/__init__.py').resolve()
        model = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        assert all(p.device.type == 'cpu' for p in model.parameters())
        for video in video_manifest:
            tick = time.perf_counter()
            path = Path(video['path'])
            assert before[str(path)] == video['sha256']
            probe = probe_video(path)
            with decoded_video(path) as left, decoded_video(path) as right:
                score = score_pair(left, right, model, reference_sha256=video['sha256'],
                                   candidate_sha256=video['sha256'])
            assert score['frames'] == 93 and all(v == 0.0 for v in score['frame_distances'])
            result['existing_video_checks'].append({'sample': video['sample'], 'path': str(path),
                'encoded_sha256': video['sha256'], 'probe': probe, 'self_pair_score': score,
                'signed_self_diagnostic': signed_diagnostic(score, score),
                'CPU_wall_seconds': time.perf_counter()-tick,
                'existing_WC_video_self_check_not_Native_or_C_D_result': True})
            save()
        assert len(result['existing_video_checks']) == 2 and not torch.cuda.is_initialized()
        result['checks']['metric_packages'] = {'torch': torch.__version__, 'LPIPS_origin': lpips.__file__}
        result['checks']['FFmpeg_version'] = subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0]
        result['status'] = 'APPROVED_W3_FROZEN_DEPLOYMENT_ACTUAL_CPU_IMPORT_READER_LPIPS_PASS_NOT_GPU_RESULT'
        result['exit_code'] = 0
    except BaseException as error:
        result.update(status='TECH_BLOCKED_APPROVED_W3_CPU_DENOMINATORS_PRESERVED',
                      error_type=type(error).__name__, error=str(error), exit_code=1)
        raise
    finally:
        after = {str(p): sha(p) for p in protected}
        result['protected_file_sha256_after'] = after
        result['original_videos_budget_and_authorization_unchanged'] = before == after
        result['CUDA_initialized'] = bool('torch' in sys.modules and sys.modules['torch'].cuda.is_initialized())
        result['CPU_wall_seconds'] = time.time()-started
        result['ended_unix'] = time.time()
        if before != after or result['CUDA_initialized']:
            result['status'] = 'TECH_BLOCKED_CPU_SCOPE_OR_PROTECTED_FILE_CHANGED'
            result['exit_code'] = 1
        save()
    if result['exit_code'] != 0:
        raise RuntimeError(result['status'])
    print(json.dumps({'status': result['status'], 'CPU_wall_seconds': result['CPU_wall_seconds'],
                      'existing_complete_self_pairs': len(result['existing_video_checks']),
                      'CUDA_initialized': result['CUDA_initialized'], 'GPU_submissions': 0}), flush=True)


if __name__ == '__main__':
    main()
