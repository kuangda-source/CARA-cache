"""Budget transition and actual-cost controls; no Torch or ledger mutation."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
from wcomr.rv0_small_execution import (admission_budget, audit_settlement,
    budget_authority, reserve_budget, settle_budget, validate_config)


def run(config, raw, budget, legacy_config):
    spec = importlib.util.spec_from_file_location('legacy_small_contracts', Path(__file__).with_name('check_rv0_small_production_cpu.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    legacy_budget = raw['budget_before']
    legacy = module.run(legacy_config, raw, legacy_budget)
    assert legacy['refusal_count'] == 32
    assert budget['used_gpu_hours'] == legacy_budget['used_gpu_hours']
    assert budget['gpu_jobs_launched'] == legacy_budget['gpu_jobs_launched'] == 45
    assert budget_authority(config)[0] == 24
    validate_config(config, selected=True)
    gate = admission_budget(budget, config)
    assert gate['required_seconds'] == 3915 and gate['fits']
    refused = []
    def reject(name, function):
        try: function()
        except (ValueError, KeyError, TypeError): refused.append(name)
        else: raise AssertionError('Malformed budget authority admitted: '+name)
    for name, changes in [('old_cap', {'cap_gpu_hours':13}),
            ('old_authority', {'budget_authorization_ref':legacy_budget['budget_authorization_ref']}),
            ('cap_overrun', {'used_gpu_hours':24.01}), ('negative_usage', {'used_gpu_hours':-1}),
            ('nonfinite_usage', {'used_gpu_hours':float('nan')}), ('boolean_usage', {'used_gpu_hours':True}),
            ('insufficient_whole_card', {'used_gpu_hours':23.5}), ('inflight', {'other_inflight':{}})]:
        reject(name, lambda changes=changes:admission_budget({**budget,**changes},config))
    for name, changes in [('authority_cap',{'cumulative_cap_gpu_hours':25}),
            ('usage_reset',{'usage_reset':True}), ('boolean_reset_alias',{'usage_reset':0}),
            ('expanded_timeout',{'single_run_inclusive_cap_seconds':6900}),
            ('different_card',{'approved_card':'other'})]:
        broken=copy.deepcopy(config);broken['execution_budget_authority'].update(changes)
        reject(name,lambda broken=broken:validate_config(broken,selected=True))
    broken=copy.deepcopy(config);broken['scope']['new_encoded_outputs']=6
    reject('science_scope_shrunk',lambda:validate_config(broken,selected=True))
    reserved=reserve_budget(budget,config,1101)
    assert reserved['cap_gpu_hours']==24 and reserved['used_gpu_hours']==budget['used_gpu_hours']+3900/3600
    assert reserved['gpu_jobs_launched']==46
    for wall in [7.0,600.0,3900.0]:
        settled=settle_budget(reserved,budget,config,wall,1101)
        assert settled['used_gpu_hours']==budget['used_gpu_hours']+wall/3600
        assert settled['gpu_jobs_launched']==46 and not any(k.endswith('_inflight') for k in settled)
        supervisor={'status':'EXITED_REQUIRES_RESULT_AUDIT','exit_code':0,'source_revision':'a'*40,
            'run_id':config['run_id'],'config':config,'reserved_seconds':3900,'hard_wall_cap_exceeded':False,
            'wall_seconds':wall,'planned_parent_phases':2,'planned_suffix_controls':12,'planned_encoded_outputs':8,
            'budget_before':budget,'budget_after':settled,'pid':1101,'child_pid':1102}
        assert audit_settlement(supervisor,{'source_revision':'a'*40,'pid':1103},config,settled,'a'*40)==[1101,1102,1103]
    changed={**reserved,'used_gpu_hours':reserved['used_gpu_hours']+.1}
    reject('concurrent_settlement_edit',lambda:settle_budget(changed,budget,config,600,1101))
    reject('historical_draft_cannot_spend24',lambda:admission_budget(budget,legacy_config))
    return {'status':'SMALL_CD_BUDGET24_CPU_DELTA_AND_LEGACY32_PASS_NOT_GPU',
        'legacy_refusal_count':legacy['refusal_count'],'delta_refusal_count':len(refused),'delta_refusals':refused,
        'failed_attempt_and_full_cap_charged_without_reset':True,'science_core67_unchanged':True,
        'budget_gate':gate,'GPU_submissions':0,'ledger_written':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['config','raw-receipt','budget','legacy-config']:
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    print(json.dumps(run(*[json.loads(getattr(a,n).read_text()) for n in ['config','raw_receipt','budget','legacy_config']]),allow_nan=False))
