"""Measurement-space and active-condition controls; CPU implementation evidence."""
import torch
from wcomr.cfg_teacher_measurement import (
    tensor_witness, condition_witness, solver_return_witness,
)


def run():
    assert not torch.cuda.is_initialized()
    rng = torch.random.get_rng_state().clone()
    x = torch.arange(24, dtype=torch.float32).reshape(1, 2, 3, 2, 2)
    original = x.clone()
    mask = torch.tensor([1, 0, 0], dtype=torch.float32).reshape(1, 1, 3, 1, 1)
    original_mask = mask.clone()
    first = condition_witness(x, mask)
    outside = x.clone(); outside[:, :, 1:] += 100
    second = condition_witness(outside, mask)
    assert first['full_gt_frames'] != second['full_gt_frames']
    assert first['active_values'] == second['active_values']
    inside = x.clone(); inside[:, :, :1] += 1
    assert condition_witness(inside, mask)['active_values'] != first['active_values']
    empty = condition_witness(x, torch.zeros_like(mask))
    assert empty['zero_active_values'] and empty['active_values']['elements'] == 0
    assert first['active_values']['elements'] == 8
    assert tensor_witness(x)['tree_sha256'] != tensor_witness(x.bfloat16())['tree_sha256']
    assert torch.equal(x, x.bfloat16().float())
    returned = solver_return_witness((x.unsqueeze(0),))
    assert returned['next_sampler_latent'] == tensor_witness(x)
    assert returned['raw_return_tree_sha256'] != returned['raw_first_tensor']['tree_sha256']
    rejected = []
    for name, bad in [('nonbinary', torch.full_like(mask, .5)),
                      ('nonfinite', torch.full_like(mask, float('nan'))),
                      ('not_broadcastable', torch.zeros(1, 1, 4, 1, 1)),
                      ('wrong_rank', torch.zeros(3))]:
        try:
            condition_witness(x, bad)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('Invalid condition measurement accepted: ' + name)
    assert torch.equal(x, original) and torch.equal(mask, original_mask)
    assert torch.equal(rng, torch.random.get_rng_state()) and not torch.cuda.is_initialized()
    return {'status': 'MEASUREMENT_SPACE_ACTIVE_CONDITION_CPU_CONTROLS_PASS_NOT_REAL_MODEL',
            'same_active_different_full_values_distinguished': True,
            'changed_active_values_distinguished': True, 'zero_active_explicit': True,
            'same_numeric_values_different_dtype_distinguished': True,
            'raw_solver_return_and_extracted_latent_distinguished': True,
            'invalid_masks_rejected': rejected, 'inputs_unmodified': True, 'RNG_unmodified': True,
            'CUDA_initialized': False, 'GPU_submissions': 0}
