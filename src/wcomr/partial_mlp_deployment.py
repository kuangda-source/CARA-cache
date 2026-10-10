"""Execute P0 on the returned trajectory with separate D-only provenance.

The pinned WC continuation owns its working residual/window updates. A P pair
uses that same deep continuation with genuinely gathered MLPs, then marks the
new working source P. It never becomes a calibration D or a zero-risk RA
anchor. This fixed-schedule core does not implement an RA source-risk policy.
"""
import copy
from contextlib import ExitStack, contextmanager
import hashlib
import math

import torch

from .calibration import ResidualCalibrator
from .cfg_guided_w1_collection import signature
from .cfg_guided_w1_forward import compile_collection
from .partial_mlp import PartialMLP, block_indices


METHODS = ('OFF', 'DENSE_CONTROL', 'ROTATION_050', 'RANDOM_050',
           'ROTATION_075', 'RANDOM_075', 'FULL_P_DECLARED_P')
P_STEPS = (12, 18, 24, 30)
D_STEPS = tuple(range(1, 8)) + (13, 19, 25, 31, 36)


class PartialDeployment:
    """Observation hooks, actual projection contexts and working-source ledger.

    Indices are prepared only after both paid probes select P, from the actual
    compatible past projection layout. The MLP owner validates the current
    layout again and records any full safe fallback without relabeling P as D.
    """
    def __init__(self, model, *, method, context, layers, block_size=128):
        if (method not in METHODS or type(context) is not tuple or len(context) != 3
                or any(type(v) is not str or not v for v in context)
                or type(block_size) is not int or block_size <= 0):
            raise ValueError('Explicit method/request/layout and block size required')
        self.model, self.net = model, model.net
        self.method, self.context, self.block_size = method, context, block_size
        self.core = None if method == 'OFF' else PartialMLP(self.net.blocks, layers).install()
        self.dense = [ResidualCalibrator(), ResidualCalibrator()]
        for c in self.dense:
            c.reset(context)
        self.working = [None, None]
        self.history = []
        self.current = None
        self.poisoned = False
        self.epoch = self.opportunities = 0
        self.warp = self.to_velocity = None
        self._condition_identity = self._noise_identity = self._layout_identity = None
        self._parameter_identity = tuple((id(p), p._version) for p in self.net.parameters())

    def begin(self, noise, latent, timestep, conditions, stack):
        step = len(self.history) + 1
        if (self.current is not None or self.poisoned or torch.is_grad_enabled()
                or not 1 <= step <= 36 or self.model.net is not self.net
                or int(self.net.cnt) != 2*(step-1) % 70
                or int(self.net.worldcache_num_steps) != 70 or len(conditions) != 2):
            raise ValueError('Healthy no-grad full36 same-request origin required')
        condition_identity = signature([vars(c) for c in conditions])
        noise_identity = signature(noise)
        layout_identity = (tuple(latent.shape), str(latent.dtype), str(latent.device))
        if (tuple((id(p), p._version) for p in self.net.parameters()) != self._parameter_identity
                or self._condition_identity not in (None, condition_identity)
                or self._noise_identity not in (None, noise_identity)
                or self._layout_identity not in (None, layout_identity)):
            raise ValueError('Changed model/condition/noise/layout requires a fresh request owner')
        self._condition_identity, self._noise_identity, self._layout_identity = (
            condition_identity, noise_identity, layout_identity)
        self.current = {'step': step, 'stack': stack, 'action': None, 'started': False,
            'indices': None, 'branches': {}, 'noise': noise, 'latent': latent,
            'timestep': timestep, 'conditions': conditions,
            'inputs': signature((noise, latent, timestep)),
            'condition_signature': condition_identity}

    def _branch(self, net, slot):
        if (self.current is None or net is not self.net or slot not in (0, 1)
                or net.cnt != (2*(self.current['step']-1)+slot) % 70):
            raise ValueError('Actual P0 branch/counter binding differs')
        return self.current['step']

    def select(self, packets):
        cur = self.current
        if (cur is None or cur['action'] is not None or len(packets) != 2
                or [(p.slot, p.counter) for p in packets] !=
                [(b, (2*(cur['step']-1)+b) % 70) for b in (0, 1)]):
            raise ValueError('Exactly one current two-paid-probe choice required')
        step = cur['step']
        action = 'D' if step in D_STEPS else 'C'
        if self.method not in ('OFF', 'DENSE_CONTROL') and step in P_STEPS:
            action = 'P'
            expected = {(l, b) for l in self.core.layers for b in (0, 1)}
            if (set(self.core.cache) != expected or any(c.context != self.context
                    or c.last_actual_D is None or c.last_actual_D >= step
                    for c in self.core.cache.values())):
                raise ValueError('P requires complete compatible strictly past D projections')
            first = self.core.cache[(self.core.layers[0], 0)]
            tokens = math.prod(first.value.shape[:-1])
            if any(tuple(c.value.shape) != tuple(first.value.shape)
                   for c in self.core.cache.values()):
                raise ValueError('Shared-mask projection layouts differ')
            if self.method == 'FULL_P_DECLARED_P':
                cur['indices'] = torch.arange(tokens, dtype=torch.int64)
            else:
                seed = None
                if self.method.startswith('RANDOM'):
                    key = 'P0-DEPLOYMENT-CORE-R1:'+repr(self.context)+':'+str(step)
                    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') % (2**63-1)
                cur['indices'] = block_indices(tokens,
                    .5 if self.method.endswith('050') else .75,
                    block_size=self.block_size, opportunity=self.opportunities, random_seed=seed)
            self.opportunities += 1
        cur['action'] = action
        # DD describes the pinned continuation, not the semantic source kind.
        return 'CC' if action == 'C' else 'DD'

    @contextmanager
    def dense_context(self, net, slot):
        self._branch(net, slot)
        cur = self.current
        if cur['action'] is None:
            cur['action'] = 'D'  # Actual warmup/new-cycle protected pair.
        if cur['action'] not in ('D', 'P'):
            raise ValueError('Deep continuation entered for a C action')
        if self.core is None:
            yield
            return
        if not cur['started']:
            cur['stack'].enter_context(self.core.pair(step=cur['step'],
                action=cur['action'], context=self.context, indices=cur['indices']))
            cur['started'] = True
        with self.core.branch(slot):
            yield

    def prewarp(self, net, slot, hidden):
        self._branch(net, slot)

    def hidden(self, net, skipped, slot, original, probe, hidden, kwargs, embedding, adaln):
        step = self._branch(net, slot)
        cur = self.current
        if slot in cur['branches'] or skipped != (cur['action'] == 'C'):
            raise ValueError('Physical continuation and semantic source differ')
        if not all(bool(torch.isfinite(t).all()) for t in (original, probe, hidden)):
            raise ValueError('Nonfinite source refused')
        branch = {'kind': cur['action'], 'output_seen': False}
        if cur['action'] in ('D', 'P'):
            branch['probe'] = net.probe_residual_cache[slot].detach().clone()
            branch['residual'] = net.residual_cache[slot].detach().clone()
        else:
            if self.working[slot] is None:
                raise ValueError('C has no tracked working source')
        cur['branches'][slot] = branch

    def output(self, net, slot, head):
        self._branch(net, slot)
        branch = self.current['branches'].get(slot)
        if branch is None or branch['output_seen']:
            raise ValueError('Exactly one actual source output required')
        branch['output_seen'] = True

    def commit(self, actual, base_last):
        cur = self.current
        if (cur is None or set(cur['branches']) != {0, 1}
                or any(not v['output_seen'] for v in cur['branches'].values())
                or base_last['action'] != ('CC' if cur['action'] == 'C' else 'DD')
                or int(self.net.cnt) != 2*cur['step'] % 70
                or not isinstance(actual, tuple) or len(actual) != 2
                or any(not bool(torch.isfinite(v).all()) for v in actual)):
            raise ValueError('Both actual branches and full counter completion required')
        if (signature((cur['noise'], cur['latent'], cur['timestep'])) != cur['inputs']
                or signature([vars(c) for c in cur['conditions']]) != cur['condition_signature']):
            raise ValueError('Deployment changed solver input or condition')
        action, step = cur['action'], cur['step']
        before = [c.receipt()['anchor_steps'] for c in self.dense]
        if action == 'D':
            for slot in (0, 1):
                b = cur['branches'][slot]
                if not self.dense[slot].observe_full(context=self.context, step=step,
                        probe=b['probe'], residual=b['residual']):
                    raise ValueError('Actual D calibration observation invalid')
        after = [c.receipt()['anchor_steps'] for c in self.dense]
        if action != 'D' and before != after:
            raise ValueError('Approximate source changed true D anchors')
        projection = ([] if self.core is None or action == 'C' else
                      [copy.deepcopy(v) for v in self.core.records if v.get('step') == step])
        if self.core is not None and action != 'C' and len(projection) != 2*len(self.core.layers):
            raise ValueError('Complete selected projection source records required')
        if action != 'C':
            for slot in (0, 1):
                self.working[slot] = {'context': list(self.context), 'slot': slot,
                    'epoch': self.epoch, 'created_step': step, 'kind': action,
                    'creation_error': 'SAME_STATE_OPERATOR_ZERO' if action == 'D' else 'UNKNOWN_NOT_ZERO',
                    'RA_zero_risk_reset_allowed': action == 'D',
                    'quality_model_version': 'TRUE_D' if action == 'D' else 'P0_UNCALIBRATED_DEPLOYMENT_R1',
                    'actual_MLP_sources': [v for v in projection if v['slot'] == slot]}
        row = {'step': step, 'action': action*2, 'physical_continuation': base_last['action'],
            'protected': base_last['protected'], 'true_D_before': before, 'true_D_after': after,
            'working_sources': copy.deepcopy(self.working),
            'working_source_ages': [step-v['created_step'] for v in self.working],
            'actual_projection_records': projection, 'teacher_calls': 0,
            'extra_candidate_heads': 0, 'actual_post_RF_returned_without_substitution': True,
            'P_updates_true_D_or_zero_risk_RA_anchor': False, 'native_cycle_reset': self.net.cnt == 0}
        self.history.append(row)
        if self.net.cnt == 0:
            self.epoch += 1
            self.working = [None, None]
            for c in self.dense:
                c.reset(self.context)
            if self.core is not None:
                self.core.cache.clear()
        self.current = None
        return actual

    def finish(self):
        if self.current is not None or self.poisoned or len(self.history) != 36:
            raise ValueError('Complete healthy full36 deployment required')
        return {'method': self.method, 'completed_pairs': 36, 'history': copy.deepcopy(self.history),
            'true_D_final': [c.receipt() for c in self.dense], 'teacher_calls': 0,
            'extra_candidate_heads': 0, 'source_risk_RA_policy_implemented': False,
            'Cosmos_or_UniPC_or_video_quality_or_speed_claim': False}

    def close(self):
        if self.core is not None:
            self.core.close()


class PartialDeploymentPair:
    def __init__(self, executor, deployment):
        if executor.model is not deployment.model or executor.net is not deployment.net:
            raise ValueError('One bound P0 owner and pair executor required')
        self.executor, self.deployment = executor, deployment
        self.model, self.net = executor.model, executor.net
        self.choose = deployment.select
        self.last = None

    def pair(self, noise, latent, timestep, conditions, choose):
        if choose is not self.choose:
            raise ValueError('Original P0 selector identity required')
        d = self.deployment
        try:
            with ExitStack() as stack:
                d.begin(noise, latent, timestep, conditions, stack)
                actual = self.executor.pair(noise, latent, timestep, conditions, self.choose)
                stack.close()  # Both projection branches commit before provenance.
                returned = d.commit(actual, self.executor.last)
                self.last = {**self.executor.last, 'semantic_action': d.history[-1]['action'],
                    'P0_deployment': copy.deepcopy(d.history[-1])}
                return returned
        except BaseException:
            d.poisoned = self.executor.poisoned = True
            raise


def compile_partial_deployment(runtime, wc, rf, deployment):
    return compile_collection(runtime, wc, rf, deployment,
                              dense_context=deployment.dense_context)
