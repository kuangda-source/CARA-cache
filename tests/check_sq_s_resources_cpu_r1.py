"""Complete before-pair ownership schemas on the pinned tiny CPU sampler."""
from pathlib import Path
from unittest.mock import patch

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.interval_grammar import Edge,compile_policy
from wcomr.sq_risk_r1 import TARGETS
from wcomr.sq_s_collection_r1 import SParentCollector,execute
from wcomr.sq_s_sources_r1 import PARENTS
from wcomr.sq_s_resources_r1 import before_pair_inventory


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*args,**kwargs):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=previous.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(cls(
        crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True])
        ).set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda batch:(None,torch.zeros(1,8,2,8,8),None)
    profile=previous.test_profile();initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},
        inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
    original=SParentCollector.copy_budget;events=[];paths=[]
    def observed(collector,inputs):
        report=before_pair_inventory(collector.owner,inputs)
        result=original(collector,inputs)
        assert report['logical_copy_guard_bytes']==result and not report['any_meta_tensors']
        assert report['native_field_names']==sorted(key for key in wc_fields if hasattr(collector.owner.net,key))
        events.append(dict(parent=collector.parent,step=collector.owner.readout.completed+1,
            flow=flow,inventory=report))
        return result
    from wcomr.mid_coverage import WC_FIELDS as wc_fields
    try:
        with patch.object(SParentCollector,'copy_budget',observed):
            for parent,dense in PARENTS.items():
                initial.restore();bounds=dense+(37,)
                policy=compile_policy(profile,[Edge(a,b) for a,b in zip(bounds,bounds[1:])])
                result=execute(inference,selected[0],parent=parent,profile=profile,policy=policy,enabled=True,
                    sink=lambda row,raw:None,logical_copy_cap_bytes=128*2**20,
                    output=Path(artifact_root)/('resource-flow-'+str(flow))/parent,**common)
                assert result['status']=='COMPLETE' and result['guided_pairs']==result['solver_steps']==36
                assert [r['step'] for r in result['S_rows']]==list(TARGETS)
                paths.append(dict(parent=parent,complete36=True,CPU_fixture=True))
        assert len(events)==54 and [r['step'] for r in events]==list(TARGETS)*2
        return [dict(flow=flow,paths=paths,events=events,CPU_fixture=True,
            actual_Cosmos_weights=False,S_real_labels=0)]
    finally:initial.restore()


def run(runtime,artifact_root):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    original=previous.body;previous.body=body
    try:return previous.run(runtime,artifact_root)
    finally:previous.body=original
