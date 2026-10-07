#!/usr/bin/env python3
"""Read-only native-tail trajectories,six new videos,four references,cost and release audit."""
import argparse
import fcntl
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-source', required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.stage/'src'))
    from wcomr.rv0_native_onset_execution import sha, validate_config, validate_stage, audit_settlement
    from wcomr.rv0_native_onset_evaluation import evaluation_plan, audit_trajectories
    from wcomr.rv0_video_reader import probe_video, decoded_video
    config = json.loads((args.stage/'onset-config.json').read_text()); validate_config(config, selected=True)
    output = args.project/'outputs'/config['run_id']
    supervisor = json.loads((output/'supervisor.json').read_text())
    path = output/'diagnostic/receipt.json'; receipt = json.loads(path.read_text())
    budget = json.loads((args.project/'reports/budget.json').read_text())
    pids = audit_settlement(supervisor, receipt, config, budget, args.expected_source)
    assert 'cleanup_error' not in receipt and receipt['network_class'] in [
        'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT',
        'cosmos_predict2._src.predict2.networks.minimal_v4_dit.MinimalV4DiT']
    assert not any(Path('/proc/'+str(pid)).exists() for pid in pids)
    with (args.project/'.sync/f1.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stage_check = validate_stage(args.project, args.stage, args.project/'runtime', config, selected=True)
    runner = importlib.util.spec_from_file_location('causal_source_and_assets', args.stage/'scripts/run_wc_w3_native_response_onset.py')
    module = importlib.util.module_from_spec(runner); runner.loader.exec_module(module)
    module.validate(args.project, args.stage, args.project/'runtime', output/'diagnostic')
    plan = evaluation_plan(receipt, config); trajectories = audit_trajectories(receipt, config, 26)
    videos = []
    for item in plan['files']+plan['references']:
        video = Path(item['path'])
        assert video.stat().st_size == item['bytes'] and sha(video) == item['sha256']
        metadata = probe_video(video)
        with decoded_video(video) as frames: decoded = sum(1 for _ in frames)
        assert decoded == 93
        videos.append({**item, 'full93_decode': True, 'probe': metadata})
    assert len(list((output/'diagnostic').glob('**/*.mp4'))) == 6
    monitors = [json.loads(line) for line in (output/'gpu-monitor.jsonl').read_text().splitlines()]
    assert monitors and all(row['uuid'] == config['gpu_uuid'] and set(row['pids']).issubset(set(pids)) for row in monitors)
    release = supervisor['release']
    assert release['uuid'] == config['gpu_uuid'] and not release['pids'] and release['memory_used_mib'] <= 1024
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True, timeout=5)
    assert not any(line.split(',')[0].strip() == config['gpu_uuid'] for line in apps.splitlines())
    gpu = subprocess.check_output(['nvidia-smi', '-i', config['gpu_uuid'], '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=5).strip().split(',')
    assert gpu[0].strip() == config['gpu_uuid'] and int(gpu[1]) <= 1024
    result = {'status': 'NATIVE_RESPONSE_ONSET_SOURCE_COST_RELEASE_AND6_NEW_4_REFERENCE_VIDEO_AUDIT_PASS_NOT_QUALITY',
        'run_id': config['run_id'], 'source_revision': args.expected_source, 'observed_unix': time.time(),
        'runner_receipt_sha256': sha(path), 'config_sha256': sha(args.stage/'onset-config.json'),
        'original_pids_absent': True, 'original_pids': pids, 'global_lock_free': True, 'budget': budget,
        'gpu_wall_seconds': supervisor['wall_seconds'], 'GPU_submissions': 0, 'RV_labels': 0,
        'stage_check': stage_check, 'trajectories': trajectories, 'videos': videos,
        'monitor_rows': len(monitors), 'monitor_peak_mib': max(row['memory_used_mib'] for row in monitors),
        'full_RV0_acceptance': False, 'quality_or_physics_acceptance': False,
        'audit_code_sha256': sha(Path(__file__))}
    if args.output.exists(): raise ValueError('Preserve original terminal audit identity')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'videos': len(videos), 'gpu_wall_seconds': result['gpu_wall_seconds']}))


if __name__ == '__main__': main()
