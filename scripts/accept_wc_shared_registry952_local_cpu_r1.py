#!/usr/bin/env python3
"""Independently reconstruct the full registry, seed, mock and source controls."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(capture):
    assert capture['status'] == 'SHARED_REGISTRY952_ORIGINAL_LOCAL_CPU_ONCE_CAPTURE'
    launch = capture['launch']
    assert capture['at_unix'] >= launch['first_collection_not_before_unix']
    assert not capture['original_handle_confirmed_live_now']
    assert capture['payload_verified'] and all(capture['payload_verified'].values())
    assert capture['registration_sha256'] == launch['registration_sha256']
    source = ROOT / launch['test_source_ref']
    endpoint = capture['files'][launch['exit_ref']]
    result = capture['files'][launch['result_ref']]
    assert endpoint['exists'] and result['exists']
    end, value = endpoint['data'], result['data']
    assert end['pid'] == launch['pid'] and end['exit_code'] == 0
    assert end['result_sha256'] == result['sha256']
    assert end['source_revision'] == value['source_revision'] == launch['source_revision']
    assert end['source_sha256'] == value['source_sha256'] == launch['payload_sha256']
    assert all(sha(source / n) == h for n, h in value['source_sha256'].items())
    assert all(sha(ROOT / launch['runtime_ref'] / n) == h for n, h in value['runtime_source_sha256'].items())
    assert value['status'] == 'FROZEN_SHARED_FULL952_LOCAL_REGISTRY_CPU_PASS_NOT_PRODUCTION'
    assert (value['actual_CPU_paths'], value['ordinary_pairs'], value['CFG_calls']) == (952, 32816, 65632)
    assert not any(value[k] for k in ('CUDA_initialized', 'production_CPU_accepted',
        'real_video_quality_or_speed_claim', 'final_inputs_selected', 'final_methods_selected',
        'weights_loaded', 'real_videos_generated', 'GPU_submissions', 'SSH_queries', 'ledger_written'))
    grid = json.loads((source / 'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json').read_text())
    simple = json.loads((source / 'configs/wc_simple26d_memory_full36_r2_20261015.json').read_text())
    methods = [m['id'] for m in grid['methods']] + simple['methods']
    assert value['available_methods'] == methods and len(methods) == 17
    assert value['seeds'] == [0, 17, 43]
    scenes = ['AV28_CPU', 'Human_CPU', 'misc_CPU', 'AV51_CPU']
    updates = {m: (int(grid['actual_native_updates'][m[6:]]) if m.startswith('NATIVE') else 36) for m in methods}
    assert sum(updates.values()) == 586
    outputs = {r['path']: r for r in capture['mock_outputs']}
    assert len(outputs) == len(capture['mock_outputs']) == 952
    for path, row in outputs.items():
        assert row['error'] is None and row['data']['CPU_MOCK_WRITER_NOT_VIDEO']
        assert row['data']['value']['shape'] == [3, 93, 16, 16]
        assert sha(ROOT / path) == row['sha256']

    def observed(path):
        path = Path(path)
        if path.is_absolute():
            path = path.relative_to(ROOT)
        return outputs[str(path)]

    assert len(value['checks']) == 2 and {x['flow'] for x in value['checks']} == {False, True}
    all_noise = {}
    native_count_controls = 0
    for flow in value['checks']:
        assert flow['status'] == 'PASS'
        assert (flow['complete_CPU_paths'], flow['ordinary_pairs'], flow['CFG_calls']) == (476, 16408, 32816)
        rows, legacy = flow['audit_lean_checks'], flow['seed0_legacy_bridges']
        assert len(rows) == 204 and len(legacy) == 68
        assert {(r['scene'], r['method'], r['seed']) for r in rows} == {
            (s, m, k) for s in scenes for m in methods for k in (0, 17, 43)}
        assert {(r['scene'], r['method']) for r in legacy} == {(s, m) for s in scenes for m in methods}
        old = {(r['scene'], r['method']): r for r in legacy}
        for row in rows:
            method, seed = row['method'], row['seed']
            assert row['actual_sampler_seed'] == seed
            assert row['audit_lean_final_actions_Ahistory_sourcehistory_mock_equal'] and row['components_released']
            assert row['actual_updates'] == len(row['guided_sha256']) == updates[method]
            assert row['installed_contexts'] and all(c[2] == (
                'fixed-seed0-request' if seed == 0 else 'frozen-input-seed' + str(seed)) for c in row['installed_contexts'])
            if method.startswith('NATIVE'):
                assert set(row['native_block_CFG_counts'].values()) == {updates[method] * 2}
                native_count_controls += 1
            if method in simple['methods']:
                assert row['semantic_plan'] == simple['plans'][method]
                assert row['semantic_plan'].count('D') == 26 and 'P' not in row['semantic_plan']
            audit, lean = observed(row['audit_mock_video_path']), observed(row['lean_mock_video_path'])
            assert audit['sha256'] == lean['sha256'] == row['mock_video_sha256']
            if seed == 0:
                reference = old[(row['scene'], method)]
                assert reference['all_guided_final_actions_Ahistory_sourcehistory_mock_equal']
                assert reference['original_guided_count'] == updates[method]
                assert observed(reference['mock_video_path'])['sha256'] == reference['mock_video_sha256'] == audit['sha256']
            key = (row['scene'], seed)
            if key in all_noise:
                assert all_noise[key] == row['initial_noise_sha256']
            all_noise[key] = row['initial_noise_sha256']
        for scene in scenes:
            assert len({all_noise[(scene, k)] for k in (0, 17, 43)}) == 3
    assert native_count_controls == 72
    return dict(status='FROZEN_SHARED_REGISTRY952_SEED_CONTEXT_AND_LEGACY_PARITY_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION',
        source_revision=launch['source_revision'], actual_CPU_paths=952, ordinary_pairs=32816,
        CFG_calls=65632, audit_lean_pairs=408, seed0_whole_trajectory_bridges=136,
        mock_files=952, native_grid_count_controls=72, actual_seed_noise_groups=12,
        finite_existing_methods=17, CPU_wall_seconds=end['ended_unix'] - end['started_unix'],
        final_inputs_frozen=False, final_methods_frozen=False, production_CPU_accepted=False,
        scientific_video_quality_or_speed_claim=False, GPU_submissions=0, SSH_queries=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = accept(json.loads(gzip.decompress(args.capture.read_bytes())))
    result.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
