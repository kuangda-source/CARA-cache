"""Independent complete180 retry contract; original numerical scope unchanged.

This validates CPU preparation. It never reuses the failed card's specific
GPU approval or selects a new input, method, parameter, price or GPU.
"""
import json
from pathlib import Path

from . import frozen_shared_production_r1 as original
from .frozen_guardrail_boundary_r2 import ORIGINAL_FIXED_SOURCE_SHA256, VERSION
from .source_aware_phase_sampling import bind_globals

CONFIG = 'configs/wc_paper_N07_refusal_repair180_r2_20261016.json'
RUN = 'wc-paper-n07-refusal-repair180-r2'
CARD = 'WC-PAPER-N07-REFUSAL-REPAIR-FULL180-R2-20261016-A'
PRODUCTION_CPU_STATUS = 'N07_REFUSAL_REPAIR180_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
STRATEGY = original.STRATEGY
sha, write, fingerprint, prepare_samples = original.sha, original.write, original.fingerprint, original.prepare_samples
REPAIR_SOURCE_FILES = (
    'src/wcomr/frozen_guardrail_boundary_r2.py', 'tests/test_frozen_guardrail_boundary_r2.py',
    'tests/check_frozen_guardrail_boundary_sampling_cpu_r2.py',
    'scripts/check_wc_N07_refusal_boundary_full520_local_cpu_r2.py')
REPAIR_REFERENCES = ('original_configuration', 'refusal_boundary_CPU',
    'refusal_boundary_CPU_exit', 'refusal_boundary_CPU_receipt')


def validate_contract(config, bound):
    check = bind_globals(original.validate_contract, {'CARD': CARD, 'RUN': RUN})
    return check(config, bound)


def match_original(config, old):
    expected = {**old, 'card': CARD, 'run_id': RUN,
        'references': {**old['references'], **{k: config['references'][k] for k in REPAIR_REFERENCES}},
        'request_boundary_repair': dict(version=VERSION, original_run_id=original.RUN,
            all180_positions_retained=True, original_failed_stage_written=False,
            input_method_parameter_or_mask_changed=False, original_approval_reused=False)}
    if config != expected:
        raise ValueError('Only retry identity and zero-step refusal handling may differ from the original180')
    if config['references']['original_configuration']['ref'] != original.CONFIG:
        raise ValueError('Bind the immutable original final-test configuration')


def read_bound(stage, binding):
    from .balanced_repeat_production_r1 import read_reference
    return read_reference(stage, binding)


def validate_repair_proof(stage, config):
    stage = Path(stage); refs = config['references']
    old, raw, exit, accepted = (read_bound(stage, refs[k]) for k in REPAIR_REFERENCES)
    match_original(config, old)
    raw_ref = refs['refusal_boundary_CPU']
    if (raw['status'] != 'N07_REFUSAL_BOUNDARY_TWO_FLOW_FULL520_CPU_PASS_NOT_PRODUCTION'
            or raw['actual_CPU_paths'] != 520 or raw['complete_sampling_CPU_paths'] != 160
            or raw['zero_step_refusal_CPU_paths'] != 360 or raw['original_reproduced_failures'] != 4
            or raw['ordinary_pairs'] != 5760 or raw['CFG_calls'] != 11520
            or any(raw[k] for k in ('CUDA_initialized', 'GPU_submissions', 'SSH_queries',
                'ledger_written', 'production_CPU_accepted', 'model_weights_loaded',
                'real_videos_generated', 'final_test_quality_or_latency_read'))
            or exit['status'] != raw['status'] or exit['exit_code'] != 0
            or exit['output_sha256'] != raw_ref['sha256'] or exit['expected_CPU_paths'] != 520
            or accepted['status'] != 'N07_REFUSAL_BOUNDARY_FULL520_LOCAL_RECEIPT_AND_SOURCE_ACCEPTED_NOT_PRODUCTION'
            or accepted['original_sha256'] != raw_ref['sha256']
            or accepted['exit_sha256'] != refs['refusal_boundary_CPU_exit']['sha256']
            or accepted['original_frozen_config_sha256'] != refs['original_configuration']['sha256']
            or accepted['original_cpu_pid'] != exit['pid']
            or accepted['bound_inputs_ref'] != old['references']['bound_inputs']
            or accepted['new_GPU_card_selected'] or accepted['production_CPU_accepted']):
        raise ValueError('Complete original two-flow rejection/parity CPU proof is required')
    if {r['flow'] for r in raw['checks']} != {False, True} or len(raw['checks']) != 2:
        raise ValueError('Both original flow settings must be preserved')
    for check in raw['checks']:
        proof = check['guardrail_boundary_proof']
        if (check['status'] != 'PASS' or check['complete_sampling_CPU_paths'] != 80
                or check['ordinary_pairs'] != 2880 or check['full_registered_refusal_paths'] != 180
                or check['registered_formal_refusals'] != 160 or check['registered_warm_refusals'] != 20
                or len(check['accepted_path_parity']) != 32 or len(check['video_refusal_parity']) != 8
                or len(check['original_failure_reproduced']) != 2
                or not check['no_text_refusal_replacement_or_generation']
                or not check['full_mask_validation_not_weakened'] or check['numerical_runtime_changed']
                or proof['version'] != VERSION or proof['original_fixed_source_sha256'] != ORIGINAL_FIXED_SOURCE_SHA256
                or proof['post_request_condition_replacements'] != 1
                or not proof['inverse_bytes_and_AST_equal'] or not proof['complete_and_video_rejected_masks_still_checked']
                or proof['original_numerical_source_modified'] or proof['refused_requests_replaced_or_retried']):
            raise ValueError('Refusal repair cannot weaken masks, remove a flow or lose the original reproductions')
        for row in check['accepted_path_parity'] + check['video_refusal_parity']:
            if (row['actual_guided'] != 36 or row['components_alive_after'] != 0
                    or not row['all_guided_when_audit_final_actions_Ahistory_sourcehistory_and_Toy_RGB_equal']):
                raise ValueError('Every full-path numerical/source/readout control must match')
    for name in REPAIR_SOURCE_FILES:
        if sha(stage / name) != raw['source_sha256'].get(name):
            raise ValueError('The rejection-tested request boundary changed: ' + name)
    if sha(stage / 'src/wcomr/source_phase_fixed_mask_r1.py') != ORIGINAL_FIXED_SOURCE_SHA256:
        raise ValueError('Do not edit the original accepted numerical executor')
    return dict(status='ACCEPTED_FULL520_REQUEST_BOUNDARY_CPU_REUSED_NOT_PRODUCTION',
        successful_CPU_paths=520, expected_original_failure_reproductions=4,
        original_CPU_sha256=raw_ref['sha256'], source_sha256={n:sha(stage/n) for n in REPAIR_SOURCE_FILES},
        source_config_sha256=refs['original_configuration']['sha256'], new_full520_paths_run=0)


def validate(project, stage):
    # The original validator still recomputes the same input selection,
    # numerical99 closure, physical assets and all original reference hashes.
    old, registration, physical, inputs, tables, previous, bound, reuse = original.validate(project, stage)
    config = json.loads((Path(stage) / CONFIG).read_text())
    match_original(config, old); validate_contract(config, bound)
    repair = validate_repair_proof(stage, config)
    from .frozen_repair_entry_r2 import validate_all_entries
    derivations = validate_all_entries(stage)
    return config, registration, physical, inputs, tables, previous, bound, dict(reuse,
        request_boundary_repair=repair, metadata_entry_derivations=derivations)


run_registered_batch = bind_globals(original.run_registered_batch, {'validate_contract': validate_contract})


def validate_launch_authority(config, bound, registration, proof, authority, **kwargs):
    from .frozen_repair_cpu_acceptance_r2 import validate_proof
    validate_proof(proof, config, bound, registration,
        registration_sha256=kwargs['registration_sha256'],config_sha256=kwargs['config_sha256'])
    verify = bind_globals(original.validate_launch_authority,
        {'validate_contract':validate_contract,'RUN':RUN,'PRODUCTION_CPU_STATUS':PRODUCTION_CPU_STATUS})
    return verify(config,bound,registration,proof,authority,**kwargs)
