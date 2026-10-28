"""Reuse numerical verification; freeze finite FIT decisions only after release."""
import copy
import json
from pathlib import Path

from .cara_fast_spec_r1 import digest, select_baselines


def verify_diagnostics(rows):
    from .wc_time_diagnostics_r1 import verify
    aliases = dict(NATIVE35='NATIVE_U36', ALLD='WC_WRAPPER_ALLD_U36',
                   WC_T006='WC_README_U36')
    # The legacy verifier compares arrays, not parameters. Preserve the actual
    # role mapping explicitly: WC_T006 is the new local PaperPort, not README.
    adapted = [dict(row,slot=dict(row['slot'],role=aliases[row['slot']['role']])) for row in rows]
    result = verify(adapted)
    result.update(actual_roles=list(aliases),legacy_verifier_role_aliases=aliases,
                  WC_T006_identity='LOCAL_PAPERPORT_U36_TAU006_NOT_OFFICIAL_README')
    return result


def freeze_selection(card, phase_state, release, accepted_scores, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Frozen selection already exists; no overwrite')
    if (phase_state.get('phase')!='A' or phase_state.get('status')!='TERMINAL'
            or phase_state.get('scope_sha256')!=card['scope_sha256']):
        raise ValueError('Complete scope-bound phaseA required')
    expected = {s['id']:s for s in card['physical_matrix'] if s['phase']=='A'}
    rows = {r['slot']['id']:r for r in phase_state['rows']}
    if (len(phase_state['rows'])!=len(expected) or set(rows)!=set(expected)
            or any(r['slot']!=expected[sid] or r['status']!='COMPLETE' for sid,r in rows.items())):
        raise ValueError('All registered A positions required; no failed-subset selection')
    gate = phase_state.get('diagnostic_gate',{})
    if gate.get('passed') is not True or gate.get('actual_roles')!=['NATIVE35','ALLD','WC_T006']:
        raise ValueError('Complete actual three-arm numerical gate required')
    state_hash = digest(phase_state)
    if (release.get('scope_sha256')!=card['scope_sha256'] or release.get('phase')!='A'
            or release.get('phase_state_sha256')!=state_hash
            or not all(release.get(k) is True for k in (
                'GPU_released','cost_settled','original_process_exited','technical_accepted'))):
        raise ValueError('Accepted, settled and released exact phaseA required')
    if (accepted_scores.get('status')!='ACCEPTED_COMPLETE'
            or accepted_scores.get('scope_sha256')!=card['scope_sha256']
            or accepted_scores.get('phase_state_sha256')!=state_hash
            or accepted_scores.get('protocol_sha256')!=card['fidelity_protocol_sha256']):
        raise ValueError('Independently accepted score denominator and protocol required')
    score_rows = {r['id']:r for r in accepted_scores['rows']}
    calibration = [s for s in card['physical_matrix'] if s['section']=='A_CALIBRATION']
    if len(score_rows)!=len(accepted_scores['rows']) or set(score_rows)!={s['id'] for s in calibration}:
        raise ValueError('Exactly the complete finite calibration score grid required')
    schedules = {s['requested_steps']:s for s in card['schedules']}

    def clean_row(slot):
        result = rows[slot['id']]['result']
        role = card['roles'][slot['role']]
        updates = schedules[role['requested_steps']]['actual_updates']
        if (not slot['eligible_clean_time'] or slot['audit_enabled']
                or result.get('CPU_fixture') is not False or result.get('audit_enabled') is not False
                or result.get('role')!=slot['role'] or result.get('concrete_role')!=slot['role']
                or result.get('solver_steps')!=updates or result.get('guided_pairs')!=updates
                or any(result.get(k)!=0 for k in (
                    'in_timing_guided_copies','in_timing_hashes','research_checkpoints'))):
            raise ValueError('Registered complete clean GPU clock required; audit/CPU data cannot be substituted')
        return dict(member=slot['member'],host=release['host'],gpu_uuid=release['gpu_uuid'],
                    scope_sha256=card['scope_sha256'],status='COMPLETE',eligible_clean_time=True,
                    T_DD=result['T_DD'])

    anchors = {s['member']:s for s in card['physical_matrix'] if s['section']=='A_ANCHOR'}
    if set(anchors)!=set(card['FIT']):
        raise ValueError('One clean Native reference per FIT input required')
    native_rows = [clean_row(anchors[member]) for member in card['FIT']]
    selection_rows = []
    for slot in calibration:
        score = score_rows[slot['id']]
        if (score.get('status')!='COMPLETE' or score.get('frames')!=93
                or score['candidate'].get('slot_id')!=slot['id']
                or score['reference'].get('slot_id')!=anchors[slot['member']]['id']):
            raise ValueError('Each calibration score must use its matched clean Native anchor')
        family = next(f for f,candidates in card['finite_grids'].items() if slot['role'] in candidates)
        selection_rows.append(dict(clean_row(slot),family=family,candidate=slot['role'],Alex=score['Alex']))
    selected = select_baselines(selection_rows,native_rows,card['FIT'],card['finite_grids'],card['scope_sha256'])
    selected.update(phase_A_GPU_released=True,phase_state_sha256=state_hash,
                    release_sha256=digest(release),accepted_scores_sha256=digest(accepted_scores),
                    science_parent_scope_sha256=card['scientific_parent_scope_sha256'],
                    CHECK_accessed=False,authorizes_phase_B=False)
    with destination.open('x') as handle:
        json.dump(selected,handle,indent=2,allow_nan=False)
        handle.write('\n')
    return selected
