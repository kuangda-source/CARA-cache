"""Independent E5 complete-sampler owner with explicit paid-head records.

Legacy samplers/controllers remain source-bound; no production or GPU benefit
is established by this module. Ordinary and AdaLN native heads are supported,
with an explicit CPU-only declared unpatchify boundary for the Toy fixture.
"""
import ast
import copy
import inspect
import functools
import hashlib
import importlib
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import torch

from . import early_head_elision_cpu_r1 as prototype
from . import partial_mlp_deployment_sampling as p0
from .partial_mlp_guided_sampling import GuidedSamplingOwner
from .partial_mlp_guided_readout import GuidedPartialDeployment
from .source_aware_partial_sampling import DynamicSamplingOwner
from .source_aware_current_birth_sampling_r2 import CurrentBirthDeployment, CurrentBirthSamplingOwner
from .source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner
from .source_aware_phase_sampling import bind_globals

VERSION='E5_COMPLETE_SAMPLER_EARLY_HEAD_R3'


def same_binding(a,b):
    return (getattr(a,'__self__',None) is getattr(b,'__self__',None)
            and getattr(a,'__func__',a) is getattr(b,'__func__',b))


def derive_method(original,edits,helpers):
    source=dedent(inspect.getsource(original));changed=source
    for old,new in edits:
        if changed.count(old)!=1:raise ValueError('E5 source derivation site changed: '+old[:60])
        changed=changed.replace(old,new)
    inverse=changed
    for old,new in reversed(edits):inverse=inverse.replace(new,old)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('E5 owner derivation changed unregistered source')
    namespace={**original.__globals__,**helpers}
    exec(compile(changed,__file__+'#source_derived_'+original.__name__,'exec'),namespace)
    return namespace[original.__name__]


_guard_validate=derive_method(prototype.PureNativeHeadGuard.validate,[
    ('self.net.final_layer is not self.head','self.net.final_layer is not self.call_head'),
    ('self.net.unpatchify is not self.unpatchify','not _e5_same_binding(self.net.unpatchify,self.unpatchify)'),
    ('flags != self.flags or flags[0] or flags[3]','flags != self.flags')],{'_e5_same_binding':same_binding})


class NativeHeadGuard(prototype.PureNativeHeadGuard):
    """Keep the actual native checkpoint call, pin its contract and leaf body."""
    def __init__(self,net,runtime,*,declared_CPU_unpatchify=False):
        cp=importlib.import_module('torch.distributed.algorithms._checkpoint.checkpoint_wrapper')
        import torch.utils.checkpoint as checkpoint
        self.declared_CPU_unpatchify=declared_CPU_unpatchify
        if type(declared_CPU_unpatchify) is not bool:raise ValueError('Explicit unpatchify contract required')
        self.net,self.call_head=net,net.final_layer
        wrapper_path=Path(inspect.getsourcefile(cp.CheckpointWrapper))
        if hashlib.sha256(wrapper_path.read_bytes()).hexdigest()!='df706f293970d4177f2ba2133c9e5ffb4e98e424df56c7a42a450a0007629b08':
            raise ValueError('Pinned Torch checkpoint wrapper source changed')
        if hashlib.sha256(Path(inspect.getsourcefile(checkpoint)).read_bytes()).hexdigest()!='b07acb21f5c727f3eace16249ca126a7c8a0ac8d97c83f2a13fff1b5a59a360f':
            raise ValueError('Pinned Torch checkpoint function source changed')
        self.wrapper_class,self.checkpoint_function,self.checkpoint_impl=cp.CheckpointWrapper,checkpoint.checkpoint,cp.CheckpointImpl.NO_REENTRANT
        if type(self.call_head) is not self.wrapper_class:
            raise ValueError('Production E5 requires the actual native checkpoint wrapper')
        self.head=self.call_head._checkpoint_wrapped_module
        self.expected=prototype.native_final_layer(runtime)
        self.forward_identity=prototype.code_identity(self.expected.forward.__code__)
        self.unpatchify=net.unpatchify
        self.parameters=tuple((id(p),p._version) for p in net.parameters())
        self.modules=tuple((n,id(m),type(m)) for n,m in self.head.named_modules())
        self.wrapper_modules=tuple((n,id(m),type(m)) for n,m in self.call_head.named_modules())
        self.flags=tuple(getattr(self.head,n) for n in
            ('use_wan_fp32_strategy','hidden_size','n_adaln_chunks','use_adaln_lora','adaln_lora_dim'))
        self.child_config=self.config()
        raw=(Path(runtime)/prototype.NATIVE_PATH).read_text();tree=ast.parse(raw)
        functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict2_2B_720_context_fn_aggressive']
        classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MiniTrainDIT']
        if len(classes)!=1 or len(functions)!=1:raise ValueError('Pinned native head/checkpoint context changed')
        methods=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=='unpatchify']
        if len(methods)!=1:raise ValueError('Pinned native unpatchify differs')
        namespace=dict(prototype.__dict__)
        exec(compile(ast.Module(body=methods+functions,type_ignores=[]),__file__+'#native_head_contract','exec'),namespace)
        self.context_code=prototype.code_identity(namespace['predict2_2B_720_context_fn_aggressive'].__code__)
        root=next(n for n in ast.parse(wrapper_path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='CheckpointWrapper')
        wrapper_namespace=dict(vars(cp))
        exec(compile(ast.Module(body=[root],type_ignores=[]),__file__+'#native_wrapper_class','exec'),wrapper_namespace)
        self.wrapper_forward_code=prototype.code_identity(wrapper_namespace['CheckpointWrapper'].forward.__code__)
        current=getattr(net.unpatchify,'__func__',net.unpatchify)
        native=prototype.code_identity(current.__code__)==prototype.code_identity(namespace['unpatchify'].__code__)
        if not native and not declared_CPU_unpatchify:
            raise ValueError('Production owner requires pinned native unpatchify body')
        self.unpatchify_contract='DECLARED_CPU_TEST_BOUNDARY' if not native else 'PINNED_NATIVE_UNPATCHIFY'
        self.validate()

    def config(self):
        return tuple((name,tuple((k,repr(getattr(m,k,None))) for k in
            ('eps','normalized_shape','elementwise_affine','in_features','out_features','inplace')))
            for name,m in self.head.named_modules())

    def validate(self):
        _guard_validate(self)
        root=self.call_head;fn=root.checkpoint_fn
        if (type(root) is not self.wrapper_class or root._checkpoint_wrapped_module is not self.head
                or root.checkpoint_impl is not self.checkpoint_impl or type(fn) is not functools.partial
                or fn.func is not self.checkpoint_function or fn.args or set(fn.keywords)!={'use_reentrant','context_fn','preserve_rng_state'}
                or fn.keywords['use_reentrant'] is not False or fn.keywords['preserve_rng_state'] is not False
                or fn.keywords['context_fn'].__closure__
                or prototype.code_identity(fn.keywords['context_fn'].__code__)!=self.context_code
                or prototype.code_identity(type(root).forward.__code__)!=self.wrapper_forward_code
                or 'forward' in vars(root)
                or tuple((n,id(m),type(m)) for n,m in root.named_modules())!=self.wrapper_modules):
            raise ValueError('Native selective checkpoint head contract changed')
        for module in root.modules():
            if (type(module).__call__ is not torch.nn.Module.__call__
                    or type(module)._call_impl is not torch.nn.Module._call_impl
                    or getattr(module,'_compiled_call_impl',None) is not None
                    or module.training or list(module.buffers())
                    or any(getattr(module,n,{}) for n in ('_forward_hooks','_forward_pre_hooks','_backward_hooks','_backward_pre_hooks'))):
                raise ValueError('Only uncompiled, eval, hook/buffer-free native head calls supported')
        if self.config()!=self.child_config:
            raise ValueError('Head child numerical configuration changed')


def native_checkpoint_head(runtime,*args,**kwargs):
    from torch.distributed.algorithms._checkpoint.checkpoint_wrapper import checkpoint_wrapper
    from cosmos_predict2._src.predict2.networks.minimal_v4_dit import predict2_2B_720_context_fn_aggressive
    return checkpoint_wrapper(prototype.native_final_layer(runtime)(*args,**kwargs),
        context_fn=predict2_2B_720_context_fn_aggressive,preserve_rng_state=False).eval()


class RecordedSemanticReadout(prototype.EarlyHeadSemanticReadout):
    paid_head_recorder=None

    def semantic_hidden(self,net,skipped,branch,*values):
        if torch.is_grad_enabled():raise ValueError('E5 native checkpoint head is inference-only')
        super().semantic_hidden(net,skipped,branch,*values)
        if self.current['branches'][branch]['extra_heads']:
            self.paid_head_recorder(branch,'CANDIDATE')

    def choose_original_head(self,net,branch):
        if torch.is_grad_enabled():raise ValueError('E5 native checkpoint head is inference-only')
        value=super().choose_original_head(net,branch)
        if value is None:self.paid_head_recorder(branch,'ORIGINAL')
        return value

    def end(self,*args,**kwargs):
        value=super().end(*args,**kwargs);self.history[-1]['early_head_version']=VERSION
        return value

    def finish(self):
        result=super().finish();result['early_head_version']=VERSION
        result['native_head_contract']={'use_adaln_lora':self.e5_guard.head.use_adaln_lora,
            'use_wan_fp32_strategy':self.e5_guard.head.use_wan_fp32_strategy,
            'unpatchify':self.e5_guard.unpatchify_contract,
            'checkpoint_wrapper':'PINNED_NATIVE_NON_REENTRANT_SELECTIVE'}
        return result


class FixedEarlyHeadDeployment(GuidedPartialDeployment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.readout=RecordedSemanticReadout(self,method=kwargs['a_method'])


class CurrentBirthEarlyHeadDeployment(CurrentBirthDeployment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.readout=RecordedSemanticReadout(self,method=kwargs['a_method'])


def compile_collection(runtime,wc,rf,collector,*,dense_context=None):
    allow=getattr(collector.model,'E5_declared_CPU_unpatchify',False)
    guard=lambda net,runtime:NativeHeadGuard(net,runtime,declared_CPU_unpatchify=allow)
    compiler=bind_globals(prototype.compile_early_head_collection,{'PureNativeHeadGuard':guard})
    return compiler(runtime,wc,rf,collector,dense_context=dense_context)


def compile_partial(runtime,wc,rf,deployment):
    return compile_collection(runtime,wc,rf,deployment,dense_context=deployment.dense_context)


_p0_constructor=bind_globals(p0.SamplingOwner.__init__,{'compile_partial_deployment':compile_partial})
_guided_constructor=derive_method(GuidedSamplingOwner.__init__,[
    ('self.hooks.append(self.net.final_layer.register_forward_hook(observe_head))',
     '# E5 paid heads are recorded at the source choice/candidate sites.')],
    {'p0':SimpleNamespace(SamplingOwner=SimpleNamespace(__init__=_p0_constructor)),
     'GuidedPartialDeployment':FixedEarlyHeadDeployment})
_dynamic_constructor=bind_globals(DynamicSamplingOwner.__init__,{
    'GuidedSamplingOwner':SimpleNamespace(__init__=_guided_constructor)})
_current_constructor=bind_globals(CurrentBirthSamplingOwner.__init__,{
    'base':SimpleNamespace(DynamicSamplingOwner=SimpleNamespace(__init__=_dynamic_constructor)),
    'WorkingEpochDeployment':CurrentBirthEarlyHeadDeployment})


def attach_recorder(owner):
    readout=owner.deployment.readout
    def record(branch,role):
        owner.head_calls.append({'step':owner.step,'slot':branch,'role':role,'head_version':VERSION})
    readout.paid_head_recorder=record


class FixedEarlyHeadSamplingOwner(GuidedSamplingOwner):
    def __init__(self,*args,**kwargs):
        _guided_constructor(self,*args,**kwargs);attach_recorder(self)

    def installation(self):
        return super().installation()+(VERSION,id(self.deployment.readout.e5_guard),
                                      id(self.deployment.readout.paid_head_recorder))


class CurrentBirthEarlyHeadSamplingOwner(CPUStorageSamplingOwner):
    def __init__(self,*args,**kwargs):
        _current_constructor(self,*args,**kwargs);attach_recorder(self)

    def installation(self):
        return super().installation()+(VERSION,id(self.deployment.readout.e5_guard),
                                      id(self.deployment.readout.paid_head_recorder))


DERIVATION_PROOFS={'legacy_methods_and_controllers_unmodified':True,
    'p0_constructor_global_binding_only':True,'guided_cost_hook_inverse_source_AST_equal':True,
    'dynamic_and_current_birth_constructor_bytecode_unchanged':True,
    'head_choice_source_and_RF_body_from_accepted_prototype':True,
    'old_owned_and_CPU_storage_snapshot_body_unchanged':True,
    'production_head_and_unpatchify_or_real_model_acceptance':False}
