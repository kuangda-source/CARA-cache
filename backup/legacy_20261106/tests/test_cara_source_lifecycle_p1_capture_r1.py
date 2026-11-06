"""P1 operational capture never opens partial scientific output."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_cara_source_lifecycle_p1_outer_fixture_r1 import Fixture
from wcomr import cara_source_lifecycle_p1_capture_r1 as capture
from wcomr.cara_budget_original_handles_r1 import ROLES
from wcomr.gpu_budget_pool_v2 import atomic_json,sha


class P1OperationalCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)
        self.f.launch['container']=self.f.stage.name+'-gpu';atomic_json(self.f.stage/'GPU-launch.json',self.f.launch)
        handles={r:None for r in ROLES};handles['guardian']=self.f.launch['guardian_identity']
        guardian=dict(self.f.guardian,status='CARA_ENDPOINT_GUARDIAN_RUNNING_R1',original_handles=handles)
        atomic_json(self.f.stage/'guardian.json',guardian)

    def read(self):
        return capture.capture_lifecycle(self.f.project,self.f.stage,sha(self.f.stage/'GPU-launch.json'))

    def test_live_original_only_opens_launch_and_guardian_metadata(self):
        original=capture.captured_file;seen=[]
        def opened(path):seen.append(Path(path).name);return original(path)
        with patch.object(capture,'captured_file',side_effect=opened),\
                patch.object(capture,'observe_original_process',return_value=dict(original_live=True)),\
                patch.object(capture,'inspect_container',return_value=None):result=self.read()
        self.assertEqual(seen,['GPU-launch.json','guardian.json'])
        self.assertFalse(result['scientific_rows_returned'])

    def test_missing_guardian_remains_unknown(self):
        (self.f.stage/'guardian.json').unlink()
        result=self.read();self.assertEqual(result['reason'],'ORIGINAL_GUARDIAN_NOT_RECORDED')

    def test_unknown_Docker_never_becomes_terminal(self):
        with patch.object(capture,'observe_original_process',return_value=dict(original_live=False)),\
                patch.object(capture,'inspect_container',side_effect=RuntimeError('CPU observation timeout')):
            result=self.read()
        self.assertEqual(result['reason'],'ORIGINAL_CONTAINER_OBSERVATION_UNKNOWN')
        self.assertFalse(result['scientific_rows_returned'])

    def test_replaced_launch_or_other_card_is_refused(self):
        with self.assertRaises(ValueError):capture.capture_lifecycle(self.f.project,self.f.stage,'f'*64)
        value=dict(self.f.launch,run_id='OLD_M1_CARD');atomic_json(self.f.stage/'GPU-launch.json',value)
        with self.assertRaisesRegex(ValueError,'stage and container'):self.read()

    def test_operational_identity_matches_the_frozen_model_entry(self):
        from wcomr import cara_source_lifecycle_p1_runner_binding_r1 as runner
        self.assertEqual((capture.STAGE_NAME,capture.RUN_ID,capture.GPU),(runner.STAGE_NAME,runner.RUN_ID,runner.GPU))


if __name__=='__main__':unittest.main()
