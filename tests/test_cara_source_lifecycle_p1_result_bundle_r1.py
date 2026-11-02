"""Portable reporting from fresh complete52 metadata; no metric computation."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_cara_source_lifecycle_p1_report_r1 as fixture
from wcomr import cara_source_lifecycle_p1_result_bundle_r1 as bundle
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.gpu_budget_pool_v2 import atomic_json


class P1BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.P1ReportTests.setUpClass()

    @classmethod
    def tearDownClass(cls):fixture.P1ReportTests.tearDownClass()

    def setUp(self):
        self.f=fixture.P1ReportTests('runTest');self.f._testMethodName='bundle_'+self._testMethodName
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        reg=read_record(self.f.stage/'registration.json')
        for name in bundle.SOURCES:
            target=self.f.stage/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((bundle.report.ROOT/name).read_bytes());reg['payload_sha256'][name]=file_sha(target)
        atomic_json(self.f.stage/'registration.json',reg)

    def export(self):
        return bundle.export(self.f.stage,cpu_validation=True,fixture_summary=self.f.summary)

    def test_complete_export_does_not_import_matplotlib_or_compute_metrics(self):
        with patch.dict('sys.modules',matplotlib=None):result=self.export()
        value,analysis=bundle.load(result['bundle_path'],result['bundle_sha256'],cpu_validation=True)
        self.assertEqual(len(analysis['rows']),52)
        self.assertEqual(value['original_metric_pairs_recomputed'],0)
        self.assertEqual(set(value['files']),{'report','analysis','freeze'})
        self.assertEqual(result,self.export())

    def test_real_local_figures_reuse_the_export_without_remote_recovery(self):
        result=self.export();target=self.f.stage/'portable-figures'
        with patch.object(bundle.report,'complete',side_effect=AssertionError('No remote/Docker on local render')):
            rendered=bundle.render(result['bundle_path'],result['bundle_sha256'],target,cpu_validation=True)
            with patch.object(bundle.figures,'plots',side_effect=AssertionError('No repeated original rendering')):
                self.assertEqual(rendered,bundle.render(result['bundle_path'],result['bundle_sha256'],target,cpu_validation=True))
        self.assertEqual(len(rendered['files_sha256']),8)
        self.assertTrue((target/'quality-latency.png').read_bytes().startswith(b'\x89PNG'))
        self.assertTrue((target/'complete93-curves.pdf').read_bytes().startswith(b'%PDF'))
        self.assertFalse(rendered['remote_handle_recovered'])

    def test_wrong_capture_hash_cpu_mode_or_local_source_refuses_before_render(self):
        result=self.export()
        with self.assertRaisesRegex(ValueError,'export-receipt'):bundle.load(result['bundle_path'],'0'*64,cpu_validation=True)
        with self.assertRaisesRegex(ValueError,'CPU evidence'):bundle.load(result['bundle_path'],result['bundle_sha256'])
        value=read_record(Path(result['bundle_path']));value['source_sha256'][bundle.SOURCE]='f'*64
        changed=self.f.stage/'changed-source.json';atomic_json(changed,value)
        with self.assertRaisesRegex(ValueError,'source/scope'):bundle.load(changed,file_sha(changed),cpu_validation=True)

    def test_changed_original_file_or_FIT_plan_cannot_become_portable_figures(self):
        result=self.export();original=read_record(Path(result['bundle_path']))
        for mode in ('file','plan'):
            value=copy.deepcopy(original);row=value['files']['freeze']
            if mode=='file':row['raw_base64']=base64.b64encode(b'{}').decode()
            else:
                data=json.loads(base64.b64decode(row['raw_base64']));data['CHECK_used_to_reselect']=True
                raw=(json.dumps(data)+'\n').encode();row.update(raw_base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
            changed=self.f.stage/('changed-'+mode+'.json');atomic_json(changed,value)
            with self.subTest(mode=mode),self.assertRaises(ValueError):bundle.load(changed,file_sha(changed),cpu_validation=True)

    def test_live_unknown_failed_or_changed_export_source_cannot_export_science(self):
        for state in ('ORIGINAL_SCORE_ACTIVE','ORIGINAL_SCORE_UNKNOWN','ORIGINAL_SCORE_FAILED'):
            self.f.current['status']=state
            with self.subTest(state=state),self.assertRaisesRegex(ValueError,'must have ended'):self.export()
            self.assertFalse((self.f.out/'complete-analysis/original-complete-result-bundle.json').exists())
        path=self.f.stage/bundle.CLI;path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'result-export'):self.export()


if __name__=='__main__':unittest.main()
