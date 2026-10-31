"""Independent acceptance controls using the original bounded Linux CPU proof."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_reuse_cpu_r1 import accept,encoded_sha


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        accepted=json.loads((ROOT/'reports/cara_s_endpoint_reuse_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/accepted['capture_ref']).read_text());cls.launch=json.loads((ROOT/accepted['launch_ref']).read_text())

    def reject(self,change,message,proof=False):
        c=copy.deepcopy(self.capture);change(c['result'])
        if proof:c['result']['CPU_proof_sha256']=encoded_sha(c['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(c,self.launch)

    def test_complete(self):self.assertEqual(accept(self.capture,self.launch)['total_controls_passed'],48)
    def test_running(self):self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')
    def test_source(self):self.reject(lambda c:c.update(payload_intact=False),'source/runtime')
    def test_resources(self):self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')
    def test_partial(self):self.reject(lambda c:c['CPU_proof'].update(tests_run=47),'CPU scope',True)
    def test_missing_child(self):self.reject(lambda c:c['CPU_proof']['observations'].clear(),'child evidence',True)
    def test_incomplete_failure_bill(self):self.reject(lambda c:c['CPU_proof']['observations'][0].update(original_failure_journal_and_bill_complete=False),'failed allocation',True)
    def test_original_still_live(self):self.reject(lambda c:c['CPU_proof']['observations'][0].update(original_child_ended=False),'failed allocation',True)
    def test_replay(self):self.reject(lambda c:c['CPU_proof']['observations'][0].update(no_replay=False),'failed allocation',True)
    def test_GPU_attempted(self):self.reject(lambda c:c['CPU_proof']['observations'][0].update(no_allocation_attempted=False),'failed allocation',True)
    def test_whole_claim(self):self.reject(lambda c:c['CPU_proof'].update(whole_GPU_card_accepted=True),'CPU-only',True)

    def test_missing_actual_file(self):self.reject(lambda c:c['CPU_proof']['actual_original_reuse']['files'].pop(),'original16',True)
    def test_changed_actual_hash(self):self.reject(lambda c:c['CPU_proof']['actual_original_reuse']['files'][0].update(sha256='0'*64),'hash must match',True)
    def test_unstable_read(self):self.reject(lambda c:c['CPU_proof']['actual_original_reuse']['files'][0].update(stable_during_read=False),'hash must match',True)
    def test_rescoring(self):self.reject(lambda c:c['CPU_proof']['actual_original_reuse'].update(metrics_computed=1),'Read-only',True)
    def test_future_admission_claim(self):self.reject(lambda c:c['CPU_proof']['actual_original_reuse'].update(future_availability_proven=True),'Read-only',True)


if __name__=='__main__':unittest.main()
