"""Prepare a source-only B36 analysis layout; never read running artifacts."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_execution_r2 import SPEC, QUOTE


def build_plan():
    card = load_card(ROOT, SPEC)
    slots = {slot['id']: slot for slot in card['physical_matrix']}
    positions = card['formal_matrix']
    roles = card['formal_roles']
    members = [row['name'] for row in card['inputs']]
    assert len(positions) == 32 and len(roles) == 8 and len(members) == 4
    assert {(row['member'], row['role']) for row in positions} == {
        (member, role) for member in members for role in roles}
    assert sum(slot['phase'] == 'B' for slot in slots.values()) == 36
    native = {row['member']: row['source'] for row in positions if row['role'] == 'NATIVE35'}
    pairs = []
    for row in positions:
        member, role, source = row['member'], row['role'], row['source']
        if 'slot_id' in source:
            slot = slots[source['slot_id']]
            assert slot['member'] == member and slot['role'] == role
            assert slot['eligible_clean_time'] and not slot['audit_enabled']
            assert slot['section'] in ('A_ANCHOR', 'B_QUALITY')
            phase = slot['phase']
        else:
            family = source['family']
            assert source['requires_frozen_selection'] is True
            choices = source['selected_candidate_slot_ids']
            assert set(choices) == set(card['finite_grids'][family])
            for candidate, slot_id in choices.items():
                slot = slots[slot_id]
                assert slot['member'] == member and slot['role'] == candidate
                assert slot['section'] == 'A_CALIBRATION' and slot['eligible_clean_time']
                assert not slot['audit_enabled']
            phase = 'A'
        pairs.append(dict(id=member+'::'+role, member=member, role=role,
            partition='FIT' if member in card['FIT'] else 'CHECK',
            candidate_source=copy.deepcopy(source), reference_source=copy.deepcopy(native[member]),
            source_phase=phase, reused_from_A=phase == 'A',
            Native_self_pair=role == 'NATIVE35', metric_status='PENDING_COMPLETE_ACCEPTED_DATA'))
    assert sum(pair['reused_from_A'] for pair in pairs) == 8
    assert sum(pair['Native_self_pair'] for pair in pairs) == 4
    policies = {role:card['roles'][role]['policy'] for role in ('F19_C','F19_A1','UNIFORM19_C')}
    assert policies['F19_C']['dense_mask'] == policies['F19_A1']['dense_mask']
    assert all(policy['actions'].count('D') == 19 for policy in policies.values())
    protocol = json.loads((ROOT/card['fidelity_protocol_ref']).read_text())
    names = [SPEC, QUOTE, card['fidelity_protocol_ref'], 'scripts/prepare_cara_fast_b36_analysis_r1.py']
    return dict(schema='CARA_FAST_B36_ANALYSIS_LAYOUT_R1',
        status='CPU_METADATA_ONLY_NO_RUNNING_OUTPUT_ACCESS',scope_sha256=card['scope_sha256'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names},
        physical_B_paths=36,B_warm_paths=6,B_quality_paths=24,B_repeat_paths=6,
        logical_formal_positions=32,reused_A_positions=8,
        A_reuse_detail=dict(clean_Native_anchors=2,selected_FIT_calibration_outputs=6),
        registered_scoring_positions=32,Native_self_checks=4,nonself_fidelity_pairs=28,
        members=members,FIT=card['FIT'],CHECK=card['CHECK'],role_display_order=roles,pairs=pairs,
        frozen_policy_controls={role:dict(fingerprint=policy['fingerprint'],
            dense_mask=policy['dense_mask'],action_counts={action:policy['actions'].count(action) for action in ('D','A','C')})
            for role,policy in policies.items()},
        existing_protocol=protocol,protocol_sha256=card['fidelity_protocol_sha256'],
        clocks=dict(primary='T_DD',secondary='T_request',
            aggregation=card['timing_analysis'],
            boundary='Keep clocks separate; never reconstruct strict T_DD from older records'),
        planned_comparisons=[
            dict(candidate='F19_C',reference='UNIFORM19_C',question='Registered dense placement at the same 19D budget'),
            dict(candidate='F19_A1',reference='F19_C',question='Registered age-1 correction rule at the same dense layout; A1 is not one A in the whole trajectory'),
            dict(candidates=['F19_C','F19_A1'],references=['WC_FAST','RA_FAST','NATIVE_K'],
                 question='Fidelity versus complete frozen fast baselines at measured time'),
            dict(candidates=['F19_C','F19_A1'],references=['SHARED25_C','NATIVE35'],
                 question='Speed and fidelity tradeoff against existing strong references')],
        report_panels=[
            dict(name='Per-member table',layout='4 members x 8 roles; keep FIT and CHECK labels'),
            dict(name='Speed versus fidelity',x='Native_T_DD / role_T_DD',y='Alex all93 mean',
                 annotations='MATCHED or UNMATCHED from the actual immutable FIT selection'),
            dict(name='Temporal and detail',fields=['reference_temporal_L1','reference_gradient_L1','gradient_energy_ratio'],
                 interpretation='Supplemental diagnostics only; no new veto thresholds'),
            dict(name='Frame curves',layout='All93 frame curves plus preregistered q95 and first worst frame')],
        awaiting=['Accepted complete A32 terminal and central bill','Accepted12 FIT scores and immutable selection',
                  'Separate B36 authorization and same-physical-GPU admission','Accepted complete B36 outputs and scores'],
        boundaries=dict(new_science_gates=False,new_statistical_claims=False,
            independent_DEV_evidence=False,protected_inputs_accessed=False,
            running_outputs_accessed=False,metrics_computed=False,
            selection_resolved=False,GPU_submissions=0,authorizes_phase_B=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan()
    with args.output.open('x') as handle:
        json.dump(plan, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key:plan[key] for key in (
        'status','physical_B_paths','logical_formal_positions','reused_A_positions','registered_scoring_positions')}))


if __name__ == '__main__':
    main()
