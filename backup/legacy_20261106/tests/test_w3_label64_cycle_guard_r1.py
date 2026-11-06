"""The fixed native70-call clear is accepted only in its exact old boundary."""
from types import SimpleNamespace
import unittest
import torch

from wcomr.w3_label64_h1_owner_r1 import reset_dense_signature,exact_native_cycle_close
from wcomr.calibration import ResidualCalibrator
from wcomr.mid_coverage import tree_digest


def cleared():
    context=('CPU_ONLY_CYCLE_GUARD',);parameters=[dict(ridge=1e-6,clip=4.,decay=.9,min_energy=1e-12,shrinkage=.5)]*2
    banks=[ResidualCalibrator(**p) for p in parameters]
    for c in banks:c.reset(context)
    net=SimpleNamespace(cnt=0,residual_cache=[None,None],probe_residual_cache=[None,None],
        previous_internal_states=[None,None],previous_input=[None,None],previous_output=[None,torch.tensor([1.,2.])],
        residual_window=[[],[]],probe_residual_window=[[],[]],accumulated_rel_l1_distance=[0.,0.],
        resume_flag=[False,False],worldcache_step_skipped_count=0)
    state=(34,'D',34,0.)
    owner=SimpleNamespace(net=net,deployment=SimpleNamespace(epoch=2,working=[None,None],core=SimpleNamespace(cache={}),dense=banks),
        controller=SimpleNamespace(_state=lambda:state))
    h={'native_cycle_reset':True,'action':'CC','joint_decision':{'state_before':state}}
    return owner,h,reset_dense_signature(context,parameters),tree_digest(net.previous_output[1])


class ExactCycle(unittest.TestCase):
    def test_only_original35_epoch_and_root_owner_are_accepted(self):
        o,h,digest,output=cleared();self.assertTrue(exact_native_cycle_close(o,35,h,1,digest,output))
        self.assertFalse(exact_native_cycle_close(o,34,h,1,digest,output))
        self.assertFalse(exact_native_cycle_close(o,35,h,2,digest,output))
        o.controller._state=lambda:(35,'D',35,0.)
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))

    def test_partial_clear_or_shadow_D_source_write_is_refused(self):
        o,h,digest,output=cleared();o.net.residual_cache=[1,None]
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))
        o,h,digest,output=cleared();o.deployment.working=[{'created_step':35,'kind':'D'},None]
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))
        o,h,digest,output=cleared();o.deployment.dense[0].numerator=.1
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))
        o,h,digest,output=cleared();o.deployment.core.cache={(4,0):object()}
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))
        o,h,digest,output=cleared();o.net.previous_output[1].add_(1.)
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))
        o,h,digest,output=cleared();o.net.previous_output=[None,None]
        self.assertFalse(exact_native_cycle_close(o,35,h,1,digest,output))


if __name__=='__main__':unittest.main()
