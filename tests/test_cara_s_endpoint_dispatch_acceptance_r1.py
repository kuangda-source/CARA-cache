"""Independent acceptance of the original CPU once-dispatch proof only."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_dispatch_cpu_r1 import accept,encoded_sha


class DispatchAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_dispatch_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,resign=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if resign:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_complete_original(self):
        self.assertEqual(accept(self.capture,self.launch)['total_controls_passed'],21)

    def test_running_refused(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_changed_source_refused(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_gpu_visible_refused(self):
        self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')

    def test_missing_scenario_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'].pop(),'Every original',True)

    def test_repeated_spawn_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0].update(repeated_dispatch_spawned=True),'boundary differs',True)

    def test_live_original_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0]['supervisor_observation'].update(original_live=True),'proved ended',True)

    def test_missing_worker_identity_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0]['original_handles'].pop('worker'),'roles differ',True)

    def test_deadline_not_exercised(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][3]['supervisor_terminal']['error'].update(type='UnrelatedFailure'),'deadline must fire',True)

    def test_foreign_process_preserved(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][5].update(foreign_process_preserved=False),'boundary differs',True)

    def test_snapshot_not_future_admission(self):
        self.reject(lambda c:c['CPU_proof']['actual_readonly_CPU_environment'].update(future_dispatch_admission=True),'environment proof differs',True)

    def test_no_metrics_computed(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(metric_computations=12),'Synthetic scope',True)

    def test_unknown_prepare_preserved(self):
        launch=copy.deepcopy(self.launch);launch['stage_name']='different-stage'
        with self.assertRaisesRegex(ValueError,'prepare binding'):accept(self.capture,launch)


if __name__=='__main__':unittest.main()
