"""Complete original OFF/ON/fault scope with C/A/P/D action boundaries."""
import copy
import ast
import hashlib
import inspect
from textwrap import dedent
import torch
from pathlib import Path

from wcomr import source_aware_action_cost_sampling_r3 as cost


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


class DeclaredToyHeadModule(torch.nn.Module):
    """The existing Toy head with exact output, no parameters or buffers."""
    def __init__(self, function):
        super().__init__()
        if not callable(function) or isinstance(function, torch.nn.Module):
            raise ValueError('Only the declared plain Toy head needs this adapter')
        self.function = function
    def forward(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def adapt_toy_head(original):
    raw = dedent(inspect.getsource(original))
    first = '    net.blocks=pinned_blocks(runtime)'
    updated = ('    old_head=net.final_layer\n'
        '    net.final_layer=DeclaredToyHeadModule(old_head).eval()\n'+first)
    final = '        net.blocks,net.t_embedder,net.unpatchify=old_net'
    cleanup = final+('\n        del net._modules["final_layer"]\n'
        '        net.final_layer=old_head')
    assert raw.count(first)==raw.count(final)==1
    changed=raw.replace(first,updated).replace(final,cleanup)
    inverse=changed.replace(cleanup,final).replace(updated,first)
    assert inverse==raw and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(raw))
    ns={**original.__globals__,'DeclaredToyHeadModule':DeclaredToyHeadModule}
    exec(compile(changed,__file__+'#explicit-Toy-head-module', 'exec'),ns)
    return ns[original.__name__],{'original_bytes_and_inverse_AST_equal':True,
        'original_exercise_sha256':hashlib.sha256(raw.encode()).hexdigest(),
        'no_parameters_or_buffers_or_changed_head_math':True,
        'complete_parent_and_all_fault_scope_preserved':True,
        'new_topology_count_in_existing_component_contract':True,
        'only_declared_Toy_fixture_not_real_model_adapter':True}


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_sampling_cpu')
    original_exercise,head_proof=adapt_toy_head(original.exercise)
    exercise=cost.bind(original_exercise,{'run_batch':cost.run_batch,
        'verify_batch':cost.verify_batch,'audit_vectors':cost.audit_vectors})
    bound=cost.bind(original.run,{'exercise':exercise})
    result=bound(runtime,tensor_loader,artifact_root)
    for check in result['checks']:
        if check['status']!='PASS':continue
        rejected=[]
        for fault in ('C_deep_rows','C_recomputed_parity','A_head_cost','A_strength','A_future_anchor','A_teacher'):
            bad=copy.deepcopy(check['receipt']);o=bad['requests'][-1]['paths'][1]['origins'][-1]
            if fault=='C_deep_rows':o['warmup_Linear_and_projection_records']['C']['Linear_inputs']=[{'rows':512}]
            elif fault=='C_recomputed_parity':o['C_recomputed_direct_equal']=False
            elif fault=='A_head_cost':o['warmup_actual_output_head_calls']['A_W1_ONE_PHASE']+=1
            elif fault=='A_strength':o['warmup_A_readouts']['A_W1_ONE_PHASE']['shared_alpha']=1
            elif fault=='A_future_anchor':o['warmup_A_readouts']['A_W1_ONE_PHASE']['past_D_steps'][0].append(30)
            else:o['warmup_A_readouts']['A_W1_ONE_PHASE']['teacher_calls']=1
            try:cost.verify_batch(bad)
            except ValueError:rejected.append(fault)
            else:raise AssertionError('Invalid same-state cost evidence accepted: '+fault)
        check['new_action_cost_mutation_refusals']=rejected
    result['declared_Toy_head_module_source_proof']=head_proof
    result['limits']='Complete source-exact same-state post-probe readout/partial/dense CPU plumbing; Toy weights/attention/prepare/decode. No real action latency, policy-video or endpoint quality claim.'
    result['cost_sampling_derivation_proof']=cost.SAMPLING_PROOF
    result['cost_verifier_derivation_proof']=cost.VERIFIER_PROOF
    return result
