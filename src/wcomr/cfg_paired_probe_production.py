"""Actual-module namespaces and explicit observations for the paired prototype.

Compile and CPU integration only. This does not install a model forward, admit a
GPU, choose a risk policy, or provide arbitrary-fault rollback. An observer is
trusted instrumentation; its real-model overhead and non-interference need the
same-action controls before production use.
"""
import builtins
import dis
import hashlib
from pathlib import Path
from types import CodeType, MappingProxyType

from .cfg_paired_probe_forward import (
    compile_core, PairedProbeExecutor, WC_PATH, WC_SHA, RF_PATH, RF_SHA,
)


def global_names(code):
    names={i.argval for i in dis.get_instructions(code) if i.opname=='LOAD_GLOBAL'}
    for value in code.co_consts:
        if isinstance(value,CodeType):names.update(global_names(value))
    return sorted(names)


def descriptor(value):
    return {'type':type(value).__module__+'.'+type(value).__qualname__,
            'module':getattr(value,'__module__',getattr(value,'__name__',None)),
            'qualname':getattr(value,'__qualname__',None)}


def _origin(module,runtime,relative,digest):
    path=Path(runtime)/relative
    if Path(module.__file__).resolve()!=path.resolve() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise ValueError('Actual paired production module origin differs: '+relative)


def _bindings(function,actual,overrides):
    observed={}
    for name in global_names(function.__code__):
        if name in overrides:
            if function.__globals__.get(name) is not overrides[name]:
                raise ValueError('Explicit paired compiler helper binding differs: '+name)
            observed[name]={'binding':'explicit_compiler_helper',**descriptor(overrides[name])}
        elif name in actual:
            if function.__globals__.get(name) is not actual[name]:
                raise ValueError('Actual production global binding differs: '+name)
            observed[name]={'binding':'actual_module_global',**descriptor(actual[name])}
        elif hasattr(builtins,name):
            if name in function.__globals__:
                raise ValueError('Production builtin was shadowed: '+name)
            observed[name]={'binding':'builtin',**descriptor(getattr(builtins,name))}
        else:
            raise ValueError('Unresolved actual production global: '+name)
    return observed


def compile_production(runtime,wc_module,rf_module,*,before=None,after=None):
    """Use each original function's own globals; observations wrap the net call."""
    _origin(wc_module,runtime,WC_PATH,WC_SHA);_origin(rf_module,runtime,RF_PATH,RF_SHA)
    wc_function=wc_module.worldcache_mini_train_dit_forward
    rf_function=rf_module.Video2WorldModelRectifiedFlow.denoise
    if wc_function.__globals__ is not vars(wc_module) or rf_function.__globals__ is not vars(rf_module):
        raise ValueError('Actual original function namespace differs')
    if (Path(wc_function.__code__.co_filename).resolve()!=(Path(runtime)/WC_PATH).resolve()
            or Path(rf_function.__code__.co_filename).resolve()!=(Path(runtime)/RF_PATH).resolve()):
        raise ValueError('Actual original function body origin differs')
    net,denoise,original_proof=compile_core(runtime,dict(vars(wc_module)))
    # The prototype takes one test namespace. Production RF globals must come
    # from its own actual module, not accidental names in the WC namespace.
    for name in global_names(rf_function.__code__):
        if name in vars(rf_module):denoise.__globals__[name]=vars(rf_module)[name]
        elif name in denoise.__globals__:del denoise.__globals__[name]
    denoise.__globals__['__name__']=rf_module.__name__
    denoise.__globals__['__file__']=rf_module.__file__
    denoise.__module__=rf_module.__name__
    net_proof=_bindings(net,vars(wc_module),{'_paid_probe':net.__globals__['_paid_probe']})
    if before is not None and not callable(before):raise ValueError('Before observer must be callable or absent')
    if after is not None and not callable(after):raise ValueError('After observer must be callable or absent')
    def observed_net(model_net,*args,**kwargs):
        slot=int(model_net.cnt)%2
        if before is not None:before(model_net,slot,args,kwargs)
        output=yield from net(model_net,*args,**kwargs)
        if after is not None:after(model_net,slot,output)
        return output
    target=net if before is None and after is None else observed_net
    denoise.__globals__['_paired_net']=target
    rf_proof=_bindings(denoise,vars(rf_module),{'_paired_net':target})
    proof={**dict(original_proof),'production_WC_globals':net_proof,'production_RF_globals':rf_proof,
           'actual_original_WC_RF_function_origins_verified':True,
           'explicit_net_observers':before is not None or after is not None,
           'outer_forward_wrapper_is_not_an_observer':True,
           'real_model_output_or_latency_claim':False}
    return net,denoise,MappingProxyType(proof)


class ProductionPairedExecutor(PairedProbeExecutor):
    """Reject the exact attribute wrappers bypassed by compiled function bodies."""
    def __init__(self,model,denoise,torch,*,wc_forward,rf_denoise):
        super().__init__(model,denoise,torch)
        self.wc_forward=wc_forward;self.rf_denoise=rf_denoise

    def _preflight(self):
        super()._preflight()
        if getattr(self.net.forward,'__self__',None) is not self.net or getattr(self.net.forward,'__func__',None) is not self.wc_forward:
            raise ValueError('Wrapped or changed net.forward would be bypassed')
        if getattr(self.model.denoise,'__self__',None) is not self.model or getattr(self.model.denoise,'__func__',None) is not self.rf_denoise:
            raise ValueError('Wrapped or changed model.denoise would be bypassed')
