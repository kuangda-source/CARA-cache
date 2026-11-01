"""Real93-frame synthetic media through the eight-pair offline Alex/PIQ CLI."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from wcomr import cara_read_write_artifacts_r1 as reader
from wcomr import cara_read_write_scores_r1 as scores
from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from check_cara_read_write_packet_fixture_r1 import packet
from check_cara_s_endpoint_real_video_r1 import write_video
from check_cara_s_endpoint_scoring_cli_r1 import write_black

ROOT = Path(__file__).resolve().parents[1]


def run(root, stage, *, deadline):
    root, stage = Path(root), Path(stage)
    root.mkdir(parents=True, exist_ok=False)
    cache = root/'media-cache'
    cache.mkdir()

    def writer(path, tag):
        member, role = tag.split('|')
        if member == 'human_199':
            tag = 'BLACK'
        elif role == 'UNIFORM19_C':
            tag = member+'|NATIVE35'
        source = cache/(hashlib.sha256(tag.encode()).hexdigest()+'.mp4')
        if not source.exists():
            if tag == 'BLACK':
                write_black(source)
            else:
                write_video(source, tag, height=64, width=64)
        shutil.copyfile(source, path)

    args = packet(root/'released', writer)
    saved = reader.released_artifacts(**args)
    overlay = stage.parent/'wc-time-score-CPU-two_card-r1-20261027'
    environment = dict(torch_home=str(overlay/'torch'), piq_site=str(overlay/'site'), weights_sha256={})
    config = scores.bind_scorer(saved, environment, cpu_validation=True)

    def child(manifest, output):
        command = [sys.executable, str(ROOT/scores.WORKER), '--manifest', str(manifest), '--output', str(output), '--cpu-validation']
        started = time.time()
        with output.with_suffix('.log').open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = bind_original_process(process.pid)
            try:
                code = process.wait(timeout=min(300, deadline-time.monotonic()))
            finally:
                stop_original(process, identity)
        observed = observe_original_process(identity)
        assert observed['original_live'] is False
        result = json.loads(output.read_text()) if output.exists() else None
        execution = dict(kind='ACTUAL_CPU_FIXTURE_CHILD', exit_code=code, original_process_ended=True, GPU_hidden=True,
            original_identity=identity, original_observation=observed, manifest_sha256=sha(manifest),
            source_actual_sha256={p:sha(ROOT/p) for p in scores.SCORER_SOURCES},
            wall_seconds=time.time()-started, result_sha256=digest(result))
        return result, execution, command

    manifest, output = root/'manifest.json', root/'scores.json'
    atomic_json(manifest, config)
    result, execution, command = child(manifest, output)
    assert execution['exit_code'] == 0, output.with_suffix('.log').read_text()[-2500:]
    accepted = scores.accept_scores(saved, config, sha(manifest), result, execution, cpu_validation=True)
    assert accepted['new_scored_pairs'] == 8 and accepted['reused_original_rows'] == 0
    assert any(r['PSNR_is_infinite'] and r['PSNR_video_dB'] == '+inf' for r in result['rows'])
    assert any(r['gradient_ratio_status'] == 'ZERO_REFERENCE_ENERGY' and r['gradient_energy_ratio'] is None for r in result['rows'])
    before = {str(p):sha(p) for p in (output, output.with_name('scores-intent.json'))}
    repeated = subprocess.run(command, capture_output=True, timeout=20)
    assert repeated.returncode != 0 and before == {p:sha(p) for p in before}

    # A separate synthetic failure fixture retains its complete denominator;
    # the successful fixture's original process/output is never relaunched.
    target = Path(config['pairs'][1]['candidate']['path'])
    original = target.read_bytes()
    bad_manifest, bad_output = root/'failed-manifest.json', root/'failed-scores.json'
    atomic_json(bad_manifest, config)
    target.write_bytes(b'INTENTIONALLY_INVALID_CPU_FIXTURE_VIDEO')
    try:
        failed, failed_execution, _ = child(bad_manifest, bad_output)
    finally:
        target.write_bytes(original)
    assert failed_execution['exit_code'] != 0 and failed['status'] == 'FAILED_DENOMINATOR_RETAINED'
    assert len(failed['registered_pairs']) == 8 and len(failed['rows']) == 1 and not failed['CUDA_initialized']
    return dict(status='REAL_RGB_COMPLETE8_FIDELITY_CPU_PASS', complete_pairs=8, frames_per_pair=93,
        actual_metric_weights=True, artifact14_read=True, latent_RGB_controls=4,
        accepted_sha256=digest(accepted), execution=execution, no_replay=True,
        failure_denominator=8, failure_completed_pairs=1, failure_execution=failed_execution,
        original_experiment_videos_read=False, generative_model_weights_loaded=False,
        GPU_submissions=0, ledger_written=False)
