"""Attach joint C/D control to the existing paid-prefix pair executor.

The underlying executor owns model computation and fault handling. This adapter
commits policy history only after both branches return. It does not calibrate,
install a velocity factory, alter the solver, or run a counterfactual teacher.
"""
from .cfg_ra_joint_control import JointCDController


class JointPolicyPairExecutor:
    def __init__(self, executor, controller):
        if not isinstance(controller, JointCDController) or controller.history:
            raise ValueError('Fresh current-protocol joint controller required')
        if executor.model.net is not executor.net or executor.poisoned or executor.running:
            raise ValueError('Fresh bound underlying pair executor required')
        self.executor = executor
        self.controller = controller
        self.model, self.net = executor.model, executor.net
        # Retain this callable identity for the source-bound velocity factory.
        self.choose = self._select
        self.last = None
        self._pending = None
        self._running = False

    def _select(self, packets):
        if not self._running or self._pending is not None:
            raise ValueError('Exactly one selection at the current pair required')
        ready = all(getattr(self.net, field)[slot] is not None
                    for field in ('previous_input', 'previous_internal_states', 'residual_cache')
                    for slot in (0, 1))
        self._pending = self.controller.decide(
            self.controller.last_completed_step + 1, packets, both_sources_ready=ready)
        return self._pending.action

    def pair(self, noise, latent, timestep, conditions, choose):
        step = self.controller.last_completed_step + 1
        if (choose is not self.choose or self._running or self.controller.poisoned
                or self.executor.poisoned or not 1 <= step <= 36
                or int(self.net.worldcache_num_steps) != 70
                or int(self.net.cnt) != 2 * (step - 1) % 70):
            raise ValueError('Bound selector/full36 sampler history differs')
        self._pending = None
        self._running = True
        try:
            outputs = self.executor.pair(noise, latent, timestep, conditions, self.choose)
            actual = self.executor.last
            if (not isinstance(outputs, tuple) or len(outputs) != 2 or not actual
                    or actual['action'] not in ('CC', 'DD')
                    or int(self.net.cnt) != (2 * step) % 70):
                raise ValueError('Complete actual pair outputs/action/counter missing')
            if actual['protected']:
                if self._pending is not None or actual['action'] != 'DD':
                    raise ValueError('Protected pair must actually complete dense')
                self.controller.commit_protected_dense(step, actual_action='DD', pair_completed=True)
            else:
                if self._pending is None:
                    raise ValueError('Actual paid pair has no current joint decision')
                self.controller.commit(self._pending, actual_action=actual['action'], pair_completed=True)
            self.last = {**actual, 'logical_step': step,
                         'joint_decision': self.controller.history[-1],
                         'shared_anchor_after': self.controller.anchor,
                         'accumulated_after': self.controller.accumulated}
            return outputs
        except BaseException:
            # A failed prefix/continuation leaves no usable deployment pair.
            # Do not reset the anchor or continue using partial branch history.
            self.controller.poisoned = True
            self.executor.poisoned = True
            raise
        finally:
            self._pending = None
            self._running = False
