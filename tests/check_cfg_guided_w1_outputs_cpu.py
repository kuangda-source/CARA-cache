"""Actual Torch tensor core and pinned RF condition processing, CPU-only.

The small supplied tensors are controlled examples, not Cosmos hidden states,
same-state supervision, scientific CAL data or new generated videos.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):raise RuntimeError('Output-core CPU forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    from wcomr.cfg_guided_w1_outputs import shared_output_fusion,guided_velocity_moments,unit_increment_residual
    from wcomr.cfg_guided_w1_grid import select_shared_alpha
    from wcomr.cfg_paired_probe_forward import RF_PATH,RF_SHA,_function,_compile
    rng=torch.get_rng_state().clone();shape=(1,2,2,2,3)
    tensor=lambda v:torch.full(shape,v,dtype=torch.float32)
    original=(tensor(1),tensor(1));proposed=(tensor(0),tensor(.5));dense=(tensor(0),tensor(0))
    all_inputs=original+proposed+dense
    clones=[v.clone() for v in all_inputs];versions=[v._version for v in all_inputs]
    moment=guided_velocity_moments(scene='coupled',state='one',original=original,proposed=proposed,dense=dense)
    choice=select_shared_alpha([moment]);assert choice['selected_alpha']==0
    assert moment['diagnostics']['proposed_branch_MSE']==[0,.25]
    assert moment['base_guided_MSE']==1 and moment['guided_update_mean_square']==20.25
    assert shared_output_fusion(original,proposed,0) is original
    assert shared_output_fusion(original,proposed,1) is proposed
    half=shared_output_fusion(original,proposed,.5)
    assert all(torch.equal(v,(x+y)/2) for v,x,y in zip(half,original,proposed))
    # A nonlinear head does not commute with hidden interpolation.
    h0,h1=tensor(-1),tensor(1)
    output_fusion=shared_output_fusion((h0.square(),)*2,(h1.square(),)*2,.5)
    assert torch.equal(output_fusion[0],tensor(1)) and not torch.equal(output_fusion[0],((h0+h1)/2).square())
    # Execute the complete source-pinned actual RF denoise body with supplied net
    # output. Check both gt-replacement settings and conditioning timesteps.
    node=_function(a.runtime,RF_PATH,RF_SHA,'denoise');denoise=_compile(node,{'torch':torch},'<actual-RF-denoise-CPU-output-core>')
    noise=tensor(3);latent=tensor(.25);time=torch.ones(1,1)
    mask=torch.zeros(1,1,2,2,3);mask[:,:,0]=1
    condition=SimpleNamespace(is_video=True,use_video_condition=True,gt_frames=tensor(2),
                              condition_video_input_mask_B_C_T_H_W=mask,to_dict=lambda:{})
    cases=[]
    for replace in (False,True):
        for conditional_time in (-1,.2):
            model=SimpleNamespace(tensor_kwargs={'dtype':torch.float32},config=SimpleNamespace(
                denoise_replace_gt_frames=replace,conditional_frame_timestep=conditional_time))
            capture=[]
            def net(*,x_B_C_T_H_W,timesteps_B_T,**kwargs):
                capture.append((x_B_C_T_H_W.clone(),timesteps_B_T.clone()));return model.supplied
            model.net=net
            def velocities(pair):
                result=[]
                for value in pair:
                    model.supplied=value;result.append(denoise(model,noise,latent,time,condition))
                return tuple(result)
            base,new,truth=velocities(original),velocities(proposed),velocities(dense)
            row=guided_velocity_moments(scene='conditioned',state=str((replace,conditional_time)),original=base,proposed=new,dense=truth)
            fused=shared_output_fusion(base,new,.5)
            for slot in (0,1):
                assert torch.equal(fused[slot],(base[slot]+new[slot])/2)
                expected=noise-condition.gt_frames if replace else original[slot]
                assert torch.equal(base[slot][:,:,0],expected[:,:,0])
            assert all(torch.equal(x[:,:,0],condition.gt_frames[:,:,0]) for x,t in capture)
            if conditional_time >= 0:
                assert all(tuple(t.shape)==(1,2) and t[0,0]==conditional_time and t[0,1]==1 for x,t in capture)
            else:assert all(torch.equal(t,time) for x,t in capture)
            if replace:assert row['base_guided_MSE']==.5 and row['guided_update_mean_square']==10.125
            else:assert row['base_guided_MSE']==1 and row['guided_update_mean_square']==20.25
            cases.append({'replace_gt':replace,'conditional_time':conditional_time,
                          'base_guided_MSE':row['base_guided_MSE'],'calls':len(capture)})
    cp,ap,ar=tensor(5),tensor(2),tensor(7)
    saved=[v.clone() for v in (cp,ap,ar)];beta1=unit_increment_residual(current_probe=cp,anchor_probe=ap,anchor_residual=ar)
    assert torch.equal(beta1,tensor(10)) and all(torch.equal(x,y) for x,y in zip((cp,ap,ar),saved))
    refused=[]
    bad_cases=[('different_shape',lambda:shared_output_fusion(original,(tensor(0)[:,:,:,:,:1],tensor(0)[:,:,:,:,:1]),.5)),
               ('hidden_BF16',lambda:shared_output_fusion(tuple(v.bfloat16() for v in original),proposed,.5)),
               ('nonfinite',lambda:shared_output_fusion(original,(tensor(float('nan')),tensor(0)),.5)),
               ('unregistered_alpha',lambda:shared_output_fusion(original,proposed,.25)),
               ('boolean_alpha',lambda:shared_output_fusion(original,proposed,True)),
               ('missing_branch',lambda:guided_velocity_moments(scene='x',state='y',original=original,proposed=proposed,dense=(tensor(0),))),
               ('nonfinite_anchor',lambda:unit_increment_residual(current_probe=cp,anchor_probe=ap,anchor_residual=tensor(float('inf'))))]
    for name,fn in bad_cases:
        try:fn()
        except ValueError:refused.append(name)
        else:raise AssertionError(name)
    assert all(torch.equal(v,c) and v._version==n for v,c,n in zip(all_inputs,clones,versions))
    assert torch.equal(torch.get_rng_state(),rng) and not torch.cuda.is_initialized()
    print(json.dumps({'status':'GUIDED_W1_POST_DENOISE_TENSOR_CORE_ACTUAL_CPU_PASS_NOT_REAL_CAL',
        'Torch_version':torch.__version__,'RF_source_sha256':hashlib.sha256((a.runtime/RF_PATH).read_bytes()).hexdigest(),
        'actual_pinned_RF_denoise_condition_cases':cases,'coupled_selected_alpha':choice['selected_alpha'],
        'nonlinear_hidden_fusion_differs_from_output_fusion':True,'exact_endpoint_objects_preserved':True,
        'inputs_versions_and_RNG_unchanged':True,'beta1_control':10,'mutation_refusals':refused,
        'real_Cosmos_teacher_or_video_or_latency_claim':False,'CUDA_initialized':False,'GPU_submissions':0}))


if __name__=='__main__':main()
