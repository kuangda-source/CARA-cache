"""E5 independent CPU prototype: elide a redundant alpha=1 C head.

This version deliberately changes the bookkeeping value previous_output to
the selected candidate. It does not claim full cross-version state identity,
real-model acceptance, latency improvement, or support for stateful heads.
The legacy compiler/readout and all in-flight payloads remain immutable.
"""
import ast
import copy
import hashlib
import inspect
import math
from pathlib import Path
from types import CodeType, MappingProxyType
from typing import Optional

import torch
from einops import rearrange

from . import cfg_guided_w1_forward as legacy_forward
from .cfg_guided_w1_deployment import GuidedW1Readout, alpha_at
from .partial_mlp_guided_readout import SemanticPartialReadout, GuidedPartialDeployment

NATIVE_PATH = 'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
NATIVE_SHA = 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'
VERSION = 'E5_EARLY_HEAD_ELISION_CPU_R1'


def code_identity(code):
    """Bytecode and constants, including nested functions; ignore line origins."""
    if not isinstance(code, CodeType):
        return code
    return (code.co_code, tuple(code_identity(c) for c in code.co_consts),
            code.co_names, code.co_varnames, code.co_argcount,
            code.co_kwonlyargcount, code.co_posonlyargcount, code.co_flags)


def native_final_layer(runtime):
    path = Path(runtime)/NATIVE_PATH
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != NATIVE_SHA:
        raise ValueError('Pinned native FinalLayer source changed')
    nodes = [n for n in ast.parse(raw).body
             if isinstance(n, ast.ClassDef) and n.name == 'FinalLayer']
    if len(nodes) != 1:
        raise ValueError('Native FinalLayer class is ambiguous')
    namespace = dict(torch=torch, nn=torch.nn, math=math, Optional=Optional,
                     rearrange=rearrange, amp=torch.amp)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(path)+'#E5_pinned_native_FinalLayer', 'exec'), namespace)
    return namespace['FinalLayer']


class PureNativeHeadGuard:
    """Refuse unsupported dynamic head state before any candidate executes.

    The unpatchify binding is immutable in this CPU fixture. Production native
    unpatchify and complete real-policy equivalence require a separate card.
    """
    def __init__(self, net, runtime):
        self.net, self.head = net, net.final_layer
        self.expected = native_final_layer(runtime)
        self.forward_identity = code_identity(self.expected.forward.__code__)
        self.unpatchify = net.unpatchify
        self.parameters = tuple((id(p), p._version) for p in net.parameters())
        self.modules = tuple((n, id(m), type(m)) for n, m in self.head.named_modules())
        self.flags = tuple(getattr(self.head, n) for n in
            ('use_wan_fp32_strategy','hidden_size','n_adaln_chunks','use_adaln_lora','adaln_lora_dim'))
        self.validate()

    def validate(self):
        if self.net.final_layer is not self.head or self.net.unpatchify is not self.unpatchify:
            raise ValueError('Head/unpatchify identity changed')
        if (tuple((id(p), p._version) for p in self.net.parameters()) != self.parameters
                or tuple((n,id(m),type(m)) for n,m in self.head.named_modules()) != self.modules):
            raise ValueError('Model parameters/head topology changed')
        if (code_identity(type(self.head).forward.__code__) != self.forward_identity
                or 'forward' in self.head.__dict__):
            raise ValueError('Only pinned native FinalLayer forward is supported')
        flags = tuple(getattr(self.head, n) for n in
            ('use_wan_fp32_strategy','hidden_size','n_adaln_chunks','use_adaln_lora','adaln_lora_dim'))
        if flags != self.flags or flags[0] or flags[3]:
            raise ValueError('CPU prototype requires unchanged ordinary native head mode')
        if list(self.head.buffers()) or any(m.training for m in self.head.modules()):
            raise ValueError('Stateful buffers or training head is unsupported')
        permitted = (type(self.head), torch.nn.LayerNorm, torch.nn.Linear,
                     torch.nn.Sequential, torch.nn.SiLU)
        for module in self.head.modules():
            if type(module) not in permitted or 'forward' in module.__dict__:
                raise ValueError('Unsupported head child module/override')
            for name in ('_forward_hooks','_forward_pre_hooks','_backward_hooks','_backward_pre_hooks'):
                if getattr(module,name,{}):
                    raise ValueError('Head hooks are unsupported')
        global_module = torch.nn.modules.module
        for name in ('_global_forward_hooks','_global_forward_pre_hooks',
                     '_global_backward_hooks','_global_backward_pre_hooks'):
            if getattr(global_module,name,{}):
                raise ValueError('Global hooks are unsupported')


def _insert_head_choice(node):
    original = copy.deepcopy(node)
    head = 'x_B_T_H_W_O = self.final_layer(x_B_T_H_W_D, t_embedding_B_T_D, adaln_lora_B_T_3D=adaln_lora_B_T_3D)'
    unpatch = 'x_B_C_Tt_Hp_Wp = self.unpatchify(x_B_T_H_W_O)'
    hits = 0
    class Insert(ast.NodeTransformer):
        def generic_visit(self, n):
            nonlocal hits
            n = super().generic_visit(n)
            for field, value in ast.iter_fields(n):
                if not isinstance(value, list):
                    continue
                for i in range(len(value)-1):
                    if (isinstance(value[i],ast.Assign) and isinstance(value[i+1],ast.Assign)
                            and ast.unparse(value[i]) == head and ast.unparse(value[i+1]) == unpatch):
                        hits += 1
                        injected = ast.parse(
                            '_e5_head = _e5_choose_head(self, current_idx)\n'
                            'if _e5_head is None:\n    pass\n'
                            'else:\n    x_B_C_Tt_Hp_Wp = _e5_head').body
                        injected[1].body = value[i:i+2]
                        setattr(n,field,value[:i]+injected+value[i+2:])
                        break
            return n
    modified = Insert().visit(copy.deepcopy(node))
    if hits != 1:
        raise ValueError('Unique adjacent native head/unpatchify site required')
    class Undo(ast.NodeTransformer):
        def visit_Assign(self,n):
            if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='_e5_head':
                return None
            return self.generic_visit(n)
        def visit_If(self,n):
            if ast.unparse(n.test)=='_e5_head is None':
                return [self.visit(x) for x in n.body]
            return self.generic_visit(n)
    inverse = Undo().visit(copy.deepcopy(modified))
    if ast.dump(inverse,include_attributes=False) != ast.dump(original,include_attributes=False):
        raise ValueError('Head transform changed other source statements')
    return modified


def compile_early_head_collection(runtime, wc, rf, collector, *, dense_context=None):
    """Derive legacy compiler with one independently invertible insertion."""
    readout = getattr(collector, 'readout', collector)
    readout.e5_guard = PureNativeHeadGuard(collector.net, runtime)
    source = ast.parse(inspect.getsource(legacy_forward.compile_collection)).body[0]
    original = copy.deepcopy(source)
    sites = []
    for i,n in enumerate(source.body):
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets):
            sites.append(i)
    if len(sites)!=1:
        raise ValueError('Legacy helper binding changed')
    i=sites[0]
    source.body.insert(i,ast.parse('node = _e5_transform(node)').body[0])
    source.body.insert(i+2,ast.parse("helpers['_e5_choose_head'] = _e5_choose").body[0])
    inverse=copy.deepcopy(source);inverse.body.pop(i+2);inverse.body.pop(i)
    if ast.dump(inverse,include_attributes=False)!=ast.dump(original,include_attributes=False):
        raise ValueError('Legacy compiler derivation changed original body')
    namespace=dict(vars(legacy_forward),_e5_transform=_insert_head_choice,
                   _e5_choose=readout.choose_original_head)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[source],type_ignores=[])),
                 __file__+'#source_derived_legacy_compiler','exec'),namespace)
    net,denoise,proof=namespace['compile_collection'](runtime,wc,rf,collector,dense_context=dense_context)
    return net,denoise,MappingProxyType(dict(proof,early_head_version=VERSION,
        compiler_derivation_inverse_AST_equal=True,head_insertion_inverse_AST_equal=True,
        bookkeeping_field_changed='previous_output',real_model_acceptance=False))


class ElidingReadoutMixin:
    e5_guard = None

    def hidden(self,*args,**kwargs):
        self.e5_guard.validate()
        return super().hidden(*args,**kwargs)

    def semantic_hidden(self,*args,**kwargs):
        self.e5_guard.validate()
        return super().semantic_hidden(*args,**kwargs)

    def choose_original_head(self,net,branch):
        step=self._branch(net,branch)
        self.e5_guard.validate()
        cur=self.current;entry=cur['branches'].get(branch)
        if entry is None or entry.get('e5_choice_seen'):
            raise ValueError('Exactly one early-head choice per actual branch required')
        entry['e5_choice_seen']=True
        if entry['action']!='C' or alpha_at(self.method,step)!=1 or entry['proposed_head'] is None:
            entry['original_head_elided']=False
            return None
        value=entry['proposed_head'];latent=cur['latent']
        if (value.shape!=latent.shape or value.dtype!=latent.dtype or value.device!=latent.device
                or not torch.isfinite(value).all()):
            raise ValueError('Elided original output requires finite coordinate-compatible candidate')
        entry['original_head_elided']=True
        return value

    def end(self,*args,**kwargs):
        branches=self.current['branches']
        if set(branches)!={0,1} or not all(b.get('e5_choice_seen') for b in branches.values()):
            raise ValueError('Both actual branch head choices required')
        mask=[branches[b]['original_head_elided'] for b in (0,1)]
        paid=sum(branches[b]['extra_heads'] for b in (0,1))
        value=super().end(*args,**kwargs)
        row=self.history[-1]
        row.update(early_head_version=VERSION,original_head_elided=mask,
            original_head_calls=2-sum(mask),candidate_head_calls=paid,
            total_head_calls=2+paid-sum(mask),extra_heads=paid-sum(mask),
            previous_output_contains_selected_candidate_when_elided=True)
        return value

    def finish(self):
        result=super().finish()
        result.update(candidate_original_head_elision_implemented=True,early_head_version=VERSION,
            original_head_calls=sum(r['original_head_calls'] for r in self.history),
            candidate_head_calls=sum(r['candidate_head_calls'] for r in self.history),
            total_head_calls=sum(r['total_head_calls'] for r in self.history),
            changed_bookkeeping_field='previous_output',full_cross_version_state_identity=False)
        return result


class EarlyHeadReadout(ElidingReadoutMixin,GuidedW1Readout):
    pass


class EarlyHeadSemanticReadout(ElidingReadoutMixin,SemanticPartialReadout):
    pass


class EarlyHeadPartialDeployment(GuidedPartialDeployment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.readout=EarlyHeadSemanticReadout(self,method=kwargs['a_method'])
