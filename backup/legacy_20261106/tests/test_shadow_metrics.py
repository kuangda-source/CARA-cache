import pytest
import torch
from wcomr.shadow_metrics import tensor_error, score_shadow_pair


def test_smaller_residual_error_can_have_larger_downstream_error_without_state_mutation():
    truth=torch.tensor([1., 1.], requires_grad=True)
    a=truth.detach()+torch.tensor([.1, 0.])
    b=truth.detach()+torch.tensor([0., .2])
    downstream=torch.diag(torch.tensor([10., 1.]))
    rng=torch.get_rng_state().clone(); original=truth.detach().clone()
    def score(x):
        return score_shadow_pair(residual_prediction=x, residual_truth=truth,
                                 velocity_prediction=downstream@x, velocity_truth=downstream@truth)
    sa,sb=score(a),score(b)
    assert sa['residual']['relative_mse'] < sb['residual']['relative_mse']
    assert sa['velocity']['relative_mse'] > sb['velocity']['relative_mse']
    assert torch.equal(truth,original) and truth.grad is None
    assert torch.equal(torch.get_rng_state(),rng)


def test_explicit_time_axis_localizes_error():
    truth=torch.ones(1,2,3,4,4)
    prediction=truth.clone();prediction[:,:,1,:,:]+=2
    r=tensor_error(prediction,truth,group_axes={'time':2,'channel':1})
    assert r['groups']['time']['mse']==[0,4,0]
    assert len(r['groups']['channel']['mse'])==2
    assert r['relative_mse']==pytest.approx(4/3)


def test_zero_reference_is_undefined_not_arbitrarily_large_score():
    r=tensor_error(torch.ones(2),torch.zeros(2),group_axes={'component':0})
    assert r['mse']==1 and r['relative_mse'] is None and r['direction_cosine'] is None
    assert r['groups']['component']['relative_mse']==[None,None]


def test_invalid_shape_and_nonfinite_are_explicit():
    with pytest.raises(ValueError):tensor_error(torch.ones(2),torch.ones(1))
    with pytest.raises(ValueError):tensor_error(torch.ones(2),torch.ones(2),group_axes={'time':2})
    assert tensor_error(torch.tensor([float('nan')]),torch.ones(1))['status']=='NONFINITE_INPUT'
    assert tensor_error(torch.tensor([1e30]),torch.ones(1))['status']=='NONFINITE_REDUCTION'
