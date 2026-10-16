"""Output identity isolation and fail-closed controls; no remote/result query."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_input_exposure_r1 import Identities, collect_outputs, registered_jobs

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('identity_capture',
    ROOT / 'scripts/capture_wc_paper_N07_fresh_identity_r1.py')
CAPTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAPTURE)


def records():
    return [dict(name=name, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                 category=name.split('_')[0], group_members=[name])
            for name, prompt in [('av_1', 'synthetic first prompt'),
                                 ('av_10', 'synthetic second prompt'),
                                 ('human_2', 'synthetic third prompt')]]


def development():
    moment = CAPTURE.N05_COLLECTION_UNIX
    return dict(N05=dict(status='N05_CORE66_INDEPENDENTLY_ACCEPTED',
                        full_denominator=66, formal_denominator=44),
        N06=dict(status='SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED',
                 full_denominator=36, formal_denominator=24),
        latest_development_observed_unix=moment + 1)


def freeze():
    return dict(method_ids=['NATIVE35', 'NATIVE26', 'NATIVE18', 'WC_DEFAULT', 'RA_DEFAULT',
        'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A', 'UNIFORM_C'],
        parameters_frozen_from='DEVELOPMENT_ONLY', final_test_outputs_seen=False,
        freeze_unix=CAPTURE.N05_COLLECTION_UNIX + 2)


class OutputIdentities(unittest.TestCase):
    def test_name_prompt_hash_path_and_keys_export_no_outcomes(self):
        rs = records(); index = Identities(rs)
        data = {'av_10': {'prompt': 'synthetic first prompt', 'lpips': 0.987654321,
                          'seconds': 987654.321,
                          'video': '/arbitrary/human_2_method_seed17/out.mp4'},
                'prompt_sha256': rs[1]['prompt_sha256']}
        hits, skipped = index.document(data)
        self.assertEqual({h['name'] for h in hits}, {'av_1', 'av_10', 'human_2'})
        self.assertFalse(skipped)
        self.assertNotIn('0.987654321', json.dumps(hits))
        self.assertNotIn('987654.321', json.dumps(hits))
        self.assertEqual(index.match('av_10_method_seed43.mp4'), 'av_10')
        self.assertEqual(index.match('av_1.json'), 'av_1')
        self.assertIsNone(index.match('av_100'))

    def test_full_catalog_and_declared_identity_metadata_are_not_exposure(self):
        rs = records(); original = copy.deepcopy(rs); index = Identities(rs)
        hits, skipped = index.document({'catalog_copy': list(reversed(rs)),
            'eligible_pools': {'av': ['av_1', 'av_10']},
            'identity_hits': {'human_2': ['old audit metadata']},
            'executed': {'name': 'av_1'}})
        self.assertEqual([h['name'] for h in hits], ['av_1'])
        self.assertEqual(len(skipped), 3)
        self.assertEqual(rs, original)
        # A partial list used by a run is conservatively retained, not erased.
        self.assertEqual({h['name'] for h in index.document([rs[2]])[0]}, {'human_2'})

    def test_only_output_names_and_declared_result_json_are_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'outputs'; out.mkdir()
            (root / 'vendor').mkdir(); (root / 'vendor' / 'receipt.json').write_text(
                json.dumps({'name': 'av_10'}))
            (out / 'run').mkdir()
            raw = json.dumps({'rows': [{'name': 'av_1', 'seconds': 9182.739}]})
            (out / 'run' / 'runner.json').write_text(raw)
            (out / 'human_2_probe.mp4').write_bytes(b'not decoded')
            value = collect_outputs(root, records())
            self.assertEqual(set(value['identity_hits']), {'av_1', 'human_2'})
            self.assertEqual(len(value['documents']), 1)
            self.assertEqual(value['documents'][0]['sha256'], hashlib.sha256(raw.encode()).hexdigest())
            self.assertNotIn('9182.739', json.dumps(value))
            self.assertFalse(value['videos_or_tensors_decoded'])
            self.assertFalse(value['read_errors'])

    def test_malformed_json_and_missing_output_tree_are_preserved_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError): collect_outputs(root, records())
            (root / 'outputs').mkdir()
            (root / 'outputs' / 'receipt.json').write_text('{')
            value = collect_outputs(root, records())
            self.assertEqual(value['read_errors'][0]['error_type'], 'JSONDecodeError')
            self.assertEqual(value['documents'], [])

    def test_alias_is_not_duplicate_data_and_external_dangling_cycle_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'outputs'; out.mkdir()
            (out / 'runner.json').write_text(json.dumps({'name': 'av_1'}))
            (out / 'receipt.json').symlink_to(out / 'runner.json')
            value = collect_outputs(root, records())
            self.assertEqual(len(value['documents']), 1)
            self.assertFalse(value['read_errors'])
            (root / 'outside.json').write_text('{}')
            (out / 'external.json').symlink_to(root / 'outside.json')
            (out / 'dangling.json').symlink_to(out / 'missing.json')
            (out / 'cycle.json').symlink_to(out / 'cycle.json')
            value = collect_outputs(root, records())
            self.assertEqual({e['kind'] for e in value['read_errors']},
                {'EXTERNAL_OUTPUT_LINK_REQUIRES_EXPLICIT_SCOPE', 'MISSING_OUTPUT_LINK_TARGET', 'OUTPUT_LINK_ERROR'})

    def test_full_original1044_catalog_indexes_without_selecting_inputs(self):
        original = json.loads((ROOT / 'reports/dataset_source_group_audit_20260930.json').read_text())['records']
        index = Identities(original)
        self.assertEqual(len(index.records), 1044)
        hits, skipped = index.document(original)
        self.assertEqual(hits, [])
        self.assertEqual(skipped[0]['reason'], 'UNEXECUTED_WHOLE_SOURCE_CATALOG')
        for record in original:
            self.assertEqual(index.match(record['name'] + '_SYNTHETIC_seed43'), record['name'])
            self.assertEqual(index.match(record['prompt_sha256']), record['name'])

    def test_original_supervisor_identity_not_pid_reuse_or_cost_export(self):
        pool = dict(jobs={'original': dict(supervisor_pid=21, supervisor_start_ticks=30,
                                          status='SETTLED', actual_gpuh=829.29821)})
        value = registered_jobs(pool, lambda pid: dict(pid=pid, state='R', start_ticks=31))
        self.assertTrue(value['all_registered_GPU_jobs_terminal'])
        self.assertNotIn('829.29821', json.dumps(value))
        self.assertFalse(registered_jobs(pool,
            lambda pid: dict(pid=pid, state='R', start_ticks=30))['all_registered_GPU_jobs_terminal'])
        pool['jobs']['original']['status'] = 'RESERVED'
        self.assertFalse(registered_jobs(pool,
            lambda pid: dict(pid=pid, state=None, start_ticks=None))['all_registered_GPU_jobs_terminal'])

    def test_freeze_requires_accepted_complete_development_and_original_ETA(self):
        now = CAPTURE.N05_COLLECTION_UNIX + 3
        CAPTURE.before_audit(development(), freeze(), now)
        for mutation in ('early', 'partial', 'missing_denominator', 'seen_test', 'old_freeze', 'drop_front', 'unknown'):
            d, f, n = development(), freeze(), now
            if mutation == 'early': n = CAPTURE.N05_COLLECTION_UNIX - 1
            elif mutation == 'partial': d['N05']['status'] = 'RUNNING'
            elif mutation == 'missing_denominator': d['N06']['full_denominator'] = 35
            elif mutation == 'seen_test': f['final_test_outputs_seen'] = True
            elif mutation == 'old_freeze': f['freeze_unix'] = d['latest_development_observed_unix'] - 1
            elif mutation == 'drop_front': f['method_ids'][-2] = 'UNIFORM_A'
            else: f['method_ids'][-1] = 'P_ACR'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                CAPTURE.before_audit(d, f, n)

    def test_cli_refuses_before_any_git_or_SSH_when_development_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); d = root / 'dev.json'; f = root / 'freeze.json'; out = root / 'result.json'
            data = development(); data['N05']['status'] = 'RUNNING'
            d.write_text(json.dumps(data)); f.write_text(json.dumps(freeze()))
            argv = ['capture', '--development', str(d), '--method-freeze', str(f), '--output', str(out)]
            with patch('sys.argv', argv), patch.object(CAPTURE.time, 'time', return_value=CAPTURE.N05_COLLECTION_UNIX + 3), \
                    patch.object(CAPTURE.subprocess, 'run') as ssh, \
                    patch.object(CAPTURE.subprocess, 'check_output') as git, self.assertRaises(ValueError):
                CAPTURE.main()
            ssh.assert_not_called(); git.assert_not_called(); self.assertFalse(out.exists())

    def test_remote_body_on_local_fixture_reads_original_ledger_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'outputs').mkdir(); (root / 'reports').mkdir()
            (root / 'outputs' / 'runner.json').write_text(json.dumps({'name': 'av_1', 'lpips': 0.91234567}))
            ledger = root / 'reports/gpu-budget-v2.json'
            ledger.write_text(json.dumps(dict(jobs={'fake_original': dict(supervisor_pid=2000000000,
                supervisor_start_ticks=100, status='SETTLED', actual_gpuh=81.23456789)})))
            original = ledger.read_bytes()
            module = (ROOT / 'src/wcomr/frozen_input_exposure_r1.py').read_text()
            payload = dict(records=records(), module_source=module,
                module_sha256=hashlib.sha256(module.encode()).hexdigest(),
                method_freeze_sha256='a' * 64, catalog_sha256='b' * 64)
            # Only this synthetic subprocess replaces the fixed project root.
            remote = CAPTURE.REMOTE.replace("'/home/gaokuangda/data/gkd/worldcache_omr'", repr(str(root)))
            call = subprocess.run([sys.executable, '-c', remote],
                input=json.dumps(payload).encode() + b'\n', capture_output=True, timeout=5)
            self.assertEqual(call.returncode, 0, call.stderr.decode())
            value = json.loads(call.stdout)
            self.assertEqual(set(value['identity_hits']), {'av_1'})
            self.assertTrue(value['all_registered_GPU_jobs_terminal'])
            self.assertEqual(value['read_errors'], [])
            self.assertEqual(ledger.read_bytes(), original)
            self.assertEqual(value['method_freeze_sha256'], 'a' * 64)
            self.assertEqual(value['original_v2_ledger_sha256'], hashlib.sha256(original).hexdigest())
            self.assertNotIn('0.91234567', call.stdout.decode())
            self.assertNotIn('81.23456789', call.stdout.decode())


if __name__ == '__main__': unittest.main()
