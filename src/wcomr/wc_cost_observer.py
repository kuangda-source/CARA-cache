"""Read-only WC component events or QKV capture; never combine their timings."""
import functools


class WCCostObserver:
    def __init__(self, net, *, event_factory=None, capture=None, calls=(), layers=()):
        if (event_factory is None) == (capture is None):
            raise ValueError('Choose profile-only or capture-only')
        self.net, self.event_factory, self.capture = net, event_factory, capture
        self.calls, self.layers = set(calls), set(layers)
        self.call = 0
        self.context = None
        self.events, self.snapshots, self._restores, self._handles = [], [], [], []
        self.wrap(net, 'forward', 'net_inclusive', net_scope=True)

    def wrap(self, owner, name, label, layer=None, net_scope=False):
        original = getattr(owner, name)
        own, own_value = name in vars(owner), vars(owner).get(name)
        def restore():
            if own:
                setattr(owner, name, own_value)
            else:
                delattr(owner, name)
        self._restores.append(restore)
        @functools.wraps(original)
        def observed(*args, **kwargs):
            if net_scope:
                self.call += 1
                counter = getattr(self.net, 'cnt', None)
                self.context = {'call': self.call, 'cache_counter_before': counter,
                                'cfg_slot': counter % 2 if counter is not None else None}
            context = dict(self.context or {})
            start = self.event_factory() if self.event_factory else None
            end = self.event_factory() if self.event_factory else None
            if start is not None:
                start.record()
            try:
                return original(*args, **kwargs)
            finally:
                if end is not None:
                    end.record()
                    self.events.append(dict(context, label=label, layer=layer, start=start, end=end))
        setattr(owner, name, observed)

    def attach_capture(self, op, layer):
        if self.capture is None:
            raise ValueError('Capture hooks forbidden in profile-only phase')
        def hook(module, args):
            if self.call in self.calls and layer in self.layers:
                context = dict(self.context, layer=layer)
                result = self.capture(args, context)
                self.snapshots.append(dict(context, **result))
            # Return None: original QKV and downstream output remain unchanged.
        self._handles.append(op.register_forward_pre_hook(hook))

    def resolve(self):
        """Caller must synchronize once before resolving; inclusive scopes overlap."""
        rows, totals = [], {}
        for event in self.events:
            row = {k: v for k, v in event.items() if k not in ('start', 'end')}
            row['milliseconds'] = float(event['start'].elapsed_time(event['end']))
            if row['milliseconds'] < 0:
                raise ValueError('Invalid event interval')
            rows.append(row)
            total = totals.setdefault(row['label'], {'calls': 0, 'milliseconds': 0.0})
            total['calls'] += 1
            total['milliseconds'] += row['milliseconds']
        return {'rows': rows, 'totals': totals,
                'warning': 'net_inclusive overlaps components; do not sum inclusive scopes; event intervals include launch gaps'}

    def close(self):
        for handle in reversed(self._handles):
            handle.remove()
        for restore in reversed(self._restores):
            restore()
        self._handles.clear()
        self._restores.clear()
