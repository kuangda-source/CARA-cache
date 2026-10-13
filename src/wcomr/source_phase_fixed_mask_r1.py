"""H1 attribution controls: fixed actions, identical physical execution.

This is a baseline/control, not a content-adaptive policy. The complete mask
is fixed before a request and includes the semantic A readout. Actual source
maintenance, current probes, heads, gates and solver history remain paid.
"""
import copy
import functools
import hashlib
import json
from dataclasses import replace

from .source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner
from .source_aware_phase_sampling import bind_globals
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController

VERSION = 'SOURCE_PHASE_FROZEN_FULL36_ACTION_READOUT_MASK_CONTROL_R1'
CAL_MASK_A = tuple(['D'] * 24 + ['A'] * 5 + ['C', 'D'] + ['C'] * 4 + ['D'])
CAL_MASK_C = tuple('C' if a == 'A' else a for a in CAL_MASK_A)


def mask_fingerprint(plan):
    plan = tuple(plan)
    if (len(plan) != 36 or any(a not in ('C', 'A', 'P', 'D') for a in plan)
            or plan[:7] != ('D',) * 7 or plan[-1] != 'D'):
        raise ValueError('Complete registered mask with protected D boundaries required')
    return hashlib.sha256(json.dumps(plan).encode()).hexdigest()


class FixedMaskH1Controller(SourcePhaseH1Controller):
    def __init__(self, *a, replay_plan, **kw):
        self.replay_plan = tuple(replay_plan)
        self.mask_sha256 = mask_fingerprint(self.replay_plan)
        super().__init__(*a, **kw)

    def _choice(self, step, packet_values, ready, partial_ready, protected=False):
        # Keep the real root/source bookkeeping, without evaluating an H1
        # optimizer whose answer this fixed baseline would immediately ignore.
        origin = CurrentBirthCPDController._choice(self, step, packet_values,
            ready, partial_ready, protected)
        name = self.replay_plan[step - 1]
        if protected:
            if name != 'D': raise ValueError('Frozen mask cannot override protected D')
            return origin
        if name != 'D' and (not ready or origin.local_proxy is None or origin.gain is None):
            raise ValueError('Frozen mask lost actual supported paid-source readiness')
        if name == 'P':
            if (not partial_ready or self.partial_prior is None or self.costs.P is None
                    or self.consecutive_P >= self.partial_prior.maximum_consecutive_P):
                raise ValueError('Frozen P must have real compatible past projections')
            floor = self.partial_prior.creation_floor_at(step)
            if floor <= 0: raise ValueError('Frozen P cannot become a zero-error D source')
            added = origin.gain * floor
        elif name == 'D':
            floor = added = 0.
        else:
            floor = self.creation_floor
            added = origin.gain * (floor + origin.local_proxy)
        return replace(origin, action='C' if name == 'A' else name,
            added_risk=added, predicted_creation_floor=floor,
            reason='MATH_EVENT_FROZEN_MASK_CONTROL:' + name)

    def state_dict(self):
        value = super().state_dict()
        value['binding'] += (VERSION, self.mask_sha256)
        return value

    def restore(self, snapshot):
        if (set(snapshot) != {'binding', 'state', 'history'}
                or snapshot['binding'] != self.state_dict()['binding']):
            raise ValueError('Exact mask, source, costs and readout binding required')
        replay = FixedMaskH1Controller(self.calibration, self.threshold, self.costs,
            self.partial_prior, strategy=self.strategy,
            table_parameters=self.table_parameters, math_parameters=self.math_parameters,
            horizon=1, sigma_at=self.sigma_at, replay_plan=self.replay_plan)
        for original in snapshot['history']:
            if original.owner != id(self): raise ValueError('Foreign fixed-mask history')
            d = replay._choice(original.step, original.packets, original.both_sources_ready,
                original.partial_ready, protected=original.reason == 'actual_protected_dense')
            if replace(d, owner=id(self)) != original:
                raise ValueError('Changed frozen-mask decision or history')
            replay.commit(d, actual_action=d.action, pair_completed=True)
        if replay._state() != snapshot['state'] or snapshot['state'][-1]:
            raise ValueError('Incomplete or poisoned fixed-mask state')
        old = self.state_dict()
        (self.anchor, self.working_kind, self.working_step, self.creation_floor,
         self.accumulated, self.consecutive_P, self.last_completed_step,
         self.generation, self.poisoned) = snapshot['state']
        self.history = copy.deepcopy(snapshot['history'])
        return old

    def query_basis(self, choice):
        return {**CurrentBirthCPDController.query_basis(self, choice),
            'fixed_mask_control_version': VERSION, 'mask_sha256': self.mask_sha256,
            'preregistered_semantic_action': self.replay_plan[choice.step - 1],
            'input_adaptive_action_selection': False,
            'H1_table_and_optimizer_evaluated': False,
            'source_before': choice.state_before[1],
            'phase': 'EARLY' if choice.step < 25 else 'LATE',
            'optimizer_selected_D': False}


class FixedMaskH1Owner(SourcePhaseH1Owner):
    def __init__(self, *a, replay_plan, **kw):
        ctor = bind_globals(SourcePhaseH1Owner.__init__, {
            'SourcePhaseH1Controller': functools.partial(FixedMaskH1Controller,
                replay_plan=tuple(replay_plan))})
        ctor(self, *a, **kw)

    def installation(self):
        return super().installation() + (VERSION, self.controller.mask_sha256)


def execute_fixed(inference, sample, *, replay_plan, table_parameters,
                  previous_parameters, **kw):
    from . import clean_speed20_r1 as clean
    holder = {}
    def factory(*a, **kwargs):
        owner = FixedMaskH1Owner(*a, replay_plan=replay_plan,
            table_parameters=table_parameters, math_parameters=previous_parameters,
            horizon=1, source_mode='FUSION', **kwargs)
        holder['owner'] = owner
        return owner
    with clean.patched(clean, 'CurrentBirthSamplingOwner', factory):
        result = clean.execute(inference, sample, 'KEEP_A_P', **kw)
    owner = holder['owner']
    result.update(method='FROZEN_MASK_CONTROL',
        source_history=copy.deepcopy(owner.deployment.history),
        mask_sha256=owner.controller.mask_sha256,
        semantic_plan=list(replay_plan), online_teacher_calls=0,
        input_adaptive_action_selection=False)
    actual = [h['A_readout']['readout_action'] for h in result['source_history']]
    if actual != list(replay_plan):
        raise ValueError('Actual semantic readouts do not equal full frozen mask')
    return result
