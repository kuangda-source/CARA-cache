"""Full40 synthetic video/profile controls and real tiny CPU tensor artifacts.

No Cosmos model, real codec, CUDA event or GPU allocator is used in this file.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import torch

from test_runtime_profile40_execution_r1 import fixture as execution_fixture, response
from wcomr import runtime_profile40_execution_r1 as execution
from wcomr import runtime_profile40_post_r1 as post
from wcomr.frozen_shared_production_r1 import sha
from wcomr.mid_coverage import tree_digest

SHAPE = (1, 2, 3)


def memory():
    cell = dict(available=False, **{k: None for k in post.MEMORY_FIELDS})
    return dict(device='cpu', memory_before=cell, memory_after=copy.deepcopy(cell),
                peak_reset_before_request=False, request_profile_wall_seconds=100.)


def scalar_profile():
    intervals = [dict(id=0, parent=None, component='complete_request_inclusive',
                      outcome='RETURNED', CPU_seconds=90., CUDA_elapsed_ms=None)]
    for name, count in dict(shallow_block=144, solver_update=36, VAE_decode=1,
            method_install_inclusive=1, output_head=72, video_write=1).items():
        for _ in range(count):
            intervals.append(dict(id=len(intervals), parent=0, component=name,
                                  outcome='RETURNED', CPU_seconds=.001, CUDA_elapsed_ms=None))
    components = {}
    for span in intervals:
        group = components.setdefault(span['component'], dict(calls=0, inclusive_CPU_seconds=0.,
            inclusive_CUDA_ms=None, exceptions=0))
        group['calls'] += 1; group['inclusive_CPU_seconds'] += span['CPU_seconds']
    return dict(memory(), status='PROFILE_COMPLETE', components=components, intervals=intervals,
        interval_semantics=post.SEMANTICS, multi_stream_work_not_attributed=True,
        no_inner_profiler_synchronize=True, scalar_records_only=True,
        timing_claim='INSTRUMENTED_PROFILE_NOT_CLEAN_LATENCY', no_direct_post_probe_action_price_claim=True)


def fixture(root):
    _, _, _, bound, samples = execution_fixture(); rows = []
    for planned in bound['execution_plan']:
        raw = response(planned, samples[(planned['scene'], planned['slot'])])
        base = int(hashlib.sha256((planned['scene'] + planned['method']).encode()).hexdigest()[:6], 16)
        final = torch.full(SHAPE, base / 1000.)
        raw.update(final_latent=final, guided=[final + i for i in range(36)] if planned['audit_guided'] else None,
            pre_request_state_identity=dict(original_state_sha256='1' * 64,
                restored_state_sha256='1' * 64, shared_eval_verified=True),
            profile_control_mode=planned['mode'], clean_repeated_latency_claim=False,
            request_memory_observation=memory(),
            component_profile_summary=scalar_profile() if planned['component_profile'] else None,
            A_history=None if planned['slot'] == 'FULL_NATIVE' else [])
        directory = root / planned['id']; directory.mkdir()
        video = directory / 'SYNTHETIC_NOT_A_VIDEO.mp4'; video.write_bytes(planned['id'].encode())
        raw['video_path'] = str(video)
        raw['timing_intervals'] = execution.audit_row({**planned, **raw}, planned, bound)
        row = execution.archive_output(raw, planned, directory, root, expected_shape=SHAPE)
        rows.append({**planned, **row})
    return bound, rows


def video(row):
    digest = row['final_latent_sha256']
    return dict(video_artifact=dict(path=row['video_path'], bytes=Path(row['video_path']).stat().st_size,
        sha256=sha(row['video_path']), frames=93, decoded_rgb_sha256=[digest] * 93),
        decoded_video=dict(frames=93, RGB_sha256=digest))


def evaluate(root, bound, rows, *, inspector=video, child_exit_code=0):
    result = post.audit_rows(rows, bound,
        lambda r, p, b: post.audit_payload(r, p, b, root, expected_shape=SHAPE), inspector,
        lambda r, p: post.audit_profile(r, p, root, expected_device='cpu'), expected_device='cpu')
    controls, failed = post.parity_controls(result['rows'], bound)
    result.update(controls); result['audit_failures'].extend(failed)
    result.update(post.summarize(result, bound, observed_paths=len(rows), child_exit_code=child_exit_code))
    return result


def rewrite_profile(row, change):
    path = Path(row['component_profile_artifact']['path']); value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value, allow_nan=False))
    row['component_profile_artifact'].update(bytes=path.stat().st_size, sha256=sha(path))
    row['profile_components'] = copy.deepcopy(value['components'])


class RuntimeProfile40PostControls(unittest.TestCase):
    def test_full40_all36_raw_and_all93_synthetic_RGB_modes_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root); original = copy.deepcopy(rows)
            result = evaluate(root, bound, rows)
            self.assertEqual(result['status'], post.COMPLETE_STATUS)
            self.assertEqual((result['raw_model_pass_paths'], result['accepted_93frame_videos'],
                result['audited_component_profile_paths'], result['accepted_complete_scene_method_mode_groups']),
                (40, 40, 20, 10))
            self.assertEqual(rows, original)
            self.assertEqual(len(result['original_to_profile_all36_controls']), 10)
            self.assertTrue(all(c['all36_guided_tree_equal'] for c in result['original_to_profile_all36_controls']))
            self.assertTrue(all(c['all93_RGB_equal'] for c in result['profile_to_lean_controls']))
            self.assertEqual(sum(len(c['observations']) for c in result['all_mode_observations']), 40)
            self.assertFalse(result['clean_repeated_latency_claim'])
            self.assertFalse(result['minimal_calibration_cost_measured'])
            self.assertNotIn('speedup', result); self.assertNotIn('timing_statistics', result)
            self.assertTrue(all(r['request_memory_observation']['memory_after']['allocated_bytes'] is None
                                for r in result['rows']))

    def test_recomputed_intervals_reject_forged_summary_even_with_valid_file_SHA(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            row = next(r for r in rows if r['component_profile'])
            rewrite_profile(row, lambda p: p['components']['solver_update'].update(inclusive_CPU_seconds=999.))
            result = evaluate(root, bound, rows)
            self.assertEqual(result['status'], 'N09_FULL40_AUDIT_FAILURE_FULL_SCOPE_RETAINED')
            self.assertEqual(result['raw_model_pass_paths'], 40)
            self.assertEqual(result['audited_component_profile_paths'], 19)
            self.assertEqual(result['accepted_complete_scene_method_mode_groups'], 9)
            self.assertEqual(result['audit_failures'][0]['kind'], 'COMPONENT_PROFILE')
            self.assertEqual(len(result['rows']), 40)

    def test_profile_parent_count_semantics_and_original_control_leak_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            source = next(r for r in rows if r['component_profile']); planned = bound['execution_plan'][rows.index(source)]
            original = Path(source['component_profile_artifact']['path']).read_bytes()
            changes = [lambda p: p['intervals'][1].update(parent=500),
                lambda p: p['intervals'][1].update(CPU_seconds=-.1),
                lambda p: p.update(interval_semantics='ADDITIVE_PURE_KERNEL_COSTS'),
                lambda p: p.update(components={}),
                lambda p: p['intervals'][1].update(component='INVENTED_FFT_COMPONENT')]
            for change in changes:
                with self.subTest(change=change):
                    row = copy.deepcopy(source); Path(row['component_profile_artifact']['path']).write_bytes(original)
                    rewrite_profile(row, change)
                    with self.assertRaises(ValueError):post.audit_profile(row, planned, root, expected_device='cpu')
            control = copy.deepcopy(rows[0]); control['component_profile_artifact'] = source['component_profile_artifact']
            with self.assertRaises(ValueError):post.audit_profile(control, bound['execution_plan'][0], root, expected_device='cpu')

    def test_guided_trace_change_is_caught_when_final_latent_and_RGB_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            row = next(r for r in rows if r['mode'] == 'PROFILE_AUDIT')
            path = Path(row['guided_artifact']['path']); content = torch.load(path, weights_only=True)
            content['guided'][23] += .25; torch.save(content, path)
            row['guided_artifact'].update(bytes=path.stat().st_size, sha256=sha(path))
            row['guided_tree_sha256'] = tree_digest(content['guided'])
            result = evaluate(root, bound, rows)
            self.assertEqual(result['raw_model_pass_paths'], 40)
            self.assertEqual(result['accepted_93frame_videos'], 40)
            self.assertEqual(sum(c['status'] == 'PARITY_FAILURE_RETAINED'
                for c in result['original_to_profile_all36_controls']), 1)
            self.assertTrue(all(c['status'] == 'PASS' for c in result['profile_to_lean_controls']))
            self.assertEqual(result['accepted_complete_scene_method_mode_groups'], 9)

    def test_actual_nonfinite_tensor_failure_keeps_other39_and_full_denominator(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root); row = rows[5]
            path = Path(row['final_artifact']['path']); value = {'final_latent': torch.full(SHAPE, float('nan'))}
            torch.save(value, path); row['final_artifact'].update(bytes=path.stat().st_size, sha256=sha(path))
            # Keep the original recorded finite-state digest. Nonfinite payloads
            # cannot legitimately obtain a new tree digest in the real executor.
            result = evaluate(root, bound, rows)
            self.assertEqual(len(result['rows']), 40); self.assertEqual(result['raw_model_pass_paths'], 39)
            self.assertTrue(any(f['kind'] == 'RAW_MODEL_OR_IDENTITY' for f in result['audit_failures']))

    def test_container_failure_preserves_raw_profiles_and_other_mode_groups(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root); target = rows[5]['id']
            def bad(row):
                if row['id'] == target:raise RuntimeError('SYNTHETIC_MISSING_MOOV_NO_RETRY')
                return video(row)
            result = evaluate(root, bound, rows, inspector=bad)
            self.assertEqual(result['accepted_93frame_videos'], 39)
            self.assertEqual(result['raw_model_pass_paths'], 40)
            self.assertEqual(result['audited_component_profile_paths'], 20)
            self.assertEqual(result['accepted_complete_scene_method_mode_groups'], 9)
            self.assertEqual(len(result['rows']), 40)

    def test_action_or_history_mismatch_cannot_be_hidden_by_equal_endpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            row = next(r for r in rows if r['mode'] == 'PROFILE_LEAN' and r['slot'] == 'GCR_EFFICIENT')
            row['A_history'].append(dict(SYNTHETIC_DIFFERENT_HISTORY=True))
            result = evaluate(root, bound, rows)
            self.assertEqual(result['raw_model_pass_paths'], 40)
            self.assertEqual(sum(c['status'] == 'PARITY_FAILURE_RETAINED' for c in result['profile_to_lean_controls']), 1)
            self.assertEqual(result['accepted_complete_scene_method_mode_groups'], 9)

    def test_rejection_and_unreached_positions_remain_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            reject = rows[0]; reject.update(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0)
            reject['timing_intervals'] = None
            for key in ('final_artifact', 'final_latent_sha256', 'guided_artifact', 'guided_tree_sha256',
                        'guided_outputs', 'video_path'):reject.pop(key, None)
            result = evaluate(root, bound, rows)
            self.assertEqual(result['status'], 'N09_FULL40_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
            self.assertEqual(len(result['rows']), 40)
            self.assertEqual(result['rows'][0]['status'], 'TEXT_REJECTED')
            subset = rows[1:3]  # A foreign non-prefix must fail instead of filling success rows.
            with self.assertRaises(ValueError):evaluate(root, bound, subset)
            subset = copy.deepcopy(rows[:3]); subset[-1]['status'] = 'TECH_FAILED'
            result = evaluate(root, bound, subset, child_exit_code=1)
            self.assertEqual(result['status'], 'N09_FULL40_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED')
            self.assertEqual(sum(r['status'] == 'NOT_REACHED' for r in result['rows']), 37)

    def test_CPU_null_and_explicit_CUDA_peak_contract_without_GPU_execution(self):
        row = {'request_memory_observation': memory()}
        post.audit_memory(row, expected_device='cpu')
        with self.assertRaises(ValueError):post.audit_memory(row)  # Production requires CUDA, never this CPU fixture.
        row['request_memory_observation']['memory_after']['allocated_bytes'] = 0
        with self.assertRaises(ValueError):post.audit_memory(row, expected_device='cpu')
        fake = dict(device='cuda:0', peak_reset_before_request=True, request_profile_wall_seconds=2.,
            memory_before=dict(available=True, allocated_bytes=10, reserved_bytes=20, peak_allocated_bytes=10, peak_reserved_bytes=20),
            memory_after=dict(available=True, allocated_bytes=8, reserved_bytes=16, peak_allocated_bytes=12, peak_reserved_bytes=24))
        row = {'request_memory_observation': fake}; post.audit_memory(row)
        fake['memory_after']['peak_reserved_bytes'] = 18
        with self.assertRaises(ValueError):post.audit_memory(row)

    def test_profile_hash_or_path_cannot_be_replaced_and_source_owner_only_is_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            row = next(r for r in rows if r['component_profile']); planned = bound['execution_plan'][rows.index(row)]
            Path(row['component_profile_artifact']['path']).write_text('{}')
            with self.assertRaises(ValueError):post.audit_profile(row, planned, root, expected_device='cpu')
            row['component_profile_artifact']['path'] = '/tmp/FOREIGN_MISSING_N09_PROFILE.json'
            with self.assertRaises(ValueError):post.audit_profile(row, planned, root, expected_device='cpu')
            self.assertEqual(post.stable_history({'owner': 'first', 'age': 2}),
                             post.stable_history({'owner': 'second', 'age': 2}))
            self.assertNotEqual(post.stable_history({'owner': 'first', 'age': 2}),
                                post.stable_history({'owner': 'second', 'age': 3}))

    def test_mode_summary_cannot_replace_original_timers_with_different_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            rows[5]['timing_intervals']['core_text_denoise_VAE_seconds'] = 999.
            result = evaluate(root, bound, rows)
            self.assertEqual(result['raw_model_pass_paths'], 39)
            self.assertTrue(any(f['kind'] == 'RAW_MODEL_OR_IDENTITY' for f in result['audit_failures']))

    def test_missing_one_real_solver_observation_rejected_after_consistent_aggregation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); bound, rows = fixture(root)
            row = next(r for r in rows if r['component_profile']); planned = bound['execution_plan'][rows.index(row)]
            def remove_one(value):
                index = next(i for i, s in enumerate(value['intervals']) if s['component'] == 'solver_update')
                value['intervals'].pop(index)
                for i, span in enumerate(value['intervals']):span['id'] = i
                value['components']['solver_update']['calls'] -= 1
                value['components']['solver_update']['inclusive_CPU_seconds'] -= .001
            rewrite_profile(row, remove_one)
            with self.assertRaisesRegex(ValueError, 'full36'):
                post.audit_profile(row, planned, root, expected_device='cpu')


if __name__ == '__main__':unittest.main()
