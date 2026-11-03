"""Pinned complete36 cache/RF/UniPC controls for the two new CAL operations."""
import copy
import json
from pathlib import Path
from types import MethodType
import unittest

import torch

from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_f19_speed190_sampling_r1 import PARTIAL_UPDATES,SpeedOwner
from wcomr.cara_f19_profile_r1 import profile_policy_owner
from wcomr.policy_generator_r1.production_sampling import PolicyOwner
from wcomr.policy_interval_readout_r1 import guided
from wcomr.mid_coverage import tree_digest,WC_FIELDS
from test_cara_read_write_provenance_r1 import bound,RUNTIME,ROOT
from test_cara_read_write_transition_r1 import modules

METRICS={}


def run(policy,flow,*,speed=True,light=False,partial=()):
    step,_=bound(flow)
    model=step.worldcache.model;wc,rf=modules()
    model.net.forward=MethodType(wc.worldcache_mini_train_dit_forward,model.net)
    model.denoise=MethodType(rf.denoise,model)
    model.tensor_kwargs['dtype']=torch.float32
    noise=step.noise.float()
    for c in step.conditions:
        c.gt_frames=c.gt_frames.float();c.cross=c.cross.float()
        c.condition_video_input_mask_B_C_T_H_W=c.condition_video_input_mask_B_C_T_H_W.float()
    manifest=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
    kwargs=dict(policy=policy,profile=profile_from(manifest['profile']),context=('F19_CPU','tiny',str(flow)),runtime=RUNTIME,wc=wc,rf=rf)
    owner=SpeedOwner(model,light_C=light,partial_updates=partial,**kwargs) if speed else PolicyOwner(model,**kwargs)
    scheduler=copy.deepcopy(step.solver._template);latent=noise.clone();outputs=[];deltas=[]
    with profile_policy_owner(owner,scheduler,device='cpu') as measurement:
        with torch.no_grad():
            for t,timestep in enumerate(step.timesteps,1):
                old_delta=owner.readout.delta.clone() if speed and owner.readout.delta is not None else None
                old_delta_step=owner.readout.delta_step if speed else None
                pair=owner.pair(noise,latent,timestep.reshape(1,1),step.conditions,owner.choose)
                if t in partial:
                    assert owner.executor.last['action']=='DC'
                    assert owner.readout.delta_step==old_delta_step and torch.equal(owner.readout.delta,old_delta)
                    assert torch.allclose(pair[0]-pair[1],old_delta,atol=1e-6,rtol=1e-5)
                    deltas.append(dict(step=t,source_step=old_delta_step,
                        true_D_steps=[c.receipt()['anchor_steps'] for c in owner.readout.calibrators]))
                velocity=guided(pair);outputs.append(velocity.clone())
                latent=scheduler.step(velocity,timestep,latent,return_dict=False)[0]
    result=dict(outputs=outputs,latent=latent,history=copy.deepcopy(owner.history),deltas=deltas,
        cache_digest=tree_digest({k:getattr(model.net,k) for k in WC_FIELDS if hasattr(model.net,k)}),
        profile=measurement.summary)
    owner.close()
    return result


class SpeedSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        cls.manifest=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
        cls.plan=cls.manifest['roles']['F19_A1']['policy']

    def test_new_path_OFF_is_exact_original_F19_for_both_flows(self):
        for flow in (False,True):
            original=run(self.plan,flow,speed=False)
            off=run(self.plan,flow)
            self.assertTrue(all(torch.equal(a,b) for a,b in zip(original['outputs'],off['outputs'])))
            self.assertTrue(torch.equal(original['latent'],off['latent']))
            self.assertEqual(original['cache_digest'],off['cache_digest'])
            METRICS['OFF_'+str(flow)]=dict(all36_guided_latent_cache_equal=True)

    def test_light_C_pays_no_C_probes_and_preserves_A_and_true_D_counts(self):
        for flow in (False,True):
            result=run(self.plan,flow,light=True)
            c=result['profile']['components']
            self.assertEqual(c['probe_shallow']['calls'],100)
            self.assertEqual(c['deep_block']['calls'],76)
            self.assertEqual(c['output_head']['calls'],84)
            self.assertEqual(c['compute_optimal_gamma']['calls'],12)
            if flow:self.assertEqual(c['estimate_optical_flow']['calls'],24)
            self.assertEqual([r['actual'] for r in result['history']],self.plan['actions'])
            self.assertFalse(any(r['fallback_reason'] for r in result['history']))
            METRICS['LIGHT_'+str(flow)]=dict(complete36=True,shallow_calls=100,A_heads_preserved=True,
                actual_GPU_speed_or_LPIPS=False)

    def test_partial_DD_difference_stays_true_and_branch_anchors_are_asymmetric(self):
        for flow in (False,True):
            result=run(self.plan,flow,light=True,partial=PARTIAL_UPDATES)
            self.assertEqual([r['source_step'] for r in result['deltas']],[8,12,16,20])
            self.assertEqual([r['step'] for r in result['deltas']],list(PARTIAL_UPDATES))
            self.assertEqual(result['deltas'][0]['true_D_steps'],[[8,10],[7,8]])
            c=result['profile']['components']
            self.assertEqual(c['probe_shallow']['calls'],92)
            self.assertEqual(c['deep_block']['calls'],68)
            self.assertEqual(sum(r['actual']=='CONDITIONAL_D_DELTA_HOLD' for r in result['history']),4)
            self.assertEqual(result['history'][-1]['actual'],'D')
            self.assertFalse(any(r['fallback_reason'] for r in result['history']))
            METRICS['DELTA_'+str(flow)]=dict(complete36=True,partial_steps=list(PARTIAL_UPDATES),
                true_delta_steps=[8,12,16,20],asymmetric_true_D_anchors=True,
                shallow_calls=92,deep_calls=68,no_external_teacher=True)

    def test_request_reset_is_deterministic_and_unsupported_partial_mask_refuses(self):
        a=run(self.plan,True,light=True,partial=PARTIAL_UPDATES)
        b=run(self.plan,True,light=True,partial=PARTIAL_UPDATES)
        self.assertTrue(torch.equal(a['latent'],b['latent']))
        self.assertEqual(a['cache_digest'],b['cache_digest'])
        for partial in ((10,12),(7,), (24,)):
            with self.assertRaises(ValueError):run(self.plan,True,light=True,partial=partial)


if __name__=='__main__':unittest.main()
