"""Read-only downstream binding of a completed, independently audited N07 repair.

The actual repaired run/source/config remain visible. The original shared
configuration identifies unchanged inference methods, never a replacement run.
"""


def is_repair_capture(capture):
    from .frozen_repair180_r2 import RUN
    return capture.get('launch', {}).get('run_id') == RUN


def accepted_repair_identity(accepted, capture, *, capture_sha256,
                             original_shared_config, original_shared_config_sha256):
    from .frozen_repair180_r2 import RUN, match_original
    from .frozen_shared_production_r1 import CONFIG as ORIGINAL_CONFIG
    from .frozen_repair_acceptance_r2 import accept

    if not is_repair_capture(capture):
        raise ValueError('The actual independent repaired N07 run is required')
    config, launch = capture['config'], capture['launch']
    original = config['references']['original_configuration']
    if (accepted.get('capture_sha256') != capture_sha256
            or accepted.get('source_revision') != launch['source_revision']
            or accepted.get('repair_run_id') != RUN
            or config.get('run_id') != RUN
            or capture.get('config_sha256') != launch['config_sha256']
            or original != dict(ref=ORIGINAL_CONFIG, sha256=original_shared_config_sha256)):
        raise ValueError('Bind the saved actual repair, original capture and unchanged method configuration')
    match_original(config, original_shared_config)

    # Re-run the full180 raw/frame/statistical/cost acceptor. A saved success
    # boolean or CPU-only preparation cannot authorize a downstream GPU run.
    if capture['observed_unix'] < launch['next_check_not_before_unix']:
        from .frozen_repair_acceptance_r2 import accept_after_human_wait_override
        recomputed = accept_after_human_wait_override(capture, launch,
            accepted.get('direct_human_waiting_override', {}))
    else:
        recomputed = accept(capture, launch)
    if any(accepted.get(k) != v for k, v in recomputed.items()):
        raise ValueError('Recompute the original full repaired N07 acceptance before downstream execution')
    counts = recomputed.get('original_status_counts', {})
    if (recomputed.get('terminal_receipt_audit_accepted') is not True
            or recomputed.get('scientific_available_cohorts_with_registered_missingness') is not True
            or recomputed.get('own_GPU_and_finance_released') is not True
            or recomputed.get('original_CPU_post_exit_code') != 0
            or recomputed.get('original_runner_paths') != 180
            or recomputed.get('scope_counts', {}).get('scientific_paths') != 160
            or recomputed.get('scope_counts', {}).get('total_paths') != 180
            or counts.get('TECH_FAILED', 0) or counts.get('NOT_REACHED', 0)
            or recomputed.get('audit_failures')):
        raise ValueError('Finish the complete repaired N07; retain valid rejections without replacing paths')
    return dict(status='COMPLETE_REPAIRED_N07_BOUND_WITH_ORIGINAL_NUMERIC_METHOD_CONTEXT',
        actual_run_id=RUN, actual_source_revision=launch['source_revision'],
        actual_config_sha256=capture['config_sha256'], original_capture_sha256=capture_sha256,
        original_method_config_ref=ORIGINAL_CONFIG,
        original_method_config_sha256=original_shared_config_sha256,
        method_freeze=config['references']['method_freeze'],
        original_runner_paths=recomputed['original_runner_paths'],
        original_status_counts=counts.copy(), original_identity_relabelled=False,
        no_method_selection_from_final_scores=True, no_new_GPU_permission=True,
        GPU_submissions=0, ledger_written=False)
