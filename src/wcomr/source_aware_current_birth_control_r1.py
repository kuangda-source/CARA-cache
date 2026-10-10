"""Current P creation loss, separate from later borrowed C-after-P drift.

The P floor is a same-state empirical creation-error estimate. Adding a full
C drift term again makes the first P dominated under measured C<P costs.
This revision preserves all physical execution and nonzero source semantics.
"""
import ast
import hashlib
import inspect
from textwrap import dedent

from . import source_aware_cpd_control as base
from .source_aware_working_epoch_control_r2 import WorkingEpochCPDController

CURRENT_BIRTH_RULE = 'CURRENT_P_GAIN_TIMES_CREATION_FLOOR_C_AFTER_P_RETAINS_FLOOR_PLUS_BORROWED_DRIFT_R1'


class CurrentBirthCPDController(WorkingEpochCPDController):
    def state_dict(self):
        value = super().state_dict()
        value['binding'] = value['binding'] + (CURRENT_BIRTH_RULE,)
        return value


def derive(source, changes, label, namespace):
    changed = source
    for before, after, count in changes:
        if changed.count(before) != count:
            raise ValueError('Pinned current-birth derivation site changed: ' + label)
        changed = changed.replace(before, after)
    inverse = changed
    for before, after, count in reversed(changes):
        if inverse.count(after) != count:
            raise ValueError('Current-birth inverse site ambiguous: ' + label)
        inverse = inverse.replace(after, before)
    if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
        raise ValueError('Current-birth source changed outside explicit sites: ' + label)
    scope = dict(namespace)
    exec(compile(changed, __file__ + '#' + label, 'exec'), scope)
    return scope, {'inverse_AST_and_original_bytes_equal': True,
        'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'explicit_derivation_sites': sum(c for _, _, c in changes)}


original = dedent(inspect.getsource(base.SourceAwareCPDController._choice))
changes = [('p.creation_floor_proxy', 'p.creation_floor_at(step)', 2),
    ('cell = (self.anchor, step)',
     "query_anchor = self.working_step if self.working_kind == 'P' else self.anchor\n        cell = (query_anchor, step)", 1),
    ('p_added = gain*(p.creation_floor_at(step)+p.drift_ratio*local)',
     'p_added = gain*p.creation_floor_at(step)', 1)]
scope, CHOICE_PROOF = derive(original, changes, 'current-P-creation', vars(base))
CurrentBirthCPDController._choice = scope['_choice']

original_restore = dedent(inspect.getsource(WorkingEpochCPDController.restore))
restore_changes = [('self.partial_prior,self.strategy)',
                    'self.partial_prior,self.strategy,CURRENT_BIRTH_RULE)', 1),
    ('replay=WorkingEpochCPDController(', 'replay=CurrentBirthCPDController(', 1)]
scope, RESTORE_PROOF = derive(original_restore, restore_changes, 'current-birth-restore',
    {**WorkingEpochCPDController.restore.__globals__,
     'CurrentBirthCPDController': CurrentBirthCPDController,
     'CURRENT_BIRTH_RULE': CURRENT_BIRTH_RULE})
CurrentBirthCPDController.restore = scope['restore']
DERIVATION_PROOFS = {'choice': CHOICE_PROOF, 'restore': RESTORE_PROOF,
    'current_P_birth_rule': CURRENT_BIRTH_RULE,
    'C_after_P_retains_nonzero_floor_plus_borrowed_local_drift': True,
    'actual_D_history_or_physical_execution_changed': False}
