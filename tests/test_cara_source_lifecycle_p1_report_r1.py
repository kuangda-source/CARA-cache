"""Fresh metadata-only complete reports; post-score transport is source-reused."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import check_cara_source_lifecycle_p1_score_fixture_r1 as fixture
import test_cara_source_lifecycle_p1_scores_r1 as score_fixture
from wcomr import cara_source_lifecycle_p1_report_r1 as report
from wcomr.cara_source_lifecycle_p1_scores_r1 import accept_scores
from wcomr.cara_budget_search_journal_r1 import create_record, read_record
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest


class P1ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f, packet = fixture.packet();packet['release']['actual_GPUh'] = .1
        helper = score_fixture.P1FinalScoreTests('runTest');helper.packet = packet
        cls.packet, cls.config, result, cls.execution = helper.configured()
        cls.accepted = accept_scores(cls.packet, cls.config, result, cls.execution, cpu_validation=True)
        cls.summary = cls.f.root/'new-final-reader-fixture/algorithm-summary.json'

    @classmethod
    def tearDownClass(cls):
        cls.f.doCleanups()

    def setUp(self):
        self.stage = self.f.root/('report-'+self._testMethodName)
        self.stage.mkdir();self.out = self.stage/'output';self.out.mkdir()
        payload = {}
        for name in report.SOURCES:
            target = self.stage/name;target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((report.ROOT/name).read_bytes());payload[name] = file_sha(target)
        create_record(self.stage/'registration.json', dict(payload_sha256=payload))
        (self.stage/'post-score-control').mkdir()
        self.intent = dict(CPU_fixture_only=True, run_id=self.packet['manifest']['run_id'],
            launch_id=self.packet['manifest']['launch_id'], scope_sha256=self.packet['manifest']['scope_sha256'])
        create_record(self.stage/'post-score-control/intent.json', self.intent)
        self.current = dict(status='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED',
            score_capture=dict(accepted=copy.deepcopy(self.accepted), execution=copy.deepcopy(self.execution)))
        # Execution observations are deliberately dynamic in the real reader.
        self.current['score_capture']['execution'].update(original_observation={'observed_unix':1.,'original_live':False},
            cli_observation={'observed_unix':1.,'original_live':False})
        self.rebind()
        for name, value in (('read_intent', (self.intent,self.packet,self.config)), ('paths', (self.stage,self.out))):
            patched = patch.object(report.scores, name, return_value=value);patched.start();self.addCleanup(patched.stop)
        patched = patch.object(report.scores,'recover',side_effect=lambda stage:self.current)
        self.reader = patched.start();self.addCleanup(patched.stop)

    def rebind(self):
        capture = self.current['score_capture']
        capture['accepted']['execution_sha256'] = digest(capture['execution'])

    def complete(self, **kwargs):
        return report.complete(self.stage, cpu_validation=True, fixture_summary=self.summary, **kwargs)

    def test_complete52_original_once_freeze_survives_fresh_liveness_observations(self):
        first = self.complete()
        paths = [Path(first[k]) for k in ('input_seal_path','analysis_path','freeze_path')]
        before = {p:p.read_bytes() for p in paths}
        self.current['score_capture']['execution']['original_observation']['observed_unix'] = 99.
        self.current['score_capture']['execution']['cli_observation']['observed_unix'] = 100.
        self.rebind()
        self.assertEqual(first, self.complete())
        self.assertEqual(before, {p:p.read_bytes() for p in paths})
        self.assertEqual(self.reader.call_count, 2)
        self.assertEqual(first['original_metric_pairs_recomputed'], 0)
        self.assertEqual(read_record(Path(first['analysis_path']))['logical_quality_positions'], 52)

    def test_changed_metric_or_original_identity_refuses_without_overwriting_freeze(self):
        first = self.complete();freeze = Path(first['freeze_path']);original = freeze.read_bytes()
        for mode in ('metric','identity'):
            saved = copy.deepcopy(self.current)
            if mode == 'metric':self.current['score_capture']['accepted']['rows'][0]['metrics']['Alex'] += .1
            else:self.current['score_capture']['execution']['original_identity']['start_ticks'] += 1
            self.rebind()
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError, 'sealed complete'):
                self.complete()
            self.assertEqual(freeze.read_bytes(), original);self.current = saved

    def test_active_unknown_and_failed_originals_create_no_analysis(self):
        for state in ('ORIGINAL_SCORE_ACTIVE','ORIGINAL_SCORE_UNKNOWN','ORIGINAL_SCORE_FAILED'):
            self.current['status'] = state
            with self.subTest(state=state),self.assertRaisesRegex(ValueError, 'must have ended'):
                self.complete()
            self.assertFalse((self.out/'complete-analysis').exists())

    def test_changed_summary_or_source_and_unbound_execution_are_refused(self):
        source = self.stage/report.CLI;raw = source.read_bytes();source.write_bytes(raw+b'\n')
        with self.assertRaisesRegex(ValueError, 'analysis source'):self.complete()
        source.write_bytes(raw)
        summary = self.summary.read_bytes();self.summary.write_bytes(summary+b' ')
        try:
            with self.assertRaisesRegex(ValueError, 'immutable complete'):self.complete()
        finally:self.summary.write_bytes(summary)
        self.current['score_capture']['accepted']['execution_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'execution binding'):self.complete()

    def test_production_mode_refuses_cpu_evidence_and_fixture_summary_override(self):
        with self.assertRaisesRegex(ValueError, 'Only explicit CPU'):
            report.complete(self.stage, fixture_summary=self.summary)
        with self.assertRaisesRegex(ValueError, 'cannot form a production'):
            report.complete(self.stage)
        self.assertFalse((self.out/'complete-analysis').exists())


if __name__ == '__main__':
    unittest.main()
