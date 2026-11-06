"""Full36 scalar control parity and actual diagnostic-history restoration."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.cfg_paired_probe_forward import PaidProbe
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_aware_current_birth_control_r1 import CurrentBirthCPDController
from wcomr.e4c_offline_intervention_control_r1 import OfflineInterventionController, TEACHER


def make(cls):
    c = Calibration('E4C_SYNTHETIC_FULL36',
        {(a, s): 1. for a in range(1, 36) for s in range(a + 1, 37)},
        {s: 1. for s in range(1, 37)})
    p = CreationPhasePrior('E4C_SYNTHETIC_POSITIVE_FLOOR', .02, 1.,
        early_creation_floor=.01, late_creation_floor=.03)
    kwargs = {'strategy': 'WORKING_P_AGE_KEEP_INTERVAL'}
    if cls is OfflineInterventionController:
        kwargs['registered_birth_steps'] = (12, 13, 25, 27)
    return cls(c, .1, Costs('E4C_SYNTHETIC_C_P_D', .01, 4., 3.), p, **kwargs)


def packet(step):
    # C fails the proxy bound but current P birth is feasible.
    return tuple(PaidProbe(b, (2*(step-1)+b) % 70, False, 1., 1., .1) for b in (0, 1))


def advance(owner, step):
    if step <= 7 or step == 36:
        owner.commit_protected_dense(step, actual_action='D', pair_completed=True)
    else:
        d = owner.decide(step, packet(step), both_sources_ready=True, partial_ready=True)
        owner.commit(d, actual_action=d.action, pair_completed=True)
    return owner.history[-1]


def run():
    original, diagnostic = make(CurrentBirthCPDController), make(OfflineInterventionController)
    for step in range(1, 37):
        a, b = advance(original, step), advance(diagnostic, step)
        assert replace(b, owner=id(original)) == a
        assert original._state() == diagnostic._state()
    # The parity trajectory is not an event-selection fixture: its natural
    # max-consecutive-P pattern need not match the captured GPU step13 event.
    assert any(d.action == 'P' for d in diagnostic.history)
    controls = []
    # Independently exercise every registered birth with a valid common prefix.
    for birth in (12, 13, 25, 27):
        for source in ('P', 'D'):
            owner = make(OfflineInterventionController)
            for step in range(1, birth):
                if step <= 7:
                    advance(owner, step)
                else:
                    owner.commit_protected_dense(step, actual_action='D', pair_completed=True)
            parent = owner.state_dict()
            with owner.intervention(birth, source):
                d = advance(owner, birth)
                assert d.action == source and d.reason == 'E4C_OFFLINE_MATCHED_BIRTH_' + source
                assert owner.anchor == (birth if source == 'D' else birth-1)
                assert owner.creation_floor > 0 if source == 'P' else owner.creation_floor == 0
                for age in (1, 2, 3, 4):
                    step = birth + age
                    if age in (1, 2, 4):
                        saved = owner.state_dict()
                        before = copy.deepcopy(owner._state())
                        with owner.same_state_teacher(step):
                            teacher = advance(owner, step)
                            assert teacher.action == 'D' and teacher.reason == TEACHER
                            try:
                                owner.state_dict()
                            except ValueError:
                                pass
                            else:
                                raise AssertionError('Active teacher was accepted as a snapshot')
                        owner.restore(saved)
                        assert owner._state() == before
                    forced = advance(owner, step)
                    assert forced.action == 'C' and forced.reason == 'E4C_OFFLINE_FIXED_C'
                    assert owner.working_step == birth
                    assert owner.anchor == (birth if source == 'D' else birth-1)
                    assert owner.creation_floor > 0 if source == 'P' else owner.creation_floor == 0
                    image = owner.state_dict()
                    owner.restore(image)
                controls.append({'birth': birth, 'source': source,
                    'teacher_ages': [1, 2, 4], 'C4_complete': True})
            owner.restore(parent)
            assert owner._state() == parent['state'] and owner.intervention_map == {}
    refusals = []
    for fault in ('foreign_binding', 'foreign_owner', 'changed_candidates', 'changed_floor',
                  'changed_state', 'invalid_window', 'teacher_age3', 'missing_birth',
                  'protected_override', 'incomplete_pair', 'active_teacher_snapshot'):
        owner = make(OfflineInterventionController)
        for step in range(1, 13):
            owner.commit_protected_dense(step, actual_action='D', pair_completed=True)
        good = owner.state_dict()
        try:
            if fault in ('foreign_binding', 'foreign_owner', 'changed_candidates', 'changed_floor', 'changed_state', 'invalid_window'):
                bad = copy.deepcopy(good)
                if fault == 'foreign_binding': bad['binding'] = ('wrong',)
                elif fault == 'foreign_owner': bad['history'][0] = replace(bad['history'][0], owner=-1)
                elif fault == 'changed_candidates': bad['history'][0] = replace(bad['history'][0], candidates=(('C', 0, 0, 0),))
                elif fault == 'changed_floor': bad['history'][0] = replace(bad['history'][0], predicted_creation_floor=3.)
                elif fault == 'changed_state': bad['state'] = tuple([-9] + list(bad['state'][1:]))
                else: bad['intervention_map'] = {13: 'P', 14: 'C'}
                owner.restore(bad)
            elif fault == 'missing_birth':
                with owner.intervention(13, 'P'):
                    zero = tuple(replace(p, delta_y=0.) for p in packet(13))
                    owner.decide(13, zero, both_sources_ready=True, partial_ready=True)
            else:
                with owner.intervention(13, 'P'):
                    if fault == 'protected_override': owner.commit_protected_dense(13, actual_action='D', pair_completed=True)
                    elif fault == 'incomplete_pair':
                        d = owner.decide(13, packet(13), both_sources_ready=True, partial_ready=True)
                        owner.commit(d, actual_action='P', pair_completed=False)
                    else:
                        advance(owner, 13)
                        if fault == 'teacher_age3':
                            advance(owner, 14); advance(owner, 15)
                            with owner.same_state_teacher(16): pass
                        else:
                            with owner.same_state_teacher(14): owner.state_dict()
        except ValueError:
            refusals.append(fault)
        else:
            raise AssertionError('Invalid offline intervention accepted: '+fault)
    assert len(controls) == 8 and len(refusals) == 11
    return {'status': 'E4C_FULL36_SCALAR_PARITY_AND_COMPLETE_C4_CONTROLLER_CPU_PASS_NOT_PHYSICAL_MODEL',
        'normal_full36_decisions_equal': True, 'complete_birth_C4_windows': controls,
        'same_state_teacher_history_restorations': 24, 'refusals': refusals,
        'frozen_controller_source_modified': False, 'Torch_imported': 'torch' in sys.modules,
        'GPU_submissions': 0, 'ledger_written': False}


if __name__ == '__main__':
    print(json.dumps(run()))
