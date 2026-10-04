#!/usr/bin/env python3
"""Read-only full causal trajectories,18videos,source,cost and release audit."""
import argparse
import fcntl
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time

TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']
PIPELINE = ['decode_input', 'decode_output', 'guardrail_input', 'guardrail_output', 'save_input']
LABELS = ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']


def audit_trajectories(receipt, deep_count):
    if type(deep_count) is not int or deep_count <= 0:
        raise ValueError('Actual positive deep block count required')
    assert len(receipt['requests']) == 2 and all(len(r['parents']) == 4 for r in receipt['requests'])
    for request in receipt['requests']:
        for row in request['parents']:
            for name in TRACE:
                assert len(row[name]) == (36 if name == 'solver_outputs' else 72)
            assert row['flags_before'] == row['flags_after'] and row['prepare_calls'] == 1
            assert row['final_latent_sha256'] == row['sample_return_sha256']
            assert [e['stage'] for e in row['pipeline']] == PIPELINE
        a, b, c, d = request['parents']
        assert a['deep'] == b['deep'] == [deep_count]*72
        for left, right in [(a, b), (c, d)]:
            for name in TRACE+['final_latent_sha256', 'final_components', 'pipeline', 'RNG_after']:
                assert left[name] == right[name]
            assert left['artifact']['sha256'] == right['artifact']['sha256']
        by = {(v['slot'], v['label']): v for v in d['children']}
        assert len(by) == 12
        for slot in (0, 1):
            off = by[slot, 'OFF1']
            for name in TRACE:
                assert off[name] == d[name][22 if name == 'solver_outputs' else 44:]
            assert off['final_latent_sha256'] == d['final_latent_sha256']
            assert off['record']['final_state_components'] == d['final_components']
            for first, second in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
                left, right = by[slot, first], by[slot, second]
                for name in TRACE+['final_latent_sha256']:
                    assert left[name] == right[name]
                assert left['record']['final_state_components'] == right['record']['final_state_components']
            cached, refreshed = by[slot, 'C_first'], by[slot, 'D_first']
            assert cached['inputs'][:slot+1] == refreshed['inputs'][:slot+1]
            assert cached['deep'][slot] == 0 and refreshed['deep'][slot] == deep_count
            for label in LABELS:
                child = by[slot, label]; record = child['record']; report = record['action_report']
                assert child['status'] == 'COMPLETE_SUFFIX_NOT_RV_LABEL' and record['parent_restored'] is True
                assert (record['completed_updates'], record['planned_remaining_updates']) == (22, 14)
                assert record['final_latent_sha256'] == child['final_latent_sha256']
                assert record['counterfactual_label'] is report['budget_matched'] is report['RV_label'] is False
                for name in TRACE:
                    assert len(child[name]) == (14 if name == 'solver_outputs' else 28)
                events = report['suffix_events']
                assert len(events) == 28 and [e['call'] for e in events] == list(range(45, 73))
                assert [e['cfg_slot'] for e in events] == [i % 2 for i in range(28)]
                assert events[slot]['paid_probe'] and all(not e['current_deep_truth_used'] for e in events)
                action = 'OFF' if label.startswith('OFF') else label[0]
                assert child['action'] == report['plan']['action'] == action
                assert (report['plan']['target_call'], report['plan']['cfg_slot']) == (45+slot, slot)
                assert report['decision_interventions'] == int(action != 'OFF')
                assert report['remaining_policy'] == 'ORIGINAL_WC_ADAPTIVE'
                if action != 'OFF':
                    target = events[slot]
                    assert target['requested'] == target['actual_action'] == action
                    assert 1 <= target['age_solver_steps'] <= 32
                    assert (target['true_full_history'][slot][-1] == 23) == (action == 'D')
                    if action == 'C': assert all(t < 23 for t in target['true_full_history'][slot])
        decoded = {v['label']: v for v in d['decoded_children']}
        for child in decoded.values():
            assert child['flags_before'] == child['flags_after']
            assert [e['stage'] for e in child['pipeline']] == PIPELINE
        assert decoded['0_OFF1']['pipeline'] == d['pipeline']
        assert decoded['0_OFF1']['artifact']['sha256'] == d['artifact']['sha256']
    return {'parents': 8, 'complete_suffixes': 24, 'encoded_outputs': 18,
            'current_C_deep': 0, 'current_D_deep': deep_count, 'formal_RV_training_labels': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-source', required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.stage/'src'))
    from wcomr.rv0_execution import sha, validate_config, validate_stage, settle_budget
    from wcomr.rv0_evaluation_plan import evaluation_plan
    from wcomr.rv0_video_reader import probe_video, decoded_video
    config = json.loads((args.stage/'causal-config.json').read_text()); validate_config(config, selected=True)
    output = args.project/'outputs'/config['run_id']
    supervisor = json.loads((output/'supervisor.json').read_text())
    path = output/'diagnostic/receipt.json'; receipt = json.loads(path.read_text())
    assert supervisor['status'] == 'EXITED_REQUIRES_RESULT_AUDIT' and supervisor['exit_code'] == 0
    assert supervisor['source_revision'] == receipt['source_revision'] == args.expected_source
    assert supervisor['run_id'] == config['run_id'] and supervisor['config'] == config
    assert supervisor['hard_wall_cap_exceeded'] is False and 0 < supervisor['wall_seconds'] <= 6900
    assert 'cleanup_error' not in receipt and receipt['network_class'] in [
        'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT',
        'cosmos_predict2._src.predict2.networks.minimal_v4_dit.MinimalV4DiT']
    pids = [supervisor['pid'], supervisor['child_pid'], receipt['pid']]
    assert len(set(pids)) == 3 and not any(Path('/proc/'+str(pid)).exists() for pid in pids)
    with (args.project/'.sync/f1.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    budget = json.loads((args.project/'reports/budget.json').read_text())
    assert budget == supervisor['budget_after'] and not any(k.endswith('_inflight') for k in budget)
    assert budget['cap_gpu_hours'] == 13 and budget['used_gpu_hours'] <= 13
    assert budget['gpu_jobs_launched'] == supervisor['budget_before']['gpu_jobs_launched']+1
    prepaid = dict(budget, used_gpu_hours=supervisor['budget_before']['used_gpu_hours']+6900/3600,
        wc_rv0_causal_inflight={'run_id': config['run_id'], 'supervisor_pid': supervisor['pid'], 'reserved_seconds': 6900})
    assert settle_budget(prepaid, supervisor['budget_before'], config, supervisor['wall_seconds'], supervisor['pid']) == budget
    stage_check = validate_stage(args.project, args.stage, args.project/'runtime', config, selected=True)
    runner = importlib.util.spec_from_file_location('causal_source_and_assets', args.stage/'scripts/run_wc_rv0_causal.py')
    module = importlib.util.module_from_spec(runner); runner.loader.exec_module(module)
    module.validate(args.project, args.stage, args.project/'runtime', output/'diagnostic')
    plan = evaluation_plan(receipt, config); trajectories = audit_trajectories(receipt, 26)
    videos = []
    for item in plan['files']:
        video = Path(item['path'])
        assert video.stat().st_size == item['bytes'] and sha(video) == item['sha256']
        metadata = probe_video(video)
        with decoded_video(video) as frames: decoded = sum(1 for _ in frames)
        assert decoded == 93
        videos.append({**item, 'full93_decode': True, 'probe': metadata})
    assert len(list((output/'diagnostic').glob('**/*.mp4'))) == 18
    monitors = [json.loads(line) for line in (output/'gpu-monitor.jsonl').read_text().splitlines()]
    assert monitors and all(row['uuid'] == config['gpu_uuid'] and set(row['pids']).issubset(set(pids)) for row in monitors)
    release = supervisor['release']
    assert release['uuid'] == config['gpu_uuid'] and not release['pids'] and release['memory_used_mib'] <= 1024
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True, timeout=5)
    assert not any(line.split(',')[0].strip() == config['gpu_uuid'] for line in apps.splitlines())
    gpu = subprocess.check_output(['nvidia-smi', '-i', config['gpu_uuid'], '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=5).strip().split(',')
    assert gpu[0].strip() == config['gpu_uuid'] and int(gpu[1]) <= 1024
    result = {'status': 'FULL_CAUSAL_SOURCE_FULL_COST_RELEASE_AND18_VIDEO_AUDIT_PASS_NOT_QUALITY',
        'run_id': config['run_id'], 'source_revision': args.expected_source, 'observed_unix': time.time(),
        'runner_receipt_sha256': sha(path), 'config_sha256': sha(args.stage/'causal-config.json'),
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
