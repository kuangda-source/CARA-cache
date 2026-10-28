"""Saved Shared25-C Q1 readouts, using the original C/warp/head/RF kernel.

The caller owns model loading, precision, resource admission and billing. This
module neither samples a new trajectory nor installs compressed deployed state.
Raw references are offline teachers; its memory is not a deployment benchmark.
"""
import copy
from dataclasses import is_dataclass
import math
import time

import torch

from .full_sampling import CompleteStateRoundtrip
from .innovation_gain_observer_r1 import restore_readout_inputs
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain, tensor_bytes
from .policy_interval_readout_r1 import guided
from .scout_readout_v22 import validate_state
from .sq_codec_r1 import packed_source, storage_bytes, transform_roundtrip, leave_one_prompt_out

PROMPTS = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199')
STEPS = (22, 23, 25, 33, 34, 35)
CODECS = tuple((basis, bits) for basis in ('I', 'M') for bits in ((8, 8), (4, 8), (8, 4)))


def cosmos_condition_schema():
    """Use the exact registered runtime classes, never import a payload name."""
    from cosmos_predict2._src.predict2.conditioner import DataType
    from cosmos_predict2._src.predict2.configs.video2world.defaults.conditioner import Video2WorldCondition
    return [(Video2WorldCondition, {'data_type': DataType}) for _ in (0, 1)]


def transfer(value, device, memo=None):
    """Preserve repeated tensor objects at the CPU/device boundary."""
    if memo is None:
        memo = {}
    if isinstance(value, torch.Tensor):
        if id(value) not in memo:
            memo[id(value)] = value.to(device=device)
        return memo[id(value)]
    if isinstance(value, dict):
        return {k: transfer(v, device, memo) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(transfer(v, device, memo) for v in value)
    if is_dataclass(value) and not isinstance(value, type):
        return type(value)(**transfer(vars(value), device, memo))
    return value


def source_from_anchors(anchors):
    return [dict(probe=last.probe, residual=last.residual,
                 residual_window=[old.residual, last.residual],
                 probe_window=[old.probe, last.probe]) for old, last in anchors]


def source_roundtrip(source):
    """Only the FP32 M basis transform, then cast back to the original dtype."""
    view = [dict(row) for row in source]
    decoded = [transform_roundtrip(c, u) for c, u in zip(
        source[0]['residual_window'], source[1]['residual_window'])]
    for branch in (0, 1):
        view[branch]['residual_window'] = [pair[branch] for pair in decoded]
        view[branch]['residual'] = view[branch]['residual_window'][-1]
    return view


def output_distortion(outputs, original_C, teacher):
    """Actual post-RF values; keep codec error and error cancellation separate."""
    values = (*outputs, *original_C, *teacher)
    if len(outputs) != 2 or len(original_C) != 2 or len(teacher) != 2:
        raise ValueError('Complete conditional/negative branch pairs required')
    first = teacher[0]
    if any(v.shape != first.shape or v.dtype != torch.float32 or not torch.isfinite(v).all() for v in values):
        raise ValueError('Aligned finite FP32 post-RF output coordinates required')
    energy = sum(float(v.double().square().mean()) for v in teacher)/2
    if energy <= 0:
        raise ValueError('Positive common teacher energy required')
    branch_e = [c.double()-d.double() for c, d in zip(original_C, teacher)]
    branch_delta = [q.double()-c.double() for q, c in zip(outputs, original_C)]
    guided_e = guided(original_C).double()-guided(teacher).double()
    guided_delta = guided(outputs).double()-guided(original_C).double()
    coordinates = {'BR': (branch_e, branch_delta), 'CFG': ([guided_e], [guided_delta])}
    result = {'teacher_branch_energy': energy, 'coordinate': 'ACTUAL_C_POST_RF'}
    for objective, (errors, deltas) in coordinates.items():
        n = len(errors)
        q_C = sum(float(e.square().mean()) for e in errors)/n
        q_codec = sum(float(d.square().mean()) for d in deltas)/n
        cross = sum(2*float((e*d).mean()) for e, d in zip(errors, deltas))/n
        total = sum(float((e+d).square().mean()) for e, d in zip(errors, deltas))/n
        tolerance = 128*torch.finfo(torch.float64).eps*max(q_C, q_codec, abs(cross), 1e-300)
        if abs(total-(q_C+q_codec+cross)) > tolerance:
            raise ArithmeticError('Q1 error decomposition outside FP64 reduction bound')
        result[objective] = dict(q_total=total, q_C=q_C, q_codec=q_codec, twice_alignment=cross,
                                 normalized_total=total/energy,
                                 decomposition_abs_error=abs(total-(q_C+q_codec+cross)))
    return result


@torch.no_grad()
def evaluate_saved_state(kernel, payload, schema, *, device, max_copy_bytes, synchronize=None):
    """Eight formal C pairs; reject original-C drift before codec evaluation.

    Original B1 teacher/control identity must be validated by the asset reader.
    Every role runs with private inputs and the same original kernel/precision.
    """
    if type(max_copy_bytes) is not int or max_copy_bytes <= 0:
        raise ValueError('Explicit private-copy resource bound required')
    if any(module.training for module in kernel.net.modules()):
        raise ValueError('The original readout model must stay in eval mode')
    cpu_inputs = restore_readout_inputs(payload, schema, 'cpu')
    validate_state(cpu_inputs['context'], cpu_inputs['step'], cpu_inputs['xi'], cpu_inputs['anchors'])
    if not all(payload[k] for k in ('P0_actual_dense', 'P1_dense_head_RF_equal', 'P2_C_actual_parent_equal')):
        raise ValueError('Accepted same-state B1 controls required')
    cpu_source = source_from_anchors(cpu_inputs['anchors'])
    current, pair_inputs = transfer((cpu_inputs['current'], cpu_inputs['pair_inputs']), device)
    logical = tensor_bytes(plain((cpu_source, current, pair_inputs[:3], [vars(c) for c in pair_inputs[3]])))
    if logical > max_copy_bytes:
        raise ValueError('Private-copy cap exceeded before role copies or head calls')
    original_digest = tree_digest(plain((cpu_inputs['anchors'], cpu_inputs['current'],
                                       cpu_inputs['pair_inputs'][:3],
                                       [vars(c) for c in cpu_inputs['pair_inputs'][3]])))
    snapshot = CompleteStateRoundtrip(kernel.net, kernel.model.sample_scheduler, pair_inputs[1])
    before = snapshot.fingerprint()
    versions = [(p, p._version) for p in kernel.net.parameters()]
    sync = synchronize or (lambda: None)
    expected = tuple(payload['readouts']['WC_C']['outputs'])
    teacher = tuple(payload['teacher'])
    rows = []
    reference_C = None
    roles = [('original_uncompressed_C', None, None), ('FP32_M_roundtrip_C', None, None)]
    roles += [(basis+'_'+str(bits[0])+'_'+str(bits[1]), basis, bits) for basis, bits in CODECS]
    try:
        for role, basis, bits in roles:
            started = time.perf_counter()
            if basis:
                cpu_view, byte_info, packets = packed_source(cpu_source, basis=basis, bits=bits)
                del packets
            else:
                cpu_view = source_roundtrip(cpu_source) if role == 'FP32_M_roundtrip_C' else cpu_source
                byte_info = dict(actual_packed_bytes=None, raw_r_unique_storage_bytes=storage_bytes(
                    [row['residual_window'] for row in cpu_source]), persistent_deployment_measured=False)
            cpu_codec_seconds = time.perf_counter()-started
            sync(); started = time.perf_counter()
            source = transfer(cpu_view, device)
            sync(); transfer_seconds = time.perf_counter()-started
            snapshot.restore()
            private = copy.deepcopy((source, current, pair_inputs))
            sync(); started = time.perf_counter()
            try:
                outputs = kernel.run('C', source=private[0], current=private[1], pair_inputs=private[2])[0]
                sync(); readout_seconds = time.perf_counter()-started
                outputs = tuple(v.detach().cpu().clone() for v in outputs)
            finally:
                snapshot.restore()
                del private
            if reference_C is None:
                if any(not torch.equal(v, d) for v, d in zip(outputs, expected)):
                    raise ValueError('Original C replay mismatch; do not score codecs or change tolerance')
                reference_C = outputs
            error = output_distortion(outputs, reference_C, teacher)
            rows.append(dict(role=role, basis=basis, bits=list(bits) if bits else None,
                             rate=('R16' if sum(bits) == 16 else 'R12') if bits else None,
                             actual_bytes=byte_info['actual_packed_bytes'], bytes=byte_info, errors=error,
                             CPU_codec_wall_seconds=cpu_codec_seconds, device_transfer_seconds=transfer_seconds,
                             actual_C_readout_seconds=readout_seconds,
                             outputs_exact_C=all(torch.equal(x, y) for x, y in zip(outputs, reference_C))))
            del outputs, source, cpu_view
    finally:
        snapshot.restore()
        after_digest = tree_digest(plain((cpu_inputs['anchors'], cpu_inputs['current'],
                                         cpu_inputs['pair_inputs'][:3],
                                         [vars(c) for c in cpu_inputs['pair_inputs'][3]])))
        if snapshot.fingerprint() != before or after_digest != original_digest:
            raise RuntimeError('Q1 changed protected model, solver, RNG or saved inputs')
        if any(p._version != version for p, version in versions):
            raise RuntimeError('Q1 mutated original model weights')
    for rate in ('R16', 'R12'):
        if len({r['actual_bytes'] for r in rows if r['rate'] == rate}) != 1:
            raise ValueError('Q1 actual window bytes differ within one registered rate')
    return dict(prompt=payload['context'][0], step=payload['step'], rows=rows,
                original_C_exact=True, state_roundtrip_equal=True, logical_private_copy_bytes=logical,
                formal_C_pairs=8, new_deep_pairs=0, deployed_memory_measured=False,
                raw_reference_scope='OFFLINE_TEACHER_ONLY')


def select_shared_codecs(states):
    """Complete two-prompt cohort, LOPO checks, then one shared final direction."""
    keys = [(s['prompt'], s['step']) for s in states]
    if len(keys) != len(set(keys)) or set(keys) != {(p, t) for p in PROMPTS for t in STEPS}:
        raise ValueError('All 12 registered states required before codec selection')
    rows = []
    for state in states:
        if not state['original_C_exact'] or not state['state_roundtrip_equal']:
            raise ValueError('Original C and transaction controls required for every state')
        if {(r['basis'], tuple(r['bits'])) for r in state['rows'] if r['basis']} != set(CODECS):
            raise ValueError('All six actual-output codecs required in every state')
        for r in state['rows']:
            if r['basis']:
                rows.append(dict(prompt=state['prompt'], state=state['step'], basis=r['basis'], bits=r['bits'],
                                 rate=r['rate'], actual_bytes=r['actual_bytes'], coordinate=r['errors']['coordinate'],
                                 BR=r['errors']['BR']['normalized_total'], CFG=r['errors']['CFG']['normalized_total']))
    selections = {}; aliases = {}
    for rate in ('R16', 'R12'):
        directions = [(8, 8)] if rate == 'R16' else [(4, 8), (8, 4)]
        for basis in ('I', 'M'):
            for objective in ('BR', 'CFG'):
                label = rate+'_'+basis+'_'+objective
                folds = leave_one_prompt_out(rows, basis=basis, rate=rate, objective=objective)
                scores = {d:sum(r[objective] for r in rows if r['basis'] == basis and r['rate'] == rate
                               and tuple(r['bits']) == d)/12 for d in directions}
                best = min(directions, key=lambda d: (scores[d], d))
                selections[label] = dict(LOPO=folds, final_bits=list(best),
                                         final_training_scores={str(d):v for d,v in scores.items()})
                aliases.setdefault(str((rate, basis, best)), []).append(label)
    return dict(selections=selections, execution_aliases=aliases, partial_state_selection=False,
                endpoint_benefit_established=False)
