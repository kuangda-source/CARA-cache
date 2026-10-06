"""Identity of five missing Native references; no Torch, model or GPU work."""
import hashlib
import json
from pathlib import Path


CARD = 'WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-DRAFT'
RUN = 'wc-w1-native-reference-cal8-r1'
INDICES = (0, 3, 4, 5, 7)
NAMES = (
    'av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'industry_084',
    'misc_13398218_3840_2160_60fps', 'physics_045',
    'av_51b45829-502e-4143-9c32-c026bd6ab191',
)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_reference_scope(draft, replay, original_cal):
    """An eight-row denominator, exactly five new references, no new algorithm."""
    if (draft['card'] != CARD or draft['run_id'] != RUN
            or draft['original_scene_denominator'] != 8 or draft['original_W1_accepted'] != 7
            or draft['original_W1_rejected'] != 1 or draft['existing_matched_Native'] != 2
            or draft['new_Native_generation_phases'] != 5 or len(draft['rows']) != 8
            or len(replay['cases']) != 8 or len(original_cal['cases']) != 8
            or draft['replacement_sample'] or draft['missing_or_rejected_filled_with_zero']
            or draft['all_seven_must_improve'] or draft['independent_confirmation_set']
            or draft['new_human_evaluation'] or draft['GPU_execution_selected']
            or draft['gpu_uuid'] is not None or draft['execution_scope_authority'] is not None
            or draft['cap_is_GPU_authorization']
            or draft['candidate_inclusive_cap_seconds'] != 3600):
        raise ValueError('Five-reference preparation scope differs; this draft cannot authorize GPU')
    selected = []
    for index, row in enumerate(draft['rows']):
        req = row['request']
        case, baseline = replay['cases'][index], original_cal['cases'][index]
        if (row['original_CAL_index'] != index or row['scene'] != case['name']
                or req != case['sample'] or req != baseline['sample']
                or canonical(req) != row['request_canonical_sha256']
                or req['name'] != row['scene']
                or (req['seed'], req['guidance'], req['inference_type'], req['input_path'],
                    req['resolution'], req['num_output_frames'], req['num_steps'],
                    req['enable_autoregressive']) != (0, 7, 'text2world', None, '432,768', 93, 35, False)):
            raise ValueError('Original request identity differs at CAL index ' + str(index))
        for key, old in [('official_WC', baseline['off']), ('W1_scalar', case['scalar_off'])]:
            saved = row[key]
            if (saved.get('outcome'), saved.get('path'), saved.get('sha256')) != (
                    old.get('outcome'), old.get('video_path'), old.get('video_sha256')):
                raise ValueError('Old WC/W1 artifact binding differs at CAL index ' + str(index))
        should_generate = index in INDICES
        if row['generate_new_Native_in_proposed_card'] is not should_generate:
            raise ValueError('Missing-reference selection differs')
        if should_generate:
            if case['scalar_off']['outcome'] != 'ACCEPTED' or row['matched_Native'] is not None:
                raise ValueError('Only accepted W1 with missing reference can enter the new card')
            selected.append(row)
        elif index in (1, 2):
            if row['matched_Native'] is None:
                raise ValueError('Two existing matched Native references must remain bound')
        elif index == 6:
            if case['scalar_off']['outcome'] != 'VIDEO_REJECTED' or row['matched_Native'] is not None:
                raise ValueError('Original rejected robot sample cannot be replaced')
    if tuple(r['scene'] for r in selected) != NAMES:
        raise ValueError('Five original scene names differ')
    if (draft['model_setup_from_original_W1'] != replay['setup']
            or draft['sampling_protocol'] != replay['sampling_protocol']
            or draft['decoder_checkpoint_sha256'] != replay['decoder_checkpoint_sha256']
            or replay['sampling_protocol'] != original_cal['sampling_protocol']
            or replay['decoder_checkpoint_sha256'] != original_cal['decoder_checkpoint_sha256']):
        raise ValueError('Original setup/scheduler/decoder binding differs')
    if draft['planned_changes_to_generation'] != {
            'worldcache_enabled': False, 'output_dir': 'new independent card directory'}:
        raise ValueError('Only Native enablement and output directory can change')
    return selected


def validate_core_stage(stage, project, runtime, config):
    """Read-only closure; source inheritance never supplies execution authority."""
    stage, project, runtime = map(Path, (stage, project, runtime))
    if (config['identity'] != 'WC_W1_NATIVE_REFERENCE_CORE_CPU_R1_20261006'
            or config['GPU_execution_selected'] is not False or config['gpu_uuid'] is not None
            or config['execution_scope_authority'] is not None
            or config['generation_supervisor_ready'] is not False):
        raise ValueError('Only the unselected CPU core is supported at this stage')
    for name, digest in config['payload_sha256'].items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or sha(stage / p) != digest:
            raise ValueError('Frozen CPU payload differs: ' + name)
    for name, digest in config['upstream_sha256'].items():
        if sha(runtime / name) != digest: raise ValueError('Pinned upstream differs: ' + name)
    for name, digest in config['project_input_sha256'].items():
        if sha(project / name) != digest: raise ValueError('Original root input differs: ' + name)
    draft = json.loads((stage / 'w1-reference-draft.json').read_text())
    for name, digest in draft['input_sha256'].items():
        if sha(stage / name) != digest: raise ValueError('Draft source snapshot differs: ' + name)
    replay = json.loads((stage / 'reports/w1_replay_r1_runner.json').read_text())
    original = json.loads((stage / 'reports/w1d_cal8_r1_runner.json').read_text())
    rows = validate_reference_scope(draft, replay, original)
    if json.loads((project / 'reports/budget.json').read_text()) != config['budget_snapshot']:
        raise ValueError('CPU preparation budget changed; inspect rather than charge or overwrite')
    return {'status': 'FIVE_REFERENCE_REAL_ROOT_SOURCE_SCOPE_CPU_PASS_NOT_GPU',
            'scene_names': [r['scene'] for r in rows], 'original_denominator': [8, 7, 1],
            'new_reference_phases': 5, 'GPU_submissions': 0, 'budget_changed': False}
