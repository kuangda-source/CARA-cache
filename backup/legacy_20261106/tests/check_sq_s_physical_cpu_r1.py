"""Actual pinned tiny CPU sampler: A6000 imports one retained tiny OFF per flow."""
import copy
import hashlib
import json
from pathlib import Path

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.mid_coverage import tree_digest
from wcomr.sq_s_batch_r1 import Requests, digest, make_scope
from wcomr.sq_s_physical_r1 import PhysicalRequests, collect, make_physical_scope
from wcomr.sq_s_storage_r1 import SCollectionStore


def run(runtime, artifact_root, tiny_tensor_loader, host, retained_fixture):
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
        origin=initial.fingerprint();root=Path(artifact_root)/('physical-flow-'+str(flow))
        samples={s.name:s for s in selected[:2]}
        upper=make_scope(profile,tuple(samples),cpu_fixture=True)
        store=SCollectionStore(root/'streaming',prompts=tuple(samples),maximum_total_bytes=16*2**20,
            maximum_file_bytes=8*2**20,minimum_free_bytes=2**20)
        common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},
            inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
        counts=dict(head=0,deep=0)
        def head_call(*args):counts['head']+=1
        def deep_call(*args):counts['deep']+=1
        hooks=[net.final_layer.register_forward_pre_hook(head_call),
               net.blocks[settings['probe_depth']].register_forward_pre_hook(deep_call)]
        originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
        model_sha=tree_digest({n:p for n,p in net.named_parameters()})
        identity=digest(dict(explicit_CPU_fixture=True,flow=flow,upper=upper['scope_sha256'],model_sha256=model_sha))
        witness=None;source_counts=dict(head=0,deep=0)
        # Old independently initialized tiny models did not retain weights and
        # cannot serve as byte-equivalent cross-run fixtures. Create one
        # separately counted CPU source role with a durable tiny checkpoint.
        if host=='two_card':
            assets=root/'CPU-fixture-assets';assets.mkdir(parents=True,exist_ok=False)
            weights=assets/'weights.pt'
            with weights.open('xb') as stream:
                torch.save({n:p.detach().cpu().clone() for n,p in net.named_parameters()},stream)
            source=Requests(scope=upper,inference=inference,samples=samples,profile=profile,
                common=common,sink=store,logical_copy_cap_bytes=128*2**20,cpu_validation=True)
            slot=next(s for s in upper['slots'] if s['id']=='p0-Shared25-C-OFF')
            initial.restore();result=source(slot,assets/'retained-OFF')
            source_counts=dict(counts);assert source_counts==dict(head=72,deep=50)
            counts.update(head=0,deep=0)
            snapshot=tiny_tensor_loader(weights,map_location='cpu',weights_only=True)
            assert tree_digest(snapshot)==model_sha
            with torch.no_grad():
                for name,parameter in net.named_parameters():parameter.copy_(snapshot[name])
            assert tree_digest({n:p for n,p in net.named_parameters()})==model_sha
            initial.restore()
            result['RGB']=dict(frames=93,sha256=result['RGB']['sha256'])
            path=assets/'retained-OFF.json';atomic_json(path,result)
            raw=path.read_bytes();result=json.loads(raw)
            witness=dict(CPU_fixture=True,slot_id=slot['id'],original_host='two_card',old_bytes_verified=True,
                new_ON_equivalence_accepted=False,execution_identity_sha256=identity,result=result,
                source=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),
                    tiny_model_sha256=model_sha,tiny_checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
                    checkpoint_reloaded_and_parameter_values_equal=True,source_CPU_paths=1))
            witness['witness_sha256']=digest(witness)
        physical=make_physical_scope(upper,host,identity,witness)
        base=Requests(scope=upper,inference=inference,samples=samples,profile=profile,
            common=common,sink=store,logical_copy_cap_bytes=128*2**20,cpu_validation=True)
        entry=PhysicalRequests(base,physical,identity,witness=witness,
            CPU_decode_fixture=lambda r:dict(frames=93,sha256=r['RGB']['sha256']))
        before_seen=[]
        def before(slot):
            before_seen.append(slot['id']);initial.restore()
            assert initial.fingerprint()==origin
            assert originals==(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
        try:
            state=collect(entry,root/'paths',before_request=before,storage=store,
                save=lambda value:atomic_json(root/'batch.json',value))
            n=physical['counts']['new_paths']
            assert len(entry.seen)==10 and len(base.seen)==len(before_seen)==n
            assert counts==dict(head=physical['counts']['branch_readouts'],deep=physical['counts']['deep_block_calls']),counts
            if witness:assert not (root/'paths'/witness['slot_id']).exists()
            rows=[r for path in state['rows'] for r in path['result']['S_rows']]
            original_loader=topology._tiny_tensor_loader;topology._tiny_tensor_loader=tiny_tensor_loader
            try:reload=topology.audit_storage(store.root,rows)
            finally:topology._tiny_tensor_loader=original_loader
            return [dict(flow=flow,status='PASS',complete_new_CPU_paths=n,logical_paths=10,warm_CPU_paths=2,
                imported_OFF_roles=len(physical['reused_slot_ids']),physical_counts=physical['counts'],
                fixture_source_CPU_paths=int(witness is not None),fixture_source_forward_counts=source_counts,
                fixture_model_sha256=model_sha,fixture_checkpoint_reloaded=witness is not None,
                total_observed_head_calls_including_source=counts['head']+source_counts['head'],
                total_observed_deep_calls_including_source=counts['deep']+source_counts['deep'],
                upper_scope_sha256=upper['scope_sha256'],physical_scope_sha256=physical['physical_scope_sha256'],
                whole_state_status=state['status'],OFF_ON_controls=state['physical_execution']['OFF_ON_controls'],
                observed_head_forward_calls=counts['head'],observed_deep_block_calls=counts['deep'],
                exact_full36_guided_final_latent_and_CPU_RGB_witness=True,
                full_pipeline_decode_uses_declared_CPU_standin=True,
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
