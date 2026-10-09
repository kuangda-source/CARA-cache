"""Physical P0 inventory restoration through actual source Block computation."""
import copy
from dataclasses import replace
import torch

from wcomr.partial_mlp_state import ProjectionRoundtrip


def run_control(executor, arm):
    rng=torch.random.get_rng_state().clone()
    baseline={key:(c.value.clone(),c.updated_at.clone(),c.source.clone(),
                   c.context,c.parameter_versions,c.last_actual_D) for key,c in executor.cache.items()}
    records=copy.deepcopy(executor.records)
    checkpoint=ProjectionRoundtrip(executor,logical_copy_cap_bytes=1<<20)
    assert checkpoint.bytes==sum(t.numel()*t.element_size() for c in executor.cache.values()
                                 for t in (c.value,c.updated_at,c.source))
    refused=[]
    for label,budget in [('zero_budget',0),('insufficient_budget',checkpoint.bytes-1)]:
        try:ProjectionRoundtrip(executor,logical_copy_cap_bytes=budget)
        except ValueError:refused.append(label)
        else:raise AssertionError(label)
    key=next(iter(executor.cache));original=executor.cache.pop(key)
    try:
        try:ProjectionRoundtrip(executor,logical_copy_cap_bytes=1<<20)
        except ValueError:refused.append('incomplete_two_branch_inventory')
        else:raise AssertionError('Incomplete projection scope accepted')
    finally:executor.cache[key]=original
    def physical_check():
        assert set(executor.cache)==set(baseline)
        for key,c in executor.cache.items():
            v,a,s,context,versions,last=baseline[key]
            assert torch.equal(c.value,v) and torch.equal(c.updated_at,a) and torch.equal(c.source,s)
            assert (c.context,c.parameter_versions,c.last_actual_D)==(context,versions,last)
        assert executor.last_step==6 and not executor.poisoned and executor.records==records
        assert torch.equal(torch.random.get_rng_state(),rng)
    first=arm()
    assert executor.last_step==7 and executor.records!=records
    for key,c in list(executor.cache.items()):
        c.value.add_(999);c.updated_at.fill_(-99);c.source.fill_(99)
        executor.cache[key]=replace(c,context=('mutated','mutated','mutated'),last_actual_D=999)
    executor.last_step=999;executor.poisoned=True;executor.records.append({'mutated':True})
    checkpoint.restore();physical_check()
    try:arm(fail_second=True)
    except ValueError as error:assert str(error)=='Injected score-only state arm second-branch failure'
    else:raise AssertionError('Score-only complete arm failure did not execute')
    assert executor.poisoned and executor.last_step==6
    checkpoint.restore();physical_check()
    replay=arm()
    assert all(torch.equal(first[key],replay[key]) for key in first)
    checkpoint.restore();physical_check()
    installed=dict(executor._original);executor._original.pop(executor.layers[0])
    try:
        try:checkpoint.restore()
        except ValueError:refused.append('changed_installation')
        else:raise AssertionError('Changed installation accepted')
    finally:executor._original=installed
    physical_check()
    assert len(refused)==4
    return {'status':'P0_ADDITIONAL_PHYSICAL_INVENTORY_ROUNDTRIP_CPU_PASS',
            'snapshot_logical_bytes':checkpoint.bytes,'complete_successful_counterfactual_pairs':2,
            'failed_second_branch_score_only_pair_retained':True,
            'all_projection_values_and_age_source_context_D_history_physically_restored':True,
            'poison_records_last_step_restored':True,'saved_checkpoint_independent_of_later_mutations':True,
            'repeat_same_origin_projection_outputs_direct_equal':True,'global_RNG_unchanged':True,
            'refusals':refused,'complete_Cosmos_or_solver_RNG_inventory_claim':False}
