"""Frozen full S science, with two alternative all-new ten-role allocations."""
RUN='cara-sq-s-complete-r2-20261029'
PLAN='plans/cara_next_stage_20261028/sq/'
SCOPE=PLAN+'S_WHOLE_SCOPE_R2.json'
PROFILE=PLAN+'S_EXECUTION_PROFILE_R3.json'
IDENTITY=PLAN+'S_EXECUTION_IDENTITY_R1.json'
RESOURCE=PLAN+'S_RESOURCE_GUARD_REAL_CONTRACT_R1.json'
ASSETS=PLAN+'S_MODEL_ASSETS_R1.json'
MODE='manifests/wc_h0_eval_mode_contract_20261003.json'
RISK=PLAN+'S_FROZEN_RISK_RULE_R3.json'
HISTORY=PLAN+'S_HISTORY_SLOTS_CPU_R3.json'
PHYSICAL={'two_card':PLAN+'S_PHYSICAL_TWO_CARD_OTHER_GPU_R2.json',
          'four_card':PLAN+'S_PHYSICAL_FOUR_CARD_R1.json'}
QUOTES={'two_card':PLAN+'S_WHOLE_QUOTE_TWO_CARD_OTHER_GPU_R2.json',
        'four_card':PLAN+'S_WHOLE_QUOTE_FOUR_CARD_R2.json'}
LIMITS={'two_card':14,'four_card':17}
IDENTITY_SHA='2104a9d053fc6e2967de363fa261bb3a514ee5b93a97d7783208bf3f187c32a6'
RESOURCE_SHA='c3f5d742cbd014838104cae6e7d5afc7adfb9b41c01650bf6a311890a500db2b'
UPPER_SHA='c1a2b18855a6692eb5a9dce45ddce0340e5573bd393677359470be1429a75a95'
OTHER_A6000='GPU-de9a5370-cd87-0f1c-a48e-288888777dd3'
COUNTS=dict(new_paths=10,reused_OFF_paths=0,logical_paths=10,warm_paths=2,
    new_ON_paths=4,new_OFF_paths=4,parent_Dense_pairs=220,parent_C_pairs=140,
    extra_Dense_teacher_pairs=56,extra_C_shadow_pairs=52,total_pairs=468,
    branch_readouts=936,deep_block_calls=552,moment_rows=108,raw_states=8,unique_anchors=24)

# Other unchanged numeric imports are also bound by the complete registration.
EXECUTION_CRITICAL=(
    'src/wcomr/sq_s_spec_r2.py','src/wcomr/sq_s_execution_r2.py','src/wcomr/sq_s_stage_r2.py',
    'src/wcomr/sq_s_capture_r2.py','src/wcomr/sq_s_terminal_r2.py',
    'src/wcomr/sq_s_monitor_terminal_r2.py','src/wcomr/sq_s_artifact_terminal_r2.py',
    'src/wcomr/sq_s_risk_post_r3.py','scripts/prepare_cara_sq_s_history_support_r3.py',
    'src/wcomr/sq_s_model_entry_r1.py','src/wcomr/sq_s_data_terminal_r2.py',
    'src/wcomr/sq_s_runner_r1.py','src/wcomr/sq_s_batch_r1.py',
    'src/wcomr/sq_s_physical_r1.py','src/wcomr/sq_s_reuse_r1.py',
    'src/wcomr/sq_s_resource_guard_r1.py','src/wcomr/sq_s_resources_r1.py',
    'src/wcomr/sq_s_collection_r1.py','src/wcomr/sq_s_sources_r1.py',
    'src/wcomr/sq_s_owner_roundtrip_r1.py','src/wcomr/sq_s_storage_r1.py',
    'src/wcomr/sq_risk_r1.py','src/wcomr/gpu_budget_pool_v2.py',
    'src/wcomr/wc73_execution_r1.py','src/wcomr/wc73_exclusive_r1.py',
    'src/wcomr/history104_storage_r2.py','src/wcomr/sq_control_storage_r1.py',
    'src/wcomr/policy_price_mode_guard_r1.py','src/wcomr/sq_gpu_allocation_r1.py',
    'scripts/run_cara_sq_s_r2.py','scripts/cara_sq_s_worker_r2.py',
    'scripts/capture_cara_sq_s_r2.py','scripts/postprocess_cara_sq_s_r2.py',
    'scripts/cara_sq_s_guardian_r2.py','scripts/cara_fast_worker_r2.py',
    'scripts/cara_fast_host_guardian_r2.py','scripts/four_card_policy_assets_port_r1.py',
    'scripts/four_card_bank24_execution_tools_r1.py')


def stage_path(project,host):
    from pathlib import Path
    if host not in LIMITS:raise ValueError('Registered S host required')
    return Path(project)/'.sync'/('cara-sq-s-complete-'+host.replace('_','-')+'-r4-20261030')
