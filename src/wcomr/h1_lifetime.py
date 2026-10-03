"""Fixed-trajectory three-source x 1/2/4-step shadow lifetime diagnostic."""
import inspect
import statistics
import time

import torch

from .h0_complement import H0ComplementProbe, cached_branch_source
from .h1_reference import HeldReference, ReferenceIdentity, SOURCE_KINDS
from .mid_coverage import tree_digest
from .prepared_input import RNGState
from .shadow_metrics import tensor_error


def build_h1_forward(original, diagnostic):
    source = inspect.getsource(original)
    namespace = dict(original.__globals__)
    exec(compile(cached_branch_source(source), '<h1-pinned-common-reuse>', 'exec'), namespace)
    diagnostic.cached_prediction = namespace['cached_prediction']
    edits = (
        ('    current_idx = self.cnt % 2', '    _h1_start(self)\n    current_idx = self.cnt % 2'),
        ('    # --- Execution Branching ---',
         '    _h1_before(self, skipped=skip_forward, branch=current_idx, original_input=ori_x, '
         'probe=test_x, block_kwargs=block_kwargs, embedding=t_embedding_B_T_D, '
         'adaln=adaln_lora_B_T_3D)\n\n    # --- Execution Branching ---'),
        ('        # Update Cache', '        _h1_collect(self, x_B_T_H_W_D)\n\n        # Update Cache'),
        ('    # Increment Step Counter',
         '    if not skip_forward:\n        _h1_observe(self, current_idx)\n\n    # Increment Step Counter'),
    )
    for anchor, replacement in edits:
        if source.count(anchor) != 1:
            raise ValueError('Pinned H1 injection anchor changed: ' + anchor)
        source = source.replace(anchor, replacement)
    namespace.update(_h1_start=diagnostic.start, _h1_before=diagnostic.before,
                     _h1_collect=diagnostic.collect, _h1_observe=diagnostic.observe)
    exec(compile(source, '<h1-lifetime-shadow-forward>', 'exec'), namespace)
    return namespace[original.__name__]


class H1LifetimeProbe(H0ComplementProbe):
    """Never deploy a held reference or change the official refresh schedule."""
    def __init__(self, config, *, context, kernel=None, raw_output=None):
        if (type(config.get('source_solver_step')) is not int
                or config['source_solver_step'] < 3
                or config.get('reuse_ages') != [1, 2, 4]
                or any(type(x) is not int for x in config['reuse_ages'])
                or type(config.get('warmups')) is not int or config['warmups'] < 1
                or type(config.get('repeats')) is not int or config['repeats'] < 3):
            raise ValueError('H1 requires fixed paired 1/2/4 ages, past anchors and repeated costs')
        super().__init__(config, kernel=kernel, raw_output=raw_output)
        if len(context) != 3 or not all(isinstance(x, str) and x for x in context):
            raise ValueError('Explicit request/model/condition context required')
        self.context = context
        self.references = {}
        self.source_records = []
        self.future_truths = {}
        self.source_attempts = []
        self.conditions = {}

    def start(self, net):
        if type(net.cnt) is not int or net.cnt != self.call:
            raise ValueError('H1 call counter drift; no relabeling source or age')
        if net.cnt == 0 and self.call:
            raise ValueError('H1 request reset requires a new diagnostic instance')
        self.call += 1
        if self.pending is not None:
            raise ValueError('Unconsumed H1 source comparison')

    def save_raw(self, attempt, arm, residual, velocity):
        result = super().save_raw(attempt, arm, residual, velocity)
        if result:
            result['role'] = 'H1_LOCAL_FIXED_TRAJECTORY_SCORE_ONLY_NOT_ROLLOUT_OR_TRAINING_INPUT'
        return result

    @staticmethod
    def require_eval(net):
        if net.training or any(module.training for module in net.modules()):
            raise ValueError('H1 requires shared eval')

    def full_group(self, net, state):
        hidden = state['probe'].clone()
        for block in net.blocks[net.probe_depth:]:
            hidden = block(hidden, **state['kwargs'])
        velocity = net.unpatchify(net.final_layer(
            hidden, state['embedding'], adaln_lora_B_T_3D=state['adaln']))
        return hidden, velocity

    def input_state(self, net, original_input, probe, block_kwargs, embedding, adaln):
        return {
            'original_input': original_input.detach().clone(), 'probe': probe.detach().clone(),
            'kwargs': block_kwargs, 'embedding': embedding, 'adaln': adaln,
            'rng': RNGState(), 'buffers': self.buffers(net),
        }

    @torch.no_grad()
    def before(self, net, *, skipped, branch, original_input, probe,
               block_kwargs, embedding, adaln):
        step = net.cnt // 2 + 1
        source_step = self.config['source_solver_step']
        if step == source_step:
            self.require_eval(net)
            attempt = {
                'call': self.call, 'cfg_slot': branch, 'solver_step': step,
                'status': 'STARTED_ALL_THREE_SOURCES_RETAINED_IN_DENOMINATOR',
                'historical_true_full_counters': list(self.histories[branch]),
            }
            self.source_attempts.append(attempt)
            if (skipped or not net.resume_flag[branch] or len(self.histories[branch]) < 2
                    or branch in self.references):
                attempt['status'] = 'FAILED_SOURCE_INTERFACE_NO_RESELECT'
                raise ValueError('Frozen H1 source call lacks official full/probe/two dense histories')
            self.conditions[branch] = tree_digest(block_kwargs['crossattn_emb'])
            attempt['condition_fingerprint'] = self.conditions[branch]
            state = self.input_state(net, original_input, probe, block_kwargs, embedding, adaln)
            state.update(attempt=attempt, branch=branch,
                         prior_residual=net.residual_window[branch][-1].detach().clone(),
                         prior_probe=net.probe_residual_window[branch][-1].detach().clone(),
                         prior_counter=self.histories[branch][-1])
            self.pending = state
        elif step - source_step in self.config['reuse_ages']:
            self.require_eval(net)
            if tree_digest(block_kwargs['crossattn_emb']) != self.conditions.get(branch):
                raise ValueError('H1 same-CFG source conditioning changed before reuse')
            self.future(net, branch=branch, skipped=skipped, step=step,
                        state=self.input_state(net, original_input, probe, block_kwargs, embedding, adaln))

    @torch.no_grad()
    def collect(self, net, actual_dense_hidden):
        if self.pending is None:
            if self.call in self.future_truths:
                hidden, record = self.future_truths.pop(self.call)
                if not torch.equal(hidden, actual_dense_hidden):
                    raise ValueError('Future shadow D differs from deployed current full')
                record['shadow_D_matches_deployed_full'] = True
            return
        state = self.pending
        self.pending = None
        attempt = state['attempt']
        branch = state['branch']
        signature = self.state(net)
        after_rng, after_buffers = RNGState(), self.buffers(net)
        attempt['completed_source_arms'] = rows = []
        held = {}
        try:
            net._w1_shadow_active = True
            truth_velocity = net.unpatchify(net.final_layer(
                actual_dense_hidden, state['embedding'], adaln_lora_B_T_3D=state['adaln']))
            truth_residual = actual_dense_hidden - state['original_input']
            for kind in SOURCE_KINDS:
                self.mode = kind
                wall = []
                bitwise = True
                for repeat in range(self.config['warmups'] + self.config['repeats']):
                    state['rng'].restore()
                    self.restore_buffers(state['buffers'])
                    self.sync(actual_dense_hidden)
                    begin = time.perf_counter()
                    hidden, velocity = self.full_group(net, state)
                    self.sync(actual_dense_hidden)
                    if repeat >= self.config['warmups']:
                        wall.append((time.perf_counter() - begin) * 1000)
                    if kind == 'dense':
                        bitwise &= torch.equal(hidden, actual_dense_hidden) and torch.equal(velocity, truth_velocity)
                residual = hidden - state['original_input']
                row = {
                    'arm': kind, 'wall_ms': wall, 'median_wall_ms': statistics.median(wall),
                    'postwarp_residual': tensor_error(residual, truth_residual),
                    'velocity': tensor_error(velocity, truth_velocity),
                    'dense_repeat_bitwise_matches_deployed': bitwise if kind == 'dense' else None,
                }
                rows.append(row)
                self.valid_metrics(row)
                if kind == 'dense' and not bitwise:
                    raise ValueError('H1 source true-D replay not bitwise deployed full')
                identity = ReferenceIdentity(*self.context[:2],
                    self.context[2] + ':' + self.conditions[branch], branch,
                    (net.probe_depth, len(net.blocks)), attempt['solver_step'], self.call, kind)
                reference = HeldReference(identity, prior_dense_counter=state['prior_counter'],
                    prior_residual=state['prior_residual'], prior_probe_residual=state['prior_probe'],
                    residual=residual, probe_residual=state['probe'] - state['original_input'],
                    deployment_full_verified=kind == 'dense', max_age=max(self.config['reuse_ages']))
                reference.bind_policy(net)
                held[kind] = reference
                row['provenance'] = reference.provenance()
                row['raw_snapshot'] = self.save_raw(attempt, 'source_' + kind, residual, velocity)
            attempt['status'] = 'THREE_HELD_SOURCES_COMPLETE'
            self.source_records.append(dict(attempt, arms=rows))
            self.references[branch] = held
        except BaseException:
            attempt['status'] = 'FAILED_RETAINED_IN_SOURCE_AND_LIFETIME_DENOMINATORS'
            raise
        finally:
            self.mode = 'dense'
            after_rng.restore()
            self.restore_buffers(after_buffers)
            net._w1_shadow_active = False
        if self.state(net) != signature:
            raise ValueError('H1 source comparison modified deployed state')

    @staticmethod
    def valid_metrics(row):
        for field in ('postwarp_residual', 'velocity'):
            if row[field]['status'] != 'OK' or row[field]['relative_rmse'] is None:
                raise ValueError('H1 nonfinite/undefined metric; retain planned denominator')

    @torch.no_grad()
    def future(self, net, *, branch, skipped, step, state):
        if branch not in self.references:
            raise ValueError('Missing held source CFG; no replacement point')
        age = step - self.config['source_solver_step']
        attempt = {
            'call': self.call, 'cfg_slot': branch, 'solver_step': step, 'age': age,
            'source_call': 2 * (self.config['source_solver_step'] - 1) + branch + 1,
            'status': 'STARTED_ALL_THREE_LIFETIME_CELLS_RETAINED',
            'official_future_skipped': skipped,
            'prediction_before_current_shadow_truth': True,
        }
        self.attempts.append(attempt)
        signature = self.state(net)
        predictions = {}
        rows = []
        attempt['completed_arms'] = rows
        try:
            net._w1_shadow_active = True
            context = (*self.context[:2], self.context[2] + ':' + self.conditions[branch],
                       branch, (net.probe_depth, len(net.blocks)))
            for kind, reference in self.references[branch].items():
                wall = []
                for repeat in range(self.config['warmups'] + self.config['repeats']):
                    state['rng'].restore()
                    self.restore_buffers(state['buffers'])
                    self.sync(state['probe'])
                    begin = time.perf_counter()
                    hidden = reference.predict(net, self.cached_prediction,
                        original_input=state['original_input'], probe=state['probe'],
                        solver_step=step, context=context)
                    velocity = net.unpatchify(net.final_layer(
                        hidden, state['embedding'], adaln_lora_B_T_3D=state['adaln']))
                    self.sync(state['probe'])
                    if repeat >= self.config['warmups']:
                        wall.append((time.perf_counter() - begin) * 1000)
                residual = hidden - state['original_input']
                raw = self.save_raw(attempt, 'reuse_' + kind, residual, velocity)
                predictions[kind] = (residual.detach().clone(), velocity.detach().clone())
                rows.append({'arm': kind, 'wall_ms': wall,
                    'median_wall_ms': statistics.median(wall), 'raw_snapshot': raw,
                    'provenance': reference.provenance()})
            # All predictions have been produced and serialized before the
            # current-state D teacher exists. Truth cannot enter the predictor.
            self.mode = 'dense'
            truths = []
            for _ in range(2):
                state['rng'].restore()
                self.restore_buffers(state['buffers'])
                truths.append(self.full_group(net, state))
            if not all(torch.equal(a, b) for a, b in zip(*truths)):
                raise ValueError('H1 future shadow true-D replay not bitwise')
            teacher_hidden, teacher_velocity = truths[0]
            teacher_residual = teacher_hidden - state['original_input']
            attempt['truth_raw_snapshot'] = self.save_raw(
                attempt, 'current_dense_truth', teacher_residual, teacher_velocity)
            for row in rows:
                residual, velocity = predictions[row['arm']]
                row['postwarp_residual'] = tensor_error(residual, teacher_residual)
                row['velocity'] = tensor_error(velocity, teacher_velocity)
                self.valid_metrics(row)
            attempt.update(status='THREE_SOURCE_LIFETIME_CELLS_COMPLETE',
                future_D_double_replay_bitwise_equal=True,
                shadow_D_matches_deployed_full=None if skipped else False,
                scope='FIXED_OFFICIAL_TRAJECTORY_LOCAL_ERRORS_NOT_FORKED_ROLLOUT_OR_VIDEO')
            self.records.append(attempt)
            if not skipped:
                self.future_truths[self.call] = (teacher_hidden.detach().clone(), attempt)
        except BaseException:
            attempt['status'] = 'FAILED_RETAINED_IN_18_CELL_DENOMINATOR'
            raise
        finally:
            self.mode = 'dense'
            state['rng'].restore()
            self.restore_buffers(state['buffers'])
            net._w1_shadow_active = False
        if self.state(net) != signature:
            raise ValueError('H1 future comparison modified deployed cache state')

    def coverage(self):
        expected = {(branch, age) for branch in (0, 1) for age in self.config['reuse_ages']}
        actual = {(row['cfg_slot'], row['age']) for row in self.records}
        if (actual != expected or len(self.records) != len(expected)
                or len(self.source_records) != 2 or self.pending or self.future_truths):
            raise ValueError('Incomplete H1 paired source/age coverage; no extra point permitted')
        for refs in self.references.values():
            for reference in refs.values():
                reference.check_immutable(digest=True)
        return {'source_cfg_states': 2, 'source_arms': 6,
                'future_cfg_age_states': 6, 'future_source_age_cells': 18,
                'all_held_references_immutable': True}
