"""Original completed media proof mutations; no remote execution or scoring."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_s_endpoint_artifact_cpu_r1 import accept,encoded_sha


class ArtifactAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((ROOT/'reports/cara_s_endpoint_artifact_CPU_accepted_r1_20261031.json').read_text())
        cls.capture=json.loads((ROOT/receipt['capture_ref']).read_text())
        cls.launch=json.loads((ROOT/receipt['launch_ref']).read_text())

    def reject(self,change,message,resign=False):
        capture=copy.deepcopy(self.capture);change(capture['result'])
        if resign:capture['result']['CPU_proof_sha256']=encoded_sha(capture['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError,message):accept(capture,self.launch)

    def test_original_complete_acceptance(self):
        result=accept(self.capture,self.launch)
        self.assertEqual(result['complete_frame_reads'],6045);self.assertFalse(result['whole_GPU_card_accepted'])

    def test_running_not_accepted(self):
        self.reject(lambda c:c['container_state'].update(Running=True),'exited zero')

    def test_no_proof_not_accepted(self):
        self.reject(lambda c:c.update(CPU_proof=None),'exited zero')

    def test_changed_source_not_accepted(self):
        self.reject(lambda c:c.update(payload_intact=False),'source/runtime')

    def test_wrong_cpu_resources(self):
        self.reject(lambda c:c['host_config'].update(MemorySwap=8*1024**3),'resource limits')

    def test_missing_case(self):
        self.reject(lambda c:c['CPU_proof']['media']['cases'].pop(),'Both full32',True)

    def test_missing_frames(self):
        self.reject(lambda c:c['CPU_proof']['media']['cases'][0].update(all_frames=92),'Full frame',True)

    def test_missing_identity_control(self):
        self.reject(lambda c:c['CPU_proof']['media']['cases'][0].update(identity_controls=8),'Full frame',True)

    def test_missing_pts_failure(self):
        self.reject(lambda c:c['CPU_proof']['media']['failure_controls'].pop(),'failure controls',True)

    def test_no_real_original_video_claim(self):
        self.reject(lambda c:c['CPU_proof']['media'].update(actual_original_experiment_videos_read=True),'synthetic scope',True)

    def test_no_metrics_recomputed(self):
        self.reject(lambda c:c['CPU_proof']['media'].update(metrics_computed=1),'synthetic scope',True)


if __name__=='__main__':unittest.main()
