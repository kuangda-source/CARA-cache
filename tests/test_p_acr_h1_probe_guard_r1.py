"""Probe forcing preserves H1 protected/support boundaries; no model forward."""
import unittest
from types import SimpleNamespace

from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_absolute_h1_control_r1 import VERSION, fingerprint
from wcomr.p_acr_h1_diagnostic_owner_r1 import ProbeH1Controller


def controller():
    cal=Calibration('CPU_PROBE_SUPPORT_GUARD',
        {(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
        {n:1. for n in range(1,37)})
    p={'version':VERSION,'gamma':.5,'table_model':{'grouping':'SOURCE_PHASE','target':'absolute_guided_MSE',
        'current_teacher_energy_is_online_feature':False,
        'cells':{s+'_'+phase:{'status':'FIT','C_scale':100.,'A_ratios':{'FUSION_A':.02},
            'actual_NEW_P_birth_mean':.0001} for s in ('D','P') for phase in ('EARLY','LATE')}},
        'cost_seconds':{'C':1.,'A':1.3,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.3},
        'lambda_seconds_per_weighted_absolute_MSE':100.}
    p['fingerprint']=fingerprint(p)
    return ProbeH1Controller(cal,2.,Costs('CPU_GUARD',1.,4.,3.5),
        CreationPhasePrior('CPU_GUARD',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        strategy='WORKING_P_AGE_NONZERO_REBASE',table_parameters=p,
        math_parameters={'fingerprint':'CPU_ONLY_GUARD','gamma':.5},horizon=1,sigma_at=lambda n:36.-n)


def packets(step):
    return tuple(SimpleNamespace(slot=b,counter=2*(step-1)+b,delta_y=.08+.01*b) for b in (0,1))


class ProbeGuard(unittest.TestCase):
    def test_protected_refusal(self):
        c=controller()
        for n in range(1,7):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        with c.action(7,'C'):
            with self.assertRaisesRegex(ValueError,'protected/missing support'):
                c._choice(7,(),False,False,protected=True)
        self.assertIsNone(c.offline)
        self.assertEqual(c.last_completed_step,6)

    def test_age7_refusal_is_retained(self):
        c=controller()
        for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        for n in range(8,14):
            with c.action(n,'C'):
                d=c.decide(n,packets(n),both_sources_ready=True,partial_ready=True)
                c.commit(d,actual_action='C',pair_completed=True)
        with c.action(14,'A'):
            with self.assertRaisesRegex(ValueError,'origin_reason'):
                c.decide(14,packets(14),both_sources_ready=True,partial_ready=True)
        self.assertEqual(c.anchor,7)
        self.assertEqual(c.last_completed_step,13)
        self.assertIsNone(c.offline)

    def test_supported_A_decision_does_not_commit(self):
        c=controller()
        for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        before=c.state_dict()
        with c.action(8,'A'):
            d=c.decide(8,packets(8),both_sources_ready=True,partial_ready=True)
            self.assertEqual((d.action,d.reason),('C','MATH_EVENT_PA_OFFLINE:A'))
            with self.assertRaisesRegex(ValueError,'No snapshot'):c.state_dict()
        self.assertEqual(before,c.state_dict())

    def test_future_step_and_non_CAD_refusal(self):
        c=controller()
        with self.assertRaises(ValueError):
            with c.action(2,'A'):pass
        with self.assertRaises(ValueError):
            with c.action(1,'P'):pass


if __name__=='__main__':unittest.main()
