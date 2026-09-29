import copy
import pytest
import torch
from wcomr.calibration import ResidualCalibrator, score_shadow


def t(x):
    return torch.full((1, 2, 2, 2, 3), float(x))


def trained():
    c = ResidualCalibrator(ridge=1e-12)
    c.observe_full(context=('request', 'cond', 'expert0'), step=0, probe=t(1), residual=t(3))
    c.observe_full(context=('request', 'cond', 'expert0'), step=6, probe=t(2), residual=t(6))
    return c


def test_actual_full_anchor_and_known_linear_map():
    c = trained()
    p, reason = c.predict(context=c.context, step=10, probe=t(4), official=t(99))
    torch.testing.assert_close(p, t(12))
    assert reason == 'scalar' and c.receipt()['anchor_steps'] == [0, 6]


def test_predict_does_not_observe_current_or_shadow_truth():
    c = trained(); before = copy.deepcopy(c.receipt())
    p, _ = c.predict(context=c.context, step=8, probe=t(3), official=t(99))
    score_shadow(p, t(999999))
    assert before == c.receipt()
    with pytest.raises(ValueError):
        c.predict(context=c.context, step=6, probe=t(3), official=t(99))


@pytest.mark.parametrize('context', [('new_request','cond','expert0'),
                                  ('request','uncond','expert0'),
                                  ('request','cond','expert1')])
def test_context_changes_and_restarts_fall_back(context):
    c = trained(); official = t(10)
    p, reason = c.predict(context=context, step=8, probe=t(3), official=official)
    assert p is official and reason == 'insufficient_anchors'
    assert not c.anchors
    assert not ResidualCalibrator().anchors


def test_invalid_observation_clears_stale_history():
    c = trained()
    assert not c.observe_full(context=c.context, step=8, probe=t(float('nan')), residual=t(10))
    assert c.receipt()['anchor_steps'] == []


@pytest.mark.parametrize('x',[float('inf'),float('nan')])
def test_nonfinite_current_falls_back(x):
    c = trained(); official = t(7)
    p, reason = c.predict(context=c.context, step=8, probe=t(x), official=official)
    assert p is official and reason == 'invalid_input_or_shape'


def test_zero_denominator_and_one_anchor():
    c = ResidualCalibrator(); official = t(9)
    for step in (0, 6):
        c.observe_full(context='x', step=step, probe=t(1), residual=t(step))
    p, reason = c.predict(context='x', step=8, probe=t(2), official=official)
    assert p is official and reason == 'small_denominator'


def test_clipping_and_detached_owned_anchors():
    c = ResidualCalibrator(clip=2, ridge=1e-12)
    p=t(1).requires_grad_(); r=t(100).requires_grad_()
    c.observe_full(context='x',step=0,probe=t(0),residual=t(0))
    c.observe_full(context='x',step=6,probe=p,residual=r)
    with torch.no_grad(): p.fill_(1000); r.fill_(1000)
    out, _ = c.predict(context='x',step=8,probe=t(2),official=t(0))
    torch.testing.assert_close(out,t(102))
    assert not c.anchors[-1].probe.requires_grad


def test_shrink_uses_actual_anchor_spacing():
    c = trained()
    out, _ = c.predict(context=c.context,step=9,probe=t(4),official=t(0),mode='shrink')
    torch.testing.assert_close(out,t(6.75))


def test_official_identity_and_nonfinite_config():
    c=trained(); official=t(9)
    p,_=c.predict(context=c.context,step=8,probe=t(3),official=official,mode='official')
    assert p is official
    with pytest.raises(ValueError): ResidualCalibrator(clip=float('inf'))
