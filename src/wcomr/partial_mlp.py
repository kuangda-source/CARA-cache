"""P0: branch-owned ungated projection caches, with genuinely gathered MLP rows.

Only MLP.forward is intercepted. The source Block retains its current norm,
modulation, full attention and current gate. This executor has its own state;
its full-MLP metadata is not a WorldCache D anchor or an RA zero-risk source.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import math
import types

import torch


@dataclass(frozen=True)
class ProjectionCache:
    value: torch.Tensor
    updated_at: torch.Tensor
    source: torch.Tensor  # 1 actual D projection; 2 P-created projection
    context: tuple
    parameter_versions: tuple
    last_actual_D: object


def block_indices(tokens, fraction, *, block_size=128, opportunity=0, random_seed=None):
    """Same-quota rotation/random; independent CPU RNG, actual density recorded."""
    if (type(tokens) is not int or tokens<=0 or fraction not in (.5,.75)
            or type(block_size) is not int or block_size<=0
            or type(opportunity) is not int or opportunity<0):
        raise ValueError('Explicit token layout and registered P0 fraction required')
    blocks=math.ceil(tokens/block_size);count=max(1,math.floor(blocks*fraction))
    if random_seed is None:
        selected=[(opportunity*count+i)%blocks for i in range(count)]
    else:
        if type(random_seed) is not int:raise ValueError('Local random seed must be an integer')
        generator=torch.Generator(device='cpu').manual_seed(random_seed)
        selected=torch.randperm(blocks,generator=generator)[:count].tolist()
        # A short final block would give different quotas. Rotate/randomize only
        # full blocks; reserve the tail consistently outside this first quota.
        full=tokens//block_size
        if full and tokens%block_size:
            count=max(1,math.floor(full*fraction))
            selected=torch.randperm(full,generator=generator)[:count].tolist()
    if tokens%block_size and tokens//block_size:
        full=tokens//block_size;count=max(1,math.floor(full*fraction))
        if random_seed is None:selected=[(opportunity*count+i)%full for i in range(count)]
    result=sorted(v for b in selected for v in range(b*block_size,min((b+1)*block_size,tokens)))
    return torch.tensor(result,dtype=torch.int64)


class PartialMLP:
    def __init__(self,blocks,layers):
        if (not layers or tuple(sorted(set(layers)))!=tuple(layers)
                or any(type(i) is not int or not 0<=i<len(blocks) for i in layers)):
            raise ValueError('Explicit unique ordered P0 layers required')
        self.blocks=blocks;self.layers=tuple(layers);self.cache={};self.records=[]
        self._original={};self._forward_attributes={};self._pair=None;self._slot=None;self._seen=set();self._readonly=0
        self.last_step=0;self.poisoned=False

    def install(self):
        if self._original:raise ValueError('P0 already installed')
        for layer in self.layers:
            mlp=self.blocks[layer].mlp
            if (type(mlp.layer1) is not torch.nn.Linear or type(mlp.layer2) is not torch.nn.Linear
                    or mlp.layer1.bias is not None or mlp.layer2.bias is not None
                    or type(mlp.activation) is not torch.nn.GELU
                    or any(m.training for m in mlp.modules())):
                raise ValueError('Pinned no-bias eval Linear/GELU/Linear MLP required')
        for layer in self.layers:
            mlp=self.blocks[layer].mlp;original=mlp.forward;self._original[layer]=original
            self._forward_attributes[layer]=('forward' in vars(mlp),vars(mlp).get('forward'))
            def execute(module,x,_layer=layer):return self._execute(_layer,module,x)
            mlp.forward=types.MethodType(execute,mlp)
        return self

    def close(self):
        if self._pair is not None:raise ValueError('Cannot uninstall P0 during a pair')
        for layer in self._original:
            owned,value=self._forward_attributes[layer];mlp=self.blocks[layer].mlp
            if owned:mlp.forward=value
            else:delattr(mlp,'forward')
        self._original.clear()
        self._forward_attributes.clear()

    @contextmanager
    def readonly(self):
        """Full score-only teacher; no deployment cache update or D observation."""
        self._readonly+=1
        try:yield
        finally:self._readonly-=1

    @contextmanager
    def pair(self,*,step,action,context,indices=None):
        if (not self._original or self.poisoned or self._pair is not None
                or type(step) is not int or step<=self.last_step or action not in ('D','P')
                or type(context) is not tuple or len(context)!=3
                or any(type(v) is not str or not v for v in context)):
            raise ValueError('Fresh monotonic bound P0 pair required')
        if action=='P':
            if (not isinstance(indices,torch.Tensor) or indices.dtype!=torch.int64 or indices.ndim!=1
                    or indices.requires_grad):raise ValueError('Explicit shared P0 index vector required')
            indices=indices.detach().cpu().clone()
            if (bool((indices<0).any()) or not torch.equal(indices,torch.unique(indices,sorted=True))):
                raise ValueError('P0 indices must be sorted unique nonnegative positions')
        elif indices is not None:raise ValueError('Actual D does not take a partial mask')
        before=dict(self.cache)
        self._pair={'step':step,'action':action,'context':context,'indices':indices,'device_indices':{},'slots':set()}
        try:
            yield self
            if self._pair['slots']!={0,1}:raise ValueError('Both complete CFG branches required')
            self.last_step=step
        except BaseException as error:
            self.cache=before;self.poisoned=True
            self.records.append({'step':step,'action':action,'status':'PAIR_FAILED_CACHE_ROLLED_BACK',
                'error_type':type(error).__name__,'error':str(error)})
            raise
        finally:self._pair=None;self._slot=None;self._seen=set()

    @contextmanager
    def branch(self,slot):
        if (self._pair is None or self._slot is not None or type(slot) is not int
                or slot not in (0,1) or slot in self._pair['slots']):
            raise ValueError('Each bound CFG branch executes exactly once')
        self._slot=slot;self._seen=set()
        try:
            yield
            if self._seen!=set(self.layers):raise ValueError('Complete selected layer scope required')
            self._pair['slots'].add(slot)
        finally:self._slot=None;self._seen=set()

    def _execute(self,layer,module,x):
        original=self._original[layer]
        if self._readonly:return original(x)
        if self._pair is None or self._slot is None:raise ValueError('P0 projection outside a bound branch')
        if layer in self._seen:raise ValueError('Repeated P0 layer in one branch')
        if (not isinstance(x,torch.Tensor) or x.ndim!=5 or x.shape[0]!=1
                or x.dtype not in (torch.float32,torch.float16,torch.bfloat16)
                or x.requires_grad or any(m.training for m in module.modules())):
            raise ValueError('P0 needs eval B1 T/H/W/D inference projections')
        self._seen.add(layer);pair=self._pair;key=(layer,self._slot)
        tokens=math.prod(x.shape[:-1]);versions=tuple((id(p),p._version) for p in module.parameters())
        old=self.cache.get(key);index=pair['indices'];reason=None
        if index is not None and len(index) and int(index[-1])>=tokens:
            raise ValueError('P0 mask outside actual latent token layout')
        if old is None:reason='COLD_CACHE'
        elif (old.context!=pair['context'] or tuple(old.value.shape)!=tuple(x.shape)
                or old.value.dtype!=x.dtype or old.value.device!=x.device
                or old.parameter_versions!=versions):reason='INCOMPATIBLE_CACHE'
        full=pair['action']=='D' or reason is not None or len(index)==tokens
        if full:
            value=original(x);active=tokens
            last_D=pair['step'] if pair['action']=='D' else (old.last_actual_D if reason is None else None)
            source=torch.full((tokens,),1 if pair['action']=='D' else 2,dtype=torch.uint8,device=x.device)
            age=torch.full((tokens,),pair['step'],dtype=torch.int32,device=x.device)
        else:
            device=str(x.device)
            if device not in pair['device_indices']:pair['device_indices'][device]=index.to(x.device)
            ids=pair['device_indices'][device];active=len(index)
            # Gather BEFORE both real Linear calls. Inactive rows execute neither.
            value=old.value.reshape(tokens,x.shape[-1]).clone()
            if active:
                gathered=x.reshape(tokens,x.shape[-1]).index_select(0,ids)
                fresh=original(gathered)
                value.index_copy_(0,ids,fresh)
            value=value.reshape(x.shape);age=old.updated_at.clone();source=old.source.clone()
            age.index_fill_(0,ids,pair['step']);source.index_fill_(0,ids,2);last_D=old.last_actual_D
        if value.shape!=x.shape or value.dtype!=x.dtype:raise ValueError('Pinned MLP projection geometry differs')
        # Never cache a result already multiplied by the Block's timestep gate.
        self.cache[key]=ProjectionCache(value.detach().clone(),age,source,pair['context'],versions,last_D)
        self.records.append({'step':pair['step'],'slot':self._slot,'layer':layer,'action':pair['action'],
            'tokens':tokens,'actual_MLP_rows':active,'actual_fraction':active/tokens,
            'fallback':reason if pair['action']=='P' else None,'full_MLP':full,
            'last_actual_D':last_D,'projection_cache_bytes':value.numel()*value.element_size(),
            'provenance_bytes':age.numel()*age.element_size()+source.numel()*source.element_size(),
            'ungated_projection_only':True,'current_Block_gate_preserved':True,
            'is_WorldCache_D_anchor_or_RA_zero_risk_source':False})
        return value
