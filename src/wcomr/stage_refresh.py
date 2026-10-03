"""Online stage selector; pinned native skip/Gamma/warp code remains unchanged."""
from .refresh_deployment import SimpleRefreshAdapter
from .stage_refresh_policy import StageRefreshPolicy


class StageRefreshAdapter(SimpleRefreshAdapter):
    def __init__(self, context, policy, **kwargs):
        if type(policy) is not StageRefreshPolicy:
            raise ValueError('Immutable current-step window policy required')
        super().__init__(context, **kwargs)
        self.policy = self.bound_policy = policy
        self.required_fallback = self.fallback_layers
        self.eligible_refreshes = [0,0]

    def install(self, net, wc):
        self.policy.validate_geometry(net.probe_depth, len(net.blocks), self.required_fallback)
        self.fallback_layers = tuple(v for v in range(net.probe_depth, len(net.blocks))
                                     if v not in self.policy.sparse_layers)
        return super().install(net, wc)

    def before(self, net, skipped, branch, original, probe):
        if self.policy != self.bound_policy:
            raise ValueError('Current-step policy changed within request')
        super().before(net, skipped, branch, original, probe)
        eligible = self.mode == 'sparse'
        inside = self.policy.in_window(self.pending['solver_step'])
        ordinal, chosen = None, False
        if eligible and inside:
            self.eligible_refreshes[branch] += 1
            ordinal = self.eligible_refreshes[branch]
            chosen = self.policy.select(ordinal, cfg=branch)
        if eligible and not chosen:
            self.mode = 'dense'
            self.pending['action'] = 'dense'
        self.pending.update(selection_policy=self.policy.to_dict(),
            selection_eligible=eligible, selection_in_window=inside,
            selection_window_eligible_ordinal=ordinal, selection_sparse_chosen=chosen,
            online_policy=True, uses_future_trace=False)

    def finish(self, net):
        reset = net.cnt == 0
        super().finish(net)
        if reset: self.eligible_refreshes = [0,0]

    def snapshot(self):
        state = super().snapshot()
        state['stage_refresh_state'] = {'policy':self.policy.to_dict(),
                                       'eligible_refreshes':list(self.eligible_refreshes)}
        return state

    def restore(self, state):
        own = state['stage_refresh_state']
        if (own['policy'] != self.policy.to_dict() or type(own['eligible_refreshes']) is not list
                or len(own['eligible_refreshes']) != 2
                or any(type(v) is not int or not 0 <= v <= self.policy.last_solver_step-self.policy.first_solver_step+1
                       for v in own['eligible_refreshes'])):
            raise ValueError('Stage checkpoint policy/counters changed')
        super().restore({k:v for k,v in state.items() if k != 'stage_refresh_state'})
        self.eligible_refreshes = list(own['eligible_refreshes'])

    def report(self):
        return {**super().report(), 'selection_policy':self.policy.to_dict(),
                'selection_counters':list(self.eligible_refreshes),
                'required_dense_fallback_layers':list(self.required_fallback),
                'online_policy':True, 'uses_future_trace':False,
                'official_skip_predicate_replaced':False, 'causal_refresh_value_labels':False}
