"""Read-only witnesses for distinct sampler, model, solver and condition spaces."""
import torch
from .mid_coverage import tree_digest

CONTRACT = 'CFG_MEASUREMENT_SPACES_AND_ACTIVE_CONDITION_V1'


@torch.no_grad()
def tensor_witness(value):
    if not isinstance(value, torch.Tensor) or not bool(torch.isfinite(value).all()):
        raise ValueError('Finite actual tensor required for measurement witness')
    return {'dtype': str(value.dtype), 'shape': list(value.shape), 'device': str(value.device),
            'elements': value.numel(), 'tree_sha256': tree_digest(value)}


@torch.no_grad()
def condition_witness(gt, mask):
    if not isinstance(gt, torch.Tensor) or not isinstance(mask, torch.Tensor):
        raise ValueError('Actual gt_frames and condition mask tensors required')
    if (gt.ndim != 5 or mask.ndim != 5 or gt.device != mask.device
            or not bool(torch.isfinite(mask).all())
            or not bool(((mask == 0) | (mask == 1)).all())):
        raise ValueError('Finite binary BCTHW mask on gt_frames device required')
    try:
        active = torch.broadcast_to(mask != 0, gt.shape)
    except RuntimeError as error:
        raise ValueError('Condition mask cannot broadcast to actual gt_frames') from error
    selected = gt.masked_select(active)
    return {'full_gt_frames': tensor_witness(gt), 'condition_mask': tensor_witness(mask),
            'active_values': tensor_witness(selected),
            'selection': 'BCTHW_CONTIGUOUS_FLAT_ORDER_WHERE_BROADCAST_MASK_IS_ONE',
            'zero_active_values': selected.numel() == 0,
            'full_condition_equality_inferred_from_active_values': False}


def net_input_witness(args, kwargs):
    x = args[0] if args else kwargs['x_B_C_T_H_W']
    if 'gt_frames' not in kwargs or 'condition_video_input_mask_B_C_T_H_W' not in kwargs:
        raise ValueError('Pinned actual Video2World net condition inputs required')
    return {'contract': CONTRACT, 'space': 'ACTUAL_NET_INPUT_AFTER_DENOISE_CONDITIONING',
            'x_B_C_T_H_W': tensor_witness(x),
            'condition': condition_witness(kwargs['gt_frames'], kwargs['condition_video_input_mask_B_C_T_H_W'])}


def origin_witness(latent, noise):
    return {'contract': CONTRACT, 'space': 'POST_SOLVER_SAMPLER_LATENT_BEFORE_DENOISE',
            'sampler_latent': tensor_witness(latent), 'noise': tensor_witness(noise)}


def solver_return_witness(value):
    if not isinstance(value, (tuple, list)) or not value or not isinstance(value[0], torch.Tensor):
        raise ValueError('Pinned scheduler return with first actual tensor required')
    return {'contract': CONTRACT, 'space': 'RAW_SOLVER_RETURN_AND_EXTRACTED_NEXT_SAMPLER_LATENT',
            'raw_return_structure': type(value).__name__, 'raw_return_tree_sha256': tree_digest(value),
            'raw_first_tensor': tensor_witness(value[0]),
            'next_sampler_latent': tensor_witness(value[0].squeeze(0)),
            'extraction': 'ORIGINAL_LOOP_VALUE_0_SQUEEZE_0'}


def validate_net_binding(witness, signature):
    try:
        kwargs = signature['kwargs']
        x_sha = signature['args'][0] if signature['args'] else kwargs['x_B_C_T_H_W']
        condition = witness['condition']
        valid = (witness['contract'] == CONTRACT
                 and witness['space'] == 'ACTUAL_NET_INPUT_AFTER_DENOISE_CONDITIONING'
                 and witness['x_B_C_T_H_W']['tree_sha256'] == x_sha
                 and condition['full_gt_frames']['tree_sha256'] == kwargs['gt_frames']
                 and condition['condition_mask']['tree_sha256'] == kwargs['condition_video_input_mask_B_C_T_H_W']
                 and condition['active_values']['elements'] >= 0
                 and condition['zero_active_values'] == (condition['active_values']['elements'] == 0)
                 and condition['full_condition_equality_inferred_from_active_values'] is False)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Incomplete actual net measurement binding') from error
    if not valid:
        raise ValueError('Actual net measurement differs from input signature')
