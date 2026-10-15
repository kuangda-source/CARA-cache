"""Failure-preserving final audit controls using explicit synthetic receipts."""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from wcomr.frozen_shared_execution_r1 import point
from wcomr.frozen_shared_post_r1 import (
    COMPLETE_STATUS, artifact_path, audit_payload, audit_rows, inspect_video,
    read_tensor, score_rows, summarize, warm_controls,
)
from wcomr.frozen_shared_production_r1 import audit_row, sha, validate_contract
from wcomr.mid_coverage import tree_digest


def fixture():
    path = Path(__file__).with_name('test_frozen_shared_batch_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_post_fixture_only', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    config, bound, samples = module.fixture()
    plan = validate_contract(config, bound)
    runs = []
    for p in plan:
        row = {**p, **module.fake_result(p, samples[(p['case_id'], p['method'])])}
        digest = hashlib.sha256((p['case_id'] + p['method']).encode()).hexdigest()
        row.update(final_latent_sha256=digest, A_history=[],
                   synthetic_RGB_digest=digest, video_path='/SYNTHETIC/' + p['id'] + '.mp4')
        runs.append(row)
    return config, bound, plan, runs


def synthetic_video(row):
    digest = row['synthetic_RGB_digest']
    return dict(video_artifact=dict(path=row['video_path'], sha256=digest, bytes=1,
        frames=93, fps=16, width=768, height=432, decoded_rgb_sha256=[digest] * 93),
        decoded_video=dict(frames=93, RGB_sha256=digest))


def synthetic_guides(row):
    return [torch.tensor([float(i)]) for i in range(point(row['method'])['actual_updates'])]


def synthetic_score(reference, candidate):
    loss = 0. if candidate['method'] == 'NATIVE35' else .1
    return dict(frames=93, frame_distances=[loss] * 93, mean_LPIPS=sum([loss] * 93) / 93,
        reference_sha256=reference['video_artifact']['sha256'], candidate_sha256=candidate['video_artifact']['sha256'])


def evaluate(bound, plan, runs, *, inspector=synthetic_video, scorer=synthetic_score):
    result = audit_rows(runs, plan, bound, audit_row, inspector)
    controls, failures = warm_controls(result['rows'], plan, synthetic_guides)
    result['warm_repeat_controls'] = controls
    result['audit_failures'].extend(failures)
    result['audit_failures'].extend(score_rows(result['rows'], scorer))
    result.update(summarize(result, bound, observed_paths=len(runs), child_exit_code=0,
                            bootstrap_repetitions=8))
    return result


class FinalPostControls(unittest.TestCase):
    def test_full180_with_all_actual_warm_lengths_and_160_N10_ready_artifacts(self):
        _, bound, plan, runs = fixture()
        original = copy.deepcopy(runs)
        result = evaluate(bound, plan, runs)
        self.assertEqual(runs, original)
        self.assertEqual(result['status'], COMPLETE_STATUS)
        self.assertEqual(result['scored_scientific_videos'], 160)
        self.assertEqual({r['all_guided_outputs_equal'] for r in result['warm_repeat_controls']}, {19, 27, 36})
        self.assertEqual(result['grouped_statistics']['registered_prompt_groups'], 8)
        self.assertEqual(len(result['grouped_statistics']['comparisons']), 18)
        from wcomr.automatic_quality_r1 import VBENCH_COMMIT, build_inputs
        formal = [r for r in result['rows'] if r['section'] == 'TIMED']
        quality = build_inputs(bound['cases'], bound['method_ids'], formal,
            ['subject_consistency', 'dynamic_degree'], dict(vbench_commit=VBENCH_COMMIT, synthetic=True))
        self.assertEqual(quality['registered_generation_positions'], 160)
        self.assertEqual(sum(r['input_status'] == 'READY_TO_SCORE' for r in quality['rows']), 320)
        self.assertFalse(result['stable_repeated_clean_speed_claim'])

    def test_one_broken_container_preserves_raw_cost_and_other_159_scores(self):
        _, bound, plan, runs = fixture()
        target = next(r for r in runs[40:] if r['section'] == 'TIMED' and r['method'] == 'A_NO_P')['id']
        def video(row):
            if row['id'] == target: raise ValueError('SYNTHETIC_MOOV_MISSING')
            return synthetic_video(row)
        result = evaluate(bound, plan, runs, inspector=video)
        row = next(r for r in result['rows'] if r['id'] == target)
        self.assertEqual(row['status'], 'COMPLETE')
        self.assertEqual(row['raw_model_audit'], 'PASS')
        self.assertEqual(result['scored_scientific_videos'], 159)
        self.assertIn('AUDIT_FAILURE', result['status'])
        ours = next(r for r in result['grouped_statistics']['methods'] if r['method'] == 'A_NO_P')
        self.assertEqual(ours['complete_two_seed_time_prompts'], 8)
        self.assertEqual(ours['complete_two_seed_quality_prompts'], 7)
        self.assertIsNone(ours['full_registered_mean_LPIPS'])

    def test_broken_full_native_is_never_replaced_by_low_step_native(self):
        _, bound, plan, runs = fixture()
        target = next(r for r in runs[40:] if r['section'] == 'TIMED' and r['method'] == 'NATIVE35')
        def video(row):
            if row['id'] == target['id']: raise ValueError('SYNTHETIC_REFERENCE_CONTAINER_FAILURE')
            return synthetic_video(row)
        result = evaluate(bound, plan, runs, inspector=video)
        self.assertEqual(result['scored_scientific_videos'], 150)
        for row in result['rows']:
            if row['section'] == 'TIMED' and row['case_id'] == target['case_id']:
                self.assertNotIn('LPIPS', row)

    def test_text_rejection_and_technical_prefix_keep_original_denominators(self):
        _, bound, plan, runs = fixture()
        target = next(r for r in runs[40:] if r['method'] == 'A_NO_P')
        target.update(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0)
        result = evaluate(bound, plan, runs)
        self.assertEqual(result['scored_scientific_videos'], 159)
        self.assertIn('REJECTIONS_OR_MISSING', result['status'])
        prefix = copy.deepcopy(runs[:27]); prefix[-1]['status'] = 'RUNNING'
        result = evaluate(bound, plan, prefix)
        self.assertEqual(len(result['rows']), 180)
        self.assertEqual(sum(r['status'] == 'NOT_REACHED' for r in result['rows']), 153)
        self.assertEqual(result['rows'][26]['status'], 'TECH_FAILED')
        self.assertIn('TECHNICAL_INCOMPLETE', result['status'])

    def test_full_native19_warm_trace_and_source_numerics_cannot_change(self):
        _, bound, plan, runs = fixture()
        result = audit_rows(runs, plan, bound, audit_row, synthetic_video)
        def bad_guides(row):
            return synthetic_guides(row) + ([torch.tensor([99.])] if row['method'] == 'NATIVE18' else [])
        controls, failures = warm_controls(result['rows'], plan, bad_guides)
        self.assertEqual(len(failures), 1)
        self.assertEqual(next(r for r in controls if r['method'] == 'NATIVE18')['status'], 'CONTROL_FAILURE_RETAINED')
        row = next(r for r in result['rows'] if r['id'] == 'warm_2_TABLE_PHASE_H1')
        row['source_history'][0]['true_D_after'] = 'FOREIGN_NUMERICAL_ANCHOR'
        _, failures = warm_controls(result['rows'], plan, synthetic_guides)
        self.assertEqual(len(failures), 1)
        row['source_history'][0]['true_D_after'] = 'SYNTHETIC_ANCHOR'
        row['source_history'][0]['owner'] = 'EPHEMERAL_OBJECT_ADDRESS'
        _, failures = warm_controls(result['rows'], plan, synthetic_guides)
        self.assertEqual(failures, [])

    def test_cross_seed_metric_and_reordered_rows_are_refused(self):
        _, bound, plan, runs = fixture()
        def wrong_score(reference, row):
            return {**synthetic_score(reference, row), 'reference_sha256': '0' * 64}
        result = evaluate(bound, plan, runs, scorer=wrong_score)
        self.assertEqual(result['scored_scientific_videos'], 0)
        self.assertEqual(len(result['audit_failures']), 160)
        runs[3], runs[4] = runs[4], runs[3]
        with self.assertRaises(ValueError): audit_rows(runs, plan, bound, audit_row, synthetic_video)

    def test_actual_cpu_tensor_bytes_root_SHA_finiteness_and_warm_count(self):
        _, bound, plan, runs = fixture()
        row = copy.deepcopy(next(r for r in runs if r['id'] == 'warm_1_NATIVE18'))
        planned = next(p for p in plan if p['id'] == row['id'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); final = root / 'final.pt'; guide = root / 'guide.pt'
            def save(path, key, tensor):
                torch.save({key: tensor}, path)
                return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
            row['final_artifact'] = save(final, 'final_latent', torch.tensor([1., 2.]))
            row['final_latent_sha256'] = tree_digest(torch.tensor([1., 2.]))
            vectors = [torch.tensor([float(i), 1.]) for i in range(19)]
            row['warm_guided_artifact'] = save(guide, 'guided', vectors)
            row['warm_guided_tree_sha256'] = tree_digest(vectors)
            audit_payload(row, planned, bound, root, expected_shape=(2,))
            self.assertEqual(len(read_tensor(root, row['warm_guided_artifact'], 'guided')), 19)
            with self.assertRaises(ValueError): artifact_path(root, {**row['final_artifact'], 'sha256': '0' * 64})
            outside = root / 'other'; outside.mkdir()
            with self.assertRaises(ValueError): artifact_path(outside, row['final_artifact'])
            vectors[0][0] = float('nan')
            row['warm_guided_artifact'] = save(guide, 'guided', vectors)
            # Keep the original finite receipt digest; even forging a digest
            # through tree_digest is refused for nonfinite tensors.
            with self.assertRaises(ValueError): audit_payload(row, planned, bound, root, expected_shape=(2,))
            row['warm_guided_artifact'] = save(guide, 'guided', [torch.ones(2)] * 36)
            row['warm_guided_tree_sha256'] = tree_digest([torch.ones(2)] * 36)
            with self.assertRaises(ValueError): audit_payload(row, planned, bound, root, expected_shape=(2,))

    def test_all93_RGB_hash_metadata_with_explicit_mock_reader(self):
        import numpy as np
        rgb = np.zeros((432, 768, 3), dtype=np.uint8)
        metadata = dict(frames=93, HWC=[432, 768, 3], fps=16, pts=list(range(93)), time_base='1/16')
        @contextmanager
        def source(path):
            yield iter((rgb, i, '1/16') for i in range(93))
        @contextmanager
        def truncated(path):
            yield iter((rgb, i, '1/16') for i in range(92))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); video = root / 'SYNTHETIC_NOT_REAL_VIDEO.mp4'
            video.write_bytes(b'SYNTHETIC_READER_METADATA_CONTROL_ONLY')
            with patch('wcomr.rv0_video_reader.probe_video', return_value=metadata):
                with patch('wcomr.rv0_video_reader.decoded_video', source):
                    result = inspect_video(root, dict(video_path=str(video)))
                self.assertEqual(len(result['video_artifact']['decoded_rgb_sha256']), 93)
                self.assertEqual(result['video_artifact']['sha256'], sha(video))
                with patch('wcomr.rv0_video_reader.decoded_video', truncated):
                    with self.assertRaises(ValueError): inspect_video(root, dict(video_path=str(video)))


if __name__ == '__main__': unittest.main()
