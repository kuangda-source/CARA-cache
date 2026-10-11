"""Bounded offline action intervention; frozen deployment rule stays intact.

Normal decisions call the exact current-birth implementation. A diagnostic
window preserves its unforced feasible candidates while explicitly executing
P/D birth followed by C4. Such choices are not online feasible-policy claims.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace

from .source_aware_current_birth_control_r1 import CurrentBirthCPDController

VERSION = 'E4C_OFFLINE_MATCHED_SOURCE_C4_SAMESTATE_TEACHER_R1'
TEACHER = 'E4C_OFFLINE_SAME_STATE_D_TEACHER'


class OfflineInterventionController(CurrentBirthCPDController):
    def __init__(self, *args, registered_birth_steps, **kwargs):
        steps = tuple(registered_birth_steps)
        if (not steps or len(set(steps)) != len(steps)
                or any(type(s) is not int or not 8 <= s <= 30 for s in steps)):
            raise ValueError('Explicit bounded registered birth events required')
        super().__init__(*args, **kwargs)
        self.registered_birth_steps = steps
        self.intervention_map = {}
        self.teacher_override = None

    def _validate_window(self, value):
        if type(value) is not dict:
            raise ValueError('Explicit diagnostic action mapping required')
        if not value:
            return
        birth = min(value)
        if (birth not in self.registered_birth_steps or len(value) != 5
                or sorted(value) != list(range(birth, birth + 5))
                or value[birth] not in ('P', 'D')
                or any(value[s] != 'C' for s in range(birth + 1, birth + 5))):
            raise ValueError('Only the complete registered birth and C4 window permitted')

    @contextmanager
    def intervention(self, birth_step, source):
        if self.intervention_map or self.teacher_override is not None:
            raise ValueError('Diagnostic windows cannot nest or overlap')
        value = {birth_step: source, **{s: 'C' for s in range(birth_step + 1, birth_step + 5)}}
        self._validate_window(value)
        if self.last_completed_step != birth_step - 1:
            raise ValueError('Matched birth must start at its preceding complete update')
        self.intervention_map = value
        try:
            yield
        finally:
            self.teacher_override = None
            self.intervention_map = {}

    @contextmanager
    def same_state_teacher(self, step):
        if (not self.intervention_map or self.teacher_override is not None
                or self.intervention_map.get(step) != 'C'
                or step - min(self.intervention_map) not in (1, 2, 4)
                or self.last_completed_step != step - 1):
            raise ValueError('Teacher must use a registered age at the actual candidate boundary')
        self.teacher_override = step
        try:
            yield
        finally:
            self.teacher_override = None

    def _choice(self, step, packet_values, ready, partial_ready, protected=False):
        original = super()._choice(step, packet_values, ready, partial_ready, protected)
        requested = ('D' if self.teacher_override == step
                     else self.intervention_map.get(step))
        if requested is None:
            return original
        if protected or original.reason != 'cheapest_feasible_bound_action':
            raise ValueError('Cannot bypass a protected or invalid physical/proxy boundary')
        birth = min(self.intervention_map)
        if step == birth and original.action != 'P':
            raise ValueError('Registered parent P event was not reproduced; retain missing event')
        if requested == 'P':
            if not partial_ready or self.partial_prior is None:
                raise ValueError('Matched P birth requires actual ready past projections')
            floor = self.partial_prior.creation_floor_at(step)
            added = original.gain * floor
        elif requested == 'C':
            if not ready:
                raise ValueError('Forced diagnostic C requires real compatible working sources')
            floor = self.creation_floor
            added = original.gain * (floor + original.local_proxy)
        else:
            floor = added = 0.
        reason = (TEACHER if self.teacher_override == step else
                  'E4C_OFFLINE_MATCHED_BIRTH_' + requested if step == birth else
                  'E4C_OFFLINE_FIXED_C')
        return replace(original, action=requested, added_risk=added,
                       predicted_creation_floor=floor, reason=reason)

    def state_dict(self):
        if self.teacher_override is not None:
            raise ValueError('Active teacher computation is not a restorable deployment boundary')
        value = super().state_dict()
        value['binding'] += (VERSION, self.registered_birth_steps)
        value['intervention_map'] = copy.deepcopy(self.intervention_map)
        return value

    def restore(self, snapshot):
        expected = super().state_dict()['binding'] + (VERSION, self.registered_birth_steps)
        if (set(snapshot) != {'binding', 'state', 'history', 'intervention_map'}
                or snapshot['binding'] != expected or type(snapshot['state']) is not tuple
                or len(snapshot['state']) != 9 or type(snapshot['history']) is not list
                or self.teacher_override is not None):
            raise ValueError('Exact inactive offline-controller state and binding required')
        self._validate_window(snapshot['intervention_map'])
        replay = type(self)(self.calibration, self.threshold, self.costs, self.partial_prior,
            strategy=self.strategy, registered_birth_steps=self.registered_birth_steps)
        replay.intervention_map = copy.deepcopy(snapshot['intervention_map'])
        for original in snapshot['history']:
            if original.owner != id(self) or original.reason == TEACHER:
                raise ValueError('Foreign or teacher-committed history cannot restore')
            decision = replay._choice(original.step, original.packets,
                original.both_sources_ready, original.partial_ready,
                protected=original.reason == 'actual_protected_dense')
            if replace(decision, owner=id(self)) != original:
                raise ValueError('Changed diagnostic action, original candidates or source history')
            replay.commit(decision, actual_action=decision.action, pair_completed=True)
        if replay._state() != snapshot['state'] or snapshot['state'][-1]:
            raise ValueError('Only complete healthy diagnostic histories restore')
        old = self.state_dict()
        (self.anchor, self.working_kind, self.working_step, self.creation_floor,
         self.accumulated, self.consecutive_P, self.last_completed_step,
         self.generation, self.poisoned) = snapshot['state']
        self.history = copy.deepcopy(snapshot['history'])
        self.intervention_map = copy.deepcopy(snapshot['intervention_map'])
        return old
