import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_budget_recovery_cpu_r1 import accept


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'capture.json'
        self.original=json.loads((ROOT/'reports/cara_budget_recovery_four_card_CPU_capture_r1_20261030.json').read_text())

    def check(self,data):
        self.path.write_text(json.dumps(data));return accept(self.path)

    def test_real_original_capture(self):
        self.assertEqual(self.check(self.original)['actual_original_copies'],4)

    def test_resource_or_live_process_refused(self):
        for key,value in [('MemorySwap',8*2**30),('DeviceRequests',[{'Count':1}]),('NetworkMode','host')]:
            d=copy.deepcopy(self.original);d['host_config'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)
        d=copy.deepcopy(self.original);d['container_state']['Running']=True
        with self.assertRaises(ValueError):self.check(d)

    def test_partial_or_new_generation_refused_even_with_recomputed_proof_sha(self):
        for key,value in [('recovered_complete_two_FIT_objectives',3),('new_generation_calls',1),('skipped_tests',1),('originals_unchanged',False)]:
            d=copy.deepcopy(self.original);d['CPU_proof'][key]=value
            d['CPU_proof_sha256']=hashlib.sha256((json.dumps(d['CPU_proof'],indent=2,allow_nan=False)+'\n').encode()).hexdigest()
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)

    def test_wrong_original_stage_or_damaged_proof_refused(self):
        d=copy.deepcopy(self.original);d['launch']['stage']+='/different'
        with self.assertRaises(ValueError):self.check(d)
        d=copy.deepcopy(self.original);d['CPU_proof']['local_controls']=8
        with self.assertRaises(ValueError):self.check(d)


if __name__=='__main__':unittest.main()
