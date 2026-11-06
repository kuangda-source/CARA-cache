"""Independent original CPU proof checks; never invoke scoring again."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_score_cpu_r1 import accept,encoded_sha


class ScoreAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_score_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,resign=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if resign:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_original_complete_acceptance(self):
        result=accept(self.capture,self.launch);self.assertEqual(result['new_synthetic_pairs_scored'],20)
        self.assertEqual(result['synthetic_metric_frames'],1953);self.assertFalse(result['whole_GPU_card_accepted'])

    def test_running_not_accepted(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_changed_source_not_accepted(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_wrong_cpu_resources(self):
        self.reject(lambda c:c['host_config'].update(DeviceRequests=[{}]),'resource limits')

    def test_missing_complete_case(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'].pop(),'Both complete12',True)

    def test_partial_score_pairs(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0].update(new_pairs=11),'Complete score',True)

    def test_missing_original_reuse(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0].update(original_rows_unchanged=11),'Complete score',True)

    def test_missing_undefined_gradient_control(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0].update(undefined_gradient_pairs=0),'Complete score',True)

    def test_failure_denominator_preserved(self):
        self.reject(lambda c:c['CPU_proof']['actual']['failed_case'].update(complete_registered_pairs=1),'Failed scorer',True)

    def test_replay_refused(self):
        self.reject(lambda c:c['CPU_proof']['actual']['failed_case'].update(no_replay=False),'Failed scorer',True)

    def test_live_original_child_rejected(self):
        self.reject(lambda c:c['CPU_proof']['actual']['cases'][0]['execution']['original_observation'].update(original_live=True),
                    'handle is not proved ended',True)

    def test_no_original_science_rescore(self):
        self.reject(lambda c:c['CPU_proof']['actual'].update(old_experiment_videos_rescored=1),'Synthetic actual-metric',True)


if __name__=='__main__':unittest.main()
