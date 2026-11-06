"""Actual production owners and pinned sampler, declared tiny CPU stand-ins."""
import copy
from pathlib import Path
import random
import tempfile
import sys

import numpy as np
import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1 import production_sampling as production
from wcomr.policy_generator_r1.interval_grammar import Edge,compile_policy
from wcomr.source_aware_phase_sampling import bind_globals
from wcomr.sq_s_sources_r1 import PARENTS
from wcomr.sq_s_owner_roundtrip_r1 import PolicyOwnerRoundtrip


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*args,**kwargs):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    net.register_buffer('_sq_owner_roundtrip_probe',torch.zeros(1))
    cls,_=previous.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),
        fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
        torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda batch:(None,torch.zeros(1,8,2,8,8),None)
    profile=previous.test_profile();initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    root=Path(artifact_root)/('S_owner_flow_'+str(flow));events=[];enabled=[False]
    class CheckedOwner(production.PolicyOwner):
        @torch.no_grad()
        def pair(self,*args,**kwargs):
            result=super().pair(*args,**kwargs)
            step=self.readout.completed
            if enabled[0] and step in (8,9,22,35):
                physical=CompleteStateRoundtrip(self.net,self.model.sample_scheduler,args[1])
                physical_origin=physical.fingerprint()
                snapshot=PolicyOwnerRoundtrip(self,logical_copy_cap_bytes=128*2**20)
                assert snapshot.bytes>0 and snapshot.restore()==snapshot.origin
                try:
                    self.history[-1]['SQ_INJECTED_METADATA']='must not survive'
                    self.readout.history[-1]['SQ_INJECTED_METADATA']='must not survive'
                    self.readout.calibrators[0].numerator+=3
                    self.readout.calibrators[0].anchors[-1].probe.add_(.125)
                    self.executor.last={'action':'SHADOW_MUST_NOT_COMMIT'}
                    self.fallback_reason='INJECTED_SHADOW_ONLY'
                    self.net._sq_owner_roundtrip_probe.add_(7)
                    torch.rand(3);random.random();np.random.random()
                finally:
                    physical.restore()
                    try:snapshot.restore()
                    except ValueError as error:
                        assert 'restored for cleanup, collection not accepted' in str(error)
                    else:raise AssertionError('Dirty owner was silently accepted')
                assert snapshot.fingerprint()==snapshot.origin and physical.fingerprint()==physical_origin
                original=self.policy['fingerprint'];self.policy['fingerprint']='CHANGED_POLICY_MUST_REFUSE'
                try:
                    try:snapshot.restore()
                    except ValueError:pass
                    else:raise AssertionError('Changed policy restored')
                finally:self.policy['fingerprint']=original
                self.executor.poisoned=True
                try:
                    try:snapshot.restore()
                    except ValueError:pass
                    else:raise AssertionError('Poisoned parent recovered')
                finally:self.executor.poisoned=False
                self.readout.sq_unregistered_mutable_field=True
                try:
                    try:snapshot.restore()
                    except ValueError:pass
                    else:raise AssertionError('Unknown readout field was silently ignored')
                finally:del self.readout.sq_unregistered_mutable_field
                old_count=self.net.cnt
                self.history.append({});self.readout.history.append({});self.readout.completed+=1
                self.net.cnt=2*self.readout.completed%70
                try:
                    try:snapshot.restore()
                    except ValueError as error:assert 'cannot be rewound' in str(error)
                    else:raise AssertionError('An advanced parent pair was rewound')
                finally:
                    self.history.pop();self.readout.history.pop();self.readout.completed-=1;self.net.cnt=old_count
                try:PolicyOwnerRoundtrip(self,logical_copy_cap_bytes=1)
                except ValueError:pass
                else:raise AssertionError('Owner copy cap was ignored')
                assert snapshot.restore()==snapshot.origin
                events.append(dict(step=step,dirty_owner_refused_and_cleaned=True,
                    policy_and_poison_changes_refused=True,logical_snapshot_bytes=snapshot.bytes))
            return result
    runner=bind_globals(production.execute,{'PolicyOwner':CheckedOwner})
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},
        inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
    rows=[]
    try:
        for parent,dense in PARENTS.items():
            bounds=dense+(37,);policy=compile_policy(profile,[Edge(a,b) for a,b in zip(bounds,bounds[1:])])
            values=[]
            for on in (False,True):
                initial.restore();enabled[0]=on
                value=runner(inference,selected[0],profile=profile,policy=policy,
                    output=root/(parent+'-'+str(on)),**common)
                assert value['status']=='COMPLETE' and value['guided_pairs']==value['solver_steps']==36
                assert [row['actual'] for row in value['semantic_history']]==policy['actions']
                values.append(value)
            a,b=values
            assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
            assert torch.equal(a['final_latent'],b['final_latent'])
            assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
            rows.append(dict(parent=parent,full36_OFF_ON_guided_latent_CPU_video_equal=True))
        assert len(events)==8
        return [dict(flow=flow,status='PASS',parents=rows,events=events,complete_CPU_paths=4,
            actual_Cosmos_weights=False,real_generated_video=False,S_labels_collected=0,
            complete_S_collector_accepted=False)]
    finally:initial.restore()


def run(runtime,artifact_root):
    runtime=Path(runtime)
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import check_cara_pg_production_sampling_cpu_r1 as previous
    original=previous.body
    previous.body=body
    try:return previous.run(runtime,artifact_root)
    finally:previous.body=original


if __name__=='__main__':
    import json
    with tempfile.TemporaryDirectory() as directory:
        print(json.dumps(run(Path(__file__).resolve().parents[1]/'cache/runtime',Path(directory)),default=str))
