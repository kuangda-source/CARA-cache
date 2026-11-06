"""CPU observer identity/exception/nested attribution/capture isolation controls."""
from unittest import TestCase
from wcomr.wc_cost_observer import WCCostObserver


class Event:
    clock = 0
    def record(self):
        self.t = Event.clock
        Event.clock += 1
    def elapsed_time(self, other):
        return other.t - self.t


class Handle:
    def __init__(self, owner, hook):
        self.owner, self.hook = owner, hook
    def remove(self):
        self.owner.hooks.remove(self.hook)


class Op:
    def __init__(self):
        self.hooks = []
    def register_forward_pre_hook(self, hook):
        self.hooks.append(hook)
        return Handle(self, hook)
    def forward(self, *args):
        for hook in self.hooks:
            assert hook(self, args) is None
        return args[0]


class Net:
    def __init__(self):
        self.cnt, self.op = 0, Op()
    def forward(self, value, fail=False):
        result = self.op.forward(value, value, value)
        if fail:
            raise RuntimeError('original failure')
        self.cnt = (self.cnt + 1) % 2
        return result


def test_nested_events_preserve_identity_cache_and_namespace():
    net, value = Net(), object()
    observer = WCCostObserver(net, event_factory=Event)
    observer.wrap(net.op, 'forward', 'self_core', layer=2)
    assert net.forward(value) is value and net.cnt == 1
    with TestCase().assertRaisesRegex(RuntimeError, 'original failure'):
        net.forward(value, fail=True)
    assert net.cnt == 1
    result = observer.resolve()
    assert result['totals']['net_inclusive']['calls'] == 2
    assert result['totals']['self_core']['calls'] == 2
    assert [r['cfg_slot'] for r in result['rows']] == [0, 0, 1, 1]
    assert result['totals']['net_inclusive']['milliseconds'] > result['totals']['self_core']['milliseconds']
    observer.close()
    assert 'forward' not in vars(net) and 'forward' not in vars(net.op)
    assert net.forward(value) is value


def test_capture_selection_uses_request_call_and_actual_cfg_counter():
    net, value, seen = Net(), object(), []
    def capture(args, context):
        assert args == (value, value, value)
        seen.append(context)
        return {'fixture': 'unchanged'}
    observer = WCCostObserver(net, capture=capture, calls=[1, 3], layers=[2])
    observer.attach_capture(net.op, 2)
    for _ in range(4):
        assert net.forward(value) is value
    assert [x['call'] for x in seen] == [1, 3]
    assert [x['cfg_slot'] for x in seen] == [0, 0]
    assert observer.events == [] and net.cnt == 0
    observer.close()
    assert net.op.hooks == [] and 'forward' not in vars(net)


def test_profile_capture_mutually_exclusive():
    for kwargs in [{}, {'event_factory': Event, 'capture': lambda *_: {}}]:
        with TestCase().assertRaisesRegex(ValueError, 'profile-only or capture-only'):
            WCCostObserver(Net(), **kwargs)
