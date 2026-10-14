"""Actual frozen full864 identity and distinct, explicitly over8 permission."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.w3_label64_production_contract_r1 import CARD,CAP,SCOPE,INPUTS,REQUESTS,validate,require_new_permission

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    return (json.loads((ROOT/SCOPE).read_text()),json.loads((ROOT/INPUTS).read_text()),
        [json.loads(line) for line in (ROOT/REQUESTS).read_text().splitlines()])


class ActualW3Contract(unittest.TestCase):
    def test_all_frozen_eight_inputs18_parents_and864_maximum(self):
        plan=validate(*inputs());self.assertEqual(len(plan),18)
        self.assertEqual(sum(p['planned_ordinary_pairs']+p['planned_extra_pairs'] for p in plan),864)

    def test_prompt_seed_steps_scope_and_teacher_reuse_mutations_refused(self):
        for role,field,value in ((0,'reuse_ordinary_D_as_free_teacher',True),(0,'GPU_authorized',True),
                (0,'label_steps',[10,16]),(1,'role','PAPER_TEST_RESERVED')):
            args=list(inputs());args[role][field]=value
            with self.assertRaises(ValueError):validate(*args)
        for field,value in (('seed',1),('prompt','different same-shaped prompt'),('num_steps',34)):
            args=list(inputs());args[2][0][field]=value
            with self.assertRaises(ValueError):validate(*args)
        args=list(inputs());args[0]['scope_counts']['full_paths']=16
        with self.assertRaises(ValueError):validate(*args)

    def test_pending_stop_old_PA_or_generic_under8_permission_cannot_launch(self):
        scope,_,_=inputs()
        for permission in (None,{'direct_user_authorization':True,'automatic_single_job_GPUh':8},
                {'direct_user_authorization':True,'card':'WC-P-ACR-H1-BASE4-DIAG4-LOCAL12-PRICE20-FULL528-R1-20261015-A'}):
            with self.assertRaises(ValueError):require_new_permission(scope,permission,None,source_revision='CPU_ONLY',scope_sha256='CPU_ONLY')

    def test_only_full_CPU_bound_card_and_explicit_over8_exception_can_pass(self):
        scope,_,_=inputs();counts=scope['scope_counts'];forecast=11.645827780327332
        proof={'status':'W3_LABEL64_FULL18_ACTUAL_PRODUCTION_CPU_ACCEPTED','source_revision':'CPU_ONLY',
            'scope_counts':counts,'full72_collector_CPU_accepted':True,'full90_post_CPU_controls_accepted':True,
            'whole_card_supervisor_CPU_accepted':True,
            'forecast_complete_GPUh':forecast}
        permission={'direct_user_authorization':True,'card':CARD,'scope_counts':counts,
            'source_revision':'CPU_ONLY','scope_sha256':'CPU_ONLY','cumulative_cap_GPUh':CAP,
            'whole_card_not_split':True,'forecast_complete_GPUh':forecast,
            'explicit_strictly_over8_GPUh_whole_card_approved':True}
        require_new_permission(scope,permission,proof,source_revision='CPU_ONLY',scope_sha256='CPU_ONLY')
        for field,new in (('explicit_strictly_over8_GPUh_whole_card_approved',False),('forecast_complete_GPUh',7.5),
                ('whole_card_not_split',False),('scope_sha256','other'),('source_revision','other')):
            bad=copy.deepcopy(permission);bad[field]=new
            with self.assertRaises(ValueError):require_new_permission(scope,bad,proof,source_revision='CPU_ONLY',scope_sha256='CPU_ONLY')
        for field in ('full72_collector_CPU_accepted','full90_post_CPU_controls_accepted','whole_card_supervisor_CPU_accepted'):
            bad=copy.deepcopy(proof);bad[field]=False
            with self.assertRaises(ValueError):require_new_permission(scope,permission,bad,source_revision='CPU_ONLY',scope_sha256='CPU_ONLY')


if __name__=='__main__':unittest.main()
