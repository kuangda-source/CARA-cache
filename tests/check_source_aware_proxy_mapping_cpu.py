"""Scientific invariants for empirical proxy-scale anchoring."""
import copy
import math

from wcomr.source_aware_proxy_mapping import map_creation_error, summarize_modes


def run():
    packets=[{'slot':0,'counter':22,'delta_y':2.}, {'slot':1,'counter':23,'delta_y':1.}]
    kw=dict(scene='s',step=12,anchor=7,packets=packets,rho=1.,
            C_guided_MSE=16.,P_guided_MSE=4.,mode='P')
    row=map_creation_error(**kw)
    assert row['C_local_WC_PAID_DELTA_Y_proxy']==9.
    assert row['empirically_mapped_creation_floor_proxy']==4.5
    scaled=copy.deepcopy(kw)
    for packet in scaled['packets']: packet['delta_y']*=3
    assert map_creation_error(**scaled)['empirically_mapped_creation_floor_proxy']==13.5
    normalized=dict(kw,C_guided_MSE=64.,P_guided_MSE=16.)
    assert map_creation_error(**normalized)['empirically_mapped_creation_floor_proxy']==4.5
    zero=map_creation_error(**dict(kw,C_guided_MSE=0.))
    assert not zero['defined'] and zero['empirically_mapped_creation_floor_proxy'] is None
    exact=map_creation_error(**dict(kw,P_guided_MSE=0.))
    assert exact['defined'] and exact['empirically_mapped_creation_floor_proxy']==0.
    reversed_pair=list(reversed(packets))
    rejected=0
    for change in [{'packets':reversed_pair},{'step':11},{'anchor':12},
                   {'rho':1.01},{'C_guided_MSE':-1.},{'P_guided_MSE':math.nan}]:
        try: map_creation_error(**dict(kw,**change))
        except ValueError: rejected+=1
        else: raise AssertionError('Invalid actual origin accepted')
    a=map_creation_error(**dict(kw,scene='a'))
    b=map_creation_error(**dict(kw,scene='b',P_guided_MSE=1.))
    one=summarize_modes([a,b],modes=['P'],origins=[('a',12),('b',12)])
    assert one==summarize_modes([b,a],modes=['P'],origins=[('b',12),('a',12)])
    unavailable=summarize_modes([a,dict(zero,scene='b')],modes=['P'],origins=[('a',12),('b',12)])
    assert unavailable[0]['median_mapped_creation_floor_proxy'] is None
    assert not unavailable[0]['positive_first_development_prior_available']
    for values in [[a],[a,a],[a,b,b]]:
        try: summarize_modes(values,modes=['P'],origins=[('a',12),('b',12)])
        except ValueError: rejected+=1
        else: raise AssertionError('Incomplete or duplicated denominator accepted')
    return {'checks':'PASS','same_unit_scaling_preserved':True,
        'actual_origin_and_complete_denominator_refusals':rejected,
        'zeros_not_hidden_by_epsilon':True,'future_drift_or_cost_not_fabricated':True}


if __name__=='__main__':
    import json
    print(json.dumps(run()))
