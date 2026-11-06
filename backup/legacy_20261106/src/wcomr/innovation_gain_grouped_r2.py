"""Amortize full-state audit across one readout group, preserve every restore.

Numerical implementations remain inherited from the accepted R1 adapters.
Every point gets private inputs and a physical snapshot restore before/after.
The enclosing parent transaction still performs its original complete hashes;
saved-input groups hash their complete physical state and inputs once per group.
"""
import contextlib
import contextvars
import copy
import torch

from . import clean_speed20_r1 as clean
from . import scout_parent_v22 as parent
from . import innovation_gain_observer_r1 as observer
from .innovation_gain_r1 import InnovationGainKernel
from .scout_readout_v22 import ScoutReadoutKernel,LABELS,validate_state,_tensors,UnsupportedReadout
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import tree_digest,WC_FIELDS
from .partial_mlp_deployment_state import plain,tensor_bytes

ACTIVE=contextvars.ContextVar('IG_R2_READOUT_GROUP',default=None)


def input_digest(inputs):
    pair=inputs['pair_inputs']
    return tree_digest(plain((inputs['anchors'],inputs['current'],pair[:3],[vars(c) for c in pair[3]])))


@contextlib.contextmanager
def group(model,inputs,*,parent_owns_complete_audit=False):
    if ACTIVE.get() is not None:raise ValueError('Nested readout transaction forbidden')
    snapshot=CompleteStateRoundtrip(model.net,model.sample_scheduler,torch.zeros(1))
    before=None if parent_owns_complete_audit else snapshot.fingerprint()
    digest=None if parent_owns_complete_audit else input_digest(inputs)
    scope=dict(model=model,snapshot=snapshot,points=0,parent_audit=parent_owns_complete_audit)
    token=ACTIVE.set(scope)
    try:yield scope
    finally:
        try:
            snapshot.restore()
            if not parent_owns_complete_audit:
                if snapshot.fingerprint()!=before or input_digest(inputs)!=digest:
                    raise RuntimeError('Grouped readouts changed protected physical state or saved inputs')
        finally:ACTIVE.reset(token)


class GroupedScoutKernel(ScoutReadoutKernel):
    @torch.no_grad()
    def evaluate(self,label,*,context,step,xi,anchors,current,pair_inputs):
        scope=ACTIVE.get()
        if scope is None or scope['model'] is not self.model:raise ValueError('Explicit enclosing full audit required')
        if label not in LABELS or len(current)!=2 or len(pair_inputs)!=4 or len(pair_inputs[3])!=2:
            raise UnsupportedReadout('Complete registered pair required')
        spans=validate_state(context,step,xi,anchors)
        if any(m.training for m in self.net.modules()):raise UnsupportedReadout('All modules must remain eval')
        for row,(old,last) in zip(current,anchors):
            _tensors(row['original'],row['probe'],old.probe,old.residual,last.probe,last.residual)
        logical=tensor_bytes(plain((anchors,current,pair_inputs[:3],[vars(c) for c in pair_inputs[3]],
            {k:getattr(self.net,k) for k in WC_FIELDS if hasattr(self.net,k)},
            {k:v for k,v in vars(self.model.sample_scheduler).items() if not callable(v)},list(self.net.buffers()))))
        if logical>self.max_logical_copy_bytes:raise UnsupportedReadout('State-copy budget exceeded before allocation')
        versions=[(p,p._version) for p in self.net.parameters()]
        scope['snapshot'].restore()
        try:
            value=self._evaluate(label,spans,copy.deepcopy(anchors),copy.deepcopy(current),copy.deepcopy(pair_inputs))
            value=copy.deepcopy(value)
        finally:
            scope['snapshot'].restore()
            if any(p._version!=v for p,v in versions):raise RuntimeError('Candidate mutated weights')
        scope['points']+=1
        value['state_roundtrip']=dict(scope='ENCLOSING_COMPLETE_HASH_WITH_EVERY_POINT_RESTORED',
            private_inputs_per_point=True,physical_restores_per_point=2,logical_copy_bytes=logical,
            logical_copy_cap_bytes=self.max_logical_copy_bytes,per_point_full_hashes=0,
            parent_owns_complete_audit=scope['parent_audit'])
        return value


class GroupedGainKernel(InnovationGainKernel,GroupedScoutKernel):
    pass


class GroupedParentOwner(observer.GainParentOwner):
    def _observe(self,step,xis,sigmas,inputs,actual,pre):
        with group(self.model,inputs,parent_owns_complete_audit=True):
            return super()._observe(step,xis,sigmas,inputs,actual,pre)


def execute(*args,**kwargs):
    with clean.patched(observer,'GainParentOwner',GroupedParentOwner), \
         clean.patched(observer,'InnovationGainKernel',GroupedGainKernel), \
         clean.patched(parent,'ScoutReadoutKernel',GroupedScoutKernel):
        return observer.execute(*args,**kwargs)
