"""Endpoint family adaptation preserves the accepted original control flow."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULES=('host_guardian','guardian_journal','supervisor','lifecycle_capture')
RENAMES={f'cara_budget_{n}_r1':f'cara_s_endpoint_{n}_r1' for n in (*MODULES,'lifecycle')}
RENAMES.update({
    'BUDGET_CALIBRATION_GUARDIAN_TERMINAL':'CARA_ENDPOINT_GUARDIAN_TERMINAL_R1',
    'BUDGET_CALIBRATION_GUARDIAN_ADMITTING':'CARA_ENDPOINT_GUARDIAN_ADMITTING_R1',
    'BUDGET_CALIBRATION_ORIGINAL_WALL_BILL':'CARA_ENDPOINT_ORIGINAL_WALL_BILL_R1',
    'BUDGET_CALIBRATION_SUPERVISOR_RUNNING':'CARA_ENDPOINT_SUPERVISOR_RUNNING_R1',
    'BUDGET_CALIBRATION_SUPERVISOR_TERMINAL':'CARA_ENDPOINT_SUPERVISOR_TERMINAL_R1',
    'ORIGINAL_CALIBRATION_LIVE_OR_UNKNOWN':'ORIGINAL_ENDPOINT_LIVE_OR_UNKNOWN',
    'ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE':'ORIGINAL_ENDPOINT_LIFECYCLE_CAPTURE',
    'cara-budget-calibration-GPU-':'cara-S-endpoint-GPU-',
    'complete_search_accepted':'complete_endpoint_accepted',
    'Original calibration':'Original endpoint',
    "original calibration's":"original endpoint's",
})


class EndpointGuardianBinding(unittest.TestCase):
    def check_component(self,name):
        original=(ROOT/f'src/wcomr/cara_budget_{name}_r1.py').read_text()
        adapted=(ROOT/f'src/wcomr/cara_s_endpoint_{name}_r1.py').read_text()
        for before,after in RENAMES.items():original=original.replace(before,after)
        self.assertEqual(ast.dump(ast.parse(original)),ast.dump(ast.parse(adapted)))

    def test_host_guardian(self):self.check_component('host_guardian')
    def test_journal(self):self.check_component('guardian_journal')
    def test_supervisor(self):self.check_component('supervisor')
    def test_readonly_capture(self):self.check_component('lifecycle_capture')


if __name__=='__main__':unittest.main()
