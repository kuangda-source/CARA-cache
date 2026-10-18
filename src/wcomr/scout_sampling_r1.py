"""Two independent scouts sharing the established fixed-mask execution.

The observer saves only existing pre-action probe and post-RF output tensors.
It performs no teacher call or cache/solver update. All copies and hashes are
paid in the diagnostic request clock; this is not a clean latency benchmark.
"""
import copy
import time
import weakref

import torch

from . import clean_speed20_r1 as clean
from . import simple26d_memory_r2 as boundary
from .source_phase_fixed_mask_r1 import FixedMaskH1Owner, mask_fingerprint
from .mid_coverage import tree_digest

TIMING = 'SCOUT_SINGLE_PASS_WITH_EXPLICIT_OBSERVER_COST_NOT_CLEAN_REPEAT'


def plans(kind):
    dense = set(range(1, 22)) | {24, 27, 30, 33, 36}
    front = tuple('D' if n in dense else 'C' for n in range(1, 37))
    if kind == 'CAL12':
        g01 = list(front); g01[20:23] = ['C', 'A', 'A']
        variation = list(front); variation[21], variation[32] = 'D', 'C'
        return dict(G01_LATE_A=tuple(g01), VARIATION26_C=tuple(variation))
    if kind == 'BANK24':
        a21 = list(front); a21[20] = 'A'
        return dict(D21=front, A21=tuple(a21), NATIVE35=('D',)*36)
    raise ValueError('Only the two registered independent scout cards are supported')


def matrix(kind, scenes):
    n = 4 if kind == 'CAL12' else 6
    if len(scenes) != n or len(set(scenes)) != n:
        raise ValueError('Keep every registered distinct prompt')
    methods = tuple(plans(kind)); rows = []
    for repeat in (1, 2):
        for method in methods if repeat == 1 else methods[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}',scene=scenes[0],method=method,
                section='WARMUP',round=repeat,observer=repeat==2 and method!='NATIVE35'))
    for i, scene in enumerate(scenes):
        order = methods if kind == 'CAL12' and i%2==0 else methods[::-1] if kind=='CAL12' else methods[i%3:]+methods[:i%3]
        for method in order:
            rows.append(dict(id=f'timed_{i}_{method}',scene=scene,method=method,
                section='TIMED',round=1,observer=method!='NATIVE35'))
    return rows


class ProbeOutputObserver:
    def __init__(self, readout):
        self.readout=readout; self.old_hidden=readout.semantic_hidden; self.old_end=readout.end
        self.own_hidden='semantic_hidden' in vars(readout); self.own_end='end' in vars(readout)
        self.vectors={}; self.metadata={}; self.copy_seconds=0.; self.probe_copies=0; self.velocity_copies=0
        readout.semantic_hidden=self.hidden; readout.end=self.end

    @torch.no_grad()
    def hidden(self, net, skipped, branch, original, probe, *values):
        step=self.readout.current['step']
        if step in (20,21):
            start=time.perf_counter()
            # This is the actual current shallow increment, before this branch's
            # dense source is observed. It is never substituted for a prediction.
            p=(probe-original).detach().cpu().clone()
            key=f'p{step}_{"c" if branch==0 else "u"}'
            if key in self.vectors: raise ValueError('Duplicate registered probe observation')
            self.vectors[key]=p; self.probe_copies+=1
            self.copy_seconds+=time.perf_counter()-start
        return self.old_hidden(net,skipped,branch,original,probe,*values)

    @torch.no_grad()
    def end(self, actual, action):
        current=self.readout.current; step=current['step']
        if step==21:
            start=time.perf_counter()
            self.metadata=dict(actual_update=21,actual_action=action,
                pre_action_input_sha256=tree_digest((current['noise'],current['latent'],current['timestep'])),
                actual_timestep=torch.as_tensor(current['timestep']).detach().cpu().tolist(),
                direct_input_snapshot_hash_saved=True)
            original=actual[0]+7*(actual[0]-actual[1])
            self.vectors['v_actual21']=original.detach().cpu().clone(); self.velocity_copies+=1
            self.copy_seconds+=time.perf_counter()-start
        returned=self.old_end(actual,action)
        if step==21:
            start=time.perf_counter()
            guided=returned[0]+7*(returned[0]-returned[1])
            self.vectors['v_returned21']=guided.detach().cpu().clone(); self.velocity_copies+=1
            self.copy_seconds+=time.perf_counter()-start
        return returned

    def close(self):
        if self.readout is not None:
            if self.own_hidden:self.readout.semantic_hidden=self.old_hidden
            else:delattr(self.readout,'semantic_hidden')
            if self.own_end:self.readout.end=self.old_end
            else:delattr(self.readout,'end')
        self.readout=self.old_hidden=self.old_end=None


def execute(inference, sample, method, *, kind, table_parameters, previous_parameters,
            observer=True, **kw):
    candidates=plans(kind)
    if method not in candidates or sample.seed!=0:
        raise ValueError('Exact registered scout method and seed0 required')
    before=boundary.collect_boundary(); refs=[]; holder={}; hooks=[]
    result=None
    def factory(*args,**kwargs):
        owner=FixedMaskH1Owner(*args,replay_plan=candidates[method],
            table_parameters=table_parameters['SOURCE_PHASE'],math_parameters=previous_parameters,
            horizon=1,source_mode='FUSION',**kwargs)
        refs.append(weakref.ref(owner)); holder['owner']=owner
        if observer:
            hook=ProbeOutputObserver(owner.deployment.readout); hooks.append(hook); holder['observer']=hook
        return owner
    try:
        if method=='NATIVE35':
            # Real production uses the existing pinned native forward. The CPU
            # sampler alone may pass its explicit declared native fixture.
            result=clean.execute(inference,sample,'NATIVE',**kw)
        else:
            with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
                result=clean.execute(inference,sample,'KEEP_A_P',**kw)
            owner=holder['owner']
            result.update(source_history=copy.deepcopy(owner.deployment.history),
                semantic_plan=list(candidates[method]),mask_sha256=mask_fingerprint(candidates[method]),
                input_adaptive_action_selection=False,online_teacher_calls=0)
            if [h['A_readout']['readout_action'] for h in result['source_history']]!=list(candidates[method]):
                raise ValueError('The executed semantic actions differ from the frozen scout plan')
            del owner
        hook=holder.get('observer')
        if hook is not None:
            if set(hook.vectors)!={'p20_c','p20_u','p21_c','p21_u','v_actual21','v_returned21'}:
                if result['status'] not in ('TEXT_REJECTED',):
                    raise ValueError('Every requested real probe/output observation is required')
            result.update(scout_vectors=hook.vectors,scout_observation=dict(**hook.metadata,
                observer_enabled=True,probe_copies=hook.probe_copies,velocity_copies=hook.velocity_copies,
                observer_copy_hash_seconds=hook.copy_seconds,teacher_calls=0,
                copies_and_hashes_in_request_clock=True,online_gate_executed=False))
        else:
            result.update(scout_observation=dict(observer_enabled=False,probe_copies=0,velocity_copies=0,
                teacher_calls=0,copies_and_hashes_in_request_clock=False,online_gate_executed=False))
        del hook
    finally:
        for hook in hooks:hook.close()
        if hooks:del hook
        hooks.clear();holder.clear()
        after=boundary.collect_boundary()
    alive=sum(r() is not None for r in refs)
    if alive:raise ValueError('Scout observer retained an algorithm owner beyond its request')
    result.update(bridge_method=result['method'],method=method,timing_claim=TIMING,
        request_memory_lifecycle=dict(version='BOUNDARY_GC_ONLY_R2',before=before,after=after,
            observed_owners=len(refs),owners_alive_after=alive,
            within_request_algorithm_or_guardrails_changed=False,cleanup_excluded_from_core_seconds=True))
    return result
