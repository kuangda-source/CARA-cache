"""Original terminal trigger and single CPU child; no real waiting or workers."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_runtime_profile40_supervision_r1 import fixture, load_script, run_supervisor, process
from wcomr.runtime_profile40_production_r1 import CONFIG, RUN, COUNTS
from wcomr.frozen_shared_production_r1 import sha, write


def trigger(root, values, *, live_sequence=None, exit_code=0, supervisor_change=None):
    _, _, stage, registration, _, _ = values
    supervisor_path = root / 'outputs' / RUN / 'supervisor.json'
    supervisor = json.loads(supervisor_path.read_text())
    identity = dict(pid=supervisor['pid'], start_ticks=supervisor['start_ticks'])
    if supervisor_change:
        supervisor.update(supervisor_change); write(supervisor_path, supervisor)
    module = load_script('watch_wc_paper_N09_post_cpu_r1')
    fake_child = SimpleNamespace(pid=65432, wait=lambda:exit_code)
    def spawn(*a, **kw):
        write(stage / 'N09-CPU-final-results.json', dict(status='SYNTHETIC_NOT_REAL_CPU_POST',
            scope_counts=COUNTS, error_retained=exit_code != 0))
        return fake_child
    with patch('wcomr.gpu_budget_pool_v2.same_live_process', side_effect=live_sequence if live_sequence is not None else [False, False]), \
            patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
            patch.object(module.time, 'sleep') as sleeps, \
            patch.object(module.subprocess, 'Popen', side_effect=spawn) as spawned:
        receipt = module.run(root, stage, identity)
    return receipt, spawned, sleeps


class RuntimeProfile40PostWatcherControls(unittest.TestCase):
    def test_original_supervisor_terminal_starts_one_CPU_child_and_keeps_full_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); run_supervisor(root, values)
            receipt, spawned, sleeps = trigger(root, values)
            self.assertEqual(spawned.call_count, 1); sleeps.assert_not_called()
            command = spawned.call_args.args[0]
            self.assertTrue(command[1].endswith('postprocess_wc_paper_N09_runtime_profile40_r1.py'))
            self.assertEqual(spawned.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
            self.assertEqual(receipt['exit_code'], 0); self.assertEqual(receipt['scope_counts'], COUNTS)
            self.assertEqual(receipt['source_revision'], values[3]['source_revision'])
            self.assertEqual(receipt['final_result_sha256'], sha(values[2] / 'N09-CPU-final-results.json'))
            self.assertTrue((values[2] / 'N09-post-CPU-child.json').is_file())
            self.assertEqual(json.loads((values[2] / 'N09-post-CPU-exit.json').read_text()), receipt)

    def test_waits_for_exact_original_process_then_triggers_without_scientific_poll(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); run_supervisor(root, values)
            receipt, spawned, sleeps = trigger(root, values, live_sequence=[True, False, False])
            sleeps.assert_called_once_with(10); self.assertEqual(spawned.call_count, 1)
            self.assertEqual(receipt['exit_code'], 0)

    def test_original_start_ticks_or_source_change_is_not_a_valid_terminal_trigger(self):
        for mode in ('identity', 'source'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root = Path(folder); values = fixture(root); state, _, _ = run_supervisor(root, values)
                module = load_script('watch_wc_paper_N09_post_cpu_r1')
                original = dict(pid=state['pid'], start_ticks=state['start_ticks'])
                changed = copy.deepcopy(state)
                if mode == 'identity':changed['start_ticks'] += 1
                else:changed['source_revision'] = '2' * 40
                write(root / 'outputs' / RUN / 'supervisor.json', changed)
                with patch('wcomr.gpu_budget_pool_v2.same_live_process', return_value=False), \
                        patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
                        patch.object(module.subprocess, 'Popen') as spawned:
                    with self.assertRaises(ValueError):module.run(root, values[2], original)
                spawned.assert_not_called()
                self.assertEqual(json.loads((values[2] / 'N09-post-CPU-exit.json').read_text())['exit_code'], 1)
                self.assertFalse((values[2] / 'N09-CPU-final-results.json').exists())

    def test_live_GPU_child_prevents_post_even_if_supervisor_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); state, _, _ = run_supervisor(root, values)
            module = load_script('watch_wc_paper_N09_post_cpu_r1')
            identity = dict(pid=state['pid'], start_ticks=state['start_ticks'])
            with patch('wcomr.gpu_budget_pool_v2.same_live_process', side_effect=[False, True]), \
                    patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
                    patch.object(module.subprocess, 'Popen') as spawned:
                with self.assertRaises(ValueError):module.run(root, values[2], identity)
            spawned.assert_not_called()

    def test_failed_CPU_exit_and_prior_result_are_preserved_without_second_child(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); run_supervisor(root, values)
            receipt, spawned, _ = trigger(root, values, exit_code=3)
            self.assertEqual(receipt['exit_code'], 3); self.assertEqual(spawned.call_count, 1)
            old_exit = (values[2] / 'N09-post-CPU-exit.json').read_bytes()
            old_final = (values[2] / 'N09-CPU-final-results.json').read_bytes()
            with self.assertRaises(FileExistsError):trigger(root, values)
            self.assertEqual((values[2] / 'N09-post-CPU-exit.json').read_bytes(), old_exit)
            self.assertEqual((values[2] / 'N09-CPU-final-results.json').read_bytes(), old_final)
            module = load_script('watch_wc_paper_N09_post_cpu_r1')
            args = ['SYNTHETIC', '--project', str(root), '--stage', str(values[2]),
                '--supervisor-pid', '123', '--supervisor-start-ticks', '1230']
            with patch.object(sys, 'argv', args),patch.object(sys, 'path', list(sys.path)), \
                    patch.object(module, 'run', return_value={'exit_code': 3}):
                with self.assertRaises(SystemExit) as caught:module.main()
            self.assertEqual(caught.exception.code, 3)

    def test_existing_CPU_terminal_result_blocks_before_claiming_new_watcher(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); state, _, _ = run_supervisor(root, values)
            original = dict(status='ORIGINAL_EXISTING_CPU_RESULT_KEEP', exit_code=1)
            write(values[2] / 'N09-post-CPU-exit.json', original)
            module = load_script('watch_wc_paper_N09_post_cpu_r1')
            with self.assertRaises(FileExistsError):module.run(root, values[2], state['supervisor_identity'])
            self.assertFalse((values[2] / 'N09-post-CPU-request.json').exists())
            self.assertEqual(json.loads((values[2] / 'N09-post-CPU-exit.json').read_text()), original)


if __name__ == '__main__':unittest.main()
