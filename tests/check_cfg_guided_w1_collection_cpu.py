"""Complete controlled full36 collection ON/OFF with actual pinned WC and RF.

Small Toy blocks/head and explicit Euler-like latent updates are declared
controls. This is not UniPC, Cosmos weights, real CAL, generated video or speed.
The source's exact flow, gamma, head call sites and RF condition body execute.
"""
import argparse
import ast
import copy
from contextlib import nullcontext
from enum import Enum
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace, ModuleType
import tempfile


def main():
    p=argparse.ArgumentParser(); p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    assert not a.output.exists(); a.output.mkdir(parents=True)
    import torch
    from einops import rearrange
    assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs): raise RuntimeError('Collection CPU forbids CUDA/download')
    torch.cuda._lazy_init=forbidden; torch.hub.download_url_to_file=forbidden; torch.set_num_threads(2)
    from wcomr.cfg_paired_probe_forward import WC_PATH,WC_SHA,RF_PATH,RF_SHA,PairedProbeExecutor
    from wcomr.cfg_paired_probe_production import compile_production
    from wcomr.cfg_guided_w1_forward import compile_collection,compile_output_denoise
    from wcomr.cfg_guided_w1_collection import GuidedW1Collector,CollectedSchedulePairExecutor,DENSE_STEPS,SELECTED_STEPS,tensor_sha
    from wcomr.cfg_ra_calibration import SharedSchedulePairExecutor
    from wcomr.cfg_guided_w1_grid import select_shared_alpha
    from wcomr.cfg_guided_w1_outputs import shared_output_fusion

    class DataType(str,Enum): VIDEO='video'; IMAGE='image'
    quiet=SimpleNamespace(**{k:lambda *x,**y:None for k in ('info','debug','warning')})
    def module(relative,digest,names):
        path=a.runtime/relative; raw=path.read_bytes(); assert hashlib.sha256(raw).hexdigest()==digest
        m=ModuleType('controlled_'+path.stem); m.__file__=str(path)
        vars(m).update(torch=torch,rearrange=rearrange,amp=torch.amp,F=torch.nn.functional,DataType=DataType,log=quiet)
        nodes=[n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name in names]
        assert sorted(n.name for n in nodes)==sorted(names)
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes,type_ignores=[])),str(path),'exec'),vars(m))
        return m
    wc=module(WC_PATH,WC_SHA,['worldcache_mini_train_dit_forward','apply_worldcache','compute_optimal_gamma','estimate_optical_flow','warp_feature'])
    rf=module(RF_PATH,RF_SHA,['denoise'])
    rf.Video2WorldModelRectifiedFlow=SimpleNamespace(denoise=rf.denoise)
    class Block(torch.nn.Module):
        def __init__(self,index):
            super().__init__(); self.gain=torch.nn.Parameter(torch.tensor(1.001+index*.0001),requires_grad=False)
            self.register_buffer('visits',torch.zeros(()))
        def forward(self,x,**kw):
            self.visits.add_(1)
            return x*self.gain+.002*kw['crossattn_emb'].mean()+.0001*kw['emb_B_T_D'].mean()+torch.rand(())*.00001
    class Head(torch.nn.Module):
        def forward(self,x,emb,**kw): return x+.01*x.square()+.003*emb.mean()
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.blocks=torch.nn.ModuleList([Block(i) for i in range(4)]); self.final_layer=Head()
            self.use_crossattn_projection=self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1),None); self.t_embedding_norm=lambda t:t
            self.prepare_embedded_sequence=lambda x,**kw:(x.movedim(1,-1).contiguous(),None,None)
            self.unpatchify=lambda x:x.movedim(-1,1).contiguous()
        def forward(self,**kw): return wc.worldcache_mini_train_dit_forward(self,**kw)
    shape=(1,8,2,8,8); noise=torch.linspace(-.3,.7,1024).reshape(shape); initial=noise+.7
    gt=torch.full(shape,.2); mask=torch.zeros(1,1,2,8,8); mask[:,:,0]=1
    conditions=tuple(SimpleNamespace(is_video=True,use_video_condition=True,gt_frames=gt.clone(),
        condition_video_input_mask_B_C_T_H_W=mask.clone(),cross=torch.ones(1,3,4)*(b+1)) for b in (0,1))
    for c in conditions:
        c.to_dict=lambda c=c:{'crossattn_emb':c.cross,'data_type':DataType.VIDEO}
    # Callable methods are kept outside dataclass instance state, as in actual
    # condition classes. The collector signs the actual tensor/scalar fields.
    class Condition:
        def __init__(self,c):
            for k,v in vars(c).items():
                if k!='to_dict':setattr(self,k,v)
        def to_dict(self): return {'crossattn_emb':self.cross,'data_type':DataType.VIDEO}
    conditions=tuple(Condition(c) for c in conditions)
    input_clones=[v.clone() for v in (noise,initial,gt,mask)]; initial_rng=torch.get_rng_state().clone()
    complete=[]; all_moments=[]; total_artifacts=0; failure=None
    with nullcontext(str(a.output)) as tmp:
        def run(flow,enabled,fail_writer=False):
            nonlocal total_artifacts
            torch.set_rng_state(initial_rng)
            net=Net().eval(); wc.apply_worldcache(net,num_steps=35,ret_ratio=.2,rel_l1_thresh=.08,probe_depth=2,
                osi_enabled=True,flow_enabled=flow,flow_scale=1)
            model=SimpleNamespace(net=net,tensor_kwargs={'dtype':torch.float32},config=SimpleNamespace(
                conditional_frame_timestep=.2,denoise_replace_gt_frames=True))
            path=Path(tmp)/('flow'+str(flow)+'_on'+str(enabled)+'_failure'+str(fail_writer)); path.mkdir()
            def writer(scene,step,tensors):
                nonlocal total_artifacts
                if fail_writer and step==30:raise ValueError('Injected second-origin complete tensor writer failure')
                file=path/('step'+str(step)+'.pt'); torch.save(tensors,file); loaded=torch.load(file,map_location='cpu',weights_only=True)
                assert list(loaded)==['ORIGINAL','BETA1','W1','DENSE']
                assert all(torch.equal(v,loaded[k][b]) for k,pair in tensors.items() for b,v in enumerate(pair))
                total_artifacts+=1
                return {'path':str(file),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                        'actual_post_RF_branch_tensors_reloaded':8}
            collector=GuidedW1Collector(model,scene='controlled',context=('CPU','own','condition'),enabled=enabled,writer=writer)
            if enabled:_,denoise,proof=compile_collection(a.runtime,wc,rf,collector)
            else:_,denoise,proof=compile_production(a.runtime,wc,rf)
            schedule=SharedSchedulePairExecutor(PairedProbeExecutor(model,denoise,torch))
            executor=CollectedSchedulePairExecutor(schedule,collector)
            latent=initial.clone(); outputs=[]; checks=[]; buffers=[]; condition_before=[tensor_sha(c.gt_frames) for c in conditions]
            error=None
            with torch.no_grad():
                try:
                    for step in range(1,37):
                        values=executor.pair(noise,latent,torch.full((1,1),1-step/50),conditions,executor.choose)
                        guided=8*values[0]-7*values[1]; outputs.append(guided.clone())
                        # Controlled state changes; the real UniPC batch is a
                        # separate integration and must not be claimed here.
                        latent=latent-.001*guided
                        checks.append({'step':step,'action':schedule.last['action'],'counter':net.cnt,
                            'guided':tensor_sha(guided),'rng':tensor_sha(torch.get_rng_state())})
                        buffers.append([float(b) for b in net.buffers()])
                    result=collector.finish()
                except ValueError as exc:
                    error=str(exc); result={'completed_pairs':collector.completed,'records':collector.records}
            if fail_writer:
                assert error=='Injected second-origin complete tensor writer failure'
                assert collector.completed==29 and schedule.executor.poisoned and len(collector.records)==1
                assert not collector.running and not collector.in_diagnostic
                return {'kind':'last_registered_origin_writer_failure','status':'EXPECTED_FAILURE','error':error,
                        'completed_pairs':collector.completed,'planned_pairs':36,'planned_origins':2,
                        'completed_origins':len(collector.records),'poisoned_no_continue':True}
            assert error is None,error
            assert len(outputs)==36 and [c['action'] for c in checks]==['DD' if s in DENSE_STEPS else 'CC' for s in range(1,37)]
            assert [c['counter'] for c in checks]==[2*s%70 for s in range(1,37)]
            assert condition_before==[tensor_sha(c.gt_frames) for c in conditions]
            if enabled:
                assert [r['step'] for r in result['records']]==list(SELECTED_STEPS)
                assert all(r['actual_post_RF_original_direct_equal'] and not r['teacher_updates_deployment_anchor'] for r in result['records'])
                assert [r['past_D_history'][0]['anchor_steps'] for r in result['records']]==[[6,7],[19,25]]
                assert result['score_only_teachers']==4 and len(result['actual_D_events'])==26
                assert all(c['anchor_steps']==[35,36] and c['pairs']==12 for c in result['D_only_final_history'])
                for r in result['records']:
                    sample=torch.load(Path(r['artifact']['path']),map_location='cpu',weights_only=True)
                    for alpha in (0,.5,1):
                        fused=shared_output_fusion(sample['ORIGINAL'],sample['W1'],alpha)
                        direct=((8*fused[0]-7*fused[1])-(8*sample['DENSE'][0]-7*sample['DENSE'][1])).double().square().mean().item()
                        m=r['moments']['W1']; equation=m['base_guided_MSE']+2*alpha*m['guided_error_update_mean_dot']+alpha*alpha*m['guided_update_mean_square']
                        assert abs(direct-equation)<2e-6*max(1,direct)
                    all_moments.append({**r['moments']['W1'],'scene':'flow'+str(flow)})
            return {'flow':flow,'enabled':enabled,'outputs':outputs,'final_latent':latent,'checks':checks,'buffers':buffers,
                    'result':result,'compiler':dict(proof),'rng_after':torch.get_rng_state().clone()}
        for flow in (False,True):
            off,on=run(flow,False),run(flow,True)
            assert off['checks']==on['checks'] and off['buffers']==on['buffers']
            assert all(torch.equal(x,y) for x,y in zip(off['outputs'],on['outputs']))
            assert torch.equal(off['final_latent'],on['final_latent']) and torch.equal(off['rng_after'],on['rng_after'])
            complete.append({'flow':flow,'complete_paths':2,'complete_pairs':72,'actual_guided_outputs_direct_equal':36,
                'actual_final_latent_direct_equal':True,'action_counter_RNG_and_buffer_values_equal':True,
                'collection':on['result'],'compiler':on['compiler']})
        failure=run(True,True,True)
        assert total_artifacts==5
        # Original inputs and global state are restored after both comparisons.
        assert all(torch.equal(v,s) for v,s in zip((noise,initial,gt,mask),input_clones))
        selection=select_shared_alpha(all_moments)
        assert selection['scenes']==2 and selection['states']==4
        torch.set_rng_state(initial_rng)
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status':'GUIDED_W1_PINNED_COLLECTION_FULL36_CONTROLLED_CPU_PASS_NOT_REAL_CAL',
        'Torch_version':torch.__version__,'complete_flow_OFF_ON_controls':complete,
        'registered_second_origin_writer_failure':failure,'actual_tensor_artifacts_reloaded':5,
        'actual_branch_tensors_reloaded':40,'controlled_scene_equal_selection':selection,
        'actual_source_WC_RF_sha256':{WC_PATH:WC_SHA,RF_PATH:RF_SHA},
        'actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim':False,
        'CUDA_initialized':False,'GPU_submissions':0},allow_nan=False))


if __name__=='__main__':main()
