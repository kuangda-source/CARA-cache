"""Pinned full Block/GPT2FeedForward with declared tiny attention and CPU weights.

The reference is an independent complete dense Block plus current-gate output
compensation, and hooks observe both actual Linear inputs. No full GEMM masked
afterward can pass the row-count controls. Not a Cosmos video or GPU speed test.
"""
import ast
import copy
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Optional

import torch
from einops import rearrange

from wcomr.partial_mlp import PartialMLP,block_indices


SOURCE_SHA='a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'


def run(runtime, *, state_control=None):
    path=Path(runtime)/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    tree=ast.parse(raw);classes=[v for v in tree.body if isinstance(v,ast.ClassDef) and v.name in ('GPT2FeedForward','Block')]
    assert len(classes)==2
    class TinyAttention(torch.nn.Module):
        def __init__(self,*args,**kw):super().__init__();self.calls=0
        def forward(self,x,context=None,**kw):
            self.calls+=1
            return x*.07+(0 if context is None else context.mean()*.03)
        def init_weights(self):pass
    @dataclass
    class VideoSize:
        T:int
        H:int
        W:int
    namespace={'torch':torch,'nn':torch.nn,'math':math,'Optional':Optional,'amp':torch.amp,
        'rearrange':rearrange,'Attention':TinyAttention,'I2VCrossAttention':TinyAttention,'VideoSize':VideoSize}
    module=ast.Module(body=classes,type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),str(path)+'#P0_CPU','exec'),namespace)
    torch.manual_seed(773);torch.set_num_threads(2)
    blocks=torch.nn.ModuleList([namespace['Block'](8,8,2,mlp_ratio=4,use_adaln_lora=lora,
        adaln_lora_dim=4,backend='declared_tiny_CPU_attention') for lora in (False,True,False,True)]).eval()
    reference=copy.deepcopy(blocks).eval();shape=(1,2,2,4,8);tokens=16
    observer=[];handles=[]
    for layer,b in enumerate(blocks):
        for name in ('layer1','layer2'):
            def observe(m,args,l=layer,n=name):observer.append((l,n,math.prod(args[0].shape[:-1])))
            handles.append(getattr(b.mlp,name).register_forward_pre_hook(observe))
    adapter=PartialMLP(blocks,(0,1,2,3)).install();context=('P0_CPU','pinned_Block','fixed_input')
    rng=torch.random.get_rng_state().clone();versions=[(p,p._version,p.clone()) for p in blocks.parameters()]
    checks=[];previous={}
    def inputs(step,slot):
        base=torch.arange(math.prod(shape),dtype=torch.float32).reshape(shape)/99
        return base+step*.021+slot*.35,torch.arange(16,dtype=torch.float32).reshape(1,2,8)/31+step*.11,
    def call(b,x,emb,slot):
        adaln=torch.linspace(-.3,.4,48).reshape(1,2,24)*(.6+slot) if b.use_adaln_lora else None
        return b(x,emb,torch.ones(1,3,8)*(slot+1),adaln_lora_B_T_3D=adaln)
    def dense(b,x,emb,slot):
        projection=[]
        h=b.mlp.register_forward_hook(lambda m,a,v:projection.append(v.detach().clone()))
        try:result=call(b,x,emb,slot)
        finally:h.remove()
        mod=b.adaln_modulation_mlp(emb)
        if b.use_adaln_lora:mod+=torch.linspace(-.3,.4,48).reshape(1,2,24)*(.6+slot)
        gate=mod.chunk(3,dim=-1)[2].reshape(1,2,1,1,8).type_as(x)
        return result,projection[0],gate
    try:
        with torch.no_grad():
            # P requested without a compatible projection must execute full MLP,
            # while remaining P provenance, never a new actual D observation.
            fallback_blocks=copy.deepcopy(reference).eval()
            fallback=PartialMLP(fallback_blocks,(0,1,2,3)).install()
            fallback_checks=[]
            try:
                for step in (1,2):
                    changed_context=context if step==1 else (context[0],context[1],'changed_input')
                    with fallback.pair(step=step,action='P',context=changed_context,indices=torch.arange(8)):
                        for slot in (0,1):
                            with fallback.branch(slot):
                                for layer,b in enumerate(fallback_blocks):
                                    x,emb=inputs(step,slot)
                                    expected,_,_=dense(reference[layer],x,emb,slot)
                                    assert torch.equal(call(b,x,emb,slot),expected)
                                    entry=fallback.cache[(layer,slot)]
                                    assert entry.last_actual_D is None and bool((entry.source==2).all())
                    rows=fallback.records[-8:]
                    reason='COLD_CACHE' if step==1 else 'INCOMPATIBLE_CACHE'
                    assert all(r['actual_MLP_rows']==tokens and r['fallback']==reason for r in rows)
                    fallback_checks.append({'step':step,'full_safe_fallback':reason,
                        'complete_both_branches_and_layers_direct_equal':True,'approximate_source_not_D':True})
            finally:fallback.close()
            for step,fraction in [(1,None),(2,.5),(3,.75),(4,'empty'),(5,'all'),(6,None)]:
                action='D' if fraction is None else 'P'
                ids=None if action=='D' else (torch.empty(0,dtype=torch.int64) if fraction=='empty'
                    else torch.arange(tokens) if fraction=='all' else block_indices(tokens,fraction,block_size=4,opportunity=step))
                observer.clear();attention_before=[(b.self_attn.calls,b.cross_attn.calls) for b in blocks]
                with adapter.pair(step=step,action=action,context=context,indices=ids):
                    for slot in (0,1):
                        with adapter.branch(slot):
                            for layer,b in enumerate(blocks):
                                x,emb=inputs(step,slot);full,projection,gate=dense(reference[layer],x,emb,slot)
                                if action=='D' or len(ids)==tokens:expected=full
                                else:
                                    inactive=torch.ones(tokens,dtype=torch.bool);inactive[ids]=False
                                    delta=previous[(layer,slot)]-projection
                                    expected=full+gate*delta*inactive.reshape(1,2,2,4,1)
                                value=call(b,x,emb,slot)
                                if action=='D' or len(ids)==tokens:assert torch.equal(value,expected)
                                else:torch.testing.assert_close(value,expected,rtol=1e-5,atol=2e-6)
                                entry=adapter.cache[(layer,slot)]
                                assert entry.last_actual_D==(step if action=='D' else 1)
                                if action=='P':
                                    assert bool((entry.source[ids]==2).all())
                                    assert bool((entry.updated_at[ids]==step).all())
                                    inactive=torch.ones(tokens,dtype=torch.bool);inactive[ids]=False
                                    assert torch.equal(entry.value.reshape(tokens,8)[inactive],previous[(layer,slot)].reshape(tokens,8)[inactive])
                                previous[(layer,slot)]=entry.value.clone()
                rows=tokens if action=='D' else len(ids)
                assert len(observer)==(16 if rows else 0)
                assert all(n==rows for _,_,n in observer),observer
                assert [(b.self_attn.calls-a,b.cross_attn.calls-c) for b,(a,c) in zip(blocks,attention_before)]==[(2,2)]*4
                checks.append({'step':step,'action':action,'rows_per_real_Linear':rows,
                    'complete_two_branch_four_layer_outputs_verified':True,'full_attention_calls_preserved':True,
                    'current_gate_independent_dense_reference_verified':True})
            state_result = None
            if state_control is not None:
                def state_arm(*, fail_second=False):
                    with adapter.pair(step=7,action='P',context=context,indices=torch.arange(8)):
                        for slot in (0,1):
                            if slot==1 and fail_second:
                                raise ValueError('Injected score-only state arm second-branch failure')
                            with adapter.branch(slot):
                                for b in blocks:
                                    x,emb=inputs(7,slot);call(b,x,emb,slot)
                    return {key: c.value.clone() for key,c in adapter.cache.items()}
                state_result = state_control(adapter, state_arm)
            # Unregistered full teacher cannot alter projection history.
            before=dict(adapter.cache);observer.clear()
            with adapter.readonly():
                for b in blocks:
                    x,emb=inputs(8,0);call(b,x,emb,0)
            assert all(adapter.cache[k] is v for k,v in before.items())
            assert len(observer)==8 and all(n==tokens for _,_,n in observer)
            # All quota selection is independent of the global CPU RNG.
            for n in (16,17,31104):
                for f in (.5,.75):
                    rotate=block_indices(n,f,block_size=4,opportunity=1)
                    random=block_indices(n,f,block_size=4,random_seed=32)
                    assert len(rotate)==len(random) and rotate.max()<n and random.max()<n
            assert torch.equal(torch.random.get_rng_state(),rng)
            assert all(p is a and p._version==v and torch.equal(p,b) for p,(a,v,b) in zip(blocks.parameters(),versions))
            refused=[]
            for label,kwargs in [('duplicate',{'indices':torch.tensor([0,0])}),('negative',{'indices':torch.tensor([-1])}),
                    ('wrong_dtype',{'indices':torch.tensor([0.])}),('old_step',{'step':6,'indices':torch.arange(8)})]:
                arg={'step':7,'action':'P','context':context,'indices':torch.arange(8)};arg.update(kwargs)
                try:
                    with adapter.pair(**arg):pass
                except ValueError:refused.append(label)
                else:raise AssertionError(label)
            saved=dict(adapter.cache)
            try:
                with adapter.pair(step=7,action='P',context=context,indices=torch.arange(8)):
                    with adapter.branch(0):
                        for b in blocks:
                            x,emb=inputs(7,0);call(b,x,emb,0)
                    raise ValueError('Injected second-branch failure')
            except ValueError as error:assert str(error)=='Injected second-branch failure'
            else:raise AssertionError('Registered failure did not execute')
            assert adapter.poisoned and adapter.last_step==6 and all(adapter.cache[k] is v for k,v in saved.items())
            try:
                with adapter.pair(step=8,action='D',context=context):pass
            except ValueError:pass
            else:raise AssertionError('Poisoned pair continued')
            assert torch.equal(torch.random.get_rng_state(),rng)
        return {'status':'P0_PINNED_BLOCK_GATHERED_MLP_CPU_PASS_NOT_COSMOS_OR_SPEED',
            'pinned_source_sha256':SOURCE_SHA,'actual_source_classes_executed':['GPT2FeedForward','Block'],
            'declared_Toy_components':['attention','CPU_weights','inputs'],
            'complete_pair_checks':checks,'actual_D_or_all_active_direct_equal':True,
            'cold_and_incompatible_full_safe_fallback_checks':fallback_checks,
            'both_Linear_gathered_row_counts_verified':True,'score_only_teacher_no_cache_update':True,
            'same_quota_rotation_and_random_global_RNG_preserved':True,'refusals':refused,
            'second_branch_failure_complete_cache_rollback_and_poison_verified':True,
            'current_gate_and_own_branch_projection_cache_verified':True,
            'parameter_versions_and_values_preserved':True,'CUDA_initialized':torch.cuda.is_initialized(),
            'GPU_submissions':0,'real_Cosmos_OR_video_OR_clean_latency_claim':False,
            'additional_projection_state_control':state_result}
    finally:
        adapter.close()
        assert all('forward' not in vars(b.mlp) for b in blocks)
        for h in handles:h.remove()
