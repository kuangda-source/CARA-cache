"""Explicit new-card extension of the unmodified V2.2 parent observer.

Three additional actual corner/midpoint outputs per selected state. The
parent, original six readouts, anchors and protected state stay unchanged.
This module has no execution/ledger authority.
"""
import copy
import time
from enum import Enum

import torch

from . import scout_parent_v22 as parent
from . import clean_speed20_r1 as clean
from .innovation_gain_r1 import InnovationGainKernel
from .innovation_gain_fit_r1 import output_moments
from .policy_interval_readout_r1 import guided
from .scout_readout_v22 import Anchor, D_STEPS, PARENT_FINGERPRINT, STATE_STEPS


class GainParentOwner(parent.ScoutParentOwner):
    def _observe(self, step, xis, sigmas, inputs, actual, pre):
        schema = condition_schema(inputs[3])
        previous = self.condition_registry.setdefault(self.scout_context[0], schema)
        if previous != schema:
            raise ValueError('Condition schema changed within one request')
        original_sink = self.sink
        def augmented_sink(payload):
            older, latest = [s for s in D_STEPS if s < step][-2:]
            anchors = tuple((self.bank[older][b],self.bank[latest][b]) for b in (0,1))
            current = [self.features[b] for b in (0,1)]
            args = dict(context=self.scout_context,step=step,xi=xis[step-1],
                        anchors=anchors,current=current,pair_inputs=inputs)
            extras = {}
            for name,gains in (('f10',(1.,0.)),('f01',(0.,1.)),('f05',(.5,.5))):
                kernel = InnovationGainKernel(self.model,self._runtime,self._wc,self._rf,
                    self.deployment.warp,max_logical_copy_bytes=self.copy_cap,gains=gains)
                value = kernel.evaluate_gain(**args)
                extras[name] = parent.tensor_record(value)
            payload['innovation_gain'] = dict(additional_guided_adapter_replays=3,
                additional_candidate_head_pairs=6, outputs=extras,
                frozen_box=[0.,1.], shared_CFG_gains=True,
                token_shape=list(current[0]['probe'].shape), token_layout='BTHWD',
                parent_mutation=False)
            r = payload['readouts']
            payload['gain_moments'] = output_moments(
                guided(payload['teacher']).numpy(),guided(r['FULL']['outputs']).numpy(),
                guided(extras['f10']['outputs']).numpy(),guided(extras['f01']['outputs']).numpy(),
                guided(r['R4_GLOBAL']['outputs']).numpy(),guided(extras['f05']['outputs']).numpy())
            original_sink(payload)
        self.sink = augmented_sink
        try:
            return super()._observe(step,xis,sigmas,inputs,actual,pre)
        finally:
            self.sink = original_sink


def execute(*args, condition_registry, **kwargs):
    # Explicit caller-selected new card. Never patch the running mainline stage.
    def factory(*a, **kw):
        owner = GainParentOwner(*a, **kw)
        owner.condition_registry = condition_registry
        return owner
    with clean.patched(parent, 'ScoutParentOwner', factory):
        return parent.execute(*args, **kwargs)


def move_tree(value, device):
    if isinstance(value,torch.Tensor):return value.to(device=device)
    if isinstance(value,dict):return {k:move_tree(v,device) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return type(value)(move_tree(v,device) for v in value)
    return value


def condition_schema(conditions):
    """In-process type registry only; no model/tensor/credentials retained."""
    return [(type(c),{k:type(v) for k,v in vars(c).items() if isinstance(v,Enum)}) for c in conditions]


def restore_readout_inputs(payload, schema, device):
    """Rebuild only explicit readout inputs, never a sampler checkpoint.

Caller must first replay stored FULL/DEEP outputs through this exact path.
This does not resume a diffusion trajectory or claim RNG/cache resumability.
"""
    context = tuple(payload['context']); step=payload['step']
    if context[-1] != PARENT_FINGERPRINT or step not in STATE_STEPS or len(schema) != 2:
        raise ValueError('Registered gain state required')
    def anchor(row):
        r=move_tree(row,device);r['context']=tuple(r['context']);return Anchor(**r)
    anchors=tuple(tuple(anchor(r) for r in pair) for pair in payload['anchors'])
    p=payload['pair_inputs'];conditions=[]
    for row,(cls,enums) in zip(p['conditions'],schema):
        if cls.__qualname__ != row['class_name']:
            raise ValueError('Condition class changed')
        fields=move_tree(row['fields'],device)
        fields.update({k:typ(fields[k]) for k,typ in enums.items()})
        conditions.append(cls(**fields))
    return dict(context=context,step=step,xi=payload['xi'],anchors=anchors,
        current=move_tree(payload['current'],device),
        pair_inputs=tuple(move_tree(p[k],device) for k in ('noise','latent','timestep'))+(tuple(conditions),))
