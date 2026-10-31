"""Accept complete original CPU integration evidence, reject partial claims."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_pipeline_cpu_r1 import accept,encoded_sha


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_pipeline_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,proof=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if proof:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_complete(self):
        self.assertEqual(accept(self.capture,self.launch)['actual_new_metric_pairs'],40)

    def test_running(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_changed_sources(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_gpu_visible(self):
        self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')

    def test_missing_flow(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'].pop(),'Both original flow',True)

    def test_missing_alias(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'].pop(),'Both complete physical',True)

    def test_changed_reuse(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(reused_rows_unchanged=11),'pipeline case',True)

    def test_partial_frames(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(full_frames_per_video=92),'pipeline case',True)

    def test_missing_RGB_control(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(RGB_controls=8),'pipeline case',True)

    def test_wrong_metric_kernel(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0]['score_execution'].update(source_actual_sha256={}),
                    'metric kernel',True)

    def test_live_scorer(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0]['cases'][0]['score_execution']['original_observation'].update(original_live=True),'scoring processes',True)

    def test_original_pairs_not_rescored(self):
        self.reject(lambda c:c['CPU_proof']['numeric']['checks'][0].update(original_experiment_pairs_rescored=1),'per-flow counts',True)

    def test_no_whole_GPU_claim(self):
        self.reject(lambda c:c['CPU_proof'].update(whole_GPU_card_accepted=True),'CPU-only scope',True)


if __name__=='__main__':unittest.main()
