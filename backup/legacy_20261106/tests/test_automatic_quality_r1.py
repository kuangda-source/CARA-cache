"""Wrong identities, missing seeds and static scope cannot inflate quality."""
import copy
import unittest

from wcomr.automatic_quality_r1 import (
    DIMENSIONS, VBENCH_COMMIT, build_inputs, fingerprint, sampling_spec,
    summarize, text_sha, vbench_metadata,
)


def fixture():
    cases = []
    methods = ['SYNTHETIC_METHOD_' + str(i) for i in range(10)]
    generation = []
    for prompt in range(8):
        text = 'Synthetic original inference prompt ' + str(prompt)
        for seed in (17, 43):
            case = dict(id=f'case{prompt}_seed{seed}', prompt_id='prompt' + str(prompt),
                        seed=seed, prompt=text, prompt_sha256=text_sha(text), static_eligible=prompt < 4)
            cases.append(case)
            for method in methods:
                file_sha = fingerprint([case['id'], method, 'mock_byte_identity'])
                generation.append(dict(case_id=case['id'], method=method, status='COMPLETE',
                    endpoint_audit='PASS', video_artifact=dict(path=f'/SYNTHETIC_ONLY/{case["id"]}/{method}.mp4',
                        sha256=file_sha, frames=93, fps=16, width=768, height=432,
                        decoded_rgb_sha256=[fingerprint([file_sha, i]) for i in range(93)])))
    evaluator = dict(vbench_commit=VBENCH_COMMIT, fixture='SYNTHETIC_NO_REAL_RESOURCES_OR_METRIC_MODEL')
    bundle = build_inputs(cases, methods, generation, list(DIMENSIONS), evaluator)
    scores = []
    for planned in bundle['rows']:
        row = {k: planned[k] for k in ('case_id', 'method', 'dimension')}
        if planned['input_status'] != 'READY_TO_SCORE':
            row.update(status=planned['input_status'], value=None)
        else:
            method = methods.index(planned['method'])
            prompt = int(planned['prompt_id'].removeprefix('prompt'))
            value = .5 + .01 * prompt + .001 * method
            if planned['dimension'] == 'dynamic_degree': value = bool(method % 2)
            row.update(status='SCORED', value=value,
                **{k: planned[k] for k in ('video_sha256', 'prompt_sha256', 'scorer_fingerprint')},
                observed_sampling=copy.deepcopy(planned['expected_sampling']))
            if planned['dimension'] == 'MUSIQ_LONGER512': row['frame_scores'] = [value] * 93
        scores.append(row)
    return cases, methods, generation, evaluator, bundle, scores


class AutomaticQualityControls(unittest.TestCase):
    def test_source_sampling_counts(self):
        self.assertEqual(sampling_spec('overall_consistency')['frame_indices'], [5, 16, 28, 39, 51, 63, 74, 86])
        self.assertEqual(len(sampling_spec('dynamic_degree')['frame_indices']), 47)
        motion = sampling_spec('motion_smoothness')
        self.assertEqual(len(motion['frame_indices']), 47)
        self.assertEqual(len(motion['target_indices']), 46)
        self.assertEqual(sampling_spec('MUSIQ_LONGER512')['frame_indices'], list(range(93)))

    def test_explicit_prompt_metadata(self):
        cases, methods, generation, evaluator, bundle, _ = fixture()
        meta = vbench_metadata(bundle, 'overall_consistency')
        self.assertEqual(len(meta), 8)
        self.assertEqual(sum(len(r['video_list']) for r in meta), 160)
        self.assertEqual(meta[0]['prompt_en'], cases[0]['prompt'])
        changed = copy.deepcopy(bundle)
        changed['rows'][0]['prompt'] = 'Changed after identity freeze'
        with self.assertRaises(ValueError): vbench_metadata(changed, 'overall_consistency')
        cases[0]['prompt_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build_inputs(cases, methods, generation, list(DIMENSIONS), evaluator)

    def test_complete_prompt_grouped_summary_and_roles(self):
        _, methods, _, _, bundle, rows = fixture()
        result = summarize(bundle, rows, [(methods[1], methods[0])])
        self.assertEqual(result['registered_generation_positions'], 160)
        self.assertEqual(result['registered_metric_positions'], 960)
        self.assertTrue(result['no_cross_dimension_total'])
        for row in result['comparisons']:
            if row['dimension'] == 'dynamic_degree':
                self.assertEqual(row['full_eligible_prompt_mean_delta'], 1.)
                self.assertFalse(row['positive_delta_is_better_on_this_dimension'])
            else:
                self.assertAlmostEqual(row['full_eligible_prompt_mean_delta'], .001)
        static = next(r for r in result['comparisons'] if r['dimension'] == 'temporal_flickering')
        self.assertEqual(static['eligible_prompt_denominator'], 4)

    def test_missing_seed_keeps_whole_prompt_missing(self):
        _, methods, _, _, bundle, rows = fixture()
        target = next(r for r in rows if r['method'] == methods[1] and r['case_id'] == 'case0_seed43'
                      and r['dimension'] == 'overall_consistency')
        target.update(status='METRIC_FAILED', value=None)
        result = summarize(bundle, rows, [(methods[1], methods[0])])
        contrast = next(r for r in result['comparisons'] if r['dimension'] == 'overall_consistency')
        self.assertIsNone(contrast['full_eligible_prompt_mean_delta'])
        self.assertEqual(contrast['missing_eligible_prompt_ids'], ['prompt0'])
        self.assertEqual(len(contrast['complete_paired_prompt_ids']), 7)

    def test_generation_failures_and_unscorable_audits_preserved(self):
        cases, methods, generation, evaluator, _, _ = fixture()
        generation[0].update(status='TEXT_REJECTED', video_artifact=None, endpoint_audit=None)
        generation[1]['endpoint_audit'] = 'FAIL_BAD_CONTAINER'
        bundle = build_inputs(cases, methods, generation, list(DIMENSIONS), evaluator)
        unavailable = [r for r in bundle['rows'] if r['input_status'] == 'VIDEO_UNAVAILABLE']
        self.assertEqual(len(unavailable), 12)
        self.assertEqual({r['original_generation_status'] for r in unavailable}, {'TEXT_REJECTED', 'COMPLETE'})
        with self.assertRaises(ValueError):
            build_inputs(cases, methods, generation[:-1], list(DIMENSIONS), evaluator)

    def test_video_prompt_evaluator_and_sample_mismatch_rejected(self):
        _, methods, _, _, bundle, original = fixture()
        for field in ('video_sha256', 'prompt_sha256', 'scorer_fingerprint'):
            rows = copy.deepcopy(original)
            rows[0][field] = '0' * 64
            with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])
        rows = copy.deepcopy(original)
        row = next(r for r in rows if r['dimension'] == 'overall_consistency' and r['status'] == 'SCORED')
        row['observed_sampling']['frame_indices'] = list(range(93))
        with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])

    def test_static_scope_and_missing_zero_fill_rejected(self):
        _, methods, _, _, bundle, original = fixture()
        rows = copy.deepcopy(original)
        row = next(r for r in rows if r['status'] == 'NOT_APPLICABLE_STATIC_SCOPE')
        row.update(status='SCORED', value=.99)
        with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])
        rows = copy.deepcopy(original)
        rows[0].update(status='RESOURCE_UNAVAILABLE', value=0.)
        with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])

    def test_musiq_frame_average_nonfinite_and_duplicate_rows_rejected(self):
        _, methods, _, _, bundle, original = fixture()
        rows = copy.deepcopy(original)
        next(r for r in rows if r['dimension'] == 'MUSIQ_LONGER512')['frame_scores'].pop()
        with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])
        rows = copy.deepcopy(original)
        rows[0]['value'] = float('nan')
        with self.assertRaises(ValueError): summarize(bundle, rows, [(methods[1], methods[0])])
        with self.assertRaises(ValueError): summarize(bundle, original + [original[0]], [(methods[1], methods[0])])


if __name__ == '__main__':
    unittest.main()
