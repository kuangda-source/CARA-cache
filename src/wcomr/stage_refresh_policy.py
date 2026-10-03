"""Immutable current-step sparse-refresh window, without a future trace."""
from dataclasses import dataclass
from .selective_refresh_policy import SparseRefreshPolicy


@dataclass(frozen=True)
class StageRefreshPolicy(SparseRefreshPolicy):
    first_solver_step: int = 23
    last_solver_step: int = 27

    def __post_init__(self):
        super().__post_init__()
        if (type(self.first_solver_step) is not int or type(self.last_solver_step) is not int
                or not 1 <= self.first_solver_step <= self.last_solver_step <= 35):
            raise ValueError('Explicit inclusive solver window within native35 required')

    def in_window(self, solver_step):
        if type(solver_step) is not int or not 1 <= solver_step <= 36:
            raise ValueError('Current actual solver step must be1..36')
        return self.first_solver_step <= solver_step <= self.last_solver_step

    def to_dict(self):
        return {**super().to_dict(), 'first_solver_step': self.first_solver_step,
                'last_solver_step': self.last_solver_step,
                'cadence': 'FIRST_IN_WINDOW_ELIGIBLE_THEN_EVERY_K_PER_CFG_NATIVE_RESET',
                'selection_role': 'CURRENT_SOLVER_STEP_AND_PAST_CFG_COUNTER_ONLY_CAL_TUNED',
                'requires_future_mask': False, 'changes_official_cache_predicate': False}
