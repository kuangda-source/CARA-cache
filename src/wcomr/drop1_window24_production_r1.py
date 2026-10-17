"""Whole24 production contract reusing the accepted complete88 numerics.

No config or quote is selected by importing this module. N09 must supply real
accepted intervals before pricing. Inclusive intervals are planning inputs,
never additive end-to-end latency or isolated post-probe action prices.
"""
import gzip
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath

from . import drop1_correction_window24_r1 as numerical
from .drop1_correction_window24_r1 import (
    CARD, RUN, METHODS, COUNTS, CPU_COUNTS, TIMING, execute, matrix, plans,
    audit_row, full_rows, summaries,
)
from .drop1_full18_r1 import MODE_REF, STRATEGY, sha, write

CONFIG = 'configs/wc_drop1_correction_window_full24_production_r1_20261018.json'
CPU_RESULT = 'window24-production-CPU-result.json'
PRODUCTION_CPU_STATUS = 'WINDOW24_FULL24_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
NUMERIC_CAPTURE_REF = 'reports/wc_drop1_window88_actual_CPU_R1_collection_20261018_0220.json.gz'
FIXED_REFERENCES = dict(
    original_config='configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json',
    static_scope='manifests/wc_drop1_correction_window_full24_static_scope_20261018.json',
    numeric_capture=NUMERIC_CAPTURE_REF,
    numeric_acceptance='reports/wc_drop1_window88_actual_CPU_R1_independent_acceptance_20261018.json',
    old_capture='reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz',
    old_acceptance='reports/wc_drop1_full18_independent_acceptance_20261018.json',
    old_controls='manifests/wc_drop1_window24_all12_original_controls_20261018.json',
    baseline='manifests/wc_simple26d_prior420_bindings_r1_20261015.json',
)
PRICE_VERSION = 'N09_FULL40_RECEIPT_VALID_READOUT_SCOPE_PLANNING_R2_NOT_ACTION_UNIT_PRICE'


def _positive(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0


def validate_contract(c):
    references = c.get('references', {})
    if (c.get('card') != CARD or c.get('run_id') != RUN
            or c.get('namespace') != 'DROP1_WINDOW24'
            or c.get('methods') != list(METHODS) or c.get('scope_counts') != COUNTS
            or c.get('CPU_scope') != CPU_COUNTS
            or c.get('plans') != {k: list(v) for k, v in plans().items()}
            or c.get('strategy') != STRATEGY or c.get('A_method') != 'BETA1_ONE_PHASE'
            or c.get('memory_policy') != 'BOUNDARY_GC_ONLY_R2'
            or c.get('cumulative_cap_GPUh') != 226 or c.get('budget_origin_used_GPUh') != 79.99637737158223
            or c.get('autonomy_exclusive_upper_GPUh') != 12 or c.get('timing_claim') != TIMING
            or c.get('deleted_D_update') != 21 or c.get('continued_A_actual_updates') != [21, 22, 23]
            or c.get('protected_steps') != [1, 2, 3, 4, 5, 6, 7, 36]
            or c.get('warmup_repeats') != 2 or len(c.get('requests', [])) != 4
            or len({r['name'] for r in c['requests']}) != 4
            or any(c.get(k) is not False for k in ('training', 'online_teachers', 'P_enabled', 'F_B_enabled',
                'endpoint_tuning', 'new_native_generation'))
            or not _positive(c.get('forecast_complete_GPUh'))
            or not _positive(c.get('billed_limit_GPUh'))
            or c['forecast_complete_GPUh'] > c['billed_limit_GPUh']
            or any(r['seed'] != 0 or r['num_steps'] != 35 or r['num_output_frames'] != 93
                or r['resolution'] != '432,768' or r['guidance'] != 7 for r in c['requests'])
            or set(references) != set(FIXED_REFERENCES) | {'N09_capture', 'N09_acceptance', 'cost'}
            or any(references.get(k, {}).get('ref') != v for k, v in FIXED_REFERENCES.items())):
        raise ValueError('Frozen complete24/88, original readout, input scope and quoted whole cost required')
    for ref in references.values():
        name = PurePosixPath(ref['ref']); digest = ref['sha256']
        if (name.is_absolute() or '..' in name.parts or str(name) != ref['ref']
                or len(digest) != 64 or any(x not in '0123456789abcdef' for x in digest)):
            raise ValueError('Exact stage-local file SHA binding required')


def read_reference(stage, c, name):
    info = c['references'][name]; path = Path(stage) / info['ref']
    if path.is_symlink() or not path.resolve().is_relative_to(Path(stage).resolve()) or sha(path) != info['sha256']:
        raise ValueError('Changed or escaped reference: ' + name)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def accept_numerical_reuse(stage, registration, capture, saved_acceptance):
    source = Path(stage) / 'scripts/capture_wc_drop1_window88_cpu_r1.py'
    spec = importlib.util.spec_from_file_location('registered_window88_original_acceptor', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    result = module.accept(capture)
    if (not result['numerical_CPU_accepted']
            or any(saved_acceptance.get(k) != v for k, v in result.items())
            or not capture['registration']['payload_sha256']
            or any(registration['payload_sha256'].get(n) != h
                   for n, h in capture['registration']['payload_sha256'].items())
            or registration['runtime_source_sha256'] != capture['registration']['runtime_source_sha256']):
        raise ValueError('Reuse only all88 accepted paths and the unchanged complete numerical dependency set')
    return result


def estimate_whole24(old_capture, N09_capture, N09_accepted, scenes):
    """Full-scope planning; no synthetic price or zero when N09 is unavailable."""
    plan = matrix(scenes)
    whole_rows = N09_capture.get('runner', {}).get('runs', [])
    if (N09_accepted.get('terminal_receipt_audit_accepted') is not True
            or N09_accepted.get('original_finance_status') != 'ORIGINAL_ACTUAL_BILL_AND_ADDITIVE_SETTLEMENT_MATCH'
            or N09_accepted.get('own_GPU_finance_released') is not True
            or N09_accepted.get('original_CPU_post_exit_code') != 0
            or N09_accepted.get('original_runner_paths') != 40
            or N09_accepted.get('registered_total_paths') != 40
            or N09_capture.get('supervisor', {}).get('child_exit_code') != 0
            or len(whole_rows) != 40
            or any(r.get('status') not in ('COMPLETE', 'VIDEO_REJECTED', 'TEXT_REJECTED') for r in whole_rows)
            or N09_accepted.get('action_unit_prices_measured') is not False):
        raise ValueError('Audited whole40 N09 with actual settlement required; no technical prefix or action-unit-price relabelling')
    old_rows = old_capture['runner']['runs']; bill = old_capture['billing']
    load = old_capture['runner']['load_seconds']
    if (len(old_rows) != 18 or any(r['status'] != 'COMPLETE' for r in old_rows)
            or not _positive(load) or not _positive(bill['wall_seconds'])
            or not math.isclose(bill['wall_seconds']/3600, bill['actual_GPUh'], abs_tol=1e-12)):
        raise ValueError('All18 accepted original request intervals, one load and real whole bill required')
    durations = [r['ended_unix'] - r['started_unix'] for r in old_rows]
    if any(not _positive(x) for x in durations):
        raise ValueError('Successful whole requests cannot be priced from rejections or missing timers')
    residual = bill['wall_seconds'] - load - sum(durations)
    if residual < -1:
        raise ValueError('Original request clocks exceed the original whole GPU bill')
    components = ('output_head', 'correction_warp', 'correction_to_velocity')
    maxima = {k: [] for k in components}
    source_rows = []
    for row in N09_capture['final']['rows']:
        if (row['method'] != 'A_NO_P' or row.get('mode') not in ('PROFILE_AUDIT', 'PROFILE_LEAN')
                or row.get('component_profile_audit') != 'PASS'
                or row.get('raw_model_audit') != 'PASS'
                or row.get('status') not in ('COMPLETE', 'VIDEO_REJECTED')):
            continue
        asset = row['component_profile_artifact']
        original = N09_capture['profile_scalar_originals'][asset['path']]
        if original['sha256'] != asset['sha256'] or not original['matches_original_row_identity']:
            raise ValueError('Original accepted scalar artifact identity required')
        selected = []
        for span in original['data']['intervals']:
            if span['component'] in maxima and span['outcome'] == 'RETURNED':
                cpu, gpu = span['CPU_seconds'], span['CUDA_elapsed_ms'] / 1000
                if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x < 0 for x in (cpu, gpu)):
                    raise ValueError('Finite original CPU/current-stream CUDA intervals required')
                value = max(cpu, gpu); maxima[span['component']].append(value)
                selected.append(dict(interval_id=span['id'], component=span['component'], seconds=value))
        if {s['component'] for s in selected} != set(components):
            raise ValueError('Every valid A_NO_P source needs all three original readout components')
        source_rows.append(dict(row_id=row['id'], scene=row['scene'], mode=row['mode'],
                                artifact_sha256=asset['sha256'], intervals=selected))
    source_scenes = {r['scene'] for r in source_rows}
    if (len(source_rows) != 4 or len({r['row_id'] for r in source_rows}) != 4
            or len(source_scenes) != 2
            or {(r['scene'], r['mode']) for r in source_rows} !=
                {(s, m) for s in source_scenes for m in ('PROFILE_AUDIT', 'PROFILE_LEAN')}
            or any(not maxima[k] for k in components)):
        raise ValueError('Both original scenes/modes and all three readout components required; unknown is not zero')
    maxima = {k: max(v) for k, v in maxima.items()}
    # Two CFG branches; nested spans may overlap. The sum is deliberately an
    # explicit planning proxy plus one second, never a measured A unit cost.
    per_extra_A = 2 * sum(maxima.values()) + 1.
    positions = []
    for row in plan:
        extra = 2 if row['method'] == 'S25-A3' else 0
        trace = 60. if row['section'] == 'WARMUP' else 0.
        positions.append(dict(row, observed_old_whole_request_max_seconds=max(durations),
            additional_A_readouts=extra, inclusive_interval_planning_proxy_seconds=extra * per_extra_A,
            warm_trace_allowance_seconds=trace,
            planned_whole_request_seconds=max(durations) + extra * per_extra_A + trace))
    before = load + sum(r['planned_whole_request_seconds'] for r in positions) + max(0., residual)/18*24 + 300.
    forecast = math.ceil(before * 1.2) / 3600
    return dict(status='WINDOW24_COMPLETE_PLANNING_QUOTE_NOT_MEASURED_NEW_SPEED',
        pricing_version=PRICE_VERSION, scope_counts=COUNTS, positions=positions,
        full_paths=24, formal_paths=16, full_warmups=8, loads=1,
        original_load_seconds=load, original_whole_request_max_seconds=max(durations),
        original_unattributed_seconds=residual, projected_unattributed_seconds=max(0., residual)/18*24,
        original_N09_readout_component_max_seconds=maxima, N09_source_rows=source_rows,
        N09_original_full_runtime_scope_accepted=N09_accepted.get('full_runtime_profile_scope_accepted') is True,
        N09_whole40_terminal_outcomes={s: sum(r['status'] == s for r in whole_rows)
            for s in ('COMPLETE', 'VIDEO_REJECTED', 'TEXT_REJECTED')},
        extra_A_readouts=12, per_extra_A_planning_proxy_seconds=per_extra_A,
        additional_setup_allowance_seconds=300., margin=1.2,
        forecast_complete_GPUh=forecast, billed_limit_GPUh=math.ceil(forecast*1.25*4)/4,
        specific_whole_card_confirmation_required=math.ceil(forecast*1.25*4)/4 >= 12,
        whole_card_selected=False, action_unit_prices_measured=False,
        inclusive_components_are_additive_total_latency=False, runtime_upper_bound_guarantee=False,
        new_A3_speed_or_quality_measured=False, GPU_submissions=0, ledger_written=False)


def validate(project, stage):
    stage = Path(stage)
    old_c, reg, old, inputs, tables, previous = numerical.original.base.validate(project, stage)
    c = json.loads((stage / CONFIG).read_text()); validate_contract(c)
    refs = {k: read_reference(stage, c, k) for k in c['references']}
    numerical.validate_static_manifest(refs['static_scope'], refs['original_config'])
    if c['requests'] != old_c['requests'] or c['requests'] != refs['static_scope']['requests']:
        raise ValueError('The four original CAL inputs must survive unchanged')
    accept_numerical_reuse(stage, reg, refs['numeric_capture'], refs['numeric_acceptance'])
    from .drop1_window_original_controls_r1 import verify
    verify(refs['old_controls'], refs['old_capture'], refs['old_acceptance'],
           refs['original_config'], refs['static_scope'], refs['baseline'], refs['old_controls']['evidence'])
    from .runtime_profile40_acceptance_r1 import accept
    accepted = accept(refs['N09_capture'], refs['N09_capture']['launch'])
    if any(refs['N09_acceptance'].get(k) != v for k, v in accepted.items()):
        raise ValueError('Real whole N09 independent acceptance differs')
    quote = estimate_whole24(refs['old_capture'], refs['N09_capture'], accepted, [r['name'] for r in c['requests']])
    if refs['cost'] != quote or any(c[k] != quote[k] for k in ('forecast_complete_GPUh', 'billed_limit_GPUh')):
        raise ValueError('Recompute every one of24 quote positions from real source intervals')
    calibration = inputs[0]
    for method, plan in plans().items():
        anchor = None
        for step, action in enumerate(plan, 1):
            if action == 'D': anchor = step
            elif (anchor, step) not in calibration.rho_at or step not in calibration.gains:
                raise ValueError('Original calibration lacks support for ' + str((method, anchor, step)))
    for binding in refs['old_controls']['rows']:
        for name in ('final_artifact', 'video_artifact'):
            asset = binding['original_row'][name]; path = Path(asset['path'])
            if sha(path) != asset['sha256'] or path.stat().st_size != asset['bytes']:
                raise ValueError('Original old12 physical endpoint changed')
    return c, reg, old, inputs, tables, previous


def old_endpoint_controls(rows, c, stage):
    from .h1_cost_curve_post_r1 import endpoint_identity
    result = []
    for binding in read_reference(stage, c, 'old_controls')['rows']:
        old = binding['original_row']
        row = next((r for r in rows if r['section'] == 'TIMED' and r['scene'] == binding['scene']
                    and r['method'] == binding['window_method'] and r.get('endpoint_audit') == 'PASS'), None)
        if row is None:
            result.append(dict(scene=binding['scene'], method=binding['window_method'], status='MISSING_OR_REJECTED_RETAINED'))
            continue
        for name in ('final_artifact', 'video_artifact'):
            asset = old[name]
            if sha(asset['path']) != asset['sha256'] or Path(asset['path']).stat().st_size != asset['bytes']:
                raise ValueError('Original old12 endpoint bytes changed')
        endpoint_identity(row, old)
        if row['A_history'] != old['A_history']:
            raise ValueError('Equivalent old readout history differs')
        result.append(dict(scene=binding['scene'], method=binding['window_method'],
                           status='PASS_ORIGINAL12_FINAL_ACTIONS_A_HISTORY_FULL93RGB_EQUAL'))
    if len(result) != 12:
        raise ValueError('All12 original controls required')
    return result


def common_prefix_controls(guided_by_id):
    import torch
    rows = []
    for repeat in (1, 2):
        keys = [f'warm_{repeat}_{m}' for m in ('S25-A1', 'S25-A3')]
        if not all(k in guided_by_id for k in keys):
            rows.append(dict(round=repeat, status='MISSING_FULL36_RETAINED')); continue
        left, right = (guided_by_id[k] for k in keys)
        if len(left) != 36 or len(right) != 36 or any(not torch.equal(x, y) for x, y in zip(left[:21], right[:21])):
            raise ValueError('A1/A3 common first21 guided outputs differ')
        rows.append(dict(round=repeat, status='PASS_ALL21_COMMON_PREFIX', compared_outputs=21))
    return rows
