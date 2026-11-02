"""Actual static exports on fresh synthetic complete52 metadata, no metrics."""
import csv
from pathlib import Path
import unittest
from unittest.mock import patch

import test_cara_source_lifecycle_p1_report_r1 as report_fixture
from wcomr import cara_source_lifecycle_p1_figures_r1 as figures
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.cara_fast_fidelity_r1 import file_sha


class P1FiguresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        report_fixture.P1ReportTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        report_fixture.P1ReportTests.tearDownClass()

    def setUp(self):
        self.f=report_fixture.P1ReportTests('runTest');self.f._testMethodName='figure_'+self._testMethodName
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        reg=read_record(self.f.stage/'registration.json')
        for name in (figures.SOURCE,figures.CLI):
            target=self.f.stage/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((figures.report.ROOT/name).read_bytes());reg['payload_sha256'][name]=file_sha(target)
        atomic_json(self.f.stage/'registration.json',reg)

    def render(self):
        return figures.render(self.f.stage,cpu_validation=True,fixture_summary=self.f.summary)

    def test_real_png_pdf_csv_and_idempotent_original_export(self):
        result=self.render();directory=Path(result['directory'])
        expected={'input-equal-means.csv':39,'frame-curves93.csv':3627,'all52-input-rows.csv':52,'actual-calibration-costs.csv':2}
        for name,count in expected.items():
            with (directory/name).open() as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),count)
        for name in ('quality-latency','complete93-curves'):
            self.assertTrue((directory/(name+'.png')).read_bytes().startswith(b'\x89PNG'))
            self.assertTrue((directory/(name+'.pdf')).read_bytes().startswith(b'%PDF'))
        with patch.object(figures,'plots',side_effect=AssertionError('Never rerender accepted originals')):
            self.assertEqual(result,self.render())
        self.assertEqual(result['original_metric_pairs_recomputed'],0)
        self.assertTrue(result['binding']['CPU_fixture_only'])

    def test_changed_export_bytes_are_preserved_and_rejected(self):
        result=self.render();path=Path(result['directory'])/'all52-input-rows.csv'
        path.write_bytes(path.read_bytes()+b'EXPLICIT_TEST_CHANGED_FILE\n');raw=path.read_bytes()
        with self.assertRaisesRegex(ValueError,'figure bytes'):self.render()
        self.assertEqual(path.read_bytes(),raw)

    def test_production_mode_refuses_fixture_and_unregistered_renderer(self):
        with self.assertRaisesRegex(ValueError,'cannot form a production'):figures.render(self.f.stage)
        path=self.f.stage/figures.CLI;path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'figure source'):self.render()
        self.assertFalse((self.f.out/'complete-analysis').exists())


if __name__=='__main__':
    unittest.main()
