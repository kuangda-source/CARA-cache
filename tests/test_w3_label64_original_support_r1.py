"""Original support and noncommitting selection controls; no model or SSH."""
from types import SimpleNamespace
import unittest

from wcomr.w3_label64_h1_owner_r1 import W3LabelOwner,LabelH1Controller
from wcomr.source_phase_absolute_h1_control_r1 import VERSION,fingerprint
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior


def controller():
    cal=Calibration('DECLARED_W3_UNIT_AGE6',{(a,n):.9 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
        {n:1. for n in range(1,37)})
    p={'version':VERSION,'gamma':.5,'table_model':{'grouping':'SOURCE_PHASE','target':'absolute_guided_MSE',
        'current_teacher_energy_is_online_feature':False,'cells':{k:{'status':'FIT','C_scale':1.,
            'A_ratios':{'FUSION_A':.5},'actual_NEW_P_birth_mean':.1} for k in ('D_EARLY','D_LATE','P_EARLY','P_LATE')}},
        'cost_seconds':{'C':1.,'A':1.1,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.1},
        'lambda_seconds_per_weighted_absolute_MSE':10.}
    p['fingerprint']=fingerprint(p)
    return LabelH1Controller(cal,2.,Costs('UNIT',1.,4.,3.5),CreationPhasePrior('UNIT',.01,.3,
        early_creation_floor=.01,late_creation_floor=.03),
        strategy='WORKING_P_AGE_NONZERO_REBASE',table_parameters=p,math_parameters={'fingerprint':'UNIT_OLD','gamma':.5},
        horizon=1,sigma_at=lambda n:1-n/40)


def healthy_owner():
    o=W3LabelOwner.__new__(W3LabelOwner);o.controller=controller()
    for n in range(1,8):o.controller.commit_protected_dense(n,actual_action='D',pair_completed=True)
    o.deployment=SimpleNamespace(epoch='e',working=[{'epoch':'e'},{'epoch':'e'}])
    o.net=SimpleNamespace(previous_input=[1,1],previous_internal_states=[1,1],residual_cache=[1,1])
    return o


class OriginalDomain(unittest.TestCase):
    def test_ready_context_and_CAD_diagnostic_uses_same_pre_action(self):
        o=healthy_owner();self.assertIsNone(o._preflight(8));c=o.controller;before=c.state_dict()
        values=((0,14,.1),(1,15,.11))
        for name in ('C','A','D'):
            with c.action(8,name):
                choice=c._choice(8,values,True,False)
                self.assertEqual(choice.action,'C' if name=='A' else name)
                self.assertEqual(choice.state_before,before['state'])
                self.assertTrue(choice.reason.endswith(':'+name))
        self.assertEqual(c.state_dict(),before)

    def test_age7_missing_calibration_or_unknown_table_never_relaxes(self):
        o=healthy_owner();self.assertEqual(o._preflight(14),'ORIGINAL_AGE_SUPPORT')
        old=o.controller.calibration
        o.controller.calibration=Calibration('DECLARED_MISSING_CELL',
            {k:v for k,v in old.rho_at.items() if k!=(7,8)},dict(old.gains))
        self.assertEqual(o._preflight(8),'ORIGINAL_CALIBRATION_MISSING')
        o=healthy_owner();o.controller.table_parameters['table_model']['cells']['D_EARLY']['status']='UNKNOWN_ZERO_FEATURE_OR_C_TARGET'
        self.assertEqual(o._preflight(8),'ORIGINAL_TABLE_UNKNOWN')

    def test_protected_unready_and_incomplete_offline_state_refused(self):
        o=healthy_owner();self.assertEqual(o._preflight(36),'ORIGINAL_PROTECTED')
        o.deployment.working[1]=None;self.assertEqual(o._preflight(8),'ORIGINAL_BOTH_SOURCES_NOT_READY')
        c=o.controller
        with c.action(8,'C'):
            with self.assertRaises(ValueError):c._choice(8,((0,14,.1),(1,15,.1)),False,False)
            with self.assertRaises(ValueError):c.state_dict()
            with self.assertRaises(ValueError):c._choice(8,(),True,False,protected=True)
        self.assertIsNone(c.offline)


if __name__=='__main__':unittest.main()
