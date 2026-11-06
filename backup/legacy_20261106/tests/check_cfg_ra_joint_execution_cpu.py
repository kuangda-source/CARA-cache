"""Independent branch-execution protocol checks; no Torch/model/GPU claims."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.cfg_ra_joint_control import Calibration, JointCDController
from wcomr.cfg_ra_joint_execution import JointPolicyPairExecutor


class BranchExecutionFixture:
    def __init__(self, failure=None):
        self.net = SimpleNamespace(cnt=0, worldcache_num_steps=70,
            previous_input=[None, None], previous_internal_states=[None, None],
            residual_cache=[None, None])
        self.model = SimpleNamespace(net=self.net)
        self.poisoned = self.running = False
        self.last = None
        self.calls = 0
        self.events = []
        self.failure = failure

    def pair(self, noise, latent, timestep, conditions, choose):
        self.calls += 1
        step = self.calls
        protected = step <= 7 or step == 36
        action = 'DD'
        if not protected:
            packets = tuple(SimpleNamespace(slot=i, counter=self.net.cnt+i,
                                            delta_y=1.) for i in (0, 1))
            self.events.append((step, 'both_prefixes_complete'))
            action = choose(packets)
            self.events.append((step, 'decision', action))
        result = []
        for slot in (0, 1):
            if self.failure == 'second_branch' and step == 8 and slot == 1:
                raise RuntimeError('actual second-branch continuation failed')
            if action[slot] == 'D':
                for field in ('previous_input', 'previous_internal_states', 'residual_cache'):
                    getattr(self.net, field)[slot] = step
                self.events.append((step, 'deep', slot))
            self.net.cnt = (self.net.cnt+1) % 70
            result.append((step, slot, action[slot]))
        self.last = {'action': action, 'protected': protected, 'paid_probes': []}
        if self.failure == 'bad_counter' and step == 8:
            self.net.cnt -= 1
        if self.failure == 'mixed_action' and step == 8:
            self.last['action'] = 'CD'
        if self.failure == 'false_protected' and step == 8:
            self.last['protected'] = True
        return tuple(result)


def build(threshold, failure=None):
    cal = Calibration('EXECUTION_FIXTURE_NOT_COSMOS_CAL',
        {(a, s): 1. for a in range(1, 36) for s in range(a+1, 37)},
        {s: 1. for s in range(1, 37)})
    base = BranchExecutionFixture(failure)
    p = JointCDController(cal, threshold)
    return base, p, JointPolicyPairExecutor(base, p)


def main():
    for threshold in (0., 10000.):
        base, policy, pair = build(threshold)
        for step in range(1, 37):
            before = (policy.last_completed_step, policy.anchor)
            outputs = pair.pair('noise', 'latent', step, ('c', 'u'), pair.choose)
            assert before[0] == step-1
            expected = 'DD' if threshold == 0 or step <= 7 or step == 36 else 'CC'
            assert outputs == ((step, 0, expected[0]), (step, 1, expected[1]))
            assert pair.last['action'] == expected
            assert policy.last_completed_step == step and len(policy.history) == step
            assert policy.anchor == (step if expected == 'DD' else 7)
            assert base.net.residual_cache == [policy.anchor]*2
            if not (step <= 7 or step == 36):
                events = [e for e in base.events if e[0] == step]
                assert events[:2] == [(step, 'both_prefixes_complete'), (step, 'decision', expected)]
        assert base.net.cnt == 2 and policy.anchor == 36
        assert sum(d.action == 'CC' for d in policy.history) == (28 if threshold else 0)

    failures = []
    for fault in ('second_branch', 'bad_counter', 'mixed_action', 'false_protected'):
        base, policy, pair = build(0., fault)
        for step in range(1, 8):
            pair.pair(None, None, step, ('c', 'u'), pair.choose)
        before = (policy.anchor, policy.last_completed_step, policy.generation, tuple(policy.history))
        try:
            pair.pair(None, None, 8, ('c', 'u'), pair.choose)
        except (ValueError, RuntimeError):
            pass
        else:
            raise AssertionError('Incomplete/incorrect pair accepted: '+fault)
        assert before == (policy.anchor, policy.last_completed_step, policy.generation, tuple(policy.history))
        assert policy.poisoned and base.poisoned
        calls = base.calls
        try:
            pair.pair(None, None, 8, ('c', 'u'), pair.choose)
        except ValueError:
            pass
        else:
            raise AssertionError('Failed pair reused')
        assert calls == base.calls
        failures.append(fault)

    base, policy, pair = build(0.)
    try:
        pair.pair(None, None, 1, ('c', 'u'), lambda x: 'CC')
    except ValueError:
        pass
    else:
        raise AssertionError('Unbound selector accepted')
    assert not base.calls and not policy.history
    print(json.dumps({'status': 'RA_PAIR_EXECUTION_PROTOCOL_CPU_PASS_FIXTURE_ONLY',
        'complete36_protocol_runs': 2, 'both_paid_prefixes_before_choice_checked': True,
        'history_commit_after_actual_two_branch_completion': True,
        'failed_partial_execution_no_false_anchor_or_reuse': failures,
        'protected_warmup_tail_counter_wrap_checked': True,
        'actual_Cosmos_or_Toy_model_execution': False,
        'calibration_generated': False, 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
