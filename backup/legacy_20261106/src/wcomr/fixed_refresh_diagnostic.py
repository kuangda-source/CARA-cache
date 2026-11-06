"""Pinned WC transition with a common offline mask; no learned/online policy."""
from .fixed_refresh_mask import FixedRefreshMask
from .refresh_deployment import SimpleRefreshAdapter


class FixedRefreshDiagnosticAdapter(SimpleRefreshAdapter):
    def __init__(self, context, mask, **kwargs):
        if not isinstance(mask, FixedRefreshMask):
            raise ValueError('Validated immutable fixed mask required')
        mask.bind(context)
        super().__init__(context, **kwargs)
        self.mask = mask
        self.native_decision = None

    def _transform_decision(self, source, namespace):
        anchor = 'if self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh:'
        if source.count(anchor) != 1:
            raise ValueError('Pinned adaptive-decision anchor changed')
        namespace['_fixed_should_skip'] = self._should_skip
        return source.replace(anchor,
            'if _fixed_should_skip(self, current_idx, '
            'self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh):')

    def _should_skip(self, net, branch, native):
        if net is not self.net:
            raise ValueError('Fixed diagnostic model object changed')
        self.native_decision = bool(native)
        skip = self.mask.skip(self.ledger.call, branch)
        if skip and not self.ledger.windows[branch]:
            raise ValueError('Fixed diagnostic cannot reuse an absent cache source')
        return skip

    def start(self, net, branch, condition):
        self.native_decision = None
        super().start(net, branch, condition)
        if net.worldcache_num_steps != self.mask.horizon:
            raise ValueError('Fixed diagnostic native horizon changed')
        if int(net.worldcache_num_steps * net.worldcache_ret_ratio) != self.mask.warm_calls:
            raise ValueError('Fixed diagnostic native warm allocation changed')

    def before(self, net, skipped, branch, original, probe):
        selected = self.mask.skip(self.ledger.call, branch)
        if bool(skipped) != selected:
            raise ValueError('Fixed mask not reached by native legal-decision branch')
        super().before(net, skipped, branch, original, probe)
        self.pending.update(fixed_diagnostic_mask=True,
            original_predicate_on_this_arm_state=self.native_decision,
            selected_fixed_skip=selected)

    def report(self):
        return {**super().report(), 'fixed_mask': self.mask.to_dict(),
                'online_policy': False, 'causal_refresh_value_labels': False}
