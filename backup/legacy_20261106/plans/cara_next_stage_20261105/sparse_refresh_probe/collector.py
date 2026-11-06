"""One R18C prefix, fixed same-state S1 interventions, then the gated S2 card."""
import copy
import gc
from pathlib import Path
import statistics
import time

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.calibration import Anchor
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_sparse_refresh_probe_r1 import LayerReuse,SparseOwner,s1_gate
from wcomr.cfg_paired_probe_velocity import compile_velocity
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.mid_coverage import PrefixComplete
from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
from wcomr.policy_generator_r1.production_sampling import _cache_snapshot
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import object_state,restore_object_state
from wcomr.source_aware_phase_sampling import bind_globals


def retain(value):
    """Copy mutable topology; pinned cache/anchor tensor storage is replaced."""
    if isinstance(value,torch.Tensor):return value.clone() if value.numel()<=1 else value
    if isinstance(value,Anchor):return copy.copy(value)
    if isinstance(value,dict):return {k:retain(v) for k,v in value.items()}
    if isinstance(value,list):return [retain(v) for v in value]
    if isinstance(value,tuple):return tuple(retain(v) for v in value)
    return copy.deepcopy(value)


class ProbeState:
    """Disposable local fork; no full GPU snapshot or teacher write to parent."""
    fields=('completed','history','current','poisoned','delta','delta_step','residual_delta',
        'probe_delta','cache_birth_steps','synthetic_uncond_anchor_step','true_uncond_anchor','partial_updates')

    def __init__(self,owner):
        self.owner=owner
        self.cache,self.versions=_cache_snapshot(owner.net)
        self.readout={k:retain(getattr(owner.readout,k)) for k in self.fields}
        self.calibrators=[retain(vars(c)) for c in owner.readout.calibrators]
        self.solver=copy.deepcopy(object_state(owner.model.sample_scheduler))
        self.buffers=[(v,v.detach().clone()) for v in owner.net.buffers()]
        self.executor={k:retain(getattr(owner.executor,k)) for k in ('running','poisoned','last')}
        self.history=copy.deepcopy(owner.history)
        self.actions=list(owner.policy['actions'])
        self.partial=owner.partial_updates
        self.sync=owner.readout.sync_residual
        self.layers=retain(owner.layers.residuals),copy.deepcopy(owner.layers.birth_steps)
        self.rng=RNGState()

    def restore_cache(self):
        owner=self.owner
        if any(version is not None and tensor._version!=version for tensor,version in self.versions):
            raise ValueError('Local probe mutated retained parent cache storage')
        for key,value in retain(self.cache).items():setattr(owner.net,key,value)
        for calibrator,value in zip(owner.readout.calibrators,self.calibrators):
            vars(calibrator).clear();vars(calibrator).update(retain(value))
        for key in ('delta','delta_step','residual_delta','probe_delta','cache_birth_steps',
                'synthetic_uncond_anchor_step','true_uncond_anchor'):
            setattr(owner.readout,key,retain(self.readout[key]))

    def restore(self):
        owner=self.owner;self.restore_cache()
        for key,value in self.readout.items():setattr(owner.readout,key,retain(value))
        restore_object_state(owner.model.sample_scheduler,self.solver)
        for target,saved in self.buffers:target.copy_(saved)
        for key,value in self.executor.items():setattr(owner.executor,key,retain(value))
        owner.history=copy.deepcopy(self.history);owner.policy['actions']=list(self.actions)
        owner.partial_updates=self.partial;owner.readout.sync_residual=self.sync
        owner.force_dense=False;owner.fallback_reason=None
        owner.layers.residuals=retain(self.layers[0]);owner.layers.birth_steps=copy.deepcopy(self.layers[1])
        self.rng.restore()


def guided(pair):return pair[0]+7*(pair[0]-pair[1])
def mse(a,b):return float((a.double()-b.double()).square().mean())


class S1Owner(SparseOwner):
    def __init__(self,*args,s1_config,save,**kwargs):
        super().__init__(*args,**kwargs)
        self.layers=LayerReuse(self.net,cache_from=min(14,len(self.net.blocks)))
        self.s1_config=s1_config;self.save=save;self.s1=None

    def sync_device(self):
        if self.device.type=='cuda':torch.cuda.synchronize(self.device)

    def local_pair(self,mode,noise,latent,timestep,conditions):
        t=self.readout.completed+1
        partial=mode in ('P_sync','P_raw')
        self.partial_updates=self.readout.partial_updates=(t,) if partial else ()
        self.readout.sync_residual=mode!='P_raw'
        self.policy['actions'][t-1]='C' if mode=='C' else 'D'
        self.force_dense=mode in ('D','P14','P20')
        layer_action='P' if mode in ('P14','P20') else 'C'
        self.layers.begin(t,layer_action,k=int(mode[1:]) if layer_action=='P' else None)
        result=super().pair(noise,latent,timestep,conditions,self.choose)
        if self.history[-1]['fallback_reason'] is not None:raise ValueError('S1 probe entered fallback')
        return guided(result)

    @torch.no_grad()
    def probe(self,noise,latent,timestep,conditions):
        self.device=latent.device
        if self.readout.delta_step!=26:raise ValueError('S1 requires the actual R18C D26 difference')
        origin=ProbeState(self);rows=[];truth=None
        for mode in ('D','C','P_sync','P14','P20'):
            for rep in range(4):
                origin.restore();self.sync_device();begin=time.perf_counter()
                value=self.local_pair(mode,noise,latent,timestep,conditions)
                self.sync_device();seconds=time.perf_counter()-begin
                if mode=='D' and truth is None:truth=value.detach().clone()
                rows.append(dict(mode=mode,repeat=rep,warmup=rep==0,seconds=seconds,guided_MSE=mse(value,truth)))
                del value
        # Same solver-state comparisons at30. P output is identical under raw
        # and sync; the cache/anchor write is the intervention being compared.
        origin.restore();sync_v=self.local_pair('P_sync',noise,latent,timestep,conditions)
        latent30=self.model.sample_scheduler.step(sync_v.unsqueeze(0),timestep.reshape(()),latent.unsqueeze(0),return_dict=False)[0].squeeze(0)
        at30=ProbeState(self);next_timestep=self.model.sample_scheduler.timesteps[29].reshape_as(timestep)
        at30.restore();D30=self.local_pair('D',noise,latent30,next_timestep,conditions)
        at30.restore();C_sync=self.local_pair('C',noise,latent30,next_timestep,conditions)
        at30.restore();origin.restore_cache();self.net.cnt=58
        C_noP=self.local_pair('C',noise,latent30,next_timestep,conditions)
        origin.restore();raw_v=self.local_pair('P_raw',noise,latent,timestep,conditions)
        raw_latent30=self.model.sample_scheduler.step(raw_v.unsqueeze(0),timestep.reshape(()),latent.unsqueeze(0),return_dict=False)[0].squeeze(0)
        if not torch.equal(sync_v,raw_v) or not torch.equal(latent30,raw_latent30):
            raise ValueError('Raw/sync P29 solver states differ; one next-state teacher is invalid')
        C_raw=self.local_pair('C',noise,raw_latent30,next_timestep,conditions)
        measurements=dict(D_seconds=[r['seconds'] for r in rows if r['mode']=='D' and not r['warmup']],
            P_seconds=[r['seconds'] for r in rows if r['mode']=='P_sync' and not r['warmup']],
            C_next_MSE=mse(C_noP,D30),sync_C_next_MSE=mse(C_sync,D30),
            **self.s1_config['gate_drift'])
        gate=s1_gate(**measurements)
        c_error=statistics.mean(r['guided_MSE'] for r in rows if r['mode']=='C' and not r['warmup'])
        D_time=statistics.median(measurements['D_seconds']);pk={}
        for k in (14,20):
            rr=[r for r in rows if r['mode']==f'P{k}' and not r['warmup']]
            ratio=statistics.median(r['seconds'] for r in rr)/D_time
            pk[str(k)]=dict(cost_ratio=ratio,relative_deviation_from_linear=abs(ratio/(k/28)-1),
                MSE_over_C=statistics.mean(r['guided_MSE'] for r in rr)/c_error if c_error else None)
        self.s1=dict(status='S1_COMPLETE',measurements=measurements,gate=gate,local29=rows,
            next30=dict(C_noP_MSE=measurements['C_next_MSE'],C_sync_MSE=measurements['sync_C_next_MSE'],
                C_raw_MSE=mse(C_raw,D30),raw_sync_same_state=True),Pk=pk,
            Pk_closed=pk['20']['MSE_over_C'] is None or pk['20']['MSE_over_C']>.5
                or any(v['relative_deviation_from_linear']>.1 for v in pk.values()),
            actual_GPU_measurement=self.device.type=='cuda',prefix_steps=28,frames_generated=0)
        self.save(self.s1)
        origin.restore()

    @torch.no_grad()
    def pair(self,noise,latent,timestep,conditions,choose):
        t=self.readout.completed+1
        if t==29:
            self.probe(noise,latent,timestep,conditions)
            raise PrefixComplete('Sparse S1 complete; no prefix video/decode')
        self.layers.begin(t,'D' if self.policy['actions'][t-1]=='D' else 'C')
        return super().pair(noise,latent,timestep,conditions,choose)

    def close(self):
        self.layers.close()
        super().close()


def execute_s1(inference,samples,card,common,output):
    holder={};output=Path(output)
    def save(value):holder['result']=value;atomic_json(output/'s1.json',value)
    def install(model,method,context,runtime,wc,rf,settings,calibration,specs,audit=False):
        wc.apply_worldcache(model.net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        owner=S1Owner(model,policy=copy.deepcopy(card['roles']['b']['policy']),profile=profile_from(card['profile']),
            context=context,runtime=runtime,wc=wc,rf=rf,light_C=True,partial_updates=(29,),
            s1_config=card['S1'],save=save)
        velocity,_=compile_velocity(runtime,rf,owner,owner.choose)
        return velocity,owner,None,owner.readout
    def prefix_patch(target,name,value):
        # The intentional prefix stop must propagate through ordinary generate.
        return clean.patched(target,name,False if target is inference.setup_args and name=='keep_going' else value)
    runner=bind_globals(clean.execute,dict(install=install,patched=prefix_patch))
    sample=request_variant(samples[card['inputs_by_alias']['O1']],seed=0,num_steps=35)
    try:
        runner(inference,sample,'KEEP_A_P',**common,output=output/'s1_prefix',settings=card['settings'],
            calibration=None,specs={},audit=False,save_video=False)
    except PrefixComplete:
        pass
    if 'result' not in holder:raise ValueError('S1 guarded prefix did not reach step29')
    gc.collect()
    return holder['result']


def collect_loaded(inference,samples,card,common,output,storage,mode_types,*,cpu_validation=False):
    from plans.cara_next_stage_20261104.sensitivity.runner import collect_loaded as collect_s2
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.h0_mode import establish_shared_eval
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    model=inference.pipe.model
    caller_owned='forward' in vars(model.net);caller_forward=model.net.forward
    establish_shared_eval(model.net,mode_types)
    common['wc'].apply_worldcache(model.net,**{k.removeprefix('worldcache_'):v for k,v in card['settings'].items()})
    initial=CompleteStateRoundtrip(model.net,model.sample_scheduler,torch.zeros(1))
    try:
        storage.check();s1=execute_s1(inference,samples,card,common,output);initial.restore()
        if not s1['gate']['gate_passed']:
            value=dict(status='S1_GATE_STOP',run_id=card['run_id'],scope_sha256=card['scope_sha256'],S1=s1,
                rows=[dict(slot=slot,status='NOT_REACHED') for slot in card['matrix']],CPU_fixture_only=cpu_validation)
            atomic_json(output/'collection.json',value)
            return value
        value=collect_s2(inference,samples,card,common,output,storage,mode_types,cpu_validation=cpu_validation)
        value['S1']=s1
        atomic_json(output/'collection.json',value)
        return value
    finally:
        initial.restore()
        if caller_owned:model.net.forward=caller_forward
        else:vars(model.net).pop('forward',None)
