"""Actual V1 original Linux CPU plus strict scope/terminal/numerical refusal."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from accept_cara_source_lifecycle_linux_cpu_r2 import accept

ROOT=Path(__file__).resolve().parents[1]


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.launch=ROOT/'reports/cara_v1_Linux_CPU_prepare_r2_20261101.json'
        self.capture=ROOT/'reports/cara_v1_Linux_CPU_capture_r3_20261101.json'

    def test_original_terminal_and_complete_matrix_accepted(self):
        value=accept(self.launch,self.capture)
        self.assertEqual(value['tests_run'],15)
        self.assertEqual(value['point_tiny_paths'],24)
        self.assertFalse(value['true_model_point20_or_video'])
        self.assertFalse(value['real_V1_planner_efficacy'])

    def rejected(self,mutate,*,rehash=True):
        value=json.loads(self.capture.read_text());cap=value['result'];mutate(cap)
        if rehash:
            cap['CPU_proof_sha256']=hashlib.sha256((json.dumps(cap['CPU_proof'],indent=2)+'\n').encode()).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'capture.json';path.write_text(json.dumps(value))
            with self.assertRaises(AssertionError):accept(self.launch,path)

    def test_live_nonzero_exit_or_extra_swap_refused(self):
        self.rejected(lambda c:c['container_state'].update(Status='running',Pid=1))
        self.rejected(lambda c:c['container_state'].update(ExitCode=1))
        self.rejected(lambda c:c['host_config'].update(MemorySwap=8*2**30))

    def test_missing_point20_or_overstated_model_scope_refused(self):
        self.rejected(lambda c:c['CPU_proof']['points'].pop())
        self.rejected(lambda c:c['CPU_proof'].update(actual_Cosmos_weights=True))
        self.rejected(lambda c:c['CPU_proof'].update(real_generated_plan_efficacy=True))

    def test_forged_solver_scale_or_wrong_reset_chart_refused(self):
        self.rejected(lambda c:c['CPU_proof']['metrics']['test_cara_source_lifecycle_planner_r1'][
            'UniPC_current_input_scale'].update(max_gradient_error=.01))
        self.rejected(lambda c:c['CPU_proof']['metrics']['test_cara_read_write_provenance_r1'][
            'reset_lifecycle'].update(output_sources_after_epilogue=[31,31]))


if __name__=='__main__':unittest.main()
