"""Reject incomplete original CPU recovery proofs without re-running them."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_capture_cpu_r1 import accept,encoded_sha


class RecoveryAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_capture_CPU_accepted_r2_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,resign=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if resign:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_complete_original(self):
        self.assertEqual(accept(self.capture,self.launch)['total_controls_passed'],27)

    def test_running_refused(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_changed_source_refused(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_gpu_visible_refused(self):
        self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')

    def test_missing_control_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(controls_passed=4),'recovery boundaries',True)

    def test_live_original_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['worker_observation'].update(original_live=True),'proved ended',True)

    def test_foreign_process_not_touched(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(foreign_process_preserved=False),'recovery boundaries',True)

    def test_unknown_boot_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(wrong_boot_status='ACCEPTED'),'recovery boundaries',True)

    def test_simulated_docker_not_actual_claim(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(Docker_observations_simulated=False),'must not be claimed',True)

    def test_no_new_metrics(self):
        self.reject(lambda c:c['CPU_proof'].update(metric_computations=12),'must not be claimed',True)


if __name__=='__main__':unittest.main()
