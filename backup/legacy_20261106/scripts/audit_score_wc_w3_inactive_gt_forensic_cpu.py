#!/usr/bin/env python3
"""H-T39 conditional CPU scoring of unchanged H-T38 artifacts, with refusal retained."""
import argparse
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from wc_w3_inactive_gt_forensic import (FAILURE, SCORE_STATUS, read, sha, require,
    verify_terminal, verify_conditional_history, reconstruct_quality)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'selected-stage', 'forensic-stage'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); start = time.monotonic()
    project, selected, stage = a.project, a.selected_stage, a.forensic_stage
    os.environ.update(CUDA_VISIBLE_DEVICES='', TORCH_HOME='/home/gaokuangda/.cache/torch',
        OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    m = read(stage/'manifest.json')
    launch = read(stage/'launch.json')
    require(sha(stage/'manifest.json') == launch['manifest_sha256']
            and sha(stage/'driver.py') == launch['driver_sha256'], 'New CPU supervisor binding differs')
    terminal = read(stage/'terminal-binding.json')
    require(terminal['original_files'] == m['original_files']
            and terminal['original_PIDs'] == m['original_PIDs'], 'Terminal binding scope differs')
    m = {**m, **terminal}
    require(m['identity'] == 'WC-W3-PAIRED-INACTIVE-GT-FORENSIC-CPU-R1-20261008'
            and m['GPU_submissions'] == 0 and m['original_GPU_stage'] == str(selected.relative_to(project)), 'New CPU binding differs')
    require(all(sha(stage/n) == h for n, h in m['payload_sha256'].items()), 'New CPU payload changed')
    original_paths = {name: project/path for name, path in m['original_files'].items()}
    require({n: sha(path) for n, path in original_paths.items()} == m['original_file_sha256'], 'Original terminal/source/evidence changed')
    prereg = read(stage/'manifests/wc_w3_paired_inactive_gt_cpu_preregistration_20261008.json')
    for name, h in prereg['inputs'].items():
        # The new stage includes frozen registration inputs; GPU selected config is separately bound.
        path = selected/'paired-config.json' if name.startswith('configs/') else stage/name
        require(sha(path) == h, 'Preregistered CPU input changed: '+name)
    proof_path = stage/'reports/wc_w3_inactive_gt_semantics_cpu_r1_20261008_result_json_native.gz'
    proof = read(proof_path)
    semantic_receipt = read(stage/'reports/wc_w3_inactive_gt_semantics_cpu_r1_20261008_receipt_json_native.gz')
    require(semantic_receipt['exit_code'] == 0 and semantic_receipt['result_sha256'] == m['semantic_result_raw_sha256']
            and semantic_receipt['source_revision'] == '4545d878d91fed6a1138cd39908655215b94ca4d', 'Actual CPU proof receipt differs')
    import gzip
    import hashlib
    require(hashlib.sha256(gzip.decompress(proof_path.read_bytes())).hexdigest() == m['semantic_result_raw_sha256'], 'Actual CPU result hash differs')
    sys.path.insert(0, str(selected/'src'))
    from wcomr.rv0_paired_cfg_production import validate, validate_selected, read_prior
    from wcomr.rv0_paired_cfg_evaluation import verify_paired_row, verify_historical_bridges
    c, _ = validate(project, selected); validate_selected(c, project, selected)
    r, sup, post, budget = [read(original_paths[n]) for n in ('runner', 'supervisor', 'original_post_CPU', 'budget')]
    row = verify_terminal(r, sup, post, budget, c)
    require(sup['config_sha256'] == sha(selected/'paired-config.json') == m['config_sha256'], 'Selected config identity differs')
    require([sup['pid'], sup['child_pid'], post['pid']] == m['original_PIDs']
            and all(not Path('/proc/'+str(pid)).exists() for pid in m['original_PIDs']), 'Original process still live')
    original_post_stage = original_paths['original_post_CPU'].parent
    require(not (original_post_stage/'score.json').exists(), 'Original no-score history altered')
    runtime = project/'runtime'
    require(sha(runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py') == proof['frozen_denoise_source_sha256']
            and sha(runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py') == proof['frozen_WC_source_sha256'], 'Semantics proof runtime source differs')
    require(c['preregistration']['same_existing_request']['inference_type'] == 'text2world'
            and c['preregistration']['same_existing_request'].get('input_path') is None, 'Not the registered unconditioned request')
    old, prior = read_prior(selected)
    require(r['model_context'] == old['model_context'] and r['existing_Native'] == c['preregistration']['existing_Native'], 'Model/reference identity differs')
    verdict = verify_paired_row(row, 26)
    # Call the unchanged original strict verifier and retain its exact refusal.
    try:
        verify_historical_bridges(row, prior)
    except ValueError as error:
        require(str(error) == FAILURE, 'Original strict refusal differs')
        strict_error = str(error)
    else:
        raise ValueError('The registered original strict failure was not reproduced')
    bridge = verify_conditional_history(row, prior, proof)
    require(prereg['registered_unix'] < m['original_terminal_ended_unix'], 'CPU preregistration was not before terminal quality analysis')
    with (project/'.sync/f1.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True)
        require(not any(x.split(',')[0].strip() == sup['gpu_uuid'] for x in apps.splitlines()), 'Original GPU not free')
        audit = {'status': 'H_T39_CONDITIONAL_CPU_AUDIT_PASS_ORIGINAL_H_T38_STRICT_FAILURE_RETAINED',
            'original_strict_error': strict_error, 'original_GPU_exit_code': sup['exit_code'],
            'original_CPU_exit_code': post['exit_code'], 'original_strict_GPU_acceptance': False,
            'current_internal_strict_verdict': verdict, 'conditional_history': bridge,
            'runner_sha256': sha(original_paths['runner']), 'config_sha256': m['config_sha256'],
            'GPU_submissions': 0, 'CUDA_initialized': False, 'independent_CONF': False}
        with (stage/'audit.json').open('x') as f: f.write(json.dumps(audit, indent=2, allow_nan=False)+'\n')
        require(not (stage/'score.json').exists(), 'This CPU scoring identity already consumed')
        spec = importlib.util.spec_from_file_location('frozen_original_metric', selected/'scripts/audit_score_wc_w3_paired_cfg_cpu.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        metric, protocol = module.prepare_metric(project, selected)
        import torch
        from wcomr.rv0_video_reader import decoded_video, probe_video
        from wcomr.rv0_lpips import score_pair
        decoded = {d['label']: d['artifact'] for d in row['decoded_children']}
        native = c['preregistration']['existing_Native']
        files = [row['artifact']] + list(decoded.values()) + [native]
        result = {'status': 'H_T39_CONDITIONAL_CPU_SCORING_STARTED_NOT_ORIGINAL_ACCEPTANCE',
            'original_GPU_source_revision': r['source_revision'], 'CPU_source_revision': m['source_revision'],
            'runner_sha256': audit['runner_sha256'], 'config_sha256': audit['config_sha256'],
            'original_strict_GPU_acceptance': False, 'original_strict_error': strict_error,
            'original_GPU_exit_code': sup['exit_code'], 'original_CPU_exit_code': post['exit_code'],
            'planned_scope': r['planned_scope'], 'budget': budget, 'videos': [], 'losses': {},
            'metric_protocol': {k: v for k, v in protocol.items() if k not in {'benefit', 'policy'}},
            'GPU_submissions': 0, 'CUDA_initialized': False, 'independent_CONF': False,
            'clean_speed_measurement': False, 'physics_or_semantic_acceptance': False}
        def save():
            temp = stage/'score.tmp'; temp.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n'); temp.replace(stage/'score.json')
        save()
        require(len(files) == 6 and len({v['path'] for v in files}) == 6, 'Full video denominator differs')
        for item in files:
            path = Path(item['path'])
            require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], 'Video changed')
            require(item == native or (project/'outputs'/c['execution_run_id']/'diagnostic').resolve() in path.resolve().parents, 'Unexpected new video path')
            meta = probe_video(path)
            with decoded_video(path) as frames: require(sum(1 for _ in frames) == 93, 'Full93 decode differs')
            result['videos'].append({**item, 'probe': meta, 'full93_decode': True}); save()
        previous = read(selected/'reports/wc_w3_d46_r3_complete_20261008_CPU_score_json_native.gz')
        oldcase = next(x for x in previous['cases'] if x['seed'] == 2)
        for label in ('BASE', 'SINGLE', 'PAIRED'):
            item = decoded[label+'_first']
            with decoded_video(native['path']) as left, decoded_video(item['path']) as right:
                loss = score_pair(left, right, metric, reference_sha256=native['sha256'], candidate_sha256=item['sha256'])
            if label in ('BASE', 'SINGLE'):
                require(loss == oldcase['losses']['BASE' if label == 'BASE' else 'REFRESH'], 'Historical full93 metric/value bridge differs')
            result['losses'][label] = loss; save()
        by = {c['label']: c for c in row['children']}
        result['control_costs'] = {label: [by[label+'_'+part]['record']['control_wall_seconds'] for part in ('first', 'second')] for label in ('BASE', 'SINGLE', 'PAIRED')}
        result['status'] = SCORE_STATUS
        result['signed_pairs'] = reconstruct_quality(row, result)['comparisons']
        require(not torch.cuda.is_initialized(), 'CPU scorer initialized CUDA')
        require({n: sha(path) for n, path in original_paths.items()} == m['original_file_sha256'], 'Original bytes changed during CPU analysis')
        require(all(sha(stage/n) == h for n, h in m['payload_sha256'].items()), 'CPU payload changed during scoring')
        result['CPU_wall_seconds'] = time.monotonic()-start; save()
    print(json.dumps({'status': result['status'], 'CPU_wall_seconds': result['CPU_wall_seconds'],
                      'original_strict_GPU_acceptance': False, 'scored_videos': 3, 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
