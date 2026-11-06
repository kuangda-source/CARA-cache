"""Saved warm guided predictions only; no sampling or deployment state changes."""
import math

METHODS = ('S26-C', 'S25-C', 'S25-A')
INDEX = 20  # Actual solver update21, not a CFG branch invocation.


def compare_round(predictions, rows, *, expected_shape, validated_same_input, torch):
    if set(predictions) != set(METHODS) or set(rows) != set(METHODS):
        raise ValueError('All three original warm positions required')
    for method in METHODS:
        guides = predictions[method]
        if len(guides) != 36:
            raise ValueError('Keep every original36 guided prediction')
        for x in guides:
            if (not isinstance(x, torch.Tensor) or x.device.type != 'cpu' or not x.is_floating_point()
                    or list(x.shape) != list(expected_shape) or not bool(torch.isfinite(x).all())):
                raise ValueError('Original finite CPU guided tensors with their expected shape required')
    reasons = []
    if validated_same_input is not True:
        reasons.append('COMMON_INPUT_AND_REPLAY_IDENTITY_NOT_VALIDATED')
    scene = rows['S26-C'].get('scene')
    if not isinstance(scene, str) or not scene or any(rows[m].get('scene') != scene for m in METHODS):
        reasons.append('SCENE_DIFFERS')
    repeat = rows['S26-C'].get('round')
    if type(repeat) is not int or repeat not in (1, 2) or any(rows[m].get('round') != repeat for m in METHODS):
        reasons.append('REPLAY_ROUND_DIFFERS')
    if any(rows[m].get('method') != m for m in METHODS):
        reasons.append('METHOD_METADATA_NOT_BOUND')
    time = rows['S26-C'].get('scheduler_timesteps')
    if (not isinstance(time, list) or len(time) < 36
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in time)
            or any(rows[m].get('scheduler_timesteps') != time for m in METHODS)):
        reasons.append('ACTUAL_TIMESTEP_SEQUENCE_NOT_EQUAL')
    actions = {m: rows[m].get('actions') for m in METHODS}
    if (any(not isinstance(a, list) or len(a) != 36 or a[:INDEX] != ['DD'] * INDEX
            for a in actions.values())
            or actions['S26-C'][INDEX] != 'DD'
            or any(actions[m][INDEX] != 'CC' for m in ('S25-C', 'S25-A'))):
        reasons.append('EXPECTED_DENSE_PREFIX_OR_UPDATE21_ACTION_NOT_VERIFIED')
    prefix = {}
    for m in ('S25-C', 'S25-A'):
        prefix[m] = [x.dtype == y.dtype and torch.equal(x, y)
                     for x, y in zip(predictions['S26-C'][:INDEX], predictions[m][:INDEX])]
        if not all(prefix[m]):
            reasons.append(m + '_GUIDED_PREFIX_NOT_BIT_EQUAL')
    out = dict(actual_solver_update=21, zero_based_guided_index=INDEX,
        prefix_guided_equal=prefix, same_state_verified=not reasons, reasons=reasons,
        reference='S26-C_FULL_D_AT_UPDATE21', absolute_guided_MSE_C=None,
        absolute_guided_MSE_A=None, reference_energy=None, relative_guided_MSE_C=None,
        relative_guided_MSE_A=None, A_over_C_when_C_positive=None,
        local_MSE_reduction_fraction=None, CFG_or_propagation_gain_applied_again=False,
        local_error_is_terminal_video_loss=False, independent_scene_count=1)
    if reasons:
        out['status'] = 'SAME_STATE_UNVERIFIED_LOCAL_ERRORS_LEFT_EMPTY'
        return out
    teacher = predictions['S26-C'][INDEX].double()
    c = predictions['S25-C'][INDEX].double()
    a = predictions['S25-A'][INDEX].double()
    qc = float((c - teacher).square().mean())
    qa = float((a - teacher).square().mean())
    energy = float(teacher.square().mean())
    if any(not math.isfinite(v) or v < 0 for v in (qc, qa, energy)):
        raise ValueError('Finite nonnegative FP64 reductions required')
    out.update(status='SAME_REPLAY_PREFIX_UPDATE21_GUIDED_ERRORS_COMPUTED',
        absolute_guided_MSE_C=qc, absolute_guided_MSE_A=qa, reference_energy=energy,
        relative_guided_MSE_C=qc / energy if energy > 0 else None,
        relative_guided_MSE_A=qa / energy if energy > 0 else None,
        A_over_C_when_C_positive=qa / qc if qc > 0 else None,
        local_MSE_reduction_fraction=(qc - qa) / qc if qc > 0 else None,
        zero_reference_energy=energy == 0, zero_C_error=qc == 0)
    return out
