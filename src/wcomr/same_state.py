"""Three approximators scored on one official trajectory, without deploying candidates.

The source-derived warp matches the current pinned candidate insertion semantics.
Truth is shared only for scoring, never for anchor updates or cache decisions.
"""
import inspect
import textwrap
import time
import torch
from .calibration import ResidualCalibrator
from .shadow_forward import ShadowProbe
from .shadow_metrics import tensor_error


class SameStateProbe(ShadowProbe):
    def __init__(self, calls, calibration_params=None):
        super().__init__(calls)
        self.calibration_params = dict(calibration_params or {})
        self.model_identity = None
        self.calibrators = None
        self.prewarp = None
        self.warp = None
        self.cycle = 0

    def begin_request(self, identity):
        super().begin_request(identity)
        self.calibrators = None
        self.prewarp = None
        self.cycle = 0
        self.model_identity = None

    def start_model_call(self, net):
        self.start_call()
        self.prewarp = None
        identity = (id(net), getattr(net, '_w1_expert_key', None))
        if net.cnt == 0 or self.calibrators is None or identity != self.model_identity:
            self.cycle += 1
            self.model_identity = identity
            self.calibrators = {mode: [ResidualCalibrator(**self.calibration_params),
                                      ResidualCalibrator(**self.calibration_params)]
                                for mode in ('scalar', 'shrink')}
            for calibrators in self.calibrators.values():
                for branch, calibrator in enumerate(calibrators):
                    calibrator.reset(self.context(net, branch))

    def context(self, net, branch):
        return (self.request, self.cycle, id(net), branch,
                getattr(net, '_w1_expert_key', None))

    def capture_prewarp(self, net, hidden):
        if self.call in self.calls:
            # Upstream warp replaces tensors rather than mutating this input.
            self.prewarp = hidden

    def observe(self, net, branch):
        # Invoked only on the real deployment full branch, before diagnostics.
        for mode in ('scalar', 'shrink'):
            self.calibrators[mode][branch].observe_full(
                context=self.context(net, branch), step=net.cnt,
                probe=net.probe_residual_cache[branch], residual=net.residual_cache[branch])

    @torch.no_grad()
    def collect(self, net, *, skipped, branch, probe, original_input,
                predicted_hidden, predicted_velocity, block_kwargs, embedding, adaln):
        if not skipped or self.call not in self.calls:
            return
        if self.prewarp is None or self.warp is None:
            raise RuntimeError('Missing same-call prewarp or pinned warp')
        if net.training or any(m.training for m in net.modules()):
            raise RuntimeError('Same-state diagnostics require eval mode')
        if getattr(net, '_w1_shadow_active', False):
            raise RuntimeError('Nested shadow execution')
        device = probe.device
        devices = [device.index if device.index is not None else torch.cuda.current_device()] if device.type == 'cuda' else []
        sync = (lambda: torch.cuda.synchronize(device)) if devices else (lambda: None)
        buffers = [(buf, buf.detach().clone()) for buf in net.buffers()]
        sync(); started = time.perf_counter()
        try:
            net._w1_shadow_active = True
            with torch.random.fork_rng(devices=devices):
                candidates = {}
                official_residual = self.prewarp - original_input
                # Predictions are made before computing current truth.
                for mode in ('scalar', 'shrink'):
                    cal = self.calibrators[mode][branch]
                    history = cal.receipt()
                    value, reason = cal.predict(context=self.context(net, branch),
                        step=net.cnt, probe=probe-original_input,
                        official=official_residual, mode=mode)
                    if cal.receipt() != history:
                        raise RuntimeError('Candidate prediction changed anchor statistics')
                    beta = None
                    ratio = None
                    if reason == 'scalar':
                        beta = max(-cal.clip, min(cal.clip, cal.numerator / (cal.denominator + cal.ridge)))
                    if reason == 'shrink':
                        a, b = cal.anchors
                        ratio = min((net.cnt-b.step)/(b.step-a.step), cal.clip)
                    hidden = original_input + value
                    warped = self.warp(net, hidden, net.residual_cache[branch], original_input.shape[1])
                    velocity = net.unpatchify(net.final_layer(warped, embedding, adaln_lora_B_T_3D=adaln))
                    candidates[mode] = {'residual': value, 'hidden': warped, 'velocity': velocity,
                                        'reason': reason, 'history': history, 'beta': beta, 'anchor_gap_ratio': ratio}
                truth = probe.detach().clone()
                sync()
                truth_started = time.perf_counter()
                for block in net.blocks[net.probe_depth:]:
                    truth = block(truth, **block_kwargs)
                truth_velocity = net.unpatchify(net.final_layer(truth, embedding, adaln_lora_B_T_3D=adaln))
                sync(); truth_seconds = time.perf_counter()-truth_started
                truth_residual = truth-original_input
                scores = {'official': {
                    'prewarp_residual': tensor_error(official_residual, truth_residual),
                    'postwarp_residual': tensor_error(predicted_hidden-original_input, truth_residual),
                    'velocity': tensor_error(predicted_velocity, truth_velocity), 'reason': 'official'}}
                for mode, item in candidates.items():
                    scores[mode] = {
                        'prewarp_residual': tensor_error(item['residual'], truth_residual),
                        'postwarp_residual': tensor_error(item['hidden']-original_input, truth_residual),
                        'velocity': tensor_error(item['velocity'], truth_velocity),
                        'reason': item['reason'], 'history': item['history'],
                        'beta': item['beta'], 'anchor_gap_ratio': item['anchor_gap_ratio']}
                    if self.calibrators[mode][branch].receipt() != item['history']:
                        raise RuntimeError('Current truth changed candidate history')
                sync()
                self.records.append({'request': self.request, 'call': self.call,
                    'cache_counter': net.cnt, 'cfg_branch': branch, 'cycle': self.cycle,
                    'shadow_deep_blocks': len(net.blocks)-net.probe_depth,
                    'truth_tail_seconds': truth_seconds,
                    'diagnostic_seconds': time.perf_counter()-started, 'candidates': scores,
                    'scope': 'SAME_OFFICIAL_STATE; candidate-specific pinned warp; current truth score-only'})
        finally:
            for buf, saved in buffers:
                buf.copy_(saved)
            net._w1_shadow_active = False
            self.prewarp = None


def build_same_state_forward(original, diagnostic):
    source = inspect.getsource(original)
    warp_start = '        # --- Flow-Warped Scaling ---'
    warp_end = '    else:\n        # CACHE MISS or PROBE PHASE'
    if source.count(warp_start) != 1 or source.count(warp_end) != 1:
        raise RuntimeError('Unsupported pinned warp section')
    warp_source = source.split(warp_start, 1)[1].split(warp_end, 1)[0]
    # Parameter names deliberately match the exact upstream warp section.
    warp_function = ('def _same_state_warp(self, x_B_T_H_W_D, residual_x, T):\n    current_idx = self.cnt % 2\n' +
                     textwrap.indent(textwrap.dedent(warp_source).strip(), '    ') +
                     '\n    return x_B_T_H_W_D\n')
    edits = [
        ('    current_idx = self.cnt % 2', '    _same_state_begin(self)\n    current_idx = self.cnt % 2'),
        ('        self.previous_internal_states[current_idx] = test_x\n',
         '        _same_state_prewarp(self, x_B_T_H_W_D)\n        self.previous_internal_states[current_idx] = test_x\n'),
        ('    # --- Final Layer & Unpatchify ---',
         '    if not skip_forward:\n        _same_state_observe(self, current_idx)\n\n    # --- Final Layer & Unpatchify ---'),
        ('    # Increment Step Counter',
         '    _same_state_collect(self, skipped=skip_forward, branch=current_idx,\n'
         '        probe=test_x, original_input=ori_x, predicted_hidden=x_B_T_H_W_D,\n'
         '        predicted_velocity=x_B_C_Tt_Hp_Wp, block_kwargs=block_kwargs,\n'
         '        embedding=t_embedding_B_T_D, adaln=adaln_lora_B_T_3D)\n\n    # Increment Step Counter'),
    ]
    for anchor, replacement in edits:
        if source.count(anchor) != 1:
            raise RuntimeError('Unsupported same-state injection anchor')
        source = source.replace(anchor, replacement)
    ns = dict(original.__globals__)
    exec(compile(warp_function, '<w1-pinned-diagnostic-warp>', 'exec'), ns)
    diagnostic.warp = ns['_same_state_warp']
    ns.update(_same_state_begin=diagnostic.start_model_call,
              _same_state_prewarp=diagnostic.capture_prewarp,
              _same_state_observe=diagnostic.observe,
              _same_state_collect=diagnostic.collect)
    exec(compile(source, '<w1-official-same-state-scores>', 'exec'), ns)
    return ns[original.__name__]
