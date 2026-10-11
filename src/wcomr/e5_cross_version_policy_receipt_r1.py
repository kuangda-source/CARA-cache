"""Compare semantic decisions while retaining each controller's owner invariant."""
import copy


def normalized_policy_history(history):
    if len(history)!=36 or [h['step'] for h in history]!=list(range(1,37)):
        raise ValueError('Complete ordered 36-step policy history required')
    rows=[];owner=None
    for h in history:
        value=copy.deepcopy(h['source_policy']);decision=value['decision']
        current=decision['owner']
        if type(current) is not int or current<=0 or (owner is not None and current!=owner):
            raise ValueError('Decision owner identity changed within its own path')
        owner=current
        if decision['step']!=h['step'] or decision['action']*2!=h['action']:
            raise ValueError('Source decision does not belong to the recorded action')
        # Only the opaque Python id differs between separately constructed
        # controllers. No state, score, candidate, floor or action is removed.
        decision.pop('owner')
        rows.append(value)
    return rows


def assert_policy_equivalent(left,right):
    if normalized_policy_history(left)!=normalized_policy_history(right):
        raise ValueError('Semantic source policy differs across versions')

