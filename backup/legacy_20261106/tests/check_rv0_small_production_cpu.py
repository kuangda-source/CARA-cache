"""CPU-only production contracts against original raw CPU controls.

No Torch, model load, subprocess launch, GPU reservation, or real-video claim.
The synthetic reference bridge is explicitly excluded from production.
"""
import argparse
import copy
import json
from pathlib import Path
from wcomr.rv0_small_execution import validate_config, reserve_budget, settle_budget, admission_budget, audit_settlement
from wcomr.rv0_small_evaluation import audit_trajectories, evaluation_plan


def run(config, raw, budget):
    rejected = []
    def refuse(name, function):
        try: function()
        except (ValueError, KeyError, AssertionError, TypeError): rejected.append(name)
        else: raise AssertionError('Malformed contract was accepted: '+name)
    validate_config(config)
    selected = copy.deepcopy(config); selected.update(GPU_execution_selected=True, gpu_uuid='GPU-CPU-CONTRACT-NOT-A-DEVICE')
    validate_config(selected, selected=True)
    refuse('unselected_not_admitted', lambda: admission_budget(budget, config))
    for name, mutation in [('missing_source', lambda c:c['payload_sha256'].pop('src/wcomr/rv0_small_causal.py')),
        ('changed_CPU_source', lambda c:c['payload_sha256'].update({'src/wcomr/rv0_actions.py':'a'*64})),
        ('removed_control',lambda c:c['scope'].update(complete_suffix_controls=10)),
        ('wrong_scene_slot',lambda c:c.update(target_calls=[46,45]))]:
        broken=copy.deepcopy(config);mutation(broken);refuse(name,lambda:validate_config(broken))
    for name, changes in [('insufficient_complete_cap',{'used_gpu_hours':12.5}),
        ('other_inflight',{'other_inflight':{}}),('nonfinite_usage',{'used_gpu_hours':float('nan')}),
        ('wrong_budget_cap',{'cap_gpu_hours':12})]:
        broken={**budget,**changes};refuse(name,lambda:admission_budget(broken,selected))
    reserved=reserve_budget(budget,selected,1101)
    assert reserved['used_gpu_hours']==budget['used_gpu_hours']+3900/3600
    settled=settle_budget(reserved,budget,selected,600.0,1101)
    assert settled['used_gpu_hours']==budget['used_gpu_hours']+600/3600
    assert settled['gpu_jobs_launched']==budget['gpu_jobs_launched']+1
    assert not any(k.endswith('_inflight') for k in settled)
    failure_settled=settle_budget(reserved,budget,selected,7.0,1101)
    assert failure_settled['used_gpu_hours']==budget['used_gpu_hours']+7/3600
    for wall in (0,-1,float('inf'),float('nan')):
        refuse('bad_actual_cost_'+str(wall),lambda: settle_budget(reserved,budget,selected,wall,1101))
    changed={**reserved,'gpu_jobs_launched':reserved['gpu_jobs_launched']+1}
    refuse('concurrent_ledger_edit',lambda:settle_budget(changed,budget,selected,600,1101))
    source='a'*40
    supervisor={'status':'EXITED_REQUIRES_RESULT_AUDIT','exit_code':0,'source_revision':source,
        'run_id':selected['run_id'],'config':selected,'reserved_seconds':3900,'hard_wall_cap_exceeded':False,
        'wall_seconds':600.0,'planned_parent_phases':2,'planned_suffix_controls':12,'planned_encoded_outputs':8,
        'budget_before':budget,'budget_after':settled,'pid':1101,'child_pid':1102}
    fake_runner={'source_revision':source,'pid':1103}
    assert audit_settlement(supervisor,fake_runner,selected,settled,source)==[1101,1102,1103]
    wrong=copy.deepcopy(supervisor);wrong['budget_after']['used_gpu_hours']+=.01
    refuse('terminal_wrong_cost',lambda:audit_settlement(wrong,fake_runner,selected,wrong['budget_after'],source))
    wrong=copy.deepcopy(supervisor);wrong['reserved_seconds']=6900
    refuse('terminal_legacy_reservation',lambda:audit_settlement(wrong,fake_runner,selected,settled,source))
    wrong=copy.deepcopy(supervisor);wrong['child_pid']=1101
    refuse('terminal_duplicate_PID',lambda:audit_settlement(wrong,fake_runner,selected,settled,source))
    controls=raw['controls']['controls']['checks']
    successes=[c['receipt'] for c in controls if c['failure'] is None]
    assert len(successes)==2
    audits=[audit_trajectories(r,2) for r in successes]
    assert sum(a['parents'] for a in audits)==4 and sum(a['complete_suffixes'] for a in audits)==24
    receipt=successes[0]
    for name, mutation in [('missing_child',lambda r:r['requests'][0]['children'].pop()),
        ('wrong_child_slot',lambda r:r['requests'][0]['children'][2].update(slot=1)),
        ('wrong_label_action',lambda r:r['requests'][0]['children'][2].update(action='OFF')),
        ('same_input_changed',lambda r:r['requests'][0]['children'][2]['inputs'][0].update(corrupt='x')),
        ('repeat_changed',lambda r:r['requests'][0]['children'][5]['outputs'].__setitem__(0,'f'*64)),
        ('partial_deep_execution',lambda r:r['requests'][0]['children'][2]['deep'].__setitem__(2,1)),
        ('unpaid_probe',lambda r:r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0].update(paid_probe=False)),
        ('current_truth_leak',lambda r:r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0].update(current_deep_truth_used=True)),
        ('future_full_anchor',lambda r:r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0]['true_full_history'][0].append(24)),
        ('lost_parent_restore',lambda r:r['requests'][0]['children'][2]['record'].update(parent_restored=False)),
        ('truncated_pipeline',lambda r:r['requests'][0]['decoded_children'][1]['pipeline'].pop()),
        ('wrong_OFF_encoded_bridge',lambda r:r['requests'][0]['decoded_children'][0]['artifact'].update(sha256='b'*64))]:
        broken=copy.deepcopy(receipt);mutation(broken);refuse(name,lambda:audit_trajectories(broken,2))
    # A synthetic bridge exercises only the pure evaluation-plan shape contract.
    # It cannot pass the default real_GPU_required=True production path.
    synthetic=copy.deepcopy(receipt);synthetic_config=copy.deepcopy(config)
    for index,row in enumerate(synthetic['requests']):
        scene=config['sample_names'][index];row['sample_name']=scene
        row['context']=['CPU_SYNTHETIC_REFERENCE_BRIDGE_ONLY',*config['references'][scene]['model_and_condition_context']]
        row['historical_WC_encoded_bridge_pass']=True
        synthetic_config['references'][scene]['official_WC']['sha256']=row['artifact']['sha256']
    plan=evaluation_plan(synthetic,synthetic_config,real_GPU_required=False)
    assert (len(plan['files']),len(plan['references']),len(plan['pairs']),len(plan['bridges']))==(8,2,4,2)
    assert [(p['CFG_slot'],p['action']) for p in plan['pairs']]==[(0,'C'),(0,'D'),(1,'C'),(1,'D')]
    refuse('CPU_fixture_not_GPU_video',lambda:evaluation_plan(synthetic,synthetic_config))
    broken=copy.deepcopy(synthetic);broken['requests'][0]['historical_WC_encoded_bridge_pass']=False
    refuse('missing_historical_bridge',lambda:evaluation_plan(broken,synthetic_config,real_GPU_required=False))
    broken=copy.deepcopy(synthetic);broken['requests'][0]['decoded_children'][1]['artifact']['path']=broken['requests'][0]['artifact']['path']
    refuse('duplicate_artifact_paths',lambda:evaluation_plan(broken,synthetic_config,real_GPU_required=False))
    return {'status':'SMALL_CD_PRODUCTION_PURE_CPU_RAW_CONTRACTS_PASS_NOT_GPU',
        'refusals':rejected,'refusal_count':len(rejected),'raw_successful_parents':4,'raw_successful_suffixes':24,
        'evaluation_shape':{'new_files':8,'existing_references':2,'Native_relative_pairs':4,'signed_diagnostics':2},
        'terminal_actual_settlement_reconstructed':True,'failed_attempt_cost_retained':True,
        'synthetic_reference_bridge_not_real_GPU':True,'GPU_submissions':0,'ledger_written':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['config','raw-receipt','budget']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(json.loads(args.config.read_text()),json.loads(args.raw_receipt.read_text()),json.loads(args.budget.read_text()))))
