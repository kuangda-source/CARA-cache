"""Bind all twelve accepted old endpoints for the registered window24 card.

This is preparation from saved raw evidence, not a fresh remote artifact audit,
production CPU acceptance, new scoring, or permission to execute a GPU card.
"""
import copy
import hashlib
import json
import math

OLD_TO_WINDOW = {'S26-C': 'S26-C', 'S25-C': 'S25-C', 'S25-A': 'S25-A1'}
CARD = 'WC-DROP1-WINDOW-CAL4-FOURARM-FULL24-R1-20261018-A'
STATUS = 'WINDOW24_ALL12_ORIGINAL_ENDPOINTS_BOUND_NOT_REMOTE_REAUDITED'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def expected_plans():
    front = set(range(1, 22)) | {24, 27, 30, 33, 36}
    dense = ['D' if n in front else 'C' for n in range(1, 37)]
    reuse = dense.copy(); reuse[20] = 'C'
    once = reuse.copy(); once[20] = 'A'
    window = once.copy(); window[21:23] = ['A', 'A']
    return dict(zip(('S26-C', 'S25-C', 'S25-A1', 'S25-A3'),
                    (dense, reuse, once, window)))


def validate_scope(scope, original_config):
    counts = dict(requests=4, methods=4, formal_paths=16, full_warmup_paths=8,
                  total_paths=24, ordinary_pairs=864, ordinary_CFG_calls=1728,
                  loads=1, new_teacher_pairs=0)
    if (scope.get('card') != CARD or scope.get('namespace') != 'DROP1_WINDOW24'
            or scope.get('methods') != list(expected_plans())
            or scope.get('plans') != expected_plans() or scope.get('scope_counts') != counts
            or scope.get('old_equivalent_methods') != {v: k for k, v in OLD_TO_WINDOW.items()}
            or scope.get('requests') != original_config['requests']
            or len(scope['requests']) != 4
            or scope.get('A_rule') != dict(beta=1, shared_alpha=1, trusted_D_write=False)
            or scope.get('only_A1_to_A3_changed_actual_updates') != [22, 23]):
        raise ValueError('The full four-arm24 scope, all old inputs and source semantics are fixed')


def bind(capture, acceptance, original_config, scope, native_bindings, evidence):
    validate_scope(scope, original_config)
    if (not acceptance.get('accepted')
            or acceptance.get('status') != 'DROP1_WHOLE18_INDEPENDENT_RAW_FRAME_COST_ACCEPTED'
            or acceptance.get('scored_scientific_paths') != 12
            or acceptance.get('scope_counts') != original_config['scope_counts']
            or capture['launch']['config_sha256'] != evidence['original_config']['sha256']
            or capture['final']['status'] != 'DROP1_FULL12_SCIENCE_ALL18_AUDITED_93FRAME_SCORED'
            or acceptance.get('capture_sha256') != evidence['original_capture']['sha256']):
        raise ValueError('Original complete18 raw and independent twelve-endpoint acceptance required')
    scenes = [r['name'] for r in scope['requests']]
    if len(set(scenes)) != 4:
        raise ValueError('All four original scenes required')
    raw = capture['final']['rows']
    if len(raw) != 18 or len({r['id'] for r in raw}) != 18:
        raise ValueError('Preserve the whole original18 denominator')
    native = {r['scene']: r for r in native_bindings['rows']
              if r['method'] == 'NATIVE' and r['scene'] in scenes}
    if set(native) != set(scenes):
        raise ValueError('All four original Native references required')
    rows, seen = [], set()
    for row in raw:
        if row['section'] != 'TIMED':
            continue
        key = (row['scene'], row['method'])
        if key in seen or key[0] not in scenes or key[1] not in OLD_TO_WINDOW:
            raise ValueError('Foreign, duplicate or substituted original endpoint')
        seen.add(key)
        plan = expected_plans()[OLD_TO_WINDOW[row['method']]]
        score = row.get('LPIPS', {})
        if (row['status'] != 'COMPLETE' or row.get('endpoint_audit') != 'PASS'
                or row['semantic_plan'] != plan
                or row['actions'] != ['DD' if a == 'D' else 'CC' for a in plan]
                or row['solver_steps'] != 36 or row['guided_pairs'] != 36
                or len(row['source_history']) != 36 or len(row['A_history']) != 36
                or row['decoded_video']['frames'] != 93
                or row['decoded_video']['probe']['HWC'] != [432, 768, 3]
                or score.get('frames') != 93 or len(score.get('frame_distances', [])) != 93
                or len(score.get('pts', [])) != 93
                or not all(math.isfinite(x) and x >= 0 for x in score['frame_distances'])
                or score['reference_sha256'] != native[row['scene']]['video_artifact']['sha256']):
            raise ValueError('Every old endpoint needs its original36 history and all93 compatible frames')
        for action, history in zip(plan, row['source_history']):
            if (history['action'] != ('DD' if action == 'D' else 'CC')
                    or history['A_readout']['readout_action'] != action
                    or history['teacher_calls'] or history['A_readout']['teacher_calls']
                    or (action != 'D' and history['true_D_before'] != history['true_D_after'])):
                raise ValueError('Actual original readout and trusted-D semantics must match')
        rows.append(dict(window_method=OLD_TO_WINDOW[row['method']],
                         original_method=row['method'], original_row_id=row['id'],
                         scene=row['scene'], original_row=copy.deepcopy(row),
                         original_row_fingerprint=fingerprint(row)))
    if seen != {(s, m) for s in scenes for m in OLD_TO_WINDOW}:
        raise ValueError('All twelve original endpoints required; no missing or winner filtering')
    native_rows = [copy.deepcopy(native[s]) for s in scenes]
    value = dict(status=STATUS, card=CARD, original_endpoint_denominator=12,
        original_generation_denominator=18, new_card_formal_denominator=16,
        new_card_total_denominator=24, rows=rows, Native_references=native_rows,
        original_to_window_methods=OLD_TO_WINDOW, evidence=copy.deepcopy(evidence),
        new_A3_original_control_exists=False, fresh_remote_artifacts_reaudited=False,
        actual_production_CPU_accepted=False, new_video_or_quality_results=0,
        GPU_submissions=0, ledger_written=False)
    value['fingerprint'] = fingerprint(value)
    return value


def verify(value, capture, acceptance, original_config, scope, native_bindings, evidence):
    expected = bind(capture, acceptance, original_config, scope, native_bindings, evidence)
    if value != expected:
        raise ValueError('Endpoint controls must equal the original accepted complete raw cohort')
    return dict(status='WINDOW24_ALL12_ORIGINAL_ENDPOINT_BINDINGS_INDEPENDENTLY_ACCEPTED',
        original_controls=12, original_scenes=4, original_methods=3,
        full24_preserved=True, fresh_remote_artifacts_reaudited=False,
        actual_production_CPU_accepted=False, new_quality_scores=0, GPU_submissions=0)
