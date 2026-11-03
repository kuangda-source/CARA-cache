"""Synthetic acceptance controls; never a production/GPU receipt."""
import copy,importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cal_accept',ROOT/'scripts/analyze_cara_f19_speed190_r1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Acceptance(unittest.TestCase):
    def fixture(self):
        card=json.loads((ROOT/'plans/cara_next_stage_20261103/f19_speed190_cal/CAL35_MANIFEST_R1.json').read_text())
        times=dict(NATIVE35=250.,WC_T006=130.,F19_A1=149.,F19_A1_LIGHT_C=130.,F17_A2_LIGHT_C=128.,F19_DELTA4_LIGHT_C=129.,F16_C=131.)
        lpips=dict(WC_T006=.46,F19_A1=.24,F19_A1_LIGHT_C=.26,F17_A2_LIGHT_C=.26,F19_DELTA4_LIGHT_C=.28,F16_C=.35)
        collection=dict(scope_sha256=card['scope_sha256'],status='COMPLETE35_PENDING_RELEASE_SCORING',rows=[],controls=[{},{}])
        scores=dict(scope_sha256=card['scope_sha256'],status='COMPLETE35_RGB_24_LPIPS_84_QUALITY_PENDING_ACCEPTANCE',CUDA_initialized=False,RGB_controls_passed=True,RGB=[{}]*35,LPIPS=[],quality_rows=[])
        for slot in card['matrix']:
            role=slot['role'];result=dict(CPU_fixture=False,guided_pairs=36,solver_steps=36,scope_sha256=card['scope_sha256'],T_DD=times.get(role,149.),T_request=times.get(role,149.)+60,in_timing_guided_copies=0,in_timing_hashes=0,research_checkpoints=0)
            collection['rows'].append(dict(slot=copy.deepcopy(slot),status='COMPLETE',result=result))
            if slot['section']!='FORMAL':continue
            if role!='NATIVE35':scores['LPIPS'].append(dict(member=slot['member'],role=role,result=dict(status='COMPLETE',frames=93,Alex_frames=[lpips[role]]*93,Alex=lpips[role])))
            for dim in ('MUSIQ_LONGER512','subject_consistency','motion_smoothness'):
                value=(68. if role=='F17_A2_LIGHT_C' else 70.) if dim=='MUSIQ_LONGER512' else .98
                scores['quality_rows'].append(dict(planned=dict(method=slot['id'],case_id=slot['member'],role=role,dimension=dim),result=dict(status='SCORED',value=value),status='SCORED'))
        release=dict(GPU_released=True,mode_restored=True,cost_settled=True,original_processes_ended=True,container_exit_success=True,hard_limit_exceeded=False,actual_GPUh=2.)
        return card,collection,scores,release

    def test_every_frozen_gate_is_required(self):
        result=module.analyze(*self.fixture())
        self.assertEqual(result['passing_roles'],['F19_A1_LIGHT_C'])
        self.assertEqual(result['quality_positions'],84)

    def test_missing_position_cannot_be_accepted(self):
        args=self.fixture();args[2]['LPIPS'].pop()
        with self.assertRaises(AssertionError):module.analyze(*args)

    def test_unreleased_allocation_cannot_be_accepted(self):
        args=self.fixture();args[3]['GPU_released']=False
        with self.assertRaises(AssertionError):module.analyze(*args)


if __name__=='__main__':unittest.main()
