"""Ten actual pinned CPU paths per flow, with declared tiny model boundaries."""
from pathlib import Path

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.sq_s_batch_r1 import Requests, collect, make_scope
from wcomr.sq_s_storage_r1 import SCollectionStore


def run(runtime, artifact_root, tiny_tensor_loader):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    import check_sq_s_collection_cpu_r1 as topology

    def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        model.config.state_ch=8
        class Head(torch.nn.Module):
            def forward(self,x,*args,**kwargs):return x+.01*x.square()
        net.final_layer=Head().eval()
        net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
        cls,_=previous.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
        def conditions(batch):
            return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b+.1*(batch['prompt']==selected[1].name)),
                fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
        model.conditioner.get_condition_with_negative_prompt=conditions
        model.get_data_and_condition=lambda batch:(None,torch.zeros(1,8,2,8,8),None)
        profile=previous.test_profile();initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
        origin=initial.fingerprint();root=Path(artifact_root)/('batch-flow-'+str(flow))
        samples={s.name:s for s in selected[:2]}
        scope=make_scope(profile,tuple(samples),cpu_fixture=True)
        store=SCollectionStore(root/'streaming',prompts=tuple(samples),maximum_total_bytes=16*2**20,
            maximum_file_bytes=8*2**20,minimum_free_bytes=2**20)
        common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},
            inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
        entry=Requests(scope=scope,inference=inference,samples=samples,profile=profile,
            common=common,sink=store,logical_copy_cap_bytes=128*2**20,cpu_validation=True)
        counts=dict(head=0,deep=0)
        def head_call(*args):counts['head']+=1
        def deep_call(*args):counts['deep']+=1
        hooks=[net.final_layer.register_forward_pre_hook(head_call),
               net.blocks[settings['probe_depth']].register_forward_pre_hook(deep_call)]
        originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
        def before(slot):
            initial.restore()
            assert initial.fingerprint()==origin
            assert originals==(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
        try:
            state=collect(entry,root/'paths',before_request=before,storage=store,
                save=lambda value:atomic_json(root/'batch.json',value))
            assert len(entry.seen)==10 and len(state['OFF_ON_controls'])==4
            assert counts==dict(head=936,deep=552),counts
            rows=[r for path in state['rows'] for r in path['result']['S_rows']]
            original_loader=topology._tiny_tensor_loader;topology._tiny_tensor_loader=tiny_tensor_loader
            try:reload=topology.audit_storage(store.root,rows)
            finally:topology._tiny_tensor_loader=original_loader
            return [dict(flow=flow,status='PASS',complete_CPU_paths=10,warm_CPU_paths=2,
                counts=scope['counts'],scope_sha256=scope['scope_sha256'],
                whole_state_status=state['status'],OFF_ON_controls=state['OFF_ON_controls'],
                observed_head_forward_calls=counts['head'],observed_deep_block_calls=counts['deep'],
                exact_full36_guided_final_latent_decoded93_RGB=True,
                all_results_JSON_metadata_only=True,storage=state['storage'],reload_audit=reload,
                S_labels_collected=0,actual_Cosmos_weights=False,real_generated_video=False)]
        finally:
            for hook in hooks:hook.remove()
            initial.restore()
            assert initial.fingerprint()==origin
            assert originals==(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)

    original=previous.body;previous.body=body
    try:return previous.run(Path(runtime),artifact_root)
    finally:previous.body=original
