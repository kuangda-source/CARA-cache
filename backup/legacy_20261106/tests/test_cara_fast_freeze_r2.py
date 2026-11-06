import copy
import tempfile
import unittest
from pathlib import Path

from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_collection_r2 import freeze_selection
from wcomr.cara_fast_spec_r1 import digest

ROOT=Path(__file__).resolve().parents[1]


class FrozenSelectionTests(unittest.TestCase):
    def fixture(self):
        card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        schedules={s['requested_steps']:s for s in card['schedules']}
        state=dict(phase='A',status='TERMINAL',scope_sha256=card['scope_sha256'],
                   diagnostic_gate=dict(passed=True,actual_roles=['NATIVE35','ALLD','WC_T006']),rows=[])
        scores=[]
        anchors={s['member']:s for s in card['physical_matrix'] if s['section']=='A_ANCHOR'}
        for slot in (s for s in card['physical_matrix'] if s['phase']=='A'):
            role=card['roles'][slot['role']]
            result=dict(role=slot['role'],concrete_role=slot['role'],CPU_fixture=False,
                audit_enabled=slot['audit_enabled'],solver_steps=schedules[role['requested_steps']]['actual_updates'],
                guided_pairs=schedules[role['requested_steps']]['actual_updates'],
                in_timing_guided_copies=36 if slot['audit_enabled'] else 0,in_timing_hashes=0,research_checkpoints=0,
                T_DD=300. if slot['role']=='NATIVE35' else 200.)
            state['rows'].append(dict(slot=slot,status='COMPLETE',result=result))
            if slot['purpose']=='calibration':
                scores.append(dict(id=slot['id'],status='COMPLETE',frames=93,Alex=.1,
                    candidate=dict(slot_id=slot['id']),reference=dict(slot_id=anchors[slot['member']]['id'])))
        release=dict(phase='A',scope_sha256=card['scope_sha256'],phase_state_sha256=digest(state),
                     GPU_released=True,cost_settled=True,original_process_exited=True,technical_accepted=True,
                     host='four_card',gpu_uuid='UNIT_TEST_NOT_AN_ACTUAL_GPU')
        score=dict(status='ACCEPTED_COMPLETE',scope_sha256=card['scope_sha256'],
                   phase_state_sha256=digest(state),protocol_sha256=card['fidelity_protocol_sha256'],rows=scores)
        return card,state,release,score

    def test_complete_grid_freezes_once_and_never_authorizes_B(self):
        card,state,release,score=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'frozen.json'
            result=freeze_selection(card,state,release,score,path)
            self.assertEqual(set(result['selected']),set(card['finite_grids']))
            self.assertFalse(result['authorizes_phase_B'])
            self.assertFalse(result['CHECK_accessed'])
            with self.assertRaises(ValueError):
                freeze_selection(card,state,release,score,path)

    def test_incomplete_unreleased_or_wrong_reference_refused(self):
        for change in ('missing_path','not_released','missing_score','diagnostic_reference'):
            card,state,release,score=self.fixture()
            if change=='missing_path':
                state['rows'].pop()
            elif change=='not_released':
                release['GPU_released']=False
            elif change=='missing_score':
                score['rows'].pop()
            else:
                score['rows'][0]['reference']['slot_id']=next(s['id'] for s in card['physical_matrix']
                    if s['section']=='A_DIAGNOSTIC' and s['role']=='NATIVE35')
            release['phase_state_sha256']=score['phase_state_sha256']=digest(state)
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                freeze_selection(card,state,release,score,Path(directory)/'frozen.json')

    def test_dirty_or_CPU_native_cannot_set_the_time_target(self):
        for key,value in [('in_timing_guided_copies',1),('CPU_fixture',True),('solver_steps',35)]:
            card,state,release,score=self.fixture()
            anchor=next(r for r in state['rows'] if r['slot']['section']=='A_ANCHOR')
            anchor['result'][key]=value
            release['phase_state_sha256']=score['phase_state_sha256']=digest(state)
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                freeze_selection(card,state,release,score,Path(directory)/'frozen.json')


if __name__=='__main__':
    unittest.main()
