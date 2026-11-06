"""Restored local CC/DD execution order comparison at one actual S22.

Owns temporary attribute bindings explicitly, including parent instrumentation.
No sampler update, learned decision, endpoint label or GPU admission is made.
Timing encloses a synchronized current velocity and optional observations;
it is not an uninstrumented deployment benchmark or future-cost label.
"""
import copy
from contextlib import contextmanager
from dataclasses import asdict
import time
from types import MethodType

import torch

from .cfg_paired_probe_forward import forced_reference
from .cfg_paired_probe_production import compile_production, ProductionPairedExecutor
from .mid_coverage import tree_digest
from .prepared_input import input_signatures
from .rv0_cfg_budget_evaluation import solver_configuration
from .rv0_fork import SamplerSuffixControl
from .rv0_restore import cuda_memory_observation


@contextmanager
def owned_bindings(model, forward, denoise):
    """Replace only this caller's bindings and restore their exact saved objects."""
    net = model.net
    saved = (net.forward, model.denoise)
    net.forward, model.denoise = forward, denoise
    try:
        yield
    finally:
        changed = model.net is not net or net.forward is not forward or model.denoise is not denoise
        net.forward, model.denoise = saved
        if changed:
            raise ValueError('Temporary interface bindings were changed during execution')


def sync(value):
    if value.is_cuda:
        torch.cuda.synchronize(value.device)


class PairedLocalInterface(SamplerSuffixControl):
    def __init__(self, *args, runtime, wc_module, rf_module, **kwargs):
        super().__init__(*args, **kwargs)
        if self.completed != 22 or self.net.cnt != 44:
            raise ValueError('Local interface requires actual S22/44 boundary')
        import inspect
        if inspect.getclosurevars(self.velocity_fn).nonlocals['guidance'] != 7:
            raise ValueError('Local interface requires original guidance7')
        self.runtime, self.wc, self.rf = runtime, wc_module, rf_module
        self.references = {a: forced_reference(runtime, dict(vars(wc_module)), a) for a in ('CC','DD')}
        self.last_tensors = None

    @torch.no_grad()
    def measure(self, label, action, order, observers, *, fail=None):
        if action not in ('CC','DD') or order not in ('ORIGINAL','PAIRED') or type(observers) is not bool:
            raise ValueError('Explicit registered local CC/DD order and observer switch required')
        if any(r['label']==label for r in self.records):
            raise ValueError('Duplicate local interface identity')
        if fail not in (None,'selector','after_first'):
            raise ValueError('Unregistered local interface fault')
        record = {'label':label,'action':action,'order':order,'observers':observers,'failure':fail,
            'status':'STARTED','origin_components':self.snapshot.components(),
            'origin_fingerprint':self.parent_fingerprint,
            'origin_solver_configuration':solver_configuration(self.scheduler),
            'observer_events':[],'selector_calls':0,'paid_probes':[],
            'endpoint_label':False,'future_cost_label':False}
        self.records.append(record)
        self.last_tensors = None
        events = record['observer_events']
        visits = [0]*len(self.net.blocks)
        handles = [block.register_forward_hook(lambda *a,index=i:visits.__setitem__(index,visits[index]+1))
            for i,block in enumerate(self.net.blocks)]
        def before(net,slot,args,kwargs):
            events.append({'kind':'before','slot':slot,'signature':input_signatures(args,kwargs)})
        def after(net,slot,value):
            if fail=='after_first' and slot==0:
                raise ValueError('Injected local first-after observation failure')
            events.append({'kind':'after','slot':slot,'output_sha256':tree_digest(value)})
        def select(packets):
            record['selector_calls']+=1
            if fail=='selector':
                raise ValueError('Injected local selector failure')
            if visits!=[2 if i<self.net.probe_depth else 0 for i in range(len(visits))]:
                raise ValueError('Both paid prefixes must precede the joint decision')
            if [(p.slot,p.counter) for p in packets]!=[(0,44),(1,45)]:
                raise ValueError('Local paid-probe boundary differs')
            record['paid_probes']=[asdict(p) for p in packets]
            return action
        executor = None
        try:
            latent = self.restore_parent()
            initial_components = self.snapshot.components()
            assert initial_components==record['origin_components']
            timestep=torch.stack([self.scheduler.timesteps[self.completed]]).unsqueeze(0)
            original_denoise=self.rf.Video2WorldModelRectifiedFlow.denoise
            if order=='PAIRED':
                _,denoise,proof=compile_production(self.runtime,self.wc,self.rf,
                    before=before if observers else None,after=after if observers else None)
                executor=ProductionPairedExecutor(self.model,denoise,torch,
                    wc_forward=self.wc.worldcache_mini_train_dit_forward,rf_denoise=original_denoise)
                forward=MethodType(self.wc.worldcache_mini_train_dit_forward,self.net)
                method=MethodType(original_denoise,self.model)
                record['compiler']=dict(proof)
                execute=lambda:executor.pair(self.noise,latent,timestep,self.conditions,select)
            else:
                def reference(net,*args,**kwargs):
                    slot=int(net.cnt)%2
                    if observers:before(net,slot,args,kwargs)
                    value=self.references[action](net,*args,**kwargs)
                    if observers:after(net,slot,value)
                    return value
                forward=MethodType(reference,self.net)
                method=MethodType(original_denoise,self.model)
                execute=lambda:tuple(self.model.denoise(self.noise,latent,timestep,c) for c in self.conditions)
            record['memory_before_core']=cuda_memory_observation()
            with owned_bindings(self.model,forward,method):
                sync(latent);started=time.perf_counter()
                outputs=execute()
                # Same arithmetic order as the pinned original velocity closure.
                guided=outputs[0]+7*(outputs[0]-outputs[1])
                sync(latent);record['current_velocity_instrumented_wall_seconds']=time.perf_counter()-started
            self.check_identity()
            if (solver_configuration(self.scheduler)!=record['origin_solver_configuration']
                    or self.scheduler._step_index!=22 or self.net.cnt!=46):
                raise ValueError('Velocity-only comparison changed solver or CFG boundary')
            if (len(outputs)!=2 or any(v.dtype!=torch.float32 or v.shape!=guided.shape
                    or not bool(torch.isfinite(v).all()) for v in (*outputs,guided))):
                raise ValueError('Complete finite post-denoise FP32 outputs required')
            expected=[2 if i<self.net.probe_depth or action=='DD' else 0 for i in range(len(visits))]
            if visits!=expected:
                raise ValueError('Actual local block visits differ from requested action')
            record.update(block_visits=visits.copy(),pair_end_components=self.snapshot.components(),
                pair_end_fingerprint=self.snapshot.fingerprint(),
                pair_end_solver_configuration=solver_configuration(self.scheduler),
                branch_sha256=[tree_digest(v) for v in outputs],guided_sha256=tree_digest(guided),
                memory_after_core=cuda_memory_observation(),status='COMPLETE_LOCAL_INTERFACE_REQUIRES_AUDIT')
            self.last_tensors={'conditional':outputs[0].detach().cpu().clone(),
                'unconditional':outputs[1].detach().cpu().clone(),'guided':guided.detach().cpu().clone()}
            return record
        except BaseException as error:
            record.update(status='LOCAL_INTERFACE_FAILED_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error),
                executor_poisoned=executor.poisoned if executor is not None else None)
            raise
        finally:
            for handle in handles:handle.remove()
            self.restore_parent()
            record.update(parent_restored=True,parent_after_components=self.snapshot.components(),
                bindings_restored=self.bindings==(self.model.denoise,self.net.forward,self.scheduler.step))


def verify_comparisons(rows):
    planned=[(a,o,r,order) for a in ('CC','DD') for o in (False,True) for r in ('first','second')
             for order in ('ORIGINAL','PAIRED')]
    if len(rows)!=16 or [(r['action'],r['observers'],r['repetition'],r['order']) for r in rows]!=planned:
        raise ValueError('Complete eight comparisons/sixteen local pairs required')
    keys=('origin_components','origin_fingerprint','origin_solver_configuration','pair_end_components',
        'pair_end_fingerprint','pair_end_solver_configuration','branch_sha256','guided_sha256','block_visits')
    for action in ('CC','DD'):
        group=[r for r in rows if r['action']==action]
        if any(r['status']!='COMPLETE_LOCAL_INTERFACE_REQUIRES_AUDIT' or not r['parent_restored']
                or not r['bindings_restored'] or r['parent_after_components']!=r['origin_components'] for r in group):
            raise ValueError('Complete restored local interface missing')
        if any(any(r[k]!=group[0][k] for k in keys) for r in group):
            raise ValueError('Output/state differs across order, observer or strict repeat')
        for observers in (False,True):
            for repetition in ('first','second'):
                old,new=[r for r in group if r['observers']==observers and r['repetition']==repetition]
                if old['selector_calls']!=0 or new['selector_calls']!=1 or len(new['paid_probes'])!=2:
                    raise ValueError('Explicit joint paid-probe execution missing')
                if observers:
                    normalize=lambda es:{(e['kind'],e['slot']):e for e in es}
                    if len(old['observer_events'])!=4 or len(new['observer_events'])!=4 or normalize(old['observer_events'])!=normalize(new['observer_events']):
                        raise ValueError('Per-branch original/paired observations differ')
                elif old['observer_events'] or new['observer_events']:
                    raise ValueError('Observer OFF emitted observations')
    return {'complete_comparisons':8,'complete_local_pairs':16,'strict_repeat_and_observer_equal':True,
            'endpoint_labels':0,'future_cost_labels':0,'full_candidate_sampler_claim':False}
