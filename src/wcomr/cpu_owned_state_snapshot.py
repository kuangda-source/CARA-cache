"""E1 storage-preserving CPU image for inactive healthy inference state.

No sampler, policy, physical state or CUDA-admission replacement is installed
by this module. GPU source storage is copied directly to CPU, without a GPU
deepcopy intermediate. This is not recovery from a poisoned computation.
"""
import copy
from dataclasses import fields, is_dataclass

import numpy as np
import torch

from .partial_mlp_deployment_state import plain, tensor_bytes
from .mid_coverage import tree_digest


def _walk_tensors(value, active=None):
    active = set() if active is None else active
    if isinstance(value, torch.Tensor):
        if (type(value) is not torch.Tensor or value.layout != torch.strided
                or value.requires_grad or value.is_quantized or value.is_conj()
                or value.is_neg() or value.device.type not in ('cpu','cuda')):
            raise ValueError('Only ordinary detached strided CPU/CUDA inference tensors snapshot')
        yield value
    elif is_dataclass(value) or isinstance(value, (dict,list,tuple)):
        if id(value) in active:
            raise ValueError('Cyclic state is outside registered inference-state scope')
        active.add(id(value))
        try:
            values = (getattr(value,f.name) for f in fields(value)) if is_dataclass(value) else (
                value.values() if isinstance(value,dict) else value)
            for item in values:
                yield from _walk_tensors(item,active)
        finally:
            active.remove(id(value))
    elif value is None or isinstance(value,(str,int,float,bool,np.generic,np.ndarray)):
        return
    else:
        raise ValueError('Uncovered owned state type: '+type(value).__name__)


def _storage_key(tensor):
    # _cdata identifies an untyped storage consistently across its wrapper
    # objects, including zero-sized storage. Pinned Torch2.7.1 control required.
    storage = tensor.untyped_storage()
    return (str(tensor.device),storage._cdata)


def storage_inventory(value):
    tensors = {}
    logical = 0
    for tensor in _walk_tensors(value):
        logical += tensor.numel()*tensor.element_size()
        tensors[id(tensor)] = tensor
    storages = {}
    for tensor in tensors.values():
        key = _storage_key(tensor)
        if key not in storages:
            storages[key] = {'device':str(tensor.device),'bytes':tensor.untyped_storage().nbytes()}
    assert logical == tensor_bytes(value)
    return {'logical_tensor_bytes_aliases_counted':logical,'unique_tensor_objects':len(tensors),
        'unique_storages':len(storages),'unique_storage_bytes':sum(s['bytes'] for s in storages.values()),
        'unique_GPU_storage_bytes':sum(s['bytes'] for s in storages.values() if s['device'].startswith('cuda:')),
        'unique_CPU_storage_bytes':sum(s['bytes'] for s in storages.values() if s['device']=='cpu'),
        'tensor_alias_topology_preserved_not_autograd':True}


def _typed_view(byte_storage_tensor, prototype):
    return torch.empty(0,dtype=prototype.dtype,device=byte_storage_tensor.device).set_(
        byte_storage_tensor.untyped_storage(),prototype.storage_offset(),
        tuple(prototype.shape),tuple(prototype.stride()))


class CPUOwnedStateImage:
    """Independent CPU storage image; each materialization is independent."""
    @torch.no_grad()
    def __init__(self, value, *, logical_copy_cap_bytes, CPU_storage_cap_bytes):
        if torch.is_grad_enabled():
            raise ValueError('Inference only snapshot')
        if (type(logical_copy_cap_bytes) is not int or logical_copy_cap_bytes<=0
                or type(CPU_storage_cap_bytes) is not int or CPU_storage_cap_bytes<=0):
            raise ValueError('Explicit positive logical and CPU-storage caps required')
        self.inventory = storage_inventory(value)
        if self.inventory['logical_tensor_bytes_aliases_counted'] > logical_copy_cap_bytes:
            raise ValueError('Owned-state image exceeds original logical copy cap')
        if self.inventory['unique_storage_bytes'] > CPU_storage_cap_bytes:
            raise ValueError('Owned-state image exceeds explicit CPU-storage cap')
        # Guard finite values before source bytes are accepted; no deepcopy of
        # GPU tensors occurs. Hashing may transfer only contiguous value bytes.
        source_digest = tree_digest(plain(value))
        self._storage_images = {}
        self._original_devices = {}
        self._CPU_views = {}
        memo = {}
        for tensor in _walk_tensors(value):
            if id(tensor) in memo:
                continue
            key = _storage_key(tensor)
            if key not in self._storage_images:
                byte_view = torch.empty(0,dtype=torch.uint8,device=tensor.device).set_(
                    tensor.untyped_storage(),0,(tensor.untyped_storage().nbytes(),),(1,))
                self._storage_images[key] = byte_view.to(device='cpu',copy=True,non_blocking=False)
                self._original_devices[key] = tensor.device
            CPU_view = _typed_view(self._storage_images[key],tensor)
            memo[id(tensor)] = CPU_view
            self._CPU_views[id(CPU_view)] = (key,CPU_view)
        self.saved = copy.deepcopy(value,memo)
        self.digest = tree_digest(plain(self.saved))
        if self.digest != source_digest or any(t.device.type!='cpu' for t in _walk_tensors(self.saved)):
            raise ValueError('Owned CPU image differs from complete original value state')
        self.GPU_snapshot_storage_allocation_bytes = 0

    @torch.no_grad()
    def materialize(self):
        if tree_digest(plain(self.saved)) != self.digest:
            raise ValueError('Saved CPU owned-state image was modified')
        stores = {key:value.to(device=self._original_devices[key],copy=True,non_blocking=False)
            for key,value in self._storage_images.items()}
        memo = {identity:_typed_view(stores[key],prototype)
            for identity,(key,prototype) in self._CPU_views.items()}
        result = copy.deepcopy(self.saved,memo)
        if tree_digest(plain(result)) != self.digest or storage_inventory(result) != self.inventory:
            raise ValueError('Materialized owned-state values, device or storage topology differ')
        return result


class CPUDeploymentRoundtrip:
    """New owner-state snapshot primitive, not installed into old checkpoints."""
    @torch.no_grad()
    def __init__(self, owner, *, logical_copy_cap_bytes, CPU_storage_cap_bytes):
        owner.check_healthy()
        self.owner = owner
        self.binding = owner.installation()
        self.image = CPUOwnedStateImage(owner.own_state(),logical_copy_cap_bytes=logical_copy_cap_bytes,
            CPU_storage_cap_bytes=CPU_storage_cap_bytes)
        self.bytes = self.image.inventory['logical_tensor_bytes_aliases_counted']
        self.origin = self.image.digest

    @torch.no_grad()
    def restore(self):
        self.owner.check_healthy()
        if self.owner.installation()!=self.binding:
            raise ValueError('Changed owner, parameters or installation cannot restore')
        self.owner.restore_own_state(self.image.materialize())
        if self.owner.fingerprint()!=self.origin:
            raise ValueError('CPU-backed additional owned-state restoration differs')
        return self.origin
