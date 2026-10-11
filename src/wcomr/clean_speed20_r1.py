"""Two scenes x five fixed configurations x forward/reverse timings.

The ordinary guarded Inference.generate body stays intact. Only its pipeline
call is timed; video writing is deferred. No research snapshots or per-step
content hashes/copies occur in CLEAN mode. Algorithm-owned tensors remain.
"""
import contextlib
import copy
import inspect
import time
import types
from pathlib import Path

import torch

from .cfg_guided_w1_deployment_sampling import _compile_A, _attach_A
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_paired_probe_velocity import compile_velocity
from .cfg_ra_joint_control import JointCDController
from .cfg_ra_joint_execution import JointPolicyPairExecutor
from .decoder_policy import decode_policy
from .full_sampling import CompleteStateRoundtrip
from .light_sampling import synchronize
from .source_aware_current_birth_sampling_r2 import CurrentBirthSamplingOwner
from .w1_native_reference_sampling import official_native_forward

METHODS=('NATIVE','WC','RA','A_NO_P','KEEP_A_P')
A_METHOD='BETA1_ONE_PHASE'
STRATEGY='WORKING_P_AGE_KEEP_INTERVAL'
SCENES=('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199')
CARD='WC-CLEAN-SPEED20-BETA1-KEEP-R2-20261012-A'
RUN='wc-clean-speed20-beta1-keep-r2'


def matrix():
    rows=[]
    for scene in SCENES:
        for method in METHODS:
            for rep in (1,2):
                rows.append(dict(id=f'{SCENES.index(scene)}_warm_{method}_{rep}',scene=scene,
                    method=method,section='WARMUP',round=rep))
        for rep in (1,2):
            for method in METHODS if rep==1 else METHODS[::-1]:
                rows.append(dict(id=f'{SCENES.index(scene)}_timed_{method}_{rep}',scene=scene,
                    method=method,section='TIMED',round=rep))
    assert len(rows)==40 and sum(r['section']=='TIMED' for r in rows)==20
    return rows


@contextlib.contextmanager
def patched(owner,name,value):
    own,prior=name in vars(owner),getattr(owner,name)
    setattr(owner,name,value)
    try:yield
    finally:
        if own:setattr(owner,name,prior)
        else:delattr(owner,name)


def install(model,method,context,runtime,wc,rf,settings,calibration,specs,audit=False):
    """Compile outside timing; preserve the registered controllers/readouts.

    The P owner diagnostic MLP/head hooks are removed. Their records are never
    inputs to the policy. No algorithm cache, anchor or projection is removed.
    """
    net=model.net
    wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
    net.worldcache_enabled=method!='NATIVE'
    owner=readout=executor=None
    original=model.get_velocity_fn_from_batch.__func__
    if method=='NATIVE':
        net.forward=official_native_forward(net)
        net.worldcache_enabled=False
    elif method in ('RA','A_NO_P'):
        mode=A_METHOD if method=='A_NO_P' else 'RA'
        _,denoise,proof,readout=_compile_A(runtime,wc,rf,mode,context,model)
        base=NativePolicyPairedExecutor(model,denoise,torch,wc_forward=wc.worldcache_mini_train_dit_forward,
            rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
        executor=JointPolicyPairExecutor(base,JointCDController(calibration,specs['SOURCE_RA']['threshold']))
        executor=_attach_A(executor,readout)
        original,_=compile_velocity(runtime,rf,executor,executor.choose)
    elif method=='KEEP_A_P':
        owner=CurrentBirthSamplingOwner(model,method='A_CPD_'+A_METHOD,context=context,
            runtime=runtime,wc=wc,rf=rf,calibration=calibration,spec=specs['A_CPD_'+A_METHOD])
        if not audit:
            for hook in owner.hooks:hook.remove()
            owner.hooks.clear()
        readout=owner.deployment.readout
        original,_=compile_velocity(runtime,rf,owner,owner.choose)
    elif method!='WC':raise ValueError('Unknown fixed clean speed method')
    return original,owner,executor,readout


def execute(inference,sample,method,*,runtime,wc,rf,settings,calibration,specs,
            inference_module,output,expected_shape,audit=False,save_video=True,CPU_native=None):
    if method not in METHODS or sample.num_steps!=35 or not inference.rank0:
        raise ValueError('Exact complete method/35-step guarded request required')
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary guardrails required')
    model,net=inference.pipe.model,inference.pipe.model.net
    scheduler=model.sample_scheduler
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    context=(RUN+':'+sample.name,'Cosmos-Predict2.5-2B','fixed-seed0-request')
    result={'method':method,'audit':audit,'guided_pairs':0,'solver_steps':0,
        'in_timing_guided_copies':0,'in_timing_hashes':0,'research_checkpoints':0}
    captured={};guided=[];deferred=[];wc_deep=[[False,False] for _ in range(36)]
    prior_forward=net.forward
    prior_enabled=inference.pipe.worldcache_enabled
    started=time.perf_counter()
    # Test-only declared Native boundary; production always uses actual class.
    if CPU_native is not None and method=='NATIVE':
        original,owner,executor,readout=install(model,'WC',context,runtime,wc,rf,settings,calibration,specs,audit=audit)
        net.forward=types.MethodType(CPU_native,net);net.worldcache_enabled=False
    else:original,owner,executor,readout=install(model,method,context,runtime,wc,rf,settings,calibration,specs,audit=audit)
    inference.pipe.worldcache_enabled=method!='NATIVE'
    def factory(bound,*a,**kw):
        velocity=original(bound,*a,**kw)
        def observed(noise,latent,timestep):
            value=velocity(noise,latent,timestep)
            result['guided_pairs']+=1
            if audit:
                guided.append(value.detach().cpu().clone())
                result['in_timing_guided_copies']+=1
            return value
        return observed
    old_step=scheduler.step
    def step(*a,**kw):
        value=old_step(*a,**kw);result['solver_steps']+=1
        if result['solver_steps']==36:
            captured['latent']=value[0].squeeze(0).detach()
            captured['version']=None if torch.is_inference(captured['latent']) else captured['latent']._version
        return value
    old_pipe=inference.pipe.generate_vid2world
    def pipeline(*a,**kw):
        synchronize();begin=time.perf_counter()
        try:return old_pipe(*a,**kw)
        finally:
            synchronize();result['core_seconds']=time.perf_counter()-begin
    old_decode=model.decode
    def decode(*a,**kw):
        with decode_policy(True):return old_decode(*a,**kw)
    def deferred_write(video,path,fps):deferred.append((video,path,fps))
    old_write=inference_module.save_img_or_video
    try:
        with contextlib.ExitStack() as stack:
            if method=='WC':
                def saw_deep(_module,_args):
                    pair,slot=result['guided_pairs'],int(net.cnt)%2
                    if pair>=36 or wc_deep[pair][slot]:raise ValueError('Duplicate WC actual deep branch')
                    wc_deep[pair][slot]=True
                hook=net.blocks[int(net.probe_depth)].register_forward_pre_hook(saw_deep)
                stack.callback(hook.remove)
            stack.enter_context(patched(model,'get_velocity_fn_from_batch',types.MethodType(factory,model)))
            stack.enter_context(patched(scheduler,'step',step))
            stack.enter_context(patched(model,'decode',decode))
            stack.enter_context(patched(inference.pipe,'generate_vid2world',pipeline))
            stack.enter_context(patched(inference_module,'save_img_or_video',deferred_write))
            stack.enter_context(patched(inference.setup_args,'keep_going',True))
            synchronize();result['method_install_seconds']=time.perf_counter()-started
            begin=time.perf_counter();paths=inference.generate([sample],output_dir=output)
            synchronize();result['guarded_pipeline_without_write_seconds']=time.perf_counter()-begin
        if not paths:
            result['status']='TEXT_REJECTED' if result['solver_steps']==0 else 'VIDEO_REJECTED'
        else:
            if len(paths)!=1 or len(deferred)!=1 or (result['solver_steps'],result['guided_pairs'])!=(36,36):
                raise ValueError('Complete guarded full36 output missing')
            result['status']='COMPLETE'
        if result['solver_steps']:
            latent=captured['latent']
            if not torch.is_inference(latent) and latent._version!=captured['version']:
                raise ValueError('Decoder mutated deferred final latent')
            final=latent.cpu().clone()
            if list(final.shape)!=expected_shape or not bool(torch.isfinite(final).all()):
                raise ValueError('Final latent geometry/nonfinite')
            result['final_latent']=final
            if owner:
                result['actions']=[h['action'] for h in owner.deployment.history]
                result['A_history']=copy.deepcopy(readout.history)
            elif executor:
                result['actions']=[d.action for d in executor.controller.history]
                result['A_history']=copy.deepcopy(readout.history) if readout else None
            else:
                result['actions']=[''.join('D' if v else 'C' for v in pair) for pair in wc_deep] if method=='WC' else None
                result['A_history']=None
            result['scheduler_timesteps']=scheduler.timesteps.cpu().tolist()
            if audit:result['guided']=guided
        begin=time.perf_counter()
        for video,path,fps in deferred:
            if save_video:old_write(video,path,fps)
        result['video_write_seconds']=time.perf_counter()-begin
        result['video_path']=paths[0] if paths and save_video else None
        result['write_deferred_after_main_timer']=True
        return result
    finally:
        begin=time.perf_counter()
        if owner:owner.close()
        if readout:
            for c in readout.calibrators:c.reset(context)
            readout.warp=readout.to_velocity=None
        net.forward=prior_forward
        inference.pipe.worldcache_enabled=prior_enabled
        synchronize();result['method_cleanup_seconds']=time.perf_counter()-begin
