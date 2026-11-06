#!/usr/bin/env python3
"""Read-only terminal failure audit and complete-row CPU scoring; original scope remains failed."""
import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'gpu-stage', 'post-stage', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--mode', choices=['audit', 'score'], required=True)
    args = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', TORCH_HOME='/home/gaokuangda/.cache/torch',
                      OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(args.gpu_stage/'src'))
    import wcomr
    wcomr.__path__.insert(0, str(args.post_stage/'src/wcomr'))
    from wcomr.rv0_small_execution import sha, validate_stage, reserve_budget, settle_budget, validate_preparation
    from wcomr.rv0_small_partial import partial_plan
    from wcomr.rv0_video_reader import probe_video, decoded_video
    manifest = json.loads((args.post_stage/'manifest.json').read_text())
    for name, digest in manifest['payload_sha256'].items():
        if sha(args.post_stage/name) != digest:
            raise ValueError('Postrun CPU source changed: '+name)
    config_path = args.gpu_stage/'small-config.json'
    config = json.loads(config_path.read_text())
    validate_stage(args.project, args.gpu_stage, args.project/'runtime', config, selected=True)
    output = args.project/'outputs'/config['run_id']
    sup_path = output/'supervisor.json'; raw_path = output/'diagnostic/receipt.json'
    sup, receipt = json.loads(sup_path.read_text()), json.loads(raw_path.read_text())
    budget_path = args.project/'reports/budget.json'; budget = json.loads(budget_path.read_text())
    original = {'supervisor': sup_path, 'runner': raw_path, 'budget': budget_path,
                'gpu_monitor': output/'gpu-monitor.jsonl', 'gpu_log': output/'small-cd.log'}
    for name, path in original.items():
        if sha(path) != manifest['original_terminal_sha256'][name]:
            raise ValueError('Original terminal receipt/log/ledger changed: '+name)
    if (sup['status'] != 'BOUNDED_TIMEOUT' or sup['exit_code'] != 124
            or sup['source_revision'] != args.expected_source or receipt['source_revision'] != args.expected_source
            or sup['config'] != config or sup['run_id'] != config['run_id']
            or sup['reserved_seconds'] != 3900 or sup['hard_wall_cap_exceeded'] is not False
            or not 0 < sup['wall_seconds'] <= 3900 or sup['budget_after'] != budget
            or budget['cap_gpu_hours'] != 24 or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Original bounded failure and actual settlement required')
    prepaid = reserve_budget(sup['budget_before'], config, sup['pid'])
    if settle_budget(prepaid, sup['budget_before'], config, sup['wall_seconds'], sup['pid']) != budget:
        raise ValueError('Actual failed-attempt cost reconstruction differs')
    pids = [sup['pid'], sup['child_pid'], receipt['pid']]
    if any(type(pid) is not int or pid <= 0 for pid in pids) or len(set(pids)) != 3 or any(Path('/proc/'+str(pid)).exists() for pid in pids):
        raise ValueError('Original GPU handles are not released')
    if (receipt['gpu_uuid'] != config['gpu_uuid'] or receipt['network_class'] not in [
            'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT',
            'cosmos_predict2._src.predict2.networks.minimal_v4_dit.MinimalV4DiT']):
        raise ValueError('Actual original GPU/dense network binding differs')
    with (args.project/'.sync/f1.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.mode == 'audit':
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True)
        memory = subprocess.check_output(['nvidia-smi', '-i', config['gpu_uuid'], '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
        if any(line.split(',')[0].strip() == config['gpu_uuid'] for line in apps.splitlines()) or int(memory[1]) > 1024:
            raise ValueError('Selected GPU not released at failure audit')
    plan = partial_plan(receipt, config)
    for item in plan['files']+plan['references']:
        path = Path(item['path'])
        if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError('Completed-row original artifact/reference changed')
    if args.output.exists():
        raise ValueError('Preserve CPU output identity')
    if args.mode == 'audit':
        videos = []
        for item in plan['files']+plan['references']:
            metadata = probe_video(item['path'])
            with decoded_video(item['path']) as frames:
                count = sum(1 for _ in frames)
            if count != 93:
                raise ValueError('Complete-row full93 video decode differs')
            videos.append({**item, 'probe': metadata, 'full93_decode': True})
        if len(list((output/'diagnostic').glob('**/*.mp4'))) != len(plan['files']):
            raise ValueError('Failure matrix does not account for all new encoded outputs')
        monitors = [json.loads(line) for line in (output/'gpu-monitor.jsonl').read_text().splitlines()]
        if not monitors or any(m['uuid'] != config['gpu_uuid'] or not set(m['pids']).issubset(set(pids)) for m in monitors):
            raise ValueError('Original monitor GPU/process source differs')
        result = {'status': 'BOUNDED_FAILED_CARD_COST_SOURCE_RELEASE_COMPLETE_ROW_AUDIT_NOT_FULL_CARD_OR_QUALITY',
                  'source_revision': args.expected_source, 'run_id': config['run_id'], 'plan': plan,
                  'runner_receipt_sha256': sha(raw_path), 'config_sha256': sha(config_path),
                  'budget': budget, 'gpu_wall_seconds': sup['wall_seconds'], 'original_pids': pids,
                  'original_pids_absent': True, 'global_lock_free': True, 'videos': videos,
                  'monitor_rows': len(monitors), 'monitor_peak_mib': max(m['memory_used_mib'] for m in monitors),
                  'GPU_submissions': 0, 'full_card_accepted': False, 'formal_RV_labels': 0}
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({'status': result['status'], 'matrix': plan['matrix'], 'videos': len(videos)})); return
    audit_path = args.post_stage/'terminal-audit.json'; audit = json.loads(audit_path.read_text())
    if (audit['status'] != 'BOUNDED_FAILED_CARD_COST_SOURCE_RELEASE_COMPLETE_ROW_AUDIT_NOT_FULL_CARD_OR_QUALITY'
            or audit['runner_receipt_sha256'] != sha(raw_path) or audit['config_sha256'] != sha(config_path)
            or audit['plan'] != plan or audit['budget'] != budget or not audit['original_pids_absent']):
        raise ValueError('Independent failed-card terminal audit required before CPU scoring')
    resource = validate_preparation(args.gpu_stage, config)['lpips_resource']
    site = args.project/config['lpips_resource_stage']/'site'; sys.path.insert(0, str(site))
    import torch
    if torch.cuda.is_initialized(): raise ValueError('No CUDA in failed-card CPU scoring')
    def forbidden(*a, **k): raise RuntimeError('CUDA/model downloads forbidden')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden; torch.set_num_threads(2)
    import lpips
    package = Path(lpips.__file__).parent
    if (package.resolve() != (site/'lpips').resolve() or importlib.metadata.version('lpips') != '0.1.4'
            or sha(package/'weights/v0.1/alex.pth') != resource['LPIPS_linear_weight_sha256']
            or sha(Path('/home/gaokuangda/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth')) != resource['AlexNet_sha256']):
        raise ValueError('Frozen isolated LPIPS resource differs')
    for name, digest in resource['installed_source_sha256'].items():
        if sha(package/name) != digest: raise ValueError('Metric source changed')
    from wcomr.rv0_lpips import PROTOCOL, score_pair, signed_diagnostic
    if PROTOCOL != resource['protocol'] or sha(args.gpu_stage/'src/wcomr/rv0_lpips.py') != resource['source_sha256']:
        raise ValueError('Frozen full-frame protocol differs')
    model = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
    for p in model.parameters(): p.requires_grad_(False)
    started = time.perf_counter()
    result = {'status': 'PARTIAL_CPU_SCORE_STARTED_NOT_FULL_CARD', 'protocol': PROTOCOL,
              'original_denominator': plan['original_denominator'], 'matrix': plan['matrix'],
              'pairs': [], 'signed_diagnostics': [], 'costs': plan['costs'],
              'full_card_accepted': False, 'budget_matched': False, 'formal_RV_training_labels': False,
              'physics_or_quality_noninferiority': False, 'GPU_submissions': 0,
              'terminal_audit_sha256': sha(audit_path), 'runner_receipt_sha256': sha(raw_path)}
    def save():
        p = args.output.with_suffix('.tmp'); p.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n'); p.replace(args.output)
    save()
    try:
        for pair in plan['pairs']:
            ref, candidate = pair['reference'], pair['candidate']
            with decoded_video(ref['path']) as left, decoded_video(candidate['path']) as right:
                score = score_pair(left, right, model, reference_sha256=ref['sha256'], candidate_sha256=candidate['sha256'])
            result['pairs'].append({**pair, 'score': score}); save()
        by = {(p['scene'], p['action']): p['score'] for p in result['pairs']}
        for row in result['matrix']:
            if row['status'] == 'COMPLETE_ROW_PENDING_METRIC':
                name = row['scene']; result['signed_diagnostics'].append({'scene': name, 'CFG_slot': row['CFG_slot'], **signed_diagnostic(by[name, 'C'], by[name, 'D'])})
                row['status'] = 'COMPLETE_ROW_DESCRIPTIVE_NATIVE_RELATIVE_DIAGNOSTIC'
        if torch.cuda.is_initialized(): raise ValueError('CPU metric created CUDA')
        result['status'] = 'FAILED_CARD_COMPLETED_ROW_ALL93_FRAME_DIAGNOSTICS_OTHER_SCENE_UNFINISHED_NOT_FULL_CARD'
    except BaseException as error:
        result.update(status='PARTIAL_CPU_METRIC_TECH_BLOCKED_DENOMINATOR_PRESERVED', error=str(error)); raise
    finally:
        result.update(CPU_wall_seconds=time.perf_counter()-started, CUDA_initialized=torch.cuda.is_initialized(),
                      analysis_code_sha256=sha(Path(__file__)), reader_code_sha256=sha(args.gpu_stage/'src/wcomr/rv0_video_reader.py'))
        save()
    print(json.dumps({'status': result['status'], 'pairs': len(result['pairs']), 'signed_diagnostics': result['signed_diagnostics']}))


if __name__ == '__main__': main()
