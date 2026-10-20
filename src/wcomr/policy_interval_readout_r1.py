"""Source-exact WC C and beta1 A heads on current, paid teacher probes.

No deep teacher is run for a candidate. Original WC skip statements execute on
an isolated cache view, never on the reference model's mutable cache. The two
post-RF alpha implementations pay their own real heads and fusion.
"""
import ast
import copy
from types import SimpleNamespace
import torch

from .cfg_paired_probe_forward import _function, _compile, WC_PATH, WC_SHA
from .cfg_guided_w1_forward import compile_output_denoise, compile_collection
from .cfg_guided_w1_outputs import unit_increment_residual, shared_output_fusion


def compile_skip(runtime, namespace):
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    found = [n for n in ast.walk(original) if isinstance(n, ast.If)
             and ast.unparse(n.test) == 'skip_forward']
    if len(found) != 1:
        raise ValueError('One pinned complete skip branch required')
    body = copy.deepcopy(found[0].body)
    target = 'self.previous_internal_states[current_idx] = test_x'
    indices = [i for i, n in enumerate(body) if ast.unparse(n) == target]
    if len(indices) != 1:
        raise ValueError('Exact prewarp boundary required')
    body.insert(indices[0], ast.parse('_prewarp = x_B_T_H_W_D').body[0])
    node = ast.parse('def source_C(self, ori_x, test_x, T):\n    pass').body[0]
    node.body = ast.parse('current_idx = self.cnt % 2\nx_B_T_H_W_D = ori_x\nresidual_x = self.residual_cache[current_idx]').body + body
    node.body += ast.parse('return _prewarp, x_B_T_H_W_D').body
    inverse = copy.deepcopy(body)
    inverse = [n for n in inverse if ast.unparse(n) != '_prewarp = x_B_T_H_W_D']
    if ast.dump(ast.Module(body=inverse, type_ignores=[])) != ast.dump(ast.Module(body=found[0].body, type_ignores=[])):
        raise ValueError('C implementation changed outside one read-only observation')
    return _compile(node, namespace, WC_PATH+'#complete-isolated-C'), dict(
        full_C_skip_branch_inverse_AST_equal=True, source_sha256=WC_SHA,
        mutation_target='ISOLATED_SOURCE_VIEW_ONLY', protected_forward_modified=False)


def guided(pair):
    return pair[0] + 7*(pair[0]-pair[1])


class ReadoutKernel:
    def __init__(self, model, runtime, wc, rf, warp):
        self.model, self.net, self.warp = model, model.net, warp
        self.C, self.proof = compile_skip(runtime, vars(wc))
        self.to_velocity, self.RF_proof = compile_output_denoise(runtime, rf)

    @torch.no_grad()
    def run(self, label, *, source, current, pair_inputs):
        device=pair_inputs[1].device
        devices=[device.index if device.index is not None else torch.cuda.current_device()] if device.type=='cuda' else []
        with torch.random.fork_rng(devices=devices):
            return self._run(label,source=source,current=current,pair_inputs=pair_inputs)

    @torch.no_grad()
    def _run(self, label, *, source, current, pair_inputs):
        if label not in ('C', 'A_HALF', 'A_ONE'):
            raise ValueError('Every requested alpha has its own real execution')
        noise, latent, timestep, conditions = pair_inputs
        C, Phi = [], []
        for b in (0, 1):
            row = current[b]; s = source[b]
            proxy = SimpleNamespace(cnt=b, residual_cache=[None,None],
                previous_input=[None,None], previous_internal_states=[None,None],
                residual_window=[[],[]], probe_residual_window=[[],[]],
                worldcache_osi_enabled=self.net.worldcache_osi_enabled,
                worldcache_flow_enabled=self.net.worldcache_flow_enabled,
                worldcache_flow_scale=self.net.worldcache_flow_scale)
            proxy.residual_cache[b]=s['residual']
            proxy.residual_window[b]=s['residual_window']
            proxy.probe_residual_window[b]=s['probe_window']
            _, hidden = self.C(proxy, row['original'], row['probe'], row['original'].shape[1])
            head=self.net.unpatchify(self.net.final_layer(hidden,row['embedding'],
                adaln_lora_B_T_3D=row['adaln']))
            C.append(self.to_velocity(self.model,noise,latent,timestep,conditions[b],_supplied_net_output=head))
            if label!='C':
                residual=unit_increment_residual(current_probe=row['probe']-row['original'],
                    anchor_probe=s['probe'],anchor_residual=s['residual'])
                corrected=self.warp(proxy,row['original']+residual,s['residual'],row['original'].shape[1])
                proposed=self.net.unpatchify(self.net.final_layer(corrected,row['embedding'],
                    adaln_lora_B_T_3D=row['adaln']))
                Phi.append(self.to_velocity(self.model,noise,latent,timestep,conditions[b],_supplied_net_output=proposed))
        C=tuple(C)
        if label=='C':return C, C, None
        Phi=tuple(Phi)
        return shared_output_fusion(C,Phi,.5 if label=='A_HALF' else 1.), C, Phi


@torch.no_grad()
def reduce_outputs(C, Phi, D, half):
    """Actual guided vectors and independent FP64 reductions, not hidden MSE."""
    values=[guided(p).detach().cpu().clone() for p in (C,Phi,D,half)]
    if any(not torch.isfinite(v).all() for v in values):
        raise ValueError('Nonfinite actual guided output')
    c,p,d,h=values;e=c.double()-d.double();delta=p.double()-c.double()
    e2=e.square().mean().item();ed=(e*delta).mean().item();d2=delta.square().mean().item()
    direct=(h.double()-d.double()).square().mean().item()
    predicted=e2+ed+.25*d2
    # FP32 branch fusion/CFG rounding is retained and bounded, never relabelled
    # as bit-exact arithmetic in a real-valued quadratic coordinate.
    scale=max(float(v.abs().max()) for v in values)
    bound=64*torch.finfo(torch.float32).eps*max(1.,scale)
    if float((h-(c+.5*(p-c))).abs().max())>bound:
        raise ValueError('Actual post-RF fusion violates its stated rounding bound')
    return dict(e2=e2,ed=ed,d2=d2,actual_half_MSE=direct,
        quadratic_half_MSE=predicted,FP32_fusion_absolute_bound=bound,
        fusion_contract='VALIDATED_GUIDED_OUTPUT_LINEAR_BLEND'), dict(C=c,Phi=p,A_HALF=h)
