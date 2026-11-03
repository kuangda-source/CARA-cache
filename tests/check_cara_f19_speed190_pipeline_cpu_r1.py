"""Complete frozen 35-path routing through pinned CPU Cosmos sampler fixtures."""
import copy
import json
from pathlib import Path
import torch
from wcomr.cara_f19_speed190_identity_r1 import MANIFEST
from wcomr.cara_f19_speed190_collection_r1 import collect_loaded
from wcomr.policy_generator_r1.frozen_request_arguments import request_variant


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    from check_cara_pg_production_sampling_cpu_r1 import load
    model=inference.pipe.model;net=model.net;model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*a,**kw):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(
        cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
        .set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    root=Path(__file__).resolve().parents[1]
    card=json.loads((root/MANIFEST).read_text())
    # Only the declared CPU flow toggle differs from the frozen production card.
    card=copy.deepcopy(card)
    for role in card['roles'].values():
        if 'settings' in role:role['settings']['worldcache_flow_enabled']=flow
    card['settings']['worldcache_flow_enabled']=flow
    from wcomr.cara_fast_spec_r1 import digest
    card['scope_sha256']=digest({k:v for k,v in card.items() if k!='scope_sha256'})
    samples={m:request_variant(selected[0],seed=0,num_steps=35) for m in card['FIT']+card['CHECK']}
    class Storage:
        def check(self):return dict(CPU_fixture_only=True)
    out=Path(artifact_root)/('flow_'+str(flow));out.mkdir(parents=True)
    result,evidence=collect_loaded(inference,samples,card,
        dict(runtime=runtime,wc=wc,rf=rf,inference_module=inference_module,expected_shape=[1,8,2,8,8]),
        out,Storage(),None,cpu_validation=True)
    assert result['status']=='COMPLETE35_PENDING_RELEASE_SCORING'
    assert len(result['rows'])==35 and all(r['status']=='COMPLETE' for r in result['rows'])
    assert len(result['controls'])==2 and evidence['request_boundary_checks']==35
    assert evidence['final_state_restored']
    for row in result['rows']:
        assert row['result']['guided_pairs']==row['result']['solver_steps']==36
        if row['slot']['role']=='F19_DELTA4_LIGHT_C':
            h=row['result']['semantic_history']
            assert [i+1 for i,r in enumerate(h) if r['actual']=='CONDITIONAL_D_DELTA_HOLD']==[10,14,18,21]
    return [dict(flow=flow,complete_paths=35,status='PASS',controls=result['controls'],
        final_state_restored=True,actual_Cosmos_weights=False,real_generated_video=False)]


def run(runtime,artifact_root):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    old=previous.body
    try:
        previous.body=body
        return previous.run(runtime,artifact_root)
    finally:previous.body=old
