"""Real-source P0 deep-group collection from a fixed complete D6 parent.

The parent only uses actual D or C. Partial actions are paid, score-only arms;
their caches and whole external state are restored before parent continuation.
This is not an online selector, partial-video result or clean pipeline timing.
"""
import copy
from contextlib import nullcontext
import hashlib
import math
import time

import torch

from .partial_mlp import PartialMLP, block_indices
from .partial_mlp_state import ProjectionRoundtrip
from .cfg_guided_w1_collection import DENSE_STEPS, SELECTED_STEPS, signature, tensor_sha
from .cfg_guided_w1_forward import compile_collection
from .cfg_guided_w1_outputs import guided_velocity_moments
from .full_sampling import CompleteStateRoundtrip
from .light_sampling import synchronize
from .rv0_restore import capture_inventory, capture_gate


LAYERS = (4, 10, 16, 22)
MODES = ('DENSE_REFERENCE', 'DENSE_WITH_P0', 'ROTATION_050', 'RANDOM_050',
         'ROTATION_075', 'RANDOM_075')
METHODS = ('ORIGINAL',)+MODES


class PartialGroupCollector:
    def __init__(self, model, *, scene, context, enabled, writer,
                 layers=LAYERS, block_size=128, warmups=1, repeats=3):
        if (type(scene) is not str or not scene or type(context) is not tuple or len(context)!=3
                or any(type(v) is not str or not v for v in context) or type(enabled) is not bool
                or not callable(writer) or warmups!=1 or repeats!=3):
            raise ValueError('Explicit complete P0 collection scope required')
        self.model, self.net = model, model.net
        self.scene, self.context, self.enabled, self.writer = scene, context, enabled, writer
        self.block_size, self.warmups, self.repeats = block_size, warmups, repeats
        self.scene_index=0
        self.core = PartialMLP(self.net.blocks,layers).install() if enabled else None
        self.completed=0;self.running=False;self.current=None;self.records=[];self.events=[]
        self.to_velocity=None;self.velocity=None;self.warp=None

    def close(self):
        if self.core is not None:
            self.core.close()
            self.core.cache.clear()

    def begin(self,noise,latent,timestep,conditions):
        if (self.running or self.completed>=36 or len(conditions)!=2
                or self.model.net is not self.net or torch.is_grad_enabled()):
            raise ValueError('One complete actual P0 parent pair required')
        self.running=True
        self.current={'step':self.completed+1,'noise':noise,'latent':latent,'timestep':timestep,
                      'conditions':conditions,'branches':{},'input_signature':signature((noise,latent,timestep)),
                      'condition_signature':signature([vars(c) for c in conditions])}

    def _branch(self,net,slot):
        if (not self.running or net is not self.net or slot not in (0,1)
                or net.cnt!=(2*(self.current['step']-1)+slot)%70):
            raise ValueError('P0 source branch differs from bound parent pair')
        return self.current['step']

    def dense_context(self,net,slot):
        step=self._branch(net,slot)
        if not self.enabled or step not in DENSE_STEPS:
            raise ValueError('Dense group must belong to an actual bound parent D')
        return self.core.branch(slot)

    def prewarp(self,net,slot,hidden):
        self._branch(net,slot)

    def hidden(self,net,skipped,slot,original,probe,hidden,kwargs,embedding,adaln):
        step=self._branch(net,slot)
        if skipped!=(step not in DENSE_STEPS):raise ValueError('Fixed complete D6 parent differs')
        if self.enabled and not skipped:
            self.events.append({'step':step,'branch':slot,'kind':'ACTUAL_D_PROJECTION_ANCHOR'})
        if self.enabled and step in SELECTED_STEPS:
            self.current['branches'][slot]={'probe':probe.detach().clone(),
                'kwargs':dict(kwargs),'embedding':embedding,'adaln':adaln}

    def output(self,net,slot,head):
        step=self._branch(net,slot)
        if self.enabled and step in SELECTED_STEPS:
            self.current['branches'][slot]['original_head']=head.detach().clone()

    def _group(self,slot):
        branch=self.current['branches'][slot];hidden=branch['probe'].detach().clone()
        for block in self.net.blocks[self.net.probe_depth:]:hidden=block(hidden,**branch['kwargs'])
        head=self.net.unpatchify(self.net.final_layer(hidden,branch['embedding'],
                 adaln_lora_B_T_3D=branch['adaln']))
        cur=self.current
        return self.to_velocity(self.model,cur['noise'],cur['latent'],cur['timestep'],
                                cur['conditions'][slot],_supplied_net_output=head)

    def _arm(self,mode):
        if mode=='DENSE_REFERENCE':
            with self.core.readonly():return tuple(self._group(slot) for slot in (0,1))
        step=self.current['step'];indices=None;action='D'
        if mode!='DENSE_WITH_P0':
            action='P';fraction=.5 if mode.endswith('050') else .75
            tokens=math.prod(self.current['branches'][0]['probe'].shape[:-1])
            seed=None
            if mode.startswith('RANDOM'):
                seed=int.from_bytes(hashlib.sha256(('P0-SAMESTATE-R1:'+self.scene+':'+str(step)).encode()).digest()[:8],'big')%(2**63-1)
            indices=block_indices(tokens,fraction,block_size=self.block_size,
                 opportunity=SELECTED_STEPS.index(step),random_seed=seed)
        values=[]
        with self.core.pair(step=step,action=action,context=self.context,indices=indices):
            for slot in (0,1):
                with self.core.branch(slot):values.append(self._group(slot))
        return tuple(values)

    @torch.no_grad()
    def end(self,actual,action):
        if not self.running or action!=('DD' if self.current['step'] in DENSE_STEPS else 'CC'):
            raise ValueError('Complete actual D6 parent pair required')
        cur=self.current;step=cur['step']
        external=projection=None
        try:
            if signature((cur['noise'],cur['latent'],cur['timestep']))!=cur['input_signature']:
                raise ValueError('P0 collector changed actual solver inputs')
            if signature([vars(c) for c in cur['conditions']])!=cur['condition_signature']:
                raise ValueError('P0 collector changed actual conditions')
            if self.enabled and step in SELECTED_STEPS:
                if set(cur['branches'])!={0,1} or self.to_velocity is None or self.velocity is None:
                    raise ValueError('Both actual paid probes, heads and condition conversion required')
                expected_D=7 if step==12 else 25
                if (self.core.last_step!=expected_D or any(c.last_actual_D!=expected_D
                        for c in self.core.cache.values())):
                    raise ValueError('P0 must use actual strictly past D projection anchors')
                before={key:(c.last_actual_D,self.core.last_step) for key,c in self.core.cache.items()}
                inventory=capture_inventory(self.net,self.model.sample_scheduler,cur['latent'],cur['noise'],self.velocity)
                extra=sum(t.numel()*t.element_size() for c in self.core.cache.values()
                          for t in (c.value,c.updated_at,c.source))
                totals=inventory['logical_copy_bytes_by_device']
                for c in self.core.cache.values():
                    totals[str(c.value.device)]=totals.get(str(c.value.device),0)+sum(t.numel()*t.element_size() for t in (c.value,c.updated_at,c.source))
                gate=capture_gate(inventory,logical_copy_cap_bytes=8*(1<<30),transient_copy_factor=2,
                     workspace_reserve_bytes=8*(1<<30),
                     available_gpu_bytes=torch.cuda.mem_get_info()[0] if cur['latent'].is_cuda else None)
                external=CompleteStateRoundtrip(self.net,self.model.sample_scheduler,cur['latent'])
                external_sha=external.fingerprint()
                projection=ProjectionRoundtrip(self.core,logical_copy_cap_bytes=2*(1<<30))
                observed=[];handles=[]
                # Necessary correctness instrumentation is restricted to warmup.
                for layer in self.core.layers:
                    for name in ('layer1','layer2'):
                        def note(m,args,l=layer,n=name):observed.append({'layer':l,'Linear':n,'rows':math.prod(args[0].shape[:-1])})
                        handles.append(getattr(self.net.blocks[layer].mlp,name).register_forward_pre_hook(note))
                pairs={};rows={};timings={mode:[] for mode in MODES};peaks={mode:[] for mode in MODES}
                try:
                    for mode in MODES:
                        external.restore();projection.restore();observed.clear()
                        pairs[mode]=self._arm(mode)
                        rows[mode]=list(observed)
                        if mode!='DENSE_REFERENCE':
                            records=self.core.records[len(projection.origin['records']):]
                            if len(records)!=2*len(self.core.layers) or any(r['fallback'] for r in records):
                                raise ValueError('Registered true past projection source was not used')
                            rows[mode]={'Linear_inputs':rows[mode],'projection_records':copy.deepcopy(records)}
                        else:rows[mode]={'Linear_inputs':rows[mode],'projection_records':[]}
                        if signature([vars(c) for c in cur['conditions']])!=cur['condition_signature']:
                            raise ValueError('Score-only P0 group mutated branch conditions')
                        external.restore();projection.restore()
                    if not all(torch.equal(x,y) for x,y in zip(pairs['DENSE_REFERENCE'],pairs['DENSE_WITH_P0'])):
                        raise ValueError('Actual full P0 group changed dense output')
                finally:
                    for h in handles:h.remove()
                origin_index=2*self.scene_index+SELECTED_STEPS.index(step)
                order=list(MODES[origin_index%len(MODES):]+MODES[:origin_index%len(MODES)])
                for repeat in range(self.repeats):
                    for mode in order if repeat%2==0 else reversed(order):
                        external.restore();projection.restore()
                        synchronize()
                        if cur['latent'].is_cuda:torch.cuda.reset_peak_memory_stats()
                        start=time.perf_counter();value=self._arm(mode);synchronize()
                        timings[mode].append(time.perf_counter()-start)
                        if cur['latent'].is_cuda:
                            peaks[mode].append({'allocated':torch.cuda.max_memory_allocated(),
                                                'reserved':torch.cuda.max_memory_reserved()})
                        del value
                external.restore();projection.restore()
                if external.fingerprint()!=external_sha or projection.components()!=projection.origin:
                    raise ValueError('Complete external or additional P0 physical state not restored')
                original=tuple(self.to_velocity(self.model,cur['noise'],cur['latent'],cur['timestep'],cur['conditions'][b],
                       _supplied_net_output=cur['branches'][b]['original_head']) for b in (0,1))
                if not all(torch.equal(x,y) for x,y in zip(actual,original)):
                    raise ValueError('P0 original branches do not recover actual source RF output')
                pairs={'ORIGINAL':original,**pairs}
                if any(not bool(torch.isfinite(v).all()) for pair in pairs.values() for v in pair):
                    raise ValueError('Nonfinite real-group branch output')
                moments={mode:guided_velocity_moments(scene=self.scene,state='step'+str(step),
                         original=original,proposed=pairs[mode],dense=pairs['DENSE_REFERENCE']) for mode in MODES}
                tensors={name:tuple(v.detach().cpu().clone() for v in pair) for name,pair in pairs.items()}
                art=self.writer(self.scene,step,tensors)
                self.records.append({'scene':self.scene,'step':step,'action':action,
                    'actual_post_RF_original_direct_equal':True,'past_actual_D_projection_step':expected_D,
                    'projection_anchor_inventory':{str(k):list(v) for k,v in before.items()},
                    'methods':list(METHODS),'layers':list(self.core.layers),'block_size':self.block_size,
                    'actual_probe_shapes':[list(cur['branches'][b]['probe'].shape) for b in (0,1)],
                    'source_parent_inputs_sha256':[tensor_sha(v) for v in (cur['noise'],cur['latent'],cur['timestep'])],
                    'projection_snapshot_logical_bytes':extra,'combined_snapshot_gate':gate,
                    'warmup_Linear_and_projection_records':rows,'group_cost_seconds':timings,
                    'group_peak_bytes':peaks,'warmups':1,'repeats':3,'method_order':order,
                    'full_D_same_origin_direct_equal':True,'complete_external_and_P0_restored':True,
                    'teacher_updates_deployment_anchor':False,
                    'velocity_sha256':{k:[tensor_sha(v) for v in pair] for k,pair in tensors.items()},
                    'moments':moments,'artifact':art,
                    'new_policy_OR_partial_video_OR_clean_end_to_end_latency_claim':False})
            self.completed+=1
        finally:
            if external is not None:external.restore()
            if projection is not None:projection.restore()
            self.current=None;self.running=False

    def finish(self):
        if (self.running or self.completed!=36
                or [r['step'] for r in self.records]!=(list(SELECTED_STEPS) if self.enabled else [])
                or [(r['step'],r['branch']) for r in self.events]!=(
                    [(s,b) for s in DENSE_STEPS for b in (0,1)] if self.enabled else [])):
            raise ValueError('Complete P0 full36, both origins and true D history required')
        return {'completed_pairs':36,'selected_steps':list(SELECTED_STEPS),'records':self.records,
                'actual_D_events':self.events,'source_is_score_only_not_deployment':True,
                'real_model_OR_quality_OR_clean_pipeline_claim':False}


class PartialCollectedPair:
    def __init__(self,executor,collector):
        if executor.model is not collector.model or executor.net is not collector.net:
            raise ValueError('P0 collector must bind the actual complete shared parent')
        self.executor,self.collector=executor,collector
        self.model,self.net,self.choose=executor.model,executor.net,executor.choose

    def pair(self,noise,latent,timestep,conditions,choose):
        if choose is not self.choose:raise ValueError('Fixed shared P0 parent selector required')
        collector=self.collector;collector.begin(noise,latent,timestep,conditions)
        step=collector.current['step']
        context=(collector.core.pair(step=step,action='D',context=collector.context)
                 if collector.enabled and step in DENSE_STEPS else nullcontext())
        try:
            with context:values=self.executor.pair(noise,latent,timestep,conditions,choose)
            collector.end(values,self.executor.last['action'])
            return values
        except BaseException:
            self.executor.executor.poisoned=True
            raise


def compile_partial_collection(runtime,wc,rf,collector):
    return compile_collection(runtime,wc,rf,collector,dense_context=collector.dense_context)
