"""Common refresh mask, selected S layers, and branch-local sparse cadence."""
from .fixed_refresh_diagnostic import FixedRefreshDiagnosticAdapter
from .selective_refresh_policy import SparseRefreshPolicy


class SelectiveFixedRefreshAdapter(FixedRefreshDiagnosticAdapter):
    def __init__(self, context, mask, policy, **kwargs):
        if not isinstance(policy, SparseRefreshPolicy):
            raise ValueError('Validated immutable selective refresh policy required')
        super().__init__(context, mask, **kwargs)
        self.policy = self.bound_policy = policy
        self.required_fallback = self.fallback_layers
        self.eligible_refreshes = [0, 0]

    def install(self, net, wc):
        self.policy.validate_geometry(net.probe_depth, len(net.blocks), self.required_fallback)
        self.fallback_layers = tuple(v for v in range(net.probe_depth, len(net.blocks))
                                     if v not in self.policy.sparse_layers)
        return super().install(net, wc)

    def before(self, net, skipped, branch, original, probe):
        if self.policy != self.bound_policy:
            raise ValueError('Frozen sparse selection policy changed within request')
        super().before(net, skipped, branch, original, probe)
        eligible = self.mode == 'sparse'
        ordinal = None
        chosen = False
        if eligible:
            self.eligible_refreshes[branch] += 1
            ordinal = self.eligible_refreshes[branch]
            chosen = self.policy.select(ordinal)
            if not chosen:
                self.mode = 'dense'
                self.pending['action'] = 'dense'
        self.pending.update(selection_policy=self.policy.to_dict(),
            selection_eligible=eligible, selection_eligible_ordinal=ordinal,
            selection_sparse_chosen=chosen)

    def finish(self, net):
        reset = net.cnt == 0
        super().finish(net)
        if reset:
            self.eligible_refreshes = [0, 0]

    def snapshot(self):
        state = super().snapshot()
        state['selective_refresh_state'] = {'policy':self.policy.to_dict(),
                                          'eligible_refreshes':list(self.eligible_refreshes)}
        return state

    def restore(self, state):
        own = state['selective_refresh_state']
        if (own['policy'] != self.policy.to_dict() or len(own['eligible_refreshes']) != 2
                or any(type(v) is not int or v < 0 for v in own['eligible_refreshes'])):
            raise ValueError('Selective refresh checkpoint policy or counters changed')
        super().restore({k:v for k,v in state.items() if k != 'selective_refresh_state'})
        self.eligible_refreshes = list(own['eligible_refreshes'])

    def report(self):
        return {**super().report(), 'selection_policy':self.policy.to_dict(),
                'selection_counters':list(self.eligible_refreshes),
                'required_dense_fallback_layers':list(self.required_fallback)}
