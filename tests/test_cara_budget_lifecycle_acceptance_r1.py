import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_budget_lifecycle_cpu_r1 import accept


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.original=json.loads((ROOT/'reports/cara_budget_lifecycle_four_card_CPU_capture_r2_20261030.json').read_text())
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'capture.json'

    def check(self,capture):
        if capture['CPU_proof'] is not None:
            capture['CPU_proof_sha256']=hashlib.sha256((json.dumps(capture['CPU_proof'],indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        self.path.write_text(json.dumps(capture));return accept(self.path)

    def test_original_complete_CPU_scope(self):
        result=self.check(self.original)
        self.assertEqual(result['tests_run'],22);self.assertFalse(result['actual_GPU_lifecycle_accepted'])

    def test_missing_failed_or_running_terminal_refused(self):
        for fault in ('proof','running','failed','oom'):
            c=copy.deepcopy(self.original)
            if fault=='proof':c['CPU_proof']=None
            elif fault=='running':c['container_state']['Running']=True
            elif fault=='failed':c['container_state']['ExitCode']=1
            else:c['container_state']['OOMKilled']=True
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.check(c)

    def test_resource_source_and_original_launch_refused(self):
        for fault in ('swap','source','launch'):
            c=copy.deepcopy(self.original)
            if fault=='swap':c['host_config']['MemorySwap']=8*2**30
            elif fault=='source':c['CPU_proof']['source_sha256']={}
            else:c['launch']['pid']+=1
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.check(c)

    def test_partial_or_upgraded_scope_refused(self):
        for key,value in [('tests_run',21),('tests_skipped',1),('capture_controls',6),
                          ('Docker_metadata_mocked',False),('whole_GPU_card_accepted',True)]:
            c=copy.deepcopy(self.original);c['CPU_proof'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(c)

    def test_actual_failed_R1_remains_refused(self):
        with self.assertRaises(ValueError):
            accept(ROOT/'reports/cara_budget_lifecycle_four_card_CPU_capture_r1_20261030.json',revision='r1')


if __name__=='__main__':unittest.main()
