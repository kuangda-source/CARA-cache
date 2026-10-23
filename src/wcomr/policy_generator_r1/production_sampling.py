"""Frozen interval policies through the pinned paired WC/RF/UniPC pipeline.

The selector reads only a registered mask. C uses the actual two-D history;
A uses the latest true D and post-RF shared alpha. No teacher or fitting runs.
"""
import copy
import inspect
import math
import types
import torch

from .interval_grammar import Edge, Profile, compile_policy
from .continuation_preparation import TIME_BOUNDARY
from .. import clean_speed20_r1 as clean
from ..cfg_guided_w1_deployment import GuidedW1Readout
from ..cfg_guided_w1_forward import compile_collection
from ..cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from ..cfg_paired_probe_velocity import compile_velocity
from ..mid_coverage import WC_FIELDS
from ..source_aware_phase_sampling import bind_globals


def validate_policy(profile, policy):
    rebuilt = compile_policy(profile, tuple(Edge(r['start'], r['end'], tuple(r['A_window']), r['alpha'])
                                            for r in policy['intervals']))
    for key in ('fingerprint', 'actions', 'shared_alpha', 'source_before', 'dense_mask', 'grammar_sha256'):
        if rebuilt[key] != policy[key]:
            raise ValueError('Policy differs from its legal graph compilation: '+key)
    if (profile.horizon != 36 or profile.protected_dense != tuple(range(1,8))+(36,)
            or profile.max_source_age != 28 or profile.min_C_anchors != 2 or profile.min_A_anchors != 1
            or profile.alpha_candidates != (.5, 1.)):
        raise ValueError('This production adapter supports only the accepted full36 Cosmos grammar')
    return rebuilt


class ReadoutFailure(ValueError):
    pass


class PolicyReadout(GuidedW1Readout):
    def __init__(self, model, *, context, policy):
        super().__init__(model, method='BETA1_GLOBAL_1', context=context)
        self.policy = policy
        self.forced_dense = False
        # Exact parent end body; the only replacement is its frozen alpha lookup.
        self._end = bind_globals(inspect.unwrap(GuidedW1Readout.end),
            {'alpha_at': lambda method, step: policy['shared_alpha'][step-1] or 0.})

    def hidden(self, net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln):
        if skipped and self.policy['actions'][self.current['step']-1] == 'C':
            self._branch(net, branch)
            if branch in self.current['branches']: raise ValueError('Duplicate C branch')
            self.current['branches'][branch] = dict(action='C', proposed_head=None,
                status='C_ONLY', past_D_steps=self.calibrators[branch].receipt()['anchor_steps'], extra_heads=0)
            self.current['prewarp'].pop(branch, None)
            return
        try:
            return super().hidden(net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln)
        except ValueError as error:
            if skipped and ('Finite' in str(error) or 'Nonfinite' in str(error)):
                raise ReadoutFailure(str(error)) from error
            raise

    def end(self, actual, action):
        try:
            result = self._end(self, actual, action)
            if any(not bool(torch.isfinite(v).all()) for v in result):
                raise ReadoutFailure('Nonfinite completed readout')
            return result
        except ValueError as error:
            if 'Finite' in str(error) or 'Nonfinite' in str(error):
                raise ReadoutFailure(str(error)) from error
            raise


def _cache_snapshot(net):
    # Cache tensors are replaced by pinned WC statements. Copy list/dict topology
    # and scalar accumulators only; verify retained tensor versions on rollback.
    versions = []
    def own(v):
        if isinstance(v, torch.Tensor):
            if v.numel() <= 1: return v.clone()
            versions.append((v, None if torch.is_inference(v) else v._version))
            return v
        if isinstance(v, list): return [own(x) for x in v]
        if isinstance(v, tuple): return tuple(own(x) for x in v)
        if isinstance(v, dict): return {k:own(x) for k,x in v.items()}
        return copy.deepcopy(v)
    return {k:own(getattr(net,k)) for k in WC_FIELDS if hasattr(net,k)}, versions


class PolicyOwner:
    def __init__(self, model, *, policy, profile, context, runtime, wc, rf):
        validate_policy(profile, policy)
        self.model, self.net, self.policy, self.profile = model, model.net, policy, profile
        self.readout = PolicyReadout(model, context=context, policy=policy)
        _, denoise, self.proof = compile_collection(runtime, wc, rf, self.readout)
        self.executor = NativePolicyPairedExecutor(model, denoise, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward, rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
        self.choose = self._choose
        self.history = []; self.deployment = self
        self.fallback_reason = None; self.force_dense = False

    def _choose(self, packets):
        t = self.readout.completed+1
        if self.force_dense or self.policy['actions'][t-1]=='D': return 'DD'
        needed = self.profile.min_A_anchors if self.policy['actions'][t-1]=='A' else self.profile.min_C_anchors
        if any(len(c.anchors)<needed or c.anchors[-1].step>=t for c in self.readout.calibrators):
            self.fallback_reason='INSUFFICIENT_TRUE_D_ANCHORS'; return 'DD'
        return 'CC'

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        if choose is not self.choose: raise ValueError('Bound frozen policy selector required')
        t=self.readout.completed+1
        if t>36 or int(self.net.cnt)!=2*(t-1)%70: raise ValueError('Full36 paired counter differs')
        planned=self.policy['actions'][t-1]
        snapshot,versions=_cache_snapshot(self.net) if planned!='D' else ({},[])
        cpu_rng=torch.get_rng_state()
        gpu_rng=torch.cuda.get_rng_state_all() if latent.is_cuda else []
        history_len=len(self.readout.history); self.fallback_reason=None
        try:
            self.readout.begin(noise,latent,timestep,conditions)
            actual=self.executor.pair(noise,latent,timestep,conditions,self.choose)
            returned=self.readout.end(actual,self.executor.last['action'])
        except ReadoutFailure as error:
            if planned=='D': raise
            if any(version is not None and tensor._version!=version for tensor,version in versions):
                raise ValueError('Cannot safely restore mutated cache tensor') from error
            for key,value in snapshot.items(): setattr(self.net,key,value)
            torch.set_rng_state(cpu_rng)
            if gpu_rng: torch.cuda.set_rng_state_all(gpu_rng)
            self.readout.current=None; self.readout.completed=t-1; self.readout.history=self.readout.history[:history_len]
            self.readout.poisoned=False; self.executor.poisoned=False; self.force_dense=True
            self.fallback_reason='NONFINITE_READOUT_RESTORED_THEN_FULL_D'
            try:
                self.readout.begin(noise,latent,timestep,conditions)
                actual=self.executor.pair(noise,latent,timestep,conditions,self.choose)
                returned=self.readout.end(actual,self.executor.last['action'])
            finally: self.force_dense=False
        self.history.append(dict(step=t,action=self.executor.last['action'],planned=planned,
            actual='D' if self.executor.last['action']=='DD' else planned,
            shared_alpha=self.policy['shared_alpha'][t-1] if self.executor.last['action']=='CC' else None,
            fallback_reason=self.fallback_reason,source_history=copy.deepcopy(self.readout.history[-1])))
        return returned

    def close(self):
        self.readout.current=None
        for c in self.readout.calibrators: c.reset(self.readout.context)
        self.readout.warp=self.readout.to_velocity=None
        # Compiled closures retain the readout until these references are cleared.
        self.executor.denoise=None


def complete_request_seconds(result):
    names=('method_install_seconds','guarded_pipeline_without_write_seconds','video_write_seconds','method_cleanup_seconds')
    values=[result[n] for n in names]
    if any(type(v) not in (float,int) or not math.isfinite(v) or v<0 for v in values):
        raise ValueError('Finite complete-request clock components required')
    seconds=math.fsum(values)
    if seconds<=0 or not 0<result.get('core_seconds',0)<=seconds:
        raise ValueError('Complete-request and core clock are inconsistent')
    return seconds


def execute(inference,sample,*,policy,profile,**kw):
    validate_policy(profile,policy)
    holder={}; base_install=clean.install
    def install(model,method,context,runtime,wc,rf,settings,calibration,specs,audit=False):
        wc.apply_worldcache(model.net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        model.net.worldcache_enabled=True
        owner=PolicyOwner(model,policy=policy,profile=profile,context=context+(policy['fingerprint'],),runtime=runtime,wc=wc,rf=rf)
        holder['owner']=owner
        velocity,_=compile_velocity(runtime,rf,owner,owner.choose)
        return velocity,owner,None,owner.readout
    # Bind this invocation's installer; do not mutate a shared module global.
    runner=bind_globals(clean.execute,{'install':install})
    try:
        result=runner(inference,sample,'KEEP_A_P',**kw)
        owner=holder.get('owner')
        result.update(policy_fingerprint=policy['fingerprint'],semantic_history=copy.deepcopy(owner.history) if owner else [],
            timing_boundary=TIME_BOUNDARY,full_request_seconds=complete_request_seconds(result) if result.get('core_seconds') else None,
            teacher_calls=0,online_fitting=False)
        if result['status']=='COMPLETE':
            if len(result['semantic_history'])!=36 or result['solver_steps']!=36: raise ValueError('Incomplete policy path')
            if result['semantic_history'][-1]['actual']!='D': raise ValueError('Cycle-reset D36 missing')
        return result
    finally:
        if holder: holder['owner'].close()
        holder.clear()
