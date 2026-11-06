"""CPU metrics for actual post-denoise, pre-solver four-cell CFG predictions.

This is a local teacher diagnostic, never an endpoint loss or routing label.
The FP32 operation order is the pinned Cosmos closure, not algebraic 8*c-7*u.
"""
import math
import torch

CELLS = ('CC', 'DC', 'CD', 'DD')
BRANCHES = ('conditional', 'unconditional')
SPACE = 'POST_DENOISE_BEFORE_SOLVER'


def guided(conditional, unconditional, guidance):
    return conditional + guidance * (conditional - unconditional)


def mse(x):
    return float(x.double().square().mean())


@torch.no_grad()
def score_four_cells(cells, *, guidance, measurement_space):
    if measurement_space != SPACE or set(cells) != set(CELLS):
        raise ValueError('Complete actual post-denoise four-cell predictions required')
    if type(guidance) not in (int, float) or not math.isfinite(guidance) or guidance < 0:
        raise ValueError('Finite nonnegative guidance required')
    shape = None
    for cell in cells.values():
        if set(cell) != set(BRANCHES):
            raise ValueError('Both named CFG branches required')
        for tensor in cell.values():
            if not isinstance(tensor, torch.Tensor) or tensor.device.type != 'cpu' or tensor.dtype != torch.float32:
                raise ValueError('Actual denoise outputs must be FP32 CPU tensors')
            if tensor.ndim != 5 or not tensor.numel() or not bool(torch.isfinite(tensor).all()):
                raise ValueError('Finite nonempty BCTHW predictions required')
            if shape is None:
                shape = list(tensor.shape)
            if list(tensor.shape) != shape:
                raise ValueError('Four-cell geometry differs')
    combined = {n: guided(cells[n]['conditional'], cells[n]['unconditional'], guidance) for n in CELLS}
    teacher = combined['DD']
    if any(not bool(torch.isfinite(x).all()) for x in combined.values()):
        raise ValueError('Nonfinite actual FP32 guided prediction')
    errors = {n: combined[n].double() - teacher.double() for n in CELLS}
    cell_scores = {n: {
        'guided_velocity_MSE_to_DD': mse(errors[n]),
        'conditional_MSE_to_DD': mse(cells[n]['conditional'].double() - cells['DD']['conditional'].double()),
        'unconditional_MSE_to_DD': mse(cells[n]['unconditional'].double() - cells['DD']['unconditional'].double()),
    } for n in CELLS}
    e0 = cells['CC']['conditional'].double() - cells['DD']['conditional'].double()
    e1 = cells['CC']['unconditional'].double() - cells['DD']['unconditional'].double()
    w0, w1 = 1 + guidance, -guidance
    a, b, dot = mse(e0), mse(e1), float((e0 * e1).mean())
    weighted = w0*w0*a + w1*w1*b
    cross = 2*w0*w1*dot
    ideal = w0*e0 + w1*e1
    ideal_mse = mse(ideal)
    if not math.isclose(ideal_mse, weighted + cross, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError('Signed error-energy reconstruction differs')
    ref = cell_scores['CC']['guided_velocity_MSE_to_DD']
    for row in cell_scores.values():
        row['relative_MSE_reduction_vs_CC_percent'] = None if ref == 0 else 100*(ref-row['guided_velocity_MSE_to_DD'])/ref
    out = {
        'status': 'SAME_ORIGIN_POST_DENOISE_GUIDED_TEACHER_METRICS_NOT_ENDPOINT_NOT_RV',
        'measurement_space': SPACE, 'guidance': guidance, 'ideal_branch_weights': [w0, w1],
        'actual_FP32_operation': 'cond_v + guidance * (cond_v - uncond_v)',
        'shape_BCTHW': shape, 'elements_per_branch': e0.numel(),
        'cells': cell_scores, 'CC_zero_error_reference': ref == 0,
        'CC_error_geometry': {
            'unweighted_conditional_MSE': a, 'unweighted_unconditional_MSE': b,
            'signed_branch_error_dot_mean': dot,
            'branch_error_cosine': None if a == 0 or b == 0 else dot/math.sqrt(a*b),
            'weighted_energy_sum': weighted, 'signed_cross_term': cross,
            'ideal_float64_guided_MSE': ideal_mse,
            'ideal_combined_to_independent_energy_ratio': None if weighted == 0 else ideal_mse/weighted,
            'actual_FP32_guided_MSE': ref,
            'FP32_combination_rounding_error_MSE': mse(errors['CC']-ideal),
        },
        'same_branch_output_factorization': {
            'DC_conditional_equals_DD': torch.equal(cells['DC']['conditional'], cells['DD']['conditional']),
            'DC_unconditional_equals_CC': torch.equal(cells['DC']['unconditional'], cells['CC']['unconditional']),
            'CD_conditional_equals_CC': torch.equal(cells['CD']['conditional'], cells['CC']['conditional']),
            'CD_unconditional_equals_DD': torch.equal(cells['CD']['unconditional'], cells['DD']['unconditional']),
        },
        'cell_output_factorization_assumed': False,
        'signed_vectors_available_to_caller': True,
        'DD_zero_is_teacher_definition': True,
        'endpoint_or_semantic_quality_claim': False,
        'formal_single_action_RV_label': False,
        'CUDA_initialized': torch.cuda.is_initialized(),
    }
    assert out['CUDA_initialized'] is False
    return out
