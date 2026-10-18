#!/usr/bin/env python3
"""Offline N09 profile summary and exact-pixel binding to accepted N08 LPIPS.

No SSH, model, video decoder, GPU, ledger or original receipt mutation.
The profile modes are not repeated clean latency measurements.
"""
import argparse
from collections import Counter
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
N09 = 'reports/wc_paper_N09_actual40_R3_terminal_collection_20261018.json.gz'
ACCEPTED = 'reports/wc_paper_N09_actual40_R3_terminal_independent_acceptance_20261018.json'
N08 = 'reports/wc_paper_N08_balanced_full40_terminal_collection_user_status_20261017.json.gz'
N08_ACCEPTED = 'reports/wc_paper_N08_balanced_full40_terminal_independent_acceptance_roundoff_r1_20261017.json'


def read(name):
    raw = (ROOT / name).read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)


def binding(name):
    raw = (ROOT / name).read_bytes()
    return dict(ref=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve the original result')
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr.runtime_profile40_acceptance_r1 import accept
    from wcomr.balanced_repeat_roundoff_acceptance_r1 import accept as accept_N08
    value, saved = read(N09), read(ACCEPTED)
    rebuilt = accept(value, value['launch'])
    assert saved['capture_sha256'] == binding(N09)['sha256']
    assert all(saved.get(k) == v for k, v in rebuilt.items())
    assert saved['full_runtime_profile_scope_accepted']
    assert saved['full_protocol_including_billed_limit_accepted']
    old, old_accept = read(N08), read(N08_ACCEPTED)
    original_N08_acceptance = accept_N08(old, old['launch'])
    assert old_accept['capture_ref'] == N08
    assert all(old_accept.get(k) == v for k, v in original_N08_acceptance.items())
    assert old_accept['full_raw_and_fidelity_scope_accepted']
    rows = value['final']['rows']
    assert len(rows) == 40 and Counter(r['status'] for r in rows) == {'COMPLETE': 40}
    old_formal = [r for r in old['final']['rows'] if r['section'] == 'TIMED']
    native = {(r['scene'], r['seed']): r for r in rows if r['method'] == 'NATIVE35'}
    bindings = []
    for row in rows:
        matching = [r for r in old_formal if all(r[k] == row[k] for k in ('scene', 'seed', 'method'))]
        assert len(matching) == 3
        for prior in matching:
            for key in ('frozen_input_identity', 'actions', 'A_history', 'scheduler_timesteps', 'final_latent_sha256'):
                assert prior[key] == row[key], (row['id'], key)
            assert row['decoded_video']['RGB_sha256'] == prior['decoded_video']['RGB_sha256']
            assert len(row['video_artifact']['decoded_rgb_sha256']) == 93
            assert row['video_artifact']['decoded_rgb_sha256'] == prior['video_artifact']['decoded_rgb_sha256']
            score = prior['LPIPS']
            assert score['frames'] == len(score['frame_distances']) == 93
            assert score['candidate_sha256'] == prior['video_artifact']['sha256']
            assert all(math.isfinite(v) and v >= 0 for v in score['frame_distances'])
            assert math.isclose(math.fsum(score['frame_distances']) / 93, score['mean_LPIPS'], rel_tol=1e-12, abs_tol=1e-12)
            old_native = [r for r in old_formal if r['scene'] == row['scene'] and r['seed'] == row['seed'] and r['method'] == 'NATIVE35']
            assert len(old_native) == 3
            for reference in old_native:
                assert reference['video_artifact']['sha256'] == score['reference_sha256']
                assert native[row['scene'], row['seed']]['video_artifact']['decoded_rgb_sha256'] == reference['video_artifact']['decoded_rgb_sha256']
            assert all(r['LPIPS'] == score for r in matching)
        bindings.append(dict(id=row['id'], scene=row['scene'], method=row['method'], mode=row['mode'],
            formal=row['mode'] != 'ORIGINAL_AUDIT_WARMUP', current_video_sha256=row['video_artifact']['sha256'],
            old_N08_row_ids=[r['id'] for r in matching], old_reference_sha256=score['reference_sha256'],
            RGB_frames_equal=93, mean_LPIPS_reused=score['mean_LPIPS'],
            frame_distances=score['frame_distances'], pts=score['pts'], newly_scored=False))
    groups = []
    components = []
    for group in value['final']['all_mode_observations']:
        observations = []
        for row in group['observations']:
            if row['mode'] == 'ORIGINAL_AUDIT_WARMUP':
                continue
            timers = row['observed_timers']
            memory = row['request_memory_observation']['memory_after']
            observations.append(dict(id=row['id'], mode=row['mode'],
                core_seconds=timers['core_text_denoise_VAE_seconds'],
                guarded_seconds=timers['guarded_pipeline_without_write_seconds'],
                peak_allocated_bytes=memory['peak_allocated_bytes'], peak_reserved_bytes=memory['peak_reserved_bytes']))
            if row['audited_component_profile']:
                components.append(dict(scene=group['scene'], method=group['method'], id=row['id'],
                    mode=row['mode'], components=row['audited_component_profile']['components']))
        assert len(observations) == 3
        groups.append(dict(scene=group['scene'], method=group['method'], observations=observations))
    result = dict(status='N09_FULL40_ACCEPTED_PROFILE_AND_EXACT_RGB_N08_FIDELITY_BINDING',
        observed_local=datetime.fromtimestamp(value['observed_unix'], ZoneInfo('Asia/Shanghai')).isoformat(),
        sources=[binding(n) for n in (N09, ACCEPTED, N08, N08_ACCEPTED)],
        original_runtime_acceptance_reexecuted=True, original_N08_acceptance_reexecuted=True,
        total_paths=40, full_warmup_paths=10, formal_paths=30,
        all_40_raw_RGB_memory_audits_passed=True, independently_reconstructed_scalar_files=20,
        formal_exact_RGB_bound_LPIPS_paths=30, formal_bound_frame_distances=2790,
        new_LPIPS_model_calls=0, independent_new_inputs=0, fidelity_bindings=bindings,
        mode_groups=groups, component_observations=components,
        actual_GPUh=saved['actual_GPUh'], actual_settled_GPUh=value['pool']['used_gpu_hours'],
        cumulative_cap_GPUh=value['pool']['cap_gpu_hours'], available_GPUh=value['pool']['available_gpu_hours'],
        original_model_load_seconds=value['final']['original_load_seconds'],
        original_CPU_post_seconds=value['final']['CPU_wall_seconds'],
        clean_repeated_latency_claim=False, component_intervals_are_additive=False,
        action_unit_prices_measured=False, minimal_calibration_collection_cost_measured=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False,
        summarizer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'formal_exact_RGB_bound_LPIPS_paths', 'actual_GPUh', 'available_GPUh')}))


if __name__ == '__main__':
    main()
