"""Complete original OFF/ON/fault scope with C/A/P/D action boundaries."""
import copy
from pathlib import Path

from wcomr import source_aware_action_cost_sampling as cost


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_sampling_cpu')
    exercise=cost.bind(original.exercise,{'run_batch':cost.run_batch,
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
    result['limits']='Complete source-exact same-state post-probe readout/partial/dense CPU plumbing; Toy weights/attention/prepare/decode. No real action latency, policy-video or endpoint quality claim.'
    result['cost_sampling_derivation_proof']=cost.SAMPLING_PROOF
    result['cost_verifier_derivation_proof']=cost.VERIFIER_PROOF
    return result
