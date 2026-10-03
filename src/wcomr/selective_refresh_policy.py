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

    def select(self, eligible_ordinal, *, cfg=None):
        if type(eligible_ordinal) is not int or eligible_ordinal < 1:
            raise ValueError('Positive branch-local eligible refresh ordinal required')
        if cfg is not None and (type(cfg) is not int or cfg not in (0, 1)):
            raise ValueError('CFG branch must be 0 or 1')
        return (eligible_ordinal - 1) % self.every == 0

    def to_dict(self):
        return {'sparse_layers':list(self.sparse_layers), 'every':self.every,
            'cadence':'FIRST_ELIGIBLE_THEN_EVERY_K_PER_CFG_RESET_WITH_NATIVE_CYCLE',
            'selection_role':'OFFLINE_FROZEN_LAYER_CADENCE_NOT_ONLINE_RISK_OR_REFRESH_ROUTING'}


@dataclass(frozen=True)
class SparsePlacementPolicy(SparseRefreshPolicy):
    """Explicit exposed-trace diagnostic positions, indexed by past counters."""
    per_cfg_eligible_ordinals: tuple = ((), ())

    def __post_init__(self):
        super().__post_init__()
        if self.every != 1:
            raise ValueError('Explicit positions cannot also apply a periodic cadence')
        slots = self.per_cfg_eligible_ordinals
        if (type(slots) is not tuple or len(slots) != 2
                or any(type(v) is not tuple for v in slots)
                or any(any(type(n) is not int or n < 1 for n in v)
                       or tuple(sorted(set(v))) != v for v in slots)):
            raise ValueError('Two explicit sorted positive CFG ordinal tuples required')

    def select(self, eligible_ordinal, *, cfg=None):
        super().select(eligible_ordinal, cfg=cfg)
        if type(cfg) is not int or cfg not in (0, 1):
            raise ValueError('Explicit placement requires its CFG branch')
        return eligible_ordinal in self.per_cfg_eligible_ordinals[cfg]

    def to_dict(self):
        return {**super().to_dict(),
            'cadence':'EXPLICIT_ELIGIBLE_ORDINALS_PER_CFG_RESET_WITH_NATIVE_CYCLE',
            'per_cfg_eligible_ordinals':[list(v) for v in self.per_cfg_eligible_ordinals],
            'placement_role':'EXPOSED_FUTURE_TRACE_ORACLE_DIAGNOSTIC_NOT_ONLINE_POLICY'}
