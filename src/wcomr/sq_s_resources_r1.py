"""S tensor ownership inventory; metadata bytes are never an allocated peak.

Logical references match the existing copy guard. Storage accounting records
the full backing allocation once, including views. No tensor values are read,
copied, hashed or transferred by this inventory.
"""
from collections.abc import Mapping
from contextlib import contextmanager
from enum import Enum

import numpy as np
import torch

from .mid_coverage import WC_FIELDS
from .partial_mlp_deployment_state import plain,tensor_bytes


def require(value,message):
    if not value:raise ValueError(message)


def registered_experiment(model,keys,checkpoints,*,expected_model,expected_experiment):
    """Read the registry's experiment only; never resolve checkpoint.path."""
    require(model==expected_model,'Frozen S model name differs')
    experiment=checkpoints[keys[model]].experiment
    require(experiment==expected_experiment,'Frozen S registered experiment differs')
    return experiment


@contextmanager
def explicit_meta_constructor(cls):
    """Use the original constructor's device argument; preserve its class/body."""
    require(issubclass(cls,torch.nn.Module),'An actual module constructor is required')
    original=cls.__init__;state=dict(calls=0,device='meta',restored=False)
    def initialize(instance,*args,**kwargs):
        device=kwargs.pop('device',None)
        require(device is None or torch.device(device).type=='meta',
                'Metadata constructor cannot allocate a real device')
        state['calls']+=1
        return original(instance,*args,device=torch.device('meta'),**kwargs)
    cls.__init__=initialize
    try:yield state
    finally:cls.__init__=original;state['restored']=True


@contextmanager
def explicit_meta_device_resolver(namespace):
    """Pass meta explicitly to the original TE resolver, including reset paths."""
    original=namespace.canonicalize_device
    state=dict(default_calls=0,explicit_calls=0,restored=False)
    def resolve(device):
        require(torch.get_default_device().type=='meta','TE metadata resolver needs an explicit meta context')
        if device is None:
            state['default_calls']+=1;device=torch.device('meta')
        else:
            require(torch.device(device).type=='meta','Metadata resolver cannot select a real device')
            state['explicit_calls']+=1
        return original(device)
    namespace.canonicalize_device=resolve
    try:yield state
    finally:namespace.canonicalize_device=original;state['restored']=True


def inventory(value):
    rows=[];objects={};storages={};arrays={}
    def walk(item,path):
        if isinstance(item,torch.Tensor):
            require(item.layout==torch.strided,'Unregistered S tensor layout at '+path)
            storage=item.untyped_storage();key=(str(item.device),storage._cdata)
            if key not in storages:
                storages[key]=dict(id=len(storages),device=str(item.device),bytes=storage.nbytes(),
                    metadata_only=item.device.type=='meta')
            if id(item) not in objects:objects[id(item)]=len(objects)
            rows.append(dict(path=path,shape=list(item.shape),stride=list(item.stride()),dtype=str(item.dtype),
                device=str(item.device),logical_bytes=item.numel()*item.element_size(),
                object_id=objects[id(item)],storage_id=storages[key]['id'],storage_offset=item.storage_offset(),
                requires_grad=item.requires_grad))
        elif isinstance(item,np.ndarray):
            # numpy RNG/scheduler arrays do not enter tensor_bytes, so retain
            # their own byte denominator instead of silently omitting them.
            base=item
            while isinstance(base.base,np.ndarray):base=base.base
            arrays.setdefault(id(base),dict(bytes=base.nbytes,dtype=str(base.dtype)))
        elif isinstance(item,Mapping):
            for key,child in item.items():
                require(type(key) in (str,int),'Unregistered S mapping key')
                walk(child,path+'/'+str(key))
        elif isinstance(item,(tuple,list)):
            for index,child in enumerate(item):walk(child,path+'/'+str(index))
        elif isinstance(item,Enum):walk(item.value,path)
        elif item is None or type(item) in (str,int,bool) or isinstance(item,(np.bool_,torch.dtype,torch.device)):pass
        elif isinstance(item,(float,np.number)):
            require(bool(np.isfinite(item)),'Nonfinite S metadata at '+path)
        else:raise TypeError('Unregistered S inventory value at '+path+': '+type(item).__name__)
    walk(plain(value),'root')
    by_device={}
    for storage in storages.values():
        by_device[storage['device']]=by_device.get(storage['device'],0)+storage['bytes']
    return dict(tensors=rows,logical_tensor_references=len(rows),unique_tensor_objects=len(objects),
        unique_tensor_storages=len(storages),logical_tensor_bytes=sum(r['logical_bytes'] for r in rows),
        backing_storage_bytes_by_device=by_device,storages=list(storages.values()),
        numpy_backing_bytes=sum(r['bytes'] for r in arrays.values()),
        any_meta_tensors=any(r['device']=='meta' for r in rows),
        measured_allocator_peak=False,tensor_values_read=False,tensor_copies_performed=0)


def state_groups(owner,inputs):
    """The exact groups counted by the accepted S copy_budget, before a pair."""
    return dict(native={key:getattr(owner.net,key) for key in WC_FIELDS if hasattr(owner.net,key)},
        solver={key:value for key,value in vars(owner.model.sample_scheduler).items() if not callable(value)},
        buffers=list(owner.net.buffers()),owner_history=owner.history,readout_history=owner.readout.history,
        calibrators=[vars(c) for c in owner.readout.calibrators],paired_inputs=inputs[:3],
        conditions=[vars(c) for c in inputs[3]])


def before_pair_inventory(owner,inputs):
    groups=state_groups(owner,inputs)
    report=inventory(groups)
    require(report['logical_tensor_bytes']==tensor_bytes(plain(groups)),
            'S inventory does not reconcile with the deployed logical byte counter')
    report.update(group_inventories={name:inventory(value) for name,value in groups.items()},
        logical_copy_guard_bytes=8*report['logical_tensor_bytes'],
        native_field_names=sorted(groups['native']),
        solver_field_names=sorted(groups['solver']),
        captured_before_pair=True,completed_parent_pairs=owner.readout.completed)
    return report


def check_limits(report,limits):
    """Future production entry checks metadata before allocating any snapshots."""
    require(report['any_meta_tensors'] is False,'A meta inventory cannot admit an actual S transaction')
    require(report['logical_copy_guard_bytes']<=limits['logical_copy_guard_bytes'],
            'S complete logical copy budget exceeds its registered cap')
    buffers=report['group_inventories']['buffers']
    require(buffers['logical_tensor_bytes']<=limits['mutable_buffer_bytes'],
            'S mutable buffers exceed their registered cap')
    for device,nbytes in report['backing_storage_bytes_by_device'].items():
        kind=device.split(':')[0]
        require(kind in limits['live_backing_storage_bytes_by_device_kind']
                and nbytes<=limits['live_backing_storage_bytes_by_device_kind'][kind],
                'S live backing storage exceeds its registered device cap')
    return dict(accepted=True,logical_copy_guard_bytes=report['logical_copy_guard_bytes'],
        tensor_values_read=False,snapshot_or_device_peak_established=False)
