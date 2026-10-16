"""Full selected180 fake end points; all numbers are synthetic test fixtures."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr.frozen_repair_acceptance_r2 import accept,derived_acceptor
from wcomr.gpu_budget_pool_v2 import BudgetPool


def fixture():
    path=Path(__file__).with_name('repair_gpu_fixture_r2.py');s=importlib.util.spec_from_file_location('synthetic_full180_repair',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.fixture()


class RepairTerminalControls(unittest.TestCase):
    def test_all180_full_frame_original_statistics_and_large_card_fee_accept(self):
        value,launch=fixture();result=accept(value,launch,bootstrap_repetitions=8)
        self.assertTrue(result['scientific_full_scope_accepted']);self.assertEqual(result['scored_scientific_videos'],160)
        self.assertEqual(result['original_runner_paths'],180);self.assertEqual(result['actual_GPUh'],1.)
        self.assertEqual(result['grouped_statistics']['registered_prompt_groups'],8)
        self.assertTrue(result['repair_terminal_acceptor_derivation']['inverse_bytes_and_AST_equal'])

    def test_original_old_run_or_wrong_CPU_proof_cannot_become_repair_result(self):
        value,launch=fixture()
        changed=copy.deepcopy(value);changed['launch']['run_id']='wc-paper-n07-frozen-shared180-r1'
        with self.assertRaises(ValueError):accept(changed,changed['launch'],bootstrap_repetitions=8)
        changed=copy.deepcopy(value);changed['production_CPU']['guardrail_checks']=changed['production_CPU']['guardrail_checks'][:-1]
        with self.assertRaises(ValueError):accept(changed,launch,bootstrap_repetitions=8)

    def test_wrong_actual_cost_own_UUID_or_changed_frame_identity_refused(self):
        value,launch=fixture();variants=[]
        bad=copy.deepcopy(value);bad['billing']['actual_GPUh']=20.;variants.append(bad)
        bad=copy.deepcopy(value);bad['own_UUID_lock_free']=False;variants.append(bad)
        bad=copy.deepcopy(value);bad['final']['rows'][30]['video_artifact']['decoded_rgb_sha256']=[];variants.append(bad)
        for changed in variants:
            with self.assertRaises(ValueError):accept(changed,launch,bootstrap_repetitions=8)

    def test_other_GPU_work_does_not_invalidate_own_release(self):
        value,launch=fixture();value['compute_apps']='GPU-OTHER-LEGAL, 999\n'
        self.assertTrue(accept(value,launch,bootstrap_repetitions=8)['own_GPU_and_finance_released'])

    def test_original_handle_alive_and_missing_post_remain_unaccepted(self):
        value,launch=fixture();alive=copy.deepcopy(value)
        alive['original_processes']['child_pid']={**value['supervisor']['child_identity'],'state':'S'}
        result=accept(alive,launch,bootstrap_repetitions=8)
        self.assertIn('STILL_RUNNING',result['status']);self.assertFalse(result['scientific_full_scope_accepted'])
        missing=copy.deepcopy(value);del missing['post_exit']
        result=accept(missing,launch,bootstrap_repetitions=8)
        self.assertFalse(result['scientific_full_scope_accepted']);self.assertTrue(result['no_GPU_relaunch_authorized'])


if __name__=='__main__':unittest.main()
