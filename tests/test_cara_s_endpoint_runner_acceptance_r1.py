"""Independent refusal controls against the retained original runner CPU proof."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_runner_cpu_r1 import accept,encoded_sha


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r=json.loads((ROOT/'reports/cara_s_endpoint_runner_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/r['capture_ref']).read_text());cls.launch=json.loads((ROOT/r['launch_ref']).read_text())

    def reject(self,change,message,proof=False):
        c=copy.deepcopy(self.capture);change(c['result'])
        if proof:c['result']['CPU_proof_sha256']=encoded_sha(c['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(c,self.launch)

    def test_complete(self):self.assertEqual(accept(self.capture,self.launch)['actual_collection_paths'],114)
    def test_running(self):self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')
    def test_source(self):self.reject(lambda c:c.update(payload_intact=False),'source/runtime')
    def test_resources(self):self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')
    def test_missing_flow(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'].pop(),'Both original flow',True)
    def test_partial_scope(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(physical_paths=31),'collection/reset',True)
    def test_missing_storage_check(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(storage_checks=32),'collection/reset',True)
    def test_state_not_restored(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0]['runner_checks'].update(final_state_restored=False),'collection/reset',True)
    def test_replay(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(replay_refused=False),'collection/reset',True)
    def test_missing_failure(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['failure_controls'].pop(),'failure controls',True)
    def test_failed_request_executed(self):self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['failure_controls'][0].update(no_sample_executed=False),'failure controls',True)
    def test_no_GPU_load_claim(self):self.reject(lambda c:c['CPU_proof'].update(actual_Cosmos_model_load=True),'CPU-only scope',True)


if __name__=='__main__':unittest.main()
