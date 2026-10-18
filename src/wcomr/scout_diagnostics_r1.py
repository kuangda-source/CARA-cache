"""Offline scouts: fixed amplitude, directional diagnostics, one schedule exchange.

No sampler, learned controller, CUDA calls or deployment state updates. Inputs
must be post-RF guided velocities from a separately verified common prefix.
"""
import math

ALPHAS = (0., .25, .5, .75, 1.)


def amplitude_and_direction(c, phi, teacher, *, torch):
    if (c.device.type != 'cpu' or phi.device.type != 'cpu' or teacher.device.type != 'cpu'
            or c.shape != phi.shape or c.shape != teacher.shape or c.ndim != 5
            or any(not x.is_floating_point() or not bool(torch.isfinite(x).all())
                   for x in (c, phi, teacher))):
        raise ValueError('Finite equal B,C,T,H,W CPU velocities required')
    c, phi, teacher = (x.double() for x in (c, phi, teacher))
    e, d = c - teacher, phi - c
    mean2 = lambda x: float(x.square().mean())
    qc, d2, ed = mean2(e), mean2(d), float((e * d).mean())
    raw_alpha = -ed / d2 if d2 > 0 else None
    alpha = max(0., min(1., raw_alpha)) if raw_alpha is not None else 0.
    curve = []
    for value in ALPHAS:
        actual = mean2(e + value * d)
        quadratic = qc + 2 * value * ed + value * value * d2
        if not math.isclose(actual, quadratic, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError('FP64 quadratic/direct reduction disagreement')
        curve.append(dict(alpha=value, guided_MSE=actual))
    # Visible direction uses C, never the current D teacher.
    err = phi - teacher
    cnorm2 = float(c.square().sum())
    coefficient = float((err * c).sum()) / cnorm2 if cnorm2 > 0 else 0.
    parallel = coefficient * c
    perpendicular = err - parallel
    q, qp, qo = mean2(err), mean2(parallel), mean2(perpendicular)
    if not math.isclose(q, qp + qo, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError('Orthogonal error decomposition failed')
    edge = torch.zeros_like(c[:, :1])
    edge[..., 1:, :] += (c[..., 1:, :] - c[..., :-1, :]).square().mean(dim=1, keepdim=True).sqrt()
    edge[..., :, 1:] += (c[..., :, 1:] - c[..., :, :-1]).square().mean(dim=1, keepdim=True).sqrt()
    edge_mean = float(edge.mean())
    raw = 1. + .5 * edge / edge_mean if edge_mean > 0 else torch.ones_like(edge)
    # Normalize first, then clip. Record the actual post-clip mean explicitly.
    weights = (raw / raw.mean()).clamp(.5, 2.)
    return dict(alpha_grid=curve, q_C=qc, q_Phi=q, correction_energy=d2,
        error_correction_inner_product=ed,
        error_correction_cosine=ed / math.sqrt(qc * d2) if qc > 0 and d2 > 0 else None,
        diagnostic_oracle_alpha_unconstrained=raw_alpha, diagnostic_oracle_alpha_clipped=alpha,
        diagnostic_oracle_MSE=mean2(e + alpha * d), zero_correction=d2 == 0,
        q_parallel=qp, q_perpendicular=qo, q_edge=float((weights * err.square()).mean()),
        q_combo=float((weights * perpendicular.square()).mean()) + .25 * qp,
        zero_visible_direction=cnorm2 == 0, edge_gamma=.5,
        edge_weight_min=float(weights.min()), edge_weight_max=float(weights.max()),
        edge_weight_mean_after_clipping=float(weights.mean()),
        normalization='all squared norms divided by tensor numel',
        uses_current_teacher=True, deployable_online_score=False,
        CFG_or_propagation_gain_applied_again=False)


def legal_mask(mask, *, maximum_age=6):
    if len(mask) != 36 or any(a not in ('C', 'D') for a in mask):
        return False
    if any(mask[n - 1] != 'D' for n in (*range(1, 8), 36)):
        return False
    last = 0
    for step, action in enumerate(mask, 1):
        if action == 'D':
            last = step
        elif not 1 <= step - last <= maximum_age:
            return False
    return True


def one_exchange(scores, base_mask):
    if (len(scores) != 36 or any(not math.isfinite(v) or v < 0 for v in scores)
            or not legal_mask(base_mask) or base_mask.count('D') != 26):
        raise ValueError('Nonnegative 36 scores and a legal 26D/10C mask required')
    candidates = []
    for remove in range(8, 36):
        if base_mask[remove - 1] != 'D':
            continue
        for add in range(8, 36):
            if base_mask[add - 1] != 'C':
                continue
            mask = list(base_mask)
            mask[remove - 1], mask[add - 1] = 'C', 'D'
            delta = scores[add - 1] - scores[remove - 1]
            if delta > 0 and legal_mask(mask):
                candidates.append((delta, remove, add, mask))
    if not candidates:
        return dict(status='NO_DISTINCT_POSITIVE_SINGLE_EXCHANGE', changed=False,
                    mask=list(base_mask), remove_D=None, add_D=None)
    delta, remove, add, mask = sorted(candidates, key=lambda q: (-q[0], q[1], q[2]))[0]
    return dict(status='ONE_LEGAL_EXCHANGE_FROZEN_NOT_ENDPOINT_RESULT', changed=True,
                remove_D=remove, add_D=add, score_delta=delta, mask=mask,
                D_count=mask.count('D'), C_count=mask.count('C'),
                equal_count_is_not_equal_real_cost=True)


def native_variation(guided, gains, *, torch):
    if len(guided) != 36 or len(gains) != 36 or any(not math.isfinite(g) or g < 0 for g in gains):
        raise ValueError('Actual36 velocities and source-bound positive gain prior required')
    if any(x.device.type != 'cpu' or not x.is_floating_point()
           or x.shape != guided[0].shape or not bool(torch.isfinite(x).all()) for x in guided):
        raise ValueError('Finite equally shaped CPU guided velocities required')
    # Step1 has no preceding saved velocity. It is protected, never exchanged.
    unweighted = [0.] + [float((b.double() - a.double()).square().mean())
                        for a, b in zip(guided, guided[1:])]
    return dict(unweighted=unweighted, gain_squared_weighted=[g*g*v for g, v in zip(gains, unweighted)],
        step1_score_missing_set_zero_only_because_protected=True,
        gain_squared_applied_times=1, independent_native_trajectory_not_same_state_teacher=True,
        geometric_curvature_or_optimal_schedule_claim=False)
