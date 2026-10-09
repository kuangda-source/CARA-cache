"""Four-scene teacher-free A plus RA comparison with matched Native references.

The complete matrix is WC, joint-native, RA and four frozen RA+A readouts,
followed by four Native reference slots: 32 full paths. The accepted guarded
samplers are source-derived with explicit inverse AST checks. No GPU card,
calibration fit, endpoint score or clean latency is supplied by this module.
"""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from . import cfg_ra_baseline_sampling as legacy
from . import cfg_ra_baseline_with_references as references
from .cfg_guided_w1_deployment import GuidedW1Readout, GuidedW1DeploymentPair, alpha_at
from .cfg_guided_w1_forward import compile_collection
from .rv0_cfg_factorial_evaluation import solver_configuration
from .rv0_fork import object_state
from .mid_coverage import tree_digest


A_METHODS = ('W1_GLOBAL_1', 'BETA1_GLOBAL_1', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE')
METHODS = ('WC', 'JOINT_NATIVE', 'RA')+A_METHODS
RA_METHODS = ('RA',)+A_METHODS
vector_file = legacy.vector_file
SOURCE_SHA = {
    'methods': '866460b1bc0865309997c983d60e6108d4a74e1053c05756f3973df32fd3deb5',
    'references': '2173c69ca176b28c32ee4732695b3593b46f1d6733caf0df34b87ca75f1586f7',
}


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _node(source):
    n = ast.parse(source).body[0]
    return n.value if isinstance(n, ast.Expr) else n


def _rewrite(node, replacements):
    patterns = [(_dump(_node(a)), _node(b)) for a, b in replacements]
    counts = [0]*len(patterns)
    class Replace(ast.NodeTransformer):
        def generic_visit(self, n):
            for index, (old, new) in enumerate(patterns):
                if _dump(n) == old:
                    counts[index] += 1
                    return copy.deepcopy(new)
            return super().generic_visit(n)
    result = Replace().visit(copy.deepcopy(node))
    if counts != [1]*len(patterns):
        raise ValueError('Explicit complete A sampler source sites differ: '+repr(counts))
    return result


def _derive(module, source_name, function_name, replacements, *, inserts=(), globals_extra=None):
    if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != SOURCE_SHA[source_name]:
        raise ValueError('Pinned guarded base sampler source changed')
    original = ast.parse(dedent(inspect.getsource(getattr(module, function_name)))).body[0]
    changed = _rewrite(original, replacements)
    insertion_counts = [0]*len(inserts)
    class Insert(ast.NodeTransformer):
        def generic_visit(self, node):
            for index, (site, before) in enumerate(inserts):
                # Insert before a whole statement. Matching the inner Call of
                # an Expr would replace its value with a list of statements.
                if _dump(node) == _dump(ast.parse(site).body[0]):
                    insertion_counts[index] += 1
                    return [copy.deepcopy(n) for n in ast.parse(before).body]+[node]
            return super().generic_visit(node)
    changed = Insert().visit(changed)
    if insertion_counts != [1]*len(inserts):
        raise ValueError('Explicit A metadata/readout injection sites differ')
    injected = {_dump(n) for _, before in inserts for n in ast.parse(before).body}
    class Uninsert(ast.NodeTransformer):
        def generic_visit(self, n):
            if _dump(n) in injected:
                return None
            return super().generic_visit(n)
    inverse = Uninsert().visit(copy.deepcopy(changed))
    inverse = _rewrite(inverse, [(b, a) for a, b in reversed(replacements)])
    if _dump(inverse) != _dump(original):
        raise ValueError('A sampler changed outside registered source edits')
    namespace = {**vars(module), **(globals_extra or {})}
    compiled = ast.fix_missing_locations(ast.Module(body=[changed], type_ignores=[]))
    exec(compile(compiled, str(Path(__file__))+'#'+function_name, 'exec'), namespace)
    return namespace[function_name], {
        'base_source_sha256': SOURCE_SHA[source_name], 'function': function_name,
        'replacement_sites': len(replacements), 'injection_sites': len(inserts),
        'inverse_AST_equal': True, 'complete_four_scene_32_path_scope': True,
        'real_model_or_video_or_latency_claim': False}


def _condition_fields(conditions):
    return [{k: tree_digest(v) for k, v in object_state(c).items()} for c in conditions]


def _condition_masks(conditions):
    return [{'shape': list(c.condition_video_input_mask_B_C_T_H_W.shape),
             'dtype': str(c.condition_video_input_mask_B_C_T_H_W.dtype),
             'nonzero_elements': int(torch.count_nonzero(c.condition_video_input_mask_B_C_T_H_W)),
             'finite': bool(torch.isfinite(c.condition_video_input_mask_B_C_T_H_W).all())}
            for c in conditions]


def _compile_A(runtime, wc, rf, method, context, model):
    if method in A_METHODS:
        readout = GuidedW1Readout(model, method=method, context=context)
        net, denoise, proof = compile_collection(runtime, wc, rf, readout)
        return net, denoise, proof, readout
    net, denoise, proof = legacy.compile_production(runtime, wc, rf)
    return net, denoise, proof, None


def _attach_A(executor, readout):
    if readout is None:
        return executor
    wrapped = GuidedW1DeploymentPair(executor, readout)
    # The existing sampler records the actual selector's completed history.
    # The readout neither owns nor changes that selector or its threshold.
    wrapped.controller = executor.controller
    return wrapped


_method_verify, METHOD_VERIFY_PROOF = _derive(legacy, 'methods', 'verify_batch', [
    ("state.get('planned_paths') != 6", "state.get('planned_paths') != 28"),
    ("state.get('planned_videos') != 6", "state.get('planned_videos') != 28"),
    ("len(state.get('requests', [])) != 2", "len(state.get('requests', [])) != 4"),
    ('len(rows) != 3', 'len(rows) != 7'), ('len(prepared) != 3', 'len(prepared) != 7'),
    ("row['method'] == 'RA'", "row['method'] in RA_METHODS"),
    ("{'complete_paths': 6, 'complete_videos': 6, 'solver_updates': 216, 'net_calls': 432, 'teacher_calls': 0, 'all_three_methods_complete_and_actual_deep_visits_verified': True, 'method_outputs_not_required_equal': True, 'instrumented_time_not_clean_latency': True, 'endpoint_quality_requires_matching_reference_scoring': True}",
     "{'complete_paths': 28, 'complete_videos': 28, 'solver_updates': 1008, 'net_calls': 2016, 'teacher_calls': 0, 'all_seven_methods_complete_and_actual_deep_visits_verified': True, 'method_outputs_not_required_equal': True, 'instrumented_time_not_clean_latency': True, 'endpoint_quality_requires_matching_reference_scoring': True}"),
], globals_extra={'METHODS': METHODS, 'RA_METHODS': RA_METHODS})


def verify_batch(state):
    result = _method_verify(state)
    for request in state['requests']:
        for row in request['paths']:
            if (row['condition_fields_before'] != row['condition_fields_after']
                    or row['condition_fields_before'] != request['paths'][0]['condition_fields_before']
                    or not row['actual_raw_solver_configuration']['raw_values']
                    or len(row['actual_condition_masks']) != 2
                    or not all(x['finite'] for x in row['actual_condition_masks'])):
                raise ValueError('Complete current condition/solver metadata missing or changed')
            readout = row['A_readout']
            if row['method'] not in A_METHODS:
                if readout is not None:
                    raise ValueError('A readout installed in an original baseline')
                continue
            if (readout['method'] != row['method'] or readout['completed_pairs'] != 36
                    or len(readout['history']) != 36 or readout['teacher_calls'] != 0
                    or readout['extra_candidate_deep_blocks'] != 0
                    or readout['candidate_original_head_elision_implemented']
                    or readout['endpoint_quality_or_clean_latency_claim']):
                raise ValueError('Complete teacher-free A deployment evidence differs')
            actual_D = []
            for step, (history, action) in enumerate(zip(readout['history'], row['actions']), 1):
                if action == 'DD':
                    actual_D.append(step)
                statuses = history['branch_status']
                paid_heads = sum(s in ('scalar', 'BETA1') for s in statuses)
                if (history['step'] != step or history['action'] != action
                        or history['shared_alpha'] != alpha_at(row['method'], step)
                        or history['past_D_steps'] != [actual_D[-2:]]*2
                        or history['teacher_calls'] != 0 or history['extra_deep_blocks'] != 0
                        or not history['post_RF_fusion'] or history['C_readout_updates_D_anchor']
                        or len(statuses) != 2
                        or action == 'DD' and statuses != ['ACTUAL_D_ONLY_ANCHOR']*2
                        or action == 'CC' and row['method'].startswith('BETA1') and statuses != ['BETA1']*2
                        or action == 'CC' and row['method'].startswith('W1') and any(s not in ('scalar', 'small_denominator', 'insufficient_anchors', 'nonfinite_beta', 'nonfinite_prediction') for s in statuses)
                        or history['extra_heads'] != paid_heads):
                    raise ValueError('A readout used wrong strength, source or computation')
            if (any(x['anchor_steps'] != actual_D[-2:] for x in readout['D_only_final_history'])
                    or readout['extra_candidate_heads'] != sum(h['extra_heads'] for h in readout['history'])):
                raise ValueError('A final anchors or paid candidate heads differ')
    return {**result, 'all_16_A_paths_D_only_history_and_post_RF_strength_verified': True}


_audit_methods, METHOD_RAW_PROOF = _derive(legacy, 'methods', 'audit_vectors', [
    ("len(files) != 6", "len(files) != 28"),
    ("{'files': files, 'actual_guided_tensors_reloaded': 216, 'actual_final_latents_reloaded': 6, 'actual_initial_7_DD_guided_direct_equal': True, 'quality_or_speed_result': False}",
     "{'files': files, 'actual_guided_tensors_reloaded': 1008, 'actual_final_latents_reloaded': 28, 'actual_initial_7_DD_guided_direct_equal': True, 'quality_or_speed_result': False}"),
], globals_extra={'verify_batch': verify_batch})


_run_methods, METHOD_SAMPLER_PROOF = _derive(legacy, 'methods', 'run_batch', [
    ('len(samples) != 2', 'len(samples) != 4'), ('len(contexts) != 2', 'len(contexts) != 4'),
    ("state.update(planned_paths=6, planned_videos=6, requests=[], teacher_calls=0, RA_threshold=threshold, calibration_fingerprint=calibration.fingerprint, clean_latency_claim=False, independent_confirmation_claim=False)",
     "state.update(planned_paths=28, planned_videos=28, requests=[], teacher_calls=0, RA_threshold=threshold, calibration_fingerprint=calibration.fingerprint, clean_latency_claim=False, independent_confirmation_claim=False)"),
    ('_, denoise, core = compile_production(runtime, wc, rf_module)',
     '_, denoise, core, readout = _compile_A(runtime, wc, rf_module, method, context, model)'),
], inserts=[
    ('factory, proof = compile_velocity(runtime, rf_module, executor, executor.choose)',
     'executor = _attach_A(executor, readout)'),
    ("row['conditions_before'] = tree_digest([object_state(c) for c in conditions])",
     "row['condition_fields_before'] = _condition_fields(conditions)\nrow['actual_condition_masks'] = _condition_masks(conditions)"),
    ("row.update(conditions_after=tree_digest([object_state(c) for c in conditions]), flags_after=backend_flags(), rng_after=RNGState().signatures(), video_artifact=artifact(paths[0]), guided_list_sha256=tree_digest(tensors), final_latent_sha256=tree_digest(capture['final_latent']))",
     "row['A_readout'] = readout.finish() if method in A_METHODS else None\nrow['condition_fields_after'] = _condition_fields(conditions)\nrow['actual_raw_solver_configuration'] = solver_configuration(scheduler)"),
], globals_extra={'METHODS': METHODS, 'A_METHODS': A_METHODS, '_compile_A': _compile_A,
    '_attach_A': _attach_A, '_condition_fields': _condition_fields, '_condition_masks': _condition_masks,
    'solver_configuration': solver_configuration, 'verify_batch': verify_batch})


_verify_references, REFERENCE_VERIFY_PROOF = _derive(references, 'references', 'verify_comparison', [
    ("state.get('planned_paths') != 8", "state.get('planned_paths') != 32"),
    ("state.get('planned_method_paths') != 6", "state.get('planned_method_paths') != 28"),
    ("state.get('planned_reference_paths') != 2", "state.get('planned_reference_paths') != 4"),
    ("len(state.get('references', [])) != 2", "len(state.get('references', [])) != 4"),
    ("{'complete_method_paths': 6, 'attempted_reference_slots': 2, 'accepted_reference_slots': accepted, 'rejected_reference_slots': 2 - accepted, 'planned_solver_updates': 288, 'planned_net_calls': 576, 'clean_latency_claim': False, 'independent_confirmation_claim': False}",
     "{'complete_method_paths': 28, 'attempted_reference_slots': 4, 'accepted_reference_slots': accepted, 'rejected_reference_slots': 4 - accepted, 'planned_solver_updates': 1152, 'planned_net_calls': 2304, 'clean_latency_claim': False, 'independent_confirmation_claim': False}"),
], globals_extra={'verify_batch': verify_batch})


def verify_comparison(state):
    result = _verify_references(state)
    for ref, request in zip(state['references'], state['batch']['requests']):
        if ref['outcome'] == 'ACCEPTED':
            if (ref['condition_fields_before'] != ref['condition_fields_after']
                    or ref['condition_fields_before'] != request['paths'][0]['condition_fields_before']
                    or not ref['actual_raw_solver_configuration']['raw_values']):
                raise ValueError('Native reference current condition/solver metadata differs')
    return result


run_comparison, COMPARISON_PROOF = _derive(references, 'references', 'run_comparison', [
    ('len(samples) != 2', 'len(samples) != 4'),
    ("state.update(planned_paths=8, planned_method_paths=6, planned_reference_paths=2, batch={}, references=[], status='METHODS_RUNNING', clean_latency_claim=False, independent_confirmation_claim=False)",
     "state.update(planned_paths=32, planned_method_paths=28, planned_reference_paths=4, batch={}, references=[], status='METHODS_RUNNING', clean_latency_claim=False, independent_confirmation_claim=False)"),
], inserts=[
    ("row['conditions_before'] = tree_digest([object_state(c) for c in conditions])",
     "row['condition_fields_before'] = _condition_fields(conditions)\nrow['actual_condition_masks'] = _condition_masks(conditions)"),
    ("row.update(conditions_after=tree_digest([object_state(c) for c in conditions]), guided_list_sha256=tree_digest(values), final_latent_sha256=tree_digest(captured['final_latent']))",
     "row['condition_fields_after'] = _condition_fields(conditions)\nrow['actual_raw_solver_configuration'] = solver_configuration(scheduler)"),
], globals_extra={'run_batch': _run_methods, 'verify_comparison': verify_comparison,
    '_condition_fields': _condition_fields, '_condition_masks': _condition_masks,
    'solver_configuration': solver_configuration})


audit_comparison_vectors, COMPARISON_RAW_PROOF = _derive(
    references, 'references', 'audit_comparison_vectors', [],
    globals_extra={'verify_comparison': verify_comparison, 'audit_vectors': _audit_methods})

COMPILER_PROOFS = [METHOD_VERIFY_PROOF, METHOD_RAW_PROOF, METHOD_SAMPLER_PROOF,
    REFERENCE_VERIFY_PROOF, COMPARISON_PROOF, COMPARISON_RAW_PROOF]
