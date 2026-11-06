"""Full40 post controls with explicit fake videos/scores and tiny CPU tensors."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr import balanced_repeat_post_r1 as post
from wcomr.balanced_repeat_production_r1 import archive_output, RUN
from wcomr.frozen_shared_production_r1 import sha
from wcomr.mid_coverage import tree_digest

SPEC = importlib.util.spec_from_file_location('synthetic_post_full40_inputs',
    Path(__file__).with_name('test_balanced_repeat_production_r1.py'))
FIXTURE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(FIXTURE)


def fixture():
    _, _, _, _, bound, samples = FIXTURE.fixture()
    rows = []
    for planned in bound['execution_plan']:
        sample = samples[(planned['scene'], planned['slot'])]
        raw = FIXTURE.FIXTURE.response(planned, sample); raw.pop('guided', None)
        digest = hashlib.sha256((planned['scene'] + planned['method']).encode()).hexdigest()
        row = {**planned, **raw}
        row.update(final_latent_sha256=digest, A_history=None if planned['slot'] == 'FULL_NATIVE' else [],
            final_artifact=dict(path='/SYNTHETIC/' + planned['id'] + '/final.pt', sha256=digest, bytes=1),
            video_path='/SYNTHETIC/' + planned['id'] + '/output.mp4',
            synthetic_RGB_sha256=digest, pre_request_state_identity=dict(
                original_state_sha256='1' * 64, restored_state_sha256='1' * 64, shared_eval_verified=True))
        if planned['section'] == 'WARMUP':
            row.update(warm_guided_artifact=dict(path='/SYNTHETIC/' + planned['id'] + '/warm.pt', sha256=digest, bytes=1),
                       warm_guided_tree_sha256=digest)
        rows.append(row)
    return bound, rows


def video(row):
    # Container identities differ between rounds. RGB identities remain equal.
    encoded = hashlib.sha256(row['id'].encode()).hexdigest(); rgb = row['synthetic_RGB_sha256']
    return dict(video_artifact=dict(path=row['video_path'], sha256=encoded, bytes=1,
        frames=93, fps=16, width=768, height=432, decoded_rgb_sha256=[rgb] * 93),
        decoded_video=dict(frames=93, RGB_sha256=rgb))


def score(reference, candidate):
    if reference['scene'] != candidate['scene'] or reference['round'] != candidate['round']:
        raise AssertionError('SYNTHETIC_CROSS_ROUND_REFERENCE')
    value = 0. if candidate['slot'] == 'FULL_NATIVE' else .2
    return dict(frames=93, frame_distances=[value] * 93, mean_LPIPS=sum([value] * 93) / 93,
        reference_sha256=reference['video_artifact']['sha256'], candidate_sha256=candidate['video_artifact']['sha256'])


def evaluate(bound, rows, *, inspector=video, scorer=score, child_exit_code=0):
    result = post.audit_rows(rows, bound, post.metadata_audit, inspector)
    warm, repeated, failed = post.repeat_controls(result['rows'], bound)
    result.update(warm_trace_controls=warm, formal_to_warm_controls=repeated)
    result['audit_failures'].extend(failed)
    result['audit_failures'].extend(post.score_rows(result['rows'], scorer))
    result.update(post.summarize(result, bound, observed_paths=len(rows), child_exit_code=child_exit_code))
    return result


class Full40PostControls(unittest.TestCase):
    def test_all40_raw_controls_30_same_round_scores_and_all_reported_rounds(self):
        bound, rows = fixture(); original = copy.deepcopy(rows)
        result = evaluate(bound, rows)
        self.assertEqual(result['status'], post.COMPLETE_STATUS)
        self.assertEqual(rows, original)
        self.assertEqual(result['scored_scientific_videos'], 30)
        self.assertEqual(len(result['warm_trace_controls']), 10)
        self.assertEqual(len(result['formal_to_warm_controls']), 30)
        self.assertEqual(len(result['all_formal_observations']), 30)
        self.assertEqual(len(result['timing_statistics']['scene_methods']), 10)
        self.assertEqual(len(result['timing_statistics']['contrasts']), 6)
        self.assertTrue(all(len(r['rounds']) == 3 for r in result['timing_statistics']['scene_methods']))
        self.assertFalse(result['stable_repeated_clean_speed_claim'])
        self.assertFalse(result['clean_interval_resource_state_accepted'])

    def test_one_broken_container_keeps_raw_clock_and_other29_scores(self):
        bound, rows = fixture()
        target = next(r for r in rows if r['section'] == 'TIMED' and r['slot'] == 'GCR_EFFICIENT')
        def broken(row):
            if row['id'] == target['id']: raise ValueError('SYNTHETIC_BAD_CONTAINER')
            return video(row)
        result = evaluate(bound, rows, inspector=broken)
        observed = next(r for r in result['rows'] if r['id'] == target['id'])
        self.assertEqual(observed['status'], 'COMPLETE')
        self.assertEqual(observed['raw_model_audit'], 'PASS')
        self.assertEqual(result['scored_scientific_videos'], 29)
        table = next(r for r in result['timing_statistics']['scene_methods']
                     if r['scene'] == target['scene'] and r['slot'] == target['slot'])
        self.assertEqual(table['valid_time_repeats'], 3)
        self.assertEqual(table['valid_quality_repeats'], 2)
        self.assertIsNone(table['complete_repeat_mean_LPIPS'])
        self.assertIn('AUDIT_FAILURE', result['status'])

    def test_missing_round_native_never_borrows_warm_or_other_round_reference(self):
        bound, rows = fixture()
        target = next(r for r in rows if r['section'] == 'TIMED' and r['slot'] == 'FULL_NATIVE' and r['round'] == 2)
        def broken(row):
            if row['id'] == target['id']: raise ValueError('SYNTHETIC_MISSING_NATIVE_ROUND')
            return video(row)
        result = evaluate(bound, rows, inspector=broken)
        self.assertEqual(result['scored_scientific_videos'], 25)
        affected = [r for r in result['rows'] if r['section'] == 'TIMED'
                    and r['scene'] == target['scene'] and r['round'] == 2]
        self.assertTrue(all('LPIPS' not in r for r in affected))

    def test_wrong_round_score_identity_is_retained_as_metric_failure(self):
        bound, rows = fixture()
        def wrong(reference, row): return {**score(reference, row), 'reference_sha256': '0' * 64}
        result = evaluate(bound, rows, scorer=wrong)
        self.assertEqual(result['scored_scientific_videos'], 0)
        self.assertEqual(sum(e['kind'] == 'LPIPS' for e in result['audit_failures']), 30)

    def test_numeric_source_change_keeps_actual_scores_but_not_certified_primary_repeat(self):
        bound, rows = fixture()
        target = next(r for r in rows if r['section'] == 'TIMED' and r['slot'] == 'CPA_HIGH_FIDELITY')
        target['source_history'][0]['true_D_after'] = 'OTHER_D_ANCHOR_NUMERICAL_STATE'
        result = evaluate(bound, rows)
        self.assertEqual(result['scored_scientific_videos'], 30)
        control = next(r for r in result['formal_to_warm_controls'] if r['id'] == target['id'])
        self.assertEqual(control['status'], 'REPEAT_CONTROL_FAILURE_RETAINED')
        table = next(r for r in result['timing_statistics']['scene_methods']
                     if r['scene'] == target['scene'] and r['slot'] == target['slot'])
        self.assertEqual(table['valid_time_repeats'], 2)
        self.assertIsNone(table['complete_repeat_mean_seconds'])
        self.assertIsNotNone(next(r for r in result['all_formal_observations'] if r['id'] == target['id'])['observed_LPIPS'])

    def test_native_repeat_failure_does_not_crash_other_scored_rows(self):
        bound, rows = fixture()
        target = next(r for r in rows if r['section'] == 'TIMED' and r['slot'] == 'FULL_NATIVE')
        target['final_latent_sha256'] = '0' * 64
        result = evaluate(bound, rows)
        self.assertEqual(result['scored_scientific_videos'], 30)
        self.assertEqual(len(result['timing_statistics']['scene_methods']), 10)
        self.assertIn('AUDIT_FAILURE', result['status'])

    def test_owner_address_only_changes_are_ignored_but_RGB_change_is_not(self):
        bound, rows = fixture()
        target = next(r for r in rows if r['section'] == 'TIMED' and r['slot'] == 'CPA_HIGH_FIDELITY')
        target['source_history'][0]['owner'] = 'DIFFERENT_REQUEST_LOCAL_OBJECT_ADDRESS'
        self.assertEqual(evaluate(bound, rows)['status'], post.COMPLETE_STATUS)
        target['synthetic_RGB_sha256'] = '0' * 64
        result = evaluate(bound, rows)
        self.assertIn('AUDIT_FAILURE', result['status'])

    def test_text_rejection_and_technical_prefix_keep_all40_positions(self):
        bound, rows = fixture(); planned = next(p for p in bound['execution_plan']
            if p['section'] == 'TIMED' and p['slot'] == 'GCR_EFFICIENT')
        index = next(i for i, r in enumerate(rows) if r['id'] == planned['id'])
        rows[index] = {**planned, 'status': 'TEXT_REJECTED', 'solver_steps': 0, 'guided_pairs': 0,
                       'pre_request_state_identity': rows[index]['pre_request_state_identity']}
        result = evaluate(bound, rows)
        self.assertEqual(result['scored_scientific_videos'], 29)
        self.assertEqual(result['status'], 'N08_FULL40_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
        bound, rows = fixture(); prefix = rows[:8]; prefix[-1]['status'] = 'RUNNING'
        result = evaluate(bound, prefix, child_exit_code=1)
        self.assertEqual(len(result['rows']), 40)
        self.assertEqual(sum(r['status'] == 'NOT_REACHED' for r in result['rows']), 32)
        self.assertEqual(result['rows'][7]['status'], 'TECH_FAILED')
        self.assertIn('TECHNICAL_INCOMPLETE', result['status'])

    def test_actual_tiny_CPU_artifacts_use_seed0_mapped_audit_and_finite36_guides(self):
        bound, rows = fixture()
        row = copy.deepcopy(next(r for r in rows if r['section'] == 'WARMUP' and r['slot'] == 'FULL_NATIVE'))
        planned = next(p for p in bound['execution_plan'] if p['id'] == row['id'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); row.pop('video_path')
            row.update(final_latent=torch.ones(2), guided=[torch.tensor([float(i), 1.]) for i in range(36)])
            actual = archive_output(row, planned, root / row['id'], root, expected_shape=(2,))
            post.audit_payload(actual, planned, bound, root, expected_shape=(2,))
            path = Path(actual['warm_guided_artifact']['path'])
            values = [torch.ones(2)] * 35; torch.save({'guided': values}, path)
            actual['warm_guided_artifact'].update(sha256=sha(path), bytes=path.stat().st_size)
            actual['warm_guided_tree_sha256'] = tree_digest(values)
            with self.assertRaises(ValueError): post.audit_payload(actual, planned, bound, root, expected_shape=(2,))

    def test_whole_v2_intervals_detect_transient_overlap_missed_by_boundaries(self):
        pool = dict(jobs={'old_without_recorded_start': dict(status='SETTLED', settled_unix=5),
            RUN: dict(status='SETTLED', reserved_unix=10, settled_unix=50),
            'transient': dict(status='SETTLED', reserved_unix=20, settled_unix=21),
            'later': dict(status='RESERVED_OR_RUNNING', reserved_unix=60)})
        result = post.registered_interval_overlaps(pool, RUN, 10, 50)
        self.assertEqual([r['job_id'] for r in result['recorded_GPU_job_overlaps']], ['transient'])
        self.assertFalse(result['external_unrecorded_GPU_or_transient_CPU_interference_excluded'])
        pool['jobs']['transient']['settled_unix'] = 9
        pool['jobs']['transient']['reserved_unix'] = 8
        self.assertTrue(post.registered_interval_overlaps(pool, RUN, 10, 50)['no_recorded_GPU_overlap'])
        pool['jobs']['later'].pop('reserved_unix')
        with self.assertRaises(ValueError): post.registered_interval_overlaps(pool, RUN, 10, 50)


if __name__ == '__main__': unittest.main()
