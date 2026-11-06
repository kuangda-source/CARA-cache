#!/usr/bin/env python3
"""All completed teacher timer scopes; no tensor, GPU, or budget writes."""
import argparse
import ast
from decimal import Decimal, getcontext
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

getcontext().prec=50
STEMS=('wc_cfg_guided_teacher_r1','wc_cfg_mechanism_confirmation_r1')
ORIGINS=('S22','S23_after_CC','S23_after_DC','S23_after_CD','S23_after_DD')
MODES=('CC','DC','CD','DD')
DONE='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def check_source(revision,payload):
    names=('src/wcomr/cfg_teacher_collection.py','src/wcomr/cfg_teacher_sampling.py')
    proof={}
    texts={}
    for name in names:
        raw=subprocess.check_output(['git','show',revision+':'+name]);assert sha(raw)==payload[name]
        texts[name]=raw.decode();proof[name]=sha(raw)
    tree=ast.parse(texts[names[0]])
    measure=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='measure')
    start=next(n for n in measure.body if isinstance(n,ast.Assign) and ast.unparse(n).startswith('started = time.perf_counter()'))
    outer=next(n for n in measure.body if isinstance(n,ast.Try))
    advances=[n for n in ast.walk(outer) if isinstance(n,ast.Call) and ast.unparse(n)=='advance(child)']
    timers=[n for n in ast.walk(outer) if isinstance(n,ast.Assign) and any(ast.unparse(t)=="record['wall_seconds']" for t in n.targets)]
    assert len(advances)==len(timers)==1 and start.lineno<outer.lineno
    assert any(timers[0] is n for body in outer.finalbody for n in ast.walk(body))
    assert ast.unparse(timers[0].value)=='time.perf_counter() - started'
    sample=ast.parse(texts[names[1]])
    child=next(n for n in ast.walk(sample) if isinstance(n,ast.FunctionDef) and n.name=='child_origin')
    assert any(isinstance(n,ast.Call) and ast.unparse(n).startswith("fork.measure(child_mode + '_' + repetition, child_mode)") for n in ast.walk(child))
    root_calls=[n for n in ast.walk(sample) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='measure' and any(k.arg=='advance' for k in n.keywords)]
    assert len(root_calls)==1 and any(isinstance(n,ast.Call) and ast.unparse(n)=='child_origin(m, child)' for n in ast.walk(root_calls[0]))
    return {'source_sha256':proof,'root_timer_contains_child_origin_pairs':True,
        'timer_starts_before_try_and_ends_after_final_restore':True,'timestamps_are_not_clean_forward_only':True}


def analyze(stem):
    prefix='reports/'+stem+'_terminal_20261009_'
    cap_path=Path(prefix+'capture.json');audit_path=Path(prefix+'independent_CPU_audit.json')
    cap=json.loads(cap_path.read_text());audit=json.loads(audit_path.read_text())
    assert cap['status']=='TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS'
    assert audit['status']=='TEACHER_TERMINAL_LOCAL_STDLIB_SCOPE_REPEAT_ENERGY_AND_FEE_RECONSTRUCTION_PASS'
    assert audit['capture_sha256']==sha(cap_path.read_bytes()) and audit['strict_repeat_groups']==20
    inputs={str(cap_path):sha(cap_path.read_bytes()),str(audit_path):sha(audit_path.read_bytes())}
    objects={}
    for key in ('runner','supervisor','config'):
        path=Path(prefix+key+'_native.gz');raw=gzip.decompress(path.read_bytes())
        assert sha(raw)==cap['files'][key]['sha256'];objects[key]=json.loads(raw)
        inputs[str(path)]={'compressed_sha256':sha(path.read_bytes()),'raw_sha256':sha(raw)}
    runner,sup,config=(objects[k] for k in ('runner','supervisor','config'))
    assert sup['exit_code']==0 and cap['source_revision']==sup['source_revision']==audit['source_revision']
    parents=runner['teacher']['parents'];assert len(parents)==2
    assert [p['phase'] for p in parents]==['OFF','ON']
    assert all(p['status']=='COMPLETE_PARENT' and len(p['inputs'])==72 and len(p['solver_outputs'])==36 for p in parents)
    origins=parents[1]['origins'];assert [o['label'] for o in origins]==list(ORIGINS)
    scope={o['label']:o for o in origins};flat=[]
    for origin in origins:
        assert origin['status']=='COMPLETE_LOCAL_ORIGIN' and len(origin['pairs'])==8
        assert [p['label'] for p in origin['pairs']]==[m+'_'+n for m in MODES for n in ('first','second')]
        for p in origin['pairs']:
            assert p['status']==DONE and p['parent_restored'] and p['wall_seconds']>0
            flat.append({'origin':origin['label'],'label':p['label'],'mode':p['mode'],
                'wall_seconds':p['wall_seconds'],'includes_child_measurement':bool(p.get('solver_step_reused_measured_velocity_without_net_call'))})
    assert len(flat)==40
    edges=[]
    for mode in MODES:
        root=next(p for p in scope['S22']['pairs'] if p['label']==mode+'_first')
        child=scope['S23_after_'+mode]
        assert root['solver_step_reused_measured_velocity_without_net_call'] and root['child_latent_sha256']
        assert all(p['origin_completed_updates']==23 and not p.get('solver_step_reused_measured_velocity_without_net_call') for p in child['pairs'])
        child_sum=sum(p['wall_seconds'] for p in child['pairs'])
        assert root['wall_seconds']>child_sum
        edges.append({'root_label':root['label'],'child_origin':child['label'],
            'root_inclusive_seconds':root['wall_seconds'],'eight_child_pair_sum_seconds':child_sum,
            'root_less_child_timers_seconds':root['wall_seconds']-child_sum,
            'remainder_still_includes_restore_hash_write_one_solver_and_child_setup':True})
    root_sum=sum(p['wall_seconds'] for p in scope['S22']['pairs'])
    child_sum=sum(p['wall_seconds'] for o in origins[1:] for p in o['pairs'])
    flat_sum=sum(p['wall_seconds'] for o in origins for p in o['pairs'])
    assert abs(flat_sum-root_sum-child_sum)<1e-8 and root_sum<parents[1]['wall_seconds']
    off,on=(p['wall_seconds'] for p in parents)
    load=runner['load_seconds'];outside=sup['wall_seconds']-load-off-on;assert outside>0
    remainder=on-root_sum;extra=remainder-off;assert extra>0
    leaves=[p for p in flat if not p['includes_child_measurement']];assert len(leaves)==36
    # Independent Decimal summation uses native JSON scalars, not float totals.
    d=lambda value:Decimal(str(value))
    decimal_flat=sum((d(p['wall_seconds']) for p in flat),Decimal(0))
    decimal_root=sum((d(p['wall_seconds']) for p in flat if p['origin']=='S22'),Decimal(0))
    decimal_child=sum((d(p['wall_seconds']) for p in flat if p['origin']!='S22'),Decimal(0))
    assert decimal_flat==decimal_root+decimal_child
    for edge in edges:
        rows=scope[edge['child_origin']]['pairs']
        expected=d(edge['root_inclusive_seconds'])-sum((d(p['wall_seconds']) for p in rows),Decimal(0))
        assert abs(float(expected)-edge['root_less_child_timers_seconds'])<1e-9
    return {'run_id':runner['run_id'],'source_revision':sup['source_revision'],'input_sha256':inputs,
        'source_timer_contract':check_source(sup['source_revision'],config['payload_sha256']),
        'all_40_pair_rows':flat,'all_four_nested_edges':edges,'flat_pair_sum_seconds':flat_sum,
        'root_timer_union_seconds':root_sum,'double_counted_child_pair_seconds':child_sum,
        'non_nested_pair_count':len(leaves),'non_nested_pair_max_seconds':max(p['wall_seconds'] for p in leaves),
        'load_seconds':load,'OFF_parent_seconds':off,'ON_parent_seconds':on,
        'ON_less_root_timer_union_seconds':remainder,'extra_uncovered_ON_vs_OFF_seconds':extra,
        'supervisor_outside_load_and_parent_timers_seconds':outside,
        'original_actual_GPU_wall_seconds':sup['wall_seconds'],'original_bill_GPUh':sup['wall_seconds']/3600,
        'original_OFF_full_net_calls':sum(n>0 for n in parents[0]['deep']),
        'Decimal_all_rows_and_edges_independent_arithmetic_pass':True,
        'pair_wall_is_not_clean_latency_or_future_action_cost_label':True}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists();started=time.perf_counter()
    sources=[analyze(s) for s in STEMS]
    maxima={key:max(s[key] for s in sources) for key in ('load_seconds','OFF_parent_seconds','non_nested_pair_max_seconds',
        'extra_uncovered_ON_vs_OFF_seconds','supervisor_outside_load_and_parent_timers_seconds')}
    # Distinct planning scenarios, not selected experiment cards or strict bounds.
    base=maxima['load_seconds']+2*maxima['OFF_parent_seconds']+16*maxima['non_nested_pair_max_seconds']+maxima['extra_uncovered_ON_vs_OFF_seconds']+maxima['supervisor_outside_load_and_parent_timers_seconds']
    full_parent_allowance=maxima['OFF_parent_seconds']*72/min(s['original_OFF_full_net_calls'] for s in sources)
    large=maxima['load_seconds']+48*full_parent_allowance+maxima['supervisor_outside_load_and_parent_timers_seconds']
    result={'status':'COMPLETE_TWO_HUMAN_TEACHER_COST_TREE_CPU_ALL80_PAIRS_NOT_DEPLOYMENT_SPEED',
        'sources':sources,'maxima':maxima,'complete_pair_rows':80,'nested_parent_child_edges':8,
        'planning_scenarios_not_selected_or_admitted':{
            'full_CPU_matrix_GPU_mirror':{'complete_comparisons':24,'full_parent_paths':48,
                'all_full_parent_allowance_seconds':full_parent_allowance,'planning_seconds_with_50percent_reserve':1.5*large,
                'planning_GPUh':1.5*large/3600,'every_parent_scaled_to72full_from35_adaptive_as_cost_allowance_not_claim':True,
                'new_GPU_collector_CPU_and_specific_authorization_not_complete':True},
            'distinct_S22_real_interface_and_local_cost_question':{'complete_comparisons':8,'local_velocity_pairs':16,
                'full_unchanged_parent_paths':2,'actions':['CC','DD'],'observer_modes':['OFF','ON'],'strict_repetitions':2,
                'planning_seconds_with_50percent_reserve':1.5*base,'planning_GPUh':1.5*base/3600,
                'not_full36_candidate_policy_parity_or_quality':True,'does_not_replace_or_shrink_H_T52_or_H_T55':True,
                'unmeasured_compiler_observer_and_controller_costs_require_new_complete_CPU_source_bound_card':True}},
        'CPU_wall_seconds':time.perf_counter()-started,'GPU_submissions':0,'Torch_or_tensor_loading':False,
        'Common_inflight_data_read':False,'budget_written':False,'old_supervisor_bills_or_hypotheses_changed':False}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','maxima')}))


if __name__=='__main__':main()
