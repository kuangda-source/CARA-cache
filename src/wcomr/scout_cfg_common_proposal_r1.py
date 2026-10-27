"""Teacher-free output-pair reference proposal, not installed in a sampler.

Keep the original phase alpha; use past-anchor age only. Both A and R4
component velocities must be computed and costed. No IG coefficients/fit,
branch skipping, Fourier operation, refresh decision, or anchor writeback.
"""
import torch
from .cfg_guided_w1_outputs import shared_output_fusion

@torch.no_grad()
def common_long_proposal(*, C, A_component, R4_component, step, anchor_step):
    if type(step) is not int or type(anchor_step) is not int or not 1<=anchor_step<step<=36:
        raise ValueError('Strictly past same-request true anchor required')
    dense_steps=tuple(range(1,22))+(24,27,30,36)
    if step in dense_steps:
        raise ValueError('Dense steps must keep the original full-compute path')
    if anchor_step!=max(s for s in dense_steps if s<step):
        raise ValueError('Latest true anchor of the frozen Shared25-C mask required')
    alpha=1. if step<25 else .5
    # Original adapter validates finite matching FP32 BCTHW pairs.
    original=shared_output_fusion(C,A_component,alpha)
    if step-anchor_step<3:return original
    shared_output_fusion(A_component,R4_component,0)
    # Apply precisely the same velocity correction to both branches.
    delta=((R4_component[0]-A_component[0])+(R4_component[1]-A_component[1]))*.5
    proposed=(A_component[0]+delta,A_component[1]+delta)
    return shared_output_fusion(C,proposed,alpha)
