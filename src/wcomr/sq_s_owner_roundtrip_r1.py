"""Healthy PolicyOwner state around an independent S shadow computation.

The caller separately owns CompleteStateRoundtrip for the physical model,
solver, buffers and RNG. This component cannot rewind a completed parent pair,
unpoison an executor or restore a serialized pipeline. A dirty owner is restored
only for cleanup and is rejected as scientific collection evidence.
"""
import copy
import torch

from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain,tensor_bytes
from .policy_generator_r1.production_sampling import PolicyOwner

OWNER_FIELDS={'model','net','policy','profile','readout','proof','executor','choose',
    'history','deployment','fallback_reason','force_dense'}
READOUT_FIELDS={'model','net','method','context','calibrators','warp','to_velocity',
    'completed','current','history','poisoned','policy','forced_dense','_end'}
EXECUTOR_FIELDS={'model','net','denoise','torch','poisoned','running','last','wc_forward','rf_denoise'}
CALIBRATOR_FIELDS={'ridge','clip','decay','min_energy','shrinkage','context','anchors',
    'numerator','denominator','pairs'}


def require(value,message):
    if not value:raise ValueError(message)


class PolicyOwnerRoundtrip:
    def __init__(self,owner,*,logical_copy_cap_bytes):
        require(isinstance(owner,PolicyOwner),'Actual production PolicyOwner required')
        require(type(logical_copy_cap_bytes) is int and logical_copy_cap_bytes>0,
                'Explicit remaining owner-state copy budget required')
        self.owner=owner;self._healthy()
        self.binding=self._binding()
        self.progress=(owner.readout.completed,len(owner.history),len(owner.readout.history))
        live=self._state();self.bytes=tensor_bytes(live)
        require(self.bytes<=logical_copy_cap_bytes,'S owner snapshot exceeds remaining logical copy budget')
        self.saved=copy.deepcopy(live);self.origin=tree_digest(plain(self.saved))

    def _healthy(self):
        owner=self.owner;readout=owner.readout;executor=owner.executor
        require(set(vars(owner))==OWNER_FIELDS,'Unregistered mutable PolicyOwner field')
        optional={'hidden'} if 'hidden' in vars(readout) else set()
        require(set(vars(readout))==READOUT_FIELDS|optional
                and (not optional or callable(readout.hidden)), 'Unregistered production readout field')
        require(set(vars(executor))==EXECUTOR_FIELDS,'Unregistered production executor field')
        require(len(readout.calibrators)==2 and all(set(vars(c))==CALIBRATOR_FIELDS
                for c in readout.calibrators),'Unregistered calibrator field')
        require(owner.model.net is owner.net and readout.model is owner.model and readout.net is owner.net
                and executor.model is owner.model and executor.net is owner.net
                and owner.deployment is owner and owner.policy is readout.policy,
                'Production owner/model/readout binding changed')
        require(readout.current is None and not readout.poisoned and not executor.poisoned
                and not torch.is_grad_enabled()
                and not executor.running and not owner.force_dense and not readout.forced_dense
                and readout.completed==len(owner.history)==len(readout.history)
                and int(owner.net.cnt)==2*readout.completed%70,
                'Healthy quiescent parent pair required; no failure recovery or pair rewind')

    def _binding(self):
        owner=self.owner;readout=owner.readout;executor=owner.executor
        return dict(identities=tuple(id(v) for v in (type(owner),owner.model,owner.net,owner.policy,
            owner.profile,readout,executor,owner.choose,readout.calibrators,
            *readout.calibrators,readout.warp,readout.to_velocity,readout._end,
            vars(readout).get('hidden'),executor.denoise,executor.wc_forward,executor.rf_denoise,executor.torch)),
            policy=tree_digest(plain(owner.policy)),profile=tree_digest(plain(owner.profile)),
            proof=tree_digest(plain(dict(owner.proof))),method=readout.method,context=readout.context)

    def _state(self):
        owner=self.owner;readout=owner.readout
        return dict(owner_history=owner.history,fallback_reason=owner.fallback_reason,
            readout_history=readout.history,completed=readout.completed,
            calibrators=[vars(c) for c in readout.calibrators],executor_last=owner.executor.last)

    def fingerprint(self):
        self._healthy()
        require(self._binding()==self.binding,'Changed policy, helpers or owner installation')
        return tree_digest(plain(self._state()))

    def restore(self):
        self._healthy()
        require(self._binding()==self.binding,'Changed policy, helpers or owner installation')
        owner=self.owner;readout=owner.readout
        require((readout.completed,len(owner.history),len(readout.history))==self.progress,
                'A completed parent pair cannot be rewound by S shadow cleanup')
        changed=tree_digest(plain(self._state()))!=self.origin
        saved=copy.deepcopy(self.saved)
        owner.history=saved['owner_history'];owner.fallback_reason=saved['fallback_reason']
        readout.history=saved['readout_history'];readout.completed=saved['completed']
        for calibrator,fields in zip(readout.calibrators,saved['calibrators']):
            calibrator.__dict__.clear();calibrator.__dict__.update(fields)
        owner.executor.last=saved['executor_last']
        require(self.fingerprint()==self.origin,'Complete S owner restoration failed')
        require(not changed,'Shadow changed protected owner state; restored for cleanup, collection not accepted')
        return self.origin
