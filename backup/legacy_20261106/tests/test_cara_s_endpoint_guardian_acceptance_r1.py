"""Acceptance mutations of the original complete Linux receipt; no execution."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_guardian_cpu_r1 import accept,encoded_sha


class GuardianAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_guardian_CPU_accepted_r2_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,resign=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if resign:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_original_acceptance(self):
        result=accept(self.capture,self.launch)
        self.assertEqual(result['total_controls_passed'],19)
        self.assertFalse(result['whole_GPU_card_accepted'])

    def test_original_must_exit(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_no_missing_proof(self):
        self.reject(lambda c:c.update(CPU_proof=None),'exited zero')

    def test_no_gpu_device(self):
        self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')

    def test_no_changed_source(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_no_partial_scenarios(self):
        self.reject(lambda c:c['CPU_proof']['control_results'][1]['observations'].pop(),'Every original',True)

    def test_no_skipped_linux_controls(self):
        self.reject(lambda c:c['CPU_proof']['control_results'][1].update(skipped=1),'All Linux',True)

    def test_no_signal_to_foreign_sentinel(self):
        self.reject(lambda c:c['CPU_proof']['control_results'][1]['observations'][0].update(foreign_CPU_sentinel_preserved=False),
                    'Original closure',True)

    def test_no_settlement_on_unknown(self):
        def change(c):
            row=next(r for r in c['CPU_proof']['control_results'][1]['observations'] if r['scenario']=='unknown')
            row['temporary_settlement_events']=1
        self.reject(change,'Original closure',True)

    def test_failure_cost_cannot_be_omitted(self):
        def change(c):
            row=next(r for r in c['CPU_proof']['control_results'][1]['observations'] if r['scenario']=='runner_failure')
            row['temporary_settlement_events']=0
        self.reject(change,'Original closure',True)

    def test_no_active_science_read(self):
        self.reject(lambda c:c['CPU_proof'].update(active_experiment_outputs_read=True),'CPU-only',True)


if __name__=='__main__':unittest.main()
