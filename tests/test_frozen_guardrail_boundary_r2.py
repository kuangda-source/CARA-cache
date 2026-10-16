import copy
import unittest

from wcomr.frozen_guardrail_boundary_r2 import requires_complete_mask


def refusal():
    return dict(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0,
        source_history=[], in_timing_guided_copies=0, in_timing_hashes=0,
        research_checkpoints=0, video_path=None)


class GuardrailBoundary(unittest.TestCase):
    def test_ordinary_zero_step_refusal_keeps_its_outcome(self):
        value = refusal(); before = copy.deepcopy(value)
        self.assertFalse(requires_complete_mask(value, []))
        self.assertEqual(value, before)

    def test_partial_computation_cannot_be_relabelled_a_text_refusal(self):
        variants = [dict(solver_steps=1), dict(guided_pairs=1), dict(source_history=[{}]),
            dict(actions=['DD']), dict(A_history=[{}]), dict(guided=[1]),
            dict(final_latent=0), dict(video_path='rejected.mp4'),
            dict(in_timing_guided_copies=1), dict(in_timing_hashes=1),
            dict(research_checkpoints=1)]
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                requires_complete_mask({**refusal(), **changed}, [])
        with self.assertRaises(ValueError):
            requires_complete_mask(refusal(), ['D'])

    def test_missing_zero_counters_are_not_assumed_to_be_zero(self):
        for name in ('solver_steps', 'guided_pairs', 'in_timing_guided_copies',
                     'in_timing_hashes', 'research_checkpoints'):
            value = refusal(); del value[name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                requires_complete_mask(value, [])

    def test_full_sampling_and_video_refusal_still_require_the_original_mask(self):
        for status in ('COMPLETE', 'VIDEO_REJECTED'):
            self.assertTrue(requires_complete_mask(dict(status=status), ['D']))
        for status in ('RUNNING', 'TECH_FAILED', 'NOT_REACHED', None):
            with self.assertRaises(ValueError):
                requires_complete_mask(dict(status=status), [])


if __name__ == '__main__':
    unittest.main()
