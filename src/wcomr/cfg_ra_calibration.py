"""Coarse same-state Cosmos RA calibration, separate from policy evaluation.

The shared D6 parent schedule is an independently registered collection policy.
Forks perform one CC/DD intervention, followed by complete dense UniPC rollout.
The frozen original/native-policy experiments and their sources stay intact.
"""
import copy
from dataclasses import asdict
import time

import torch

from .mid_coverage import tree_digest
from .rv0_fork import SamplerSuffixControl


TARGET_STEPS = (13, 23, 33)
DENSE_STEPS = tuple(range(1, 8)) + (13, 19, 25, 31, 36)
ORIGIN_ANCHORS = {13: 7, 23: 19, 33: 31}


class SharedSchedulePairExecutor:
    """Both paid prefixes, shared actual anchors, and restorable own history."""
    def __init__(self, executor):
        if executor.running or executor.poisoned or executor.model.net is not executor.net:
            raise ValueError('Fresh bound pair executor required')
        self.executor = executor
        self.model, self.net = executor.model, executor.net
        self.choose = self._select
        self.history = []
        self.anchor = None
        self.forced_action = None
        self.last = None
        self.branches = None
        self.running = False
        self._selection = None

    def _select(self, packets):
        step = len(self.history) + 1
        if (not self.running or self._selection is not None or len(packets) != 2
                or [(p.slot, p.counter) for p in packets]
                != [(0, 2*(step-1) % 70), (1, 2*(step-1) % 70+1)]):
            raise ValueError('One actual two-prefix selection required')
        action = self.forced_action or ('DD' if step in DENSE_STEPS else 'CC')
        if action not in ('CC', 'DD'):
            raise ValueError('Shared collection supports CC/DD only')
        self._selection = action
        return action

    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history) + 1
        if (choose is not self.choose or self.running or self.executor.poisoned
                or not 1 <= step <= 36 or int(self.net.worldcache_num_steps) != 70
                or int(self.net.cnt) != 2*(step-1) % 70):
            raise ValueError('Shared full36 history/bound selector differs')
        self.running = True
        self._selection = None
        try:
            result = self.executor.pair(noise, latent, timestep, conditions, self.choose)
            actual = self.executor.last
            if (not isinstance(result, tuple) or len(result) != 2 or not actual
                    or actual['action'] not in ('CC', 'DD')
                    or int(self.net.cnt) != 2*step % 70
                    or (actual['protected'] and (actual['action'] != 'DD' or self._selection is not None))
                    or (not actual['protected'] and actual['action'] != self._selection)
                    or (self.forced_action == 'CC' and actual['protected'])):
                raise ValueError('Actual shared action/output/counter differs')
            before = self.anchor
            if actual['action'] == 'DD':
                self.anchor = step
            self.history.append({'step': step, 'action': actual['action'],
                'protected': actual['protected'], 'anchor_before': before,
                'anchor_after': self.anchor,
                'paid_probes': [asdict(p) for p in actual['paid_probes']]})
            self.last = actual
            self.branches = result
            return result
        except BaseException:
            self.executor.poisoned = True
            raise
        finally:
            self._selection = None
            self.running = False

    def snapshot(self):
        if self.running or self.executor.running or self.executor.poisoned:
            raise ValueError('Only complete healthy shared-pair boundaries can be captured')
        return {'history': copy.deepcopy(self.history), 'anchor': self.anchor,
                'forced_action': self.forced_action, 'last': copy.deepcopy(self.last),
                'base_last': copy.deepcopy(self.executor.last), 'branches': self.branches}

    def restore(self, saved):
        # A failed execution is discarded. This is successful-fork restoration,
        # never permission to unpoison an arbitrarily failed deployment.
        if self.running or self.executor.running or self.executor.poisoned:
            raise ValueError('Failed shared pair cannot be restored and continued')
        self.history = copy.deepcopy(saved['history'])
        self.anchor = saved['anchor']
        self.forced_action = saved['forced_action']
        self.last = copy.deepcopy(saved['last'])
        self.executor.last = copy.deepcopy(saved['base_last'])
        self.branches = saved['branches']

    def fingerprint(self):
        def canonical(last):
            if last is None:
                return None
            return {**last, 'paid_probes': [asdict(p) for p in last['paid_probes']]}
        return tree_digest({'history': self.history, 'anchor': self.anchor,
            'forced_action': self.forced_action, 'last': canonical(self.last),
            'base_last': canonical(self.executor.last), 'branches': self.branches})


class CoarseCalibrationFork(SamplerSuffixControl):
    """One real same-state action and unchanged complete dense solver suffix."""
    def __init__(self, *args, executor, **kwargs):
        super().__init__(*args, **kwargs)
        step = self.completed + 1
        if (step not in TARGET_STEPS or len(executor.history) != self.completed
                or executor.anchor != ORIGIN_ANCHORS[step]
                or executor.model is not self.model or executor.forced_action is not None):
            raise ValueError('Registered own-shared-history origin required')
        self.executor = executor
        self.own_state = executor.snapshot()
        self.own_fingerprint = executor.fingerprint()

    def restore_parent(self):
        latent = super().restore_parent()
        self.executor.restore(self.own_state)
        if self.executor.fingerprint() != self.own_fingerprint:
            raise ValueError('Shared collection history failed restoration')
        return latent

    @torch.no_grad()
    def measure(self, mode, *, writer, label, save):
        if mode not in ('CC', 'DD') or any(r['label'] == label for r in self.records):
            raise ValueError('Unique current CC/DD calibration arm required')
        step = self.completed + 1
        row = {'label': label, 'mode': mode, 'status': 'STARTED',
               'target_step': step, 'origin_completed_updates': self.completed,
               'shared_anchor': self.own_state['anchor'], 'reuse_age': step-self.own_state['anchor'],
               'origin_components': self.snapshot.components(),
               'origin_fingerprint': self.parent_fingerprint,
               'origin_own_fingerprint': self.own_fingerprint,
               'origin_own_history': copy.deepcopy(self.own_state['history']),
               'planned_remaining_updates': 37-step, 'current_action_intervention': True,
               'endpoint_latent_calibration_not_video_quality': True}
        self.records.append(row)
        save()
        start = time.perf_counter()
        try:
            latent = self.restore_parent()
            self.executor.forced_action = mode
            timestep = torch.stack([self.scheduler.timesteps[self.completed]]).unsqueeze(0)
            input_sha = tree_digest((self.noise, latent, timestep))
            solver_before = tree_digest({k: v for k, v in vars(self.scheduler).items() if not callable(v)})
            guided = self.velocity_fn(self.noise, latent, timestep)
            self.check_identity()
            branches = self.executor.branches
            if (self.scheduler._step_index != self.completed or self.net.cnt != 2*step
                    or tree_digest({k: v for k, v in vars(self.scheduler).items() if not callable(v)}) != solver_before
                    or self.executor.history[-1]['action'] != mode
                    or self.executor.history[-1]['protected']
                    or any(v.dtype != torch.float32 or v.shape != guided.shape
                           or not bool(torch.isfinite(v).all()) for v in branches)
                    or guided.dtype != torch.float32
                    or not torch.equal(guided, branches[0]+7*(branches[0]-branches[1]))):
                raise ValueError('Actual same-state post-denoise CFG/solver measurement differs')
            tensors = {k: v.detach().cpu().clone() for k, v in zip(
                ('conditional', 'unconditional', 'guided'), (*branches, guided))}
            row.update(pair_history=copy.deepcopy(self.executor.history[-1]),
                       current_input_sha256=input_sha, current_guided_sha256=tree_digest(guided))
            self.executor.forced_action = 'DD'
            calls = 0
            def suffix_velocity(noise, x, t):
                nonlocal calls
                calls += 1
                if calls == 1:
                    if tree_digest((noise, x, t)) != input_sha:
                        raise ValueError('First suffix velocity input differs from measured current input')
                    return guided
                return self.velocity_fn(noise, x, t)
            final = self.suffix(self.model, self.noise, latent, suffix_velocity, self.generator,
                                self.scheduler.timesteps[self.completed:])
            self.check_identity()
            history = self.executor.history[self.completed:]
            if (self.scheduler._step_index != 36 or self.net.cnt != 2
                    or calls != 37-step or len(history) != 37-step
                    or [h['step'] for h in history] != list(range(step, 37))
                    or [h['action'] for h in history] != [mode]+['DD']*(36-step)
                    or not bool(torch.isfinite(final).all())):
                raise ValueError('Complete unchanged dense UniPC suffix missing')
            tensors['final_latent'] = final.detach().cpu().clone()
            row.update(final_latent_sha256=tree_digest(final), suffix_history=copy.deepcopy(history),
                actual_suffix_solver_updates=calls, actual_suffix_net_pairs=len(history),
                first_velocity_reused_without_extra_net_pair=True,
                artifact=writer(label, tensors), status='COMPLETE_SAME_STATE_DENSE_SUFFIX_CALIBRATION')
            return row
        except BaseException as error:
            row.update(status='CALIBRATION_ARM_FAILED_COMPLETE_SCOPE_RETAINED',
                       error=str(error), error_type=type(error).__name__)
            raise
        finally:
            # On pair failure this intentionally raises too: discard the entire
            # batch; no claimed arbitrary-fault rollback or passing subset.
            self.restore_parent()
            row.update(parent_restored=True, own_shared_history_restored=True,
                       wall_seconds=time.perf_counter()-start)
            save()
