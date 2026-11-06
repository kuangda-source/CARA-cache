#!/usr/bin/env python3
"""Reuse the accepted actual model entry with explicit two-flow bindings."""
from pathlib import Path


old = Path(__file__).with_name('run_wc_e4c_source_age_r1.py')
source = old.read_text()
changes = [
    ('wcomr.e4c_source_age_production_r1', 'wcomr.p_reference_same_state_production_r1'),
    ('wcomr.e4c_matched_source_age_sampling_r1', 'wcomr.p_reference_same_state_sampling_r1'),
    ("p.add_argument('--cpu-check',action='store_true');p.add_argument('--arm')",
     "p.add_argument('--cpu-check',action='store_true');p.add_argument('--arm',required=True,choices=['FLOW_OFF','FLOW_ON'])"),
    ("args.stage/'e4c-requests.jsonl'", "args.stage/'p-reference-requests.jsonl'"),
    ("'E4C_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'", "'P_REFERENCE_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'"),
    ("'forecast_complete_GPUh':8.1", "'forecast_complete_GPUh':float('nan')"),
    ("'training':True,'human_review':True,'empty_cache_or_gate_bypass':True,'continue_after_failure':'CONTINUE'",
     "'training':True,'human_review':True,'empty_cache_or_gate_bypass':True,'continue_after_failure':'CONTINUE',\n            'flow_arms':{'FLOW_ON':True},'candidate_variants':['OFFICIAL_C'],'native_head_elision_combined':True"),
    ("'scope_counts':c['scope_counts'],", "'scope_counts':c['scope_counts'],'arm':args.arm,'flow':c['flow_arms'][args.arm],\n            'per_flow_scope_counts':scope['per_flow_scope_counts'],'production_entry_inverse_proof':ENTRY_PROOF,"),
    ("if args.arm is not None:raise ValueError('E4c is one complete model job, without arm selection')",
     "if args.arm not in c['flow_arms']:raise ValueError('One of two registered whole flow arms required')"),
    ("output=args.project/'outputs'/RUN/'model'", "output=args.project/'outputs'/RUN/args.arm"),
    ("'scope':scope,'planned_paths':4,", "'scope':scope,'arm':args.arm,'flow':c['flow_arms'][args.arm],'planned_paths':4,"),
    ("params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))",
     "params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output),worldcache_flow_enabled=c['flow_arms'][args.arm])"),
    ("settings=old['historical_wc_settings'];assert all(getattr(net,k)==v for k,v in settings.items())",
     "settings=dict(old['historical_wc_settings']);settings['worldcache_flow_enabled']=c['flow_arms'][args.arm]\n        assert all(getattr(net,k)==v for k,v in settings.items())"),
    ("'E4C_ARM_INITIALIZING'", "'P_REFERENCE_ARM_INITIALIZING'"),
    ("'E4C_ARM_COMPLETE_SCOPE_RUNNING'", "'P_REFERENCE_ARM_COMPLETE_SCOPE_RUNNING'"),
    ("'E4C_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT'", "'P_REFERENCE_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT'"),
    ("'E4C_ARM_PROTECTED_CAPACITY_STOP'", "'P_REFERENCE_ARM_PROTECTED_CAPACITY_STOP'"),
    ("'E4C_ARM_TECH_FAILED_SCOPE_RETAINED'", "'P_REFERENCE_ARM_TECH_FAILED_SCOPE_RETAINED'")]
changed = source
for before, after in changes:
    if changed.count(before) != 1: raise ValueError('Accepted actual entry source site differs: '+before)
    changed = changed.replace(before, after)
inverse = changed
for before, after in reversed(changes):
    if inverse.count(after) != 1: raise ValueError('Actual entry inverse source site ambiguous')
    inverse = inverse.replace(after, before)
if inverse != source: raise ValueError('Unregistered actual model entry change')
ENTRY_PROOF = {'accepted_E4c_actual_entry_inverse_bytes_equal': True,
    'changes': [before for before, after in changes],
    'numeric_P_readout_sources_unchanged': True, 'shared_flow_setting_for_OFF_ON_collection': True,
    'full_native_heads_and_copy_gates_preserved': True, 'GPU_launch_or_authorization': False}
exec(compile(changed, __file__+'#actual-two-flow-entry', 'exec'), globals())
