"""Two scientific points across cards, preserving every failed attempt and cost.

No Torch, scoring, GPU launch or ledger mutation. CPU fixtures never count as
completed real points and are rejected by the production CLI.
"""
import math
from fractions import Fraction
from .rv0_execution import digest_valid
from .rv0_small_partial import partial_plan
from .rv0_small_human_evaluation import audit_trajectories as audit_human, evaluation_plan as human_plan
from .rv0_small_execution import reserve_budget as reserve_first, settle_budget as settle_first
from .rv0_small_human_execution import validate_config as validate_human_config, audit_settlement as audit_human_settlement

COMMON = 'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191'
HUMAN = 'human_199'
ORIGINAL = {'parents': 2, 'suffixes': 12, 'new_outputs': 8,
            'Native_relative_losses': 4, 'signed_diagnostics': 2}
PROTOCOL = {'package': 'lpips', 'package_version': '0.1.4', 'metric_version': '0.1',
    'backbone': 'alex', 'spatial': False, 'precision': 'torch.float32', 'device': 'cpu',
    'RGB_input': 'UINT8_HWC_TO_NCHW_MINUS1_TO_PLUS1', 'resize_crop_subsample': False,
    'expected_frames': 93, 'expected_HWC': [432, 768, 3],
    'aggregation': 'ARITHMETIC_MEAN_ALL93_FRAME_DISTANCES',
    'reference': 'MATCHED_NATIVE_FULL35_SAME_REQUEST_NOISE_DECODE',
    'benefit': 'J_C_MINUS_J_D_NEGATIVE_VALUES_RETAINED',
    'policy': 'ONE_ACTION_ADAPTIVE_DIAGNOSTIC_NOT_BUDGET_MATCHED',
    'formal_RV_training_labels': False, 'physics_or_quality_noninferiority': False}


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_video_denominator(terminal, plan):
    expected = plan['files']+plan['references']
    actual = terminal['videos']
    if len(actual) != 5 or len(expected) != 5 or len({v['path'] for v in actual}) != 5:
        raise ValueError('All four new videos and one Native original are required')
    by = {v['path']: v for v in actual}
    for item in expected:
        video = by[item['path']]
        if video['full93_decode'] is not True or any(video[k] != item[k] for k in ['bytes', 'sha256']):
            raise ValueError('Every planned new/reference artifact must have a matching full93 audit')


def validate_scores(score, pairs, terminal):
    if (score['protocol'] != PROTOCOL or len(score['pairs']) != 2 or len(score['signed_diagnostics']) != 1
            or score['formal_RV_training_labels'] is not False or score['budget_matched'] is not False
            or score['physics_or_quality_noninferiority'] is not False or score['GPU_submissions'] != 0
            or score['CUDA_initialized'] is not False):
        raise ValueError('Complete identical CPU full93 protocol and two-loss denominator required')
    videos = {v['path']: v for v in terminal['videos']}
    for actual, expected in zip(score['pairs'], pairs):
        for name in ['scene', 'CFG_slot', 'target_call', 'action', 'reference', 'candidate']:
            if actual[name] != expected[name]:
                raise ValueError('Scored point/action/artifact differs: '+name)
        metric = actual['score']
        values, pts = metric['frame_distances'], metric['pts']
        if (metric['frames'] != 93 or len(values) != 93 or len(pts) != 93
                or not all(finite_number(v) for v in values)
                or metric['mean_LPIPS'] != sum(values)/93
                or metric['Native_fidelity_not_physics'] is not True):
            raise ValueError('Complete raw93 frame scores and exact arithmetic mean required')
        times = [Fraction(n)*Fraction(base) for n, base in pts]
        if (any(type(n) is not int for n, _ in pts) or times[0] != 0
                or any(b-a != Fraction(1, 16) for a, b in zip(times, times[1:]))):
            raise ValueError('All93 distinct chronological 16fps frame timestamps required')
        for kind in ['reference', 'candidate']:
            item = actual[kind]; video = videos[item['path']]
            if (not digest_valid(item['sha256']) or video['sha256'] != item['sha256']
                    or metric[kind+'_sha256'] != item['sha256'] or video['bytes'] != item['bytes']
                    or video['full93_decode'] is not True):
                raise ValueError('Scoring source must match independent full-video audit')
    c, d = [p['score'] for p in score['pairs']]
    if c['pts'] != d['pts'] or c['reference_sha256'] != d['reference_sha256']:
        raise ValueError('C/D full93 Native timestamps and reference must match')
    signed = score['signed_diagnostics'][0]
    if (signed['scene'] != pairs[0]['scene'] or signed['CFG_slot'] != pairs[0]['CFG_slot']
            or signed['LPIPS_C_minus_D'] != c['mean_LPIPS']-d['mean_LPIPS']
            or signed['protocol'] != PROTOCOL or signed['signed_negative_retained'] is not True
            or signed['budget_matched'] is not False or signed['formal_RV_training_label'] is not False):
        raise ValueError('Signed full-video consequence must be recomputed without dropping negatives')
    return {'LPIPS_C': c['mean_LPIPS'], 'LPIPS_D': d['mean_LPIPS'],
            'LPIPS_C_minus_D': c['mean_LPIPS']-d['mean_LPIPS']}


def source_binding(bundle):
    score, terminal, hashes = bundle['score'], bundle['terminal'], bundle['sha256']
    if (score['terminal_audit_sha256'] != hashes['terminal']
            or score['runner_receipt_sha256'] != hashes['receipt']
            or terminal['runner_receipt_sha256'] != hashes['receipt']
            or terminal['config_sha256'] != hashes['config']
            or terminal['source_revision'] != bundle['receipt']['source_revision']
            or terminal['run_id'] != bundle['config']['run_id']
            or not all(digest_valid(d) for d in hashes.values())):
        raise ValueError('Original config/GPU/score/terminal identities must be bound')
    audit = bundle['score_audit']
    if audit['score_original_sha256'] != hashes['score']:
        raise ValueError('Independent native score original SHA differs')
    supervisor = bundle['supervisor']
    if (supervisor['source_revision'] != terminal['source_revision'] or supervisor['run_id'] != terminal['run_id']
            or supervisor['config'] != bundle['config'] or supervisor['budget_after'] != terminal['budget']
            or supervisor['wall_seconds'] != terminal['gpu_wall_seconds']):
        raise ValueError('Original supervisor identity and failure/complete cost differ')
    # The score audit's supervisor is the CPU scorer, not the GPU supervisor.
    originals = bundle['originals']['files']
    for original_name, bundle_name in [('supervisor', 'supervisor'), ('runner', 'receipt')]:
        item = originals[original_name]
        if (item['original_sha256'] != hashes[bundle_name]
                or item['original_bytes'] != bundle['bytes'][bundle_name]
                or not item['original_path'].startswith(bundle['config']['expected_project_root']+'/outputs/'+bundle['config']['run_id']+'/')):
            raise ValueError('GPU originals must be bound separately from CPU scoring supervision')


def point(row, cost):
    by = {child['label']: child for child in row['children']}
    target = by['D_first']['record']['action_report']['suffix_events'][row['slot']]
    native = 'C' if target['native_skip'] else 'D'
    actions = {}
    for action in ['C', 'D']:
        child = by[action+'_first']
        if not finite_number(child['record']['control_wall_seconds']) or child['record']['control_wall_seconds'] <= 0:
            raise ValueError('Measured positive branch cost required')
        actions[action] = {'full_calls_per_CFG': [sum(v > 0 for v in child['deep'][slot::2]) for slot in [0, 1]],
                           'control_wall_seconds': child['record']['control_wall_seconds']}
    return {'scene': row['sample_name'], 'CFG_slot': row['slot'], 'target_call': row['target_call'],
            'status': 'COMPLETE_REAL_POINT_NATIVE_RELATIVE_DIAGNOSTIC', **cost,
            'official_WC_target_action': native,
            'native_action_is_comparator_not_new_policy': True,
            'branch_costs': actions, 'inclusive_parent_with_controls_wall_seconds': row['inclusive_parent_wall_seconds'],
            'not_same_quota_or_clean_speed': True}


def physical_accounting(costs):
    return {
        'planned_parents': sum(c['planned_attempts']['parents'] for c in costs),
        'planned_suffixes': sum(c['planned_attempts']['suffixes'] for c in costs),
        'planned_new_videos': sum(c['planned_attempts']['new_videos'] for c in costs),
        'started_parents': sum(c['started_parents'] for c in costs),
        'started_suffixes': sum(c['started_suffixes'] for c in costs),
        'completed_suffixes': sum(c['completed_suffixes'] for c in costs),
        'audited_new_videos': sum(c['audited_new_videos'] for c in costs),
        'total_actual_GPU_wall_seconds_including_failed_card': sum(c['actual_GPU_wall_seconds'] for c in costs)}


def historical_masks(config, historical):
    if historical['wc_settings'] != config['historical_wc_settings']:
        raise ValueError('Historical original WC settings differ')
    requests = historical['measurements']['requests']
    if [r['sample_name'] for r in requests] != [COMMON, HUMAN]:
        raise ValueError('Historical two-scene identity/order differs')
    rows = []
    for slot, row in enumerate(requests):
        scene = row['sample_name']; reference = config['references'][scene]
        phases = [p for p in row['phases'] if p['workpoint']['name'] == 'wc006']
        if len(phases) != 1 or row['context'][1:] != reference['model_and_condition_context']:
            raise ValueError('Unique historical original WC and matching condition/model required')
        phase = phases[0]; trace = phase['trace']
        if (phase['workpoint'] != {'name': 'wc006', 'mode': 'worldcache', 'requested_steps': 35, 'threshold': 0.06}
                or phase['solver_steps'] != 36 or phase['CFG_calls'] != 72
                or phase['sampling']['timesteps'] != reference['timesteps']
                or phase['sampling']['worldcache_horizon'] != 70
                or [t['call'] for t in trace] != list(range(1, 73))
                or [t['cache_counter_before'] for t in trace] != [n % 70 for n in range(72)]
                or any(type(t['deep_executed']) is not bool for t in trace)
                or len(phase['artifacts']) != 1
                or phase['artifacts'][0]['sha256'] != reference['official_WC']['sha256']
                or phase['artifacts'][0]['bytes'] != reference['official_WC']['bytes']):
            raise ValueError('Complete original 36-update/72-call grid, mask and encoded bridge required')
        suffix = trace[44:]
        rows.append({'scene': scene, 'target_call': 45+slot, 'CFG_slot': slot,
            'historical_official_WC_target_action': 'D' if suffix[slot]['deep_executed'] else 'C',
            'historical_suffix_full_calls_per_CFG': [sum(t['deep_executed'] for t in suffix[s::2]) for s in [0, 1]],
            'historical_suffix_actions': ['D' if t['deep_executed'] else 'C' for t in suffix],
            'historical_parent_not_new_Human_counterfactual': True})
    return rows


def summarize(first, human=None):
    if first.get('CPU_fixture') or human is not None and human.get('CPU_fixture'):
        raise ValueError('CPU mock completion is not a real missing scientific point')
    source_binding(first)
    fscore, fterminal, freceipt, fconfig = [first[n] for n in ['score', 'terminal', 'receipt', 'config']]
    if (fscore['status'] != 'FAILED_CARD_COMPLETED_ROW_ALL93_FRAME_DIAGNOSTICS_OTHER_SCENE_UNFINISHED_NOT_FULL_CARD'
            or fterminal['status'] != 'BOUNDED_FAILED_CARD_COST_SOURCE_RELEASE_COMPLETE_ROW_AUDIT_NOT_FULL_CARD_OR_QUALITY'
            or fconfig['sample_names'] != [COMMON, HUMAN] or fscore['original_denominator'] != ORIGINAL
            or fscore['full_card_accepted'] is not False or fterminal['full_card_accepted'] is not False
            or fterminal['formal_RV_labels'] != 0 or fterminal['original_pids_absent'] is not True
            or fterminal['global_lock_free'] is not True):
        raise ValueError('Original failed card and complete first point must be retained')
    audit = first['score_audit']
    if (audit['status'] != 'FAILED_CARD_COMPLETED_ROW_FULL93_CPU_SCORE_ORIGINAL_AUDIT_PASS_NOT_FULL_CARD_OR_METHOD_GAIN'
            or audit['original_source_artifact_and_budget_native_hashes_unchanged'] is not True
            or audit['original_denominator'] != ORIGINAL or audit['actual_complete_losses'] != 2
            or audit['actual_complete_signed_diagnostics'] != 1 or audit['unfinished_original_points'] != 1
            or audit['full_card_accepted'] is not False or audit['formal_RV_labels'] != 0):
        raise ValueError('Original completed-row independent score audit incomplete')
    supervisor = first['supervisor']
    if (supervisor['status'] != 'BOUNDED_TIMEOUT' or supervisor['exit_code'] != 124
            or supervisor['hard_wall_cap_exceeded'] is not False or supervisor['reserved_seconds'] != 3900
            or not finite_number(supervisor['wall_seconds']) or not 0 < supervisor['wall_seconds'] <= 3900
            or (supervisor['planned_parent_phases'], supervisor['planned_suffix_controls'], supervisor['planned_encoded_outputs']) != (2, 12, 8)):
        raise ValueError('Original failed reservation, cap and physical scope must be retained')
    prepaid = reserve_first(supervisor['budget_before'], fconfig, supervisor['pid'])
    if settle_first(prepaid, supervisor['budget_before'], fconfig, supervisor['wall_seconds'], supervisor['pid']) != fterminal['budget']:
        raise ValueError('Original failed GPU cost must be reconstructed')
    plan = partial_plan(freceipt, fconfig)
    if len(plan['pairs']) != 2 or plan['matrix'][0]['scene'] != COMMON or fterminal['plan'] != plan:
        raise ValueError('Exactly the original complete Common point is allowed')
    validate_video_denominator(fterminal, plan)
    rows = [point(freceipt['requests'][0], validate_scores(fscore, plan['pairs'], fterminal)),
            {'scene': HUMAN, 'CFG_slot': 1, 'target_call': 46, 'status': 'MISSING_REAL_POINT',
             'LPIPS_C': None, 'LPIPS_D': None, 'LPIPS_C_minus_D': None}]
    costs = [{'run_id': fconfig['run_id'], 'terminal_status': 'BOUNDED_TIMEOUT',
              'actual_GPU_wall_seconds': fterminal['gpu_wall_seconds'],
              'planned_attempts': {'parents': 2, 'suffixes': 12, 'new_videos': 8},
              'started_parents': len(freceipt['requests']),
              'started_suffixes': sum(len(r['children']) for r in freceipt['requests']),
              'completed_suffixes': 6, 'audited_new_videos': 4, 'full_card_accepted': False}]
    result = {'status': 'ONE_REAL_POINT_OTHER_MISSING_ORIGINAL_FAILED_CARD_PRESERVED',
        'original_scientific_denominator': ORIGINAL, 'points': rows, 'actual_complete_scientific_points': 1,
        'whole_requested_scene_mean_C_minus_D': None, 'cards_and_failure_costs': costs,
        'original_GPU_card_accepted': False, 'same_batch_or_clean_speed': False,
        'budget_matched': False, 'formal_RV_training_labels': False,
        'CONF_or_physics_quality_noninferiority': False, 'GPU_submissions': 0}
    if human is not None:
        hconfig, hreceipt, hterminal, hscore = [human[n] for n in ['config', 'receipt', 'terminal', 'score']]
        audit_human(hreceipt, 26)
        if (hconfig['sample_names'] != [HUMAN] or hconfig['target_calls'] != [46]
                or hconfig['historical_wc_settings'] != fconfig['historical_wc_settings']
                or hconfig['references'][HUMAN] != fconfig['references'][HUMAN]
                or hconfig['cal_config_sha256'] != fconfig['cal_config_sha256']
                or hconfig['f1_setup_sha256'] != fconfig['f1_setup_sha256']
                or hconfig['references'][HUMAN]['timesteps'] != fconfig['references'][COMMON]['timesteps']):
            raise ValueError('Human complement must preserve original input/model/sampler and protocol')
        hplan = human_plan(hreceipt, hconfig)
        validate_video_denominator(hterminal, hplan)
        hcost = validate_scores(hscore, hplan['pairs'], hterminal)
        hrow = point(hreceipt['requests'][0], hcost)
        validate_human_config(hconfig, selected=True)
        source_binding(human)
        pids = audit_human_settlement(human['supervisor'], hreceipt, hconfig, hterminal['budget'], hterminal['source_revision'])
        if pids != hterminal['original_pids']:
            raise ValueError('Human actual settlement/PID provenance differs')
        if (hscore['status'] != 'HUMAN_FULL93_FRAME_TWO_NATIVE_RELATIVE_LPIPS_AND1_SIGNED_DIAGNOSTIC_NOT_RV_LABELS'
                    or hterminal['status'] != 'HUMAN_COMPLEMENT_SOURCE_COST_RELEASE_AND4_NEW_1_REFERENCE_VIDEO_AUDIT_PASS_NOT_QUALITY'
                    or hterminal['original_pids_absent'] is not True or hterminal['global_lock_free'] is not True
                    or hscore['planned_new_outputs'] != 4 or hscore['planned_C_D_pairs_to_Native'] != 2
                    or hscore['planned_signed_diagnostics'] != 1
                    or hscore['reader_code_sha256'] != fscore['reader_code_sha256']
                    or human['score_audit']['status'] != 'HUMAN_SCORE_ORIGINAL_NATIVE_SHA_PASS_NOT_METHOD_GAIN'
                    or human['score_audit']['original_source_video_and_budget_hashes_unchanged'] is not True
                    or human['score_audit']['GPU_submissions'] != 0):
            raise ValueError('Human complete GPU/terminal/all93-score independent provenance missing')
        rows[1] = hrow; result['actual_complete_scientific_points'] = 2
        result['whole_requested_scene_mean_C_minus_D'] = sum(r['LPIPS_C_minus_D'] for r in rows)/2
        result['status'] = 'TWO_REAL_POINTS_ACROSS_CARDS_ORIGINAL_TIMEOUT_RETAINED_NOT_METHOD_GAIN'
        costs.append({'run_id': hconfig['run_id'], 'terminal_status': 'EXITED_REQUIRES_RESULT_AUDIT',
            'actual_GPU_wall_seconds': hterminal['gpu_wall_seconds'],
            'planned_attempts': {'parents': 1, 'suffixes': 6, 'new_videos': 4},
            'started_parents': 1, 'started_suffixes': 6, 'completed_suffixes': 6,
            'audited_new_videos': 4, 'full_card_accepted': True})
    result['physical_attempt_accounting'] = physical_accounting(costs)
    return result
