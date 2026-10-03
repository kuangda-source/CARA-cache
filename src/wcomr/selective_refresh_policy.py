"""Frozen offline sparse-layer/cadence policy; no error-based online selection."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SparseRefreshPolicy:
    sparse_layers: tuple
    every: int = 1

    def __post_init__(self):
        if (type(self.sparse_layers) is not tuple or not self.sparse_layers
                or any(type(v) is not int or v < 0 for v in self.sparse_layers)
                or tuple(sorted(set(self.sparse_layers))) != self.sparse_layers):
            raise ValueError('Explicit sorted nonempty sparse layer tuple required')
        if type(self.every) is not int or self.every < 1:
            raise ValueError('Sparse cadence must be a positive integer')

    def validate_geometry(self, probe_depth, blocks, fallback):
        if (any(not probe_depth <= v < blocks for v in self.sparse_layers)
                or set(self.sparse_layers).intersection(fallback)):
            raise ValueError('Sparse layer selection enters probe, fallback, or missing block')

    def select(self, eligible_ordinal):
        if type(eligible_ordinal) is not int or eligible_ordinal < 1:
            raise ValueError('Positive branch-local eligible refresh ordinal required')
        return (eligible_ordinal - 1) % self.every == 0

    def to_dict(self):
        return {'sparse_layers':list(self.sparse_layers), 'every':self.every,
            'cadence':'FIRST_ELIGIBLE_THEN_EVERY_K_PER_CFG_RESET_WITH_NATIVE_CYCLE',
            'selection_role':'OFFLINE_FROZEN_LAYER_CADENCE_NOT_ONLINE_RISK_OR_REFRESH_ROUTING'}
