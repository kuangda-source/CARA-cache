"""Official/W1/full teacher on the deployed W1 state; diagnostics never observe anchors."""
import hashlib
import inspect
import textwrap
import time
import torch

from .integration import inject_source
from .shadow_forward import ShadowProbe
from .shadow_metrics import tensor_error

CACHE_FIELDS = ['cnt', 'worldcache_step_skipped_count', 'accumulated_rel_l1_distance',
    'residual_cache', 'probe_residual_cache', 'residual_window', 'probe_residual_window',
    'previous_internal_states', 'previous_input', 'previous_output', 'resume_flag',
    'affline_scale_log_info', 'affline_emb', 'crossattn_emb']


def tensor_identity(value):
    digest = hashlib.sha256()
    digest.update(str((list(value.shape), str(value.dtype))).encode())
    digest.update(value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
    return digest.hexdigest()


def mutation_signature(value):
    """Cheap structural/version witness; full output/cache hash parity remains required."""
    if isinstance(value, torch.Tensor):
        version = None if torch.is_inference(value) else value._version
        return ('tensor', id(value), version, tuple(value.shape), str(value.dtype), str(value.device))
    if isinstance(value, dict):
        return ('dict', tuple((k, mutation_signature(v)) for k, v in sorted(value.items())))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(mutation_signature(v) for v in value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError('Uncovered deployment state in diagnostic witness')


class OwnStateProbe(ShadowProbe):
    def __init__(self, calls, replay):
        super().__init__(calls)
        ordered = sorted(self.calls)
        if (len(ordered) != len(calls) or len(ordered) % 2 or replay.mode != 'scalar'
                or any(ordered[i] % 2 != 1 or ordered[i+1] != ordered[i]+1
                       for i in range(0, len(ordered), 2))
                or any(c > len(replay.trace) or replay.trace[c-1]['deep_executed'] for c in ordered)):
            raise ValueError('Complete frozen skipped CFG pairs on scalar trajectory required')
        self.replay = replay
        self.warp = None

    def begin_request(self, identity):
        super().begin_request(identity)
        self.official_hidden = self.scalar_hidden = None
        self.input_identity = None
        self.pair_identities = {}

    def start_model_call(self, net, latent, timestep):
        if self.request != self.replay.request:
            raise RuntimeError('Own-state replay/shadow request identity differs')
        self.start_call()
        self.official_hidden = self.scalar_hidden = None
        if self.call != self.replay.call:
            raise RuntimeError('Own-state replay/shadow call differs')
        if self.call in self.calls:
            branch = net.cnt % 2
            if branch != (self.call-1) % 2:
                raise RuntimeError('Frozen CFG counter layout differs')
            pair = (self.call-1)//2
            identity = {'latent_sha256': tensor_identity(latent), 'timestep_sha256': tensor_identity(timestep)}
            if branch == 0:
                self.pair_identities[pair] = identity
            elif self.pair_identities.get(pair) != identity:
                raise RuntimeError('CFG branches are not from the same actual solver input')
            self.input_identity = identity

    def capture_official(self, net, hidden):
        if self.call in self.calls:
            self.official_hidden = hidden.detach().clone()

    def capture_scalar(self, net, hidden):
        if self.call in self.calls:
            self.scalar_hidden = hidden.detach().clone()

    def deployment_signature(self, net):
        return mutation_signature({
            'cache': {k: getattr(net, k) for k in CACHE_FIELDS if hasattr(net, k)},
            'anchors': [[(a.step, a.probe, a.residual) for a in c.anchors] for c in self.replay.calibrators],
            'history': [c.receipt() for c in self.replay.calibrators], 'records': self.replay.records})

    @torch.no_grad()
    def collect(self, net, *, skipped, branch, probe, original_input,
                predicted_hidden, predicted_velocity, block_kwargs, embedding, adaln):
        if self.call not in self.calls:
            return
        if (not skipped or self.official_hidden is None or self.scalar_hidden is None or self.warp is None
                or net.training or any(m.training for m in net.modules())
                or getattr(net, '_w1_shadow_active', False)):
            raise RuntimeError('Own-state selected skip/capture/eval/shadow contract differs')
        from .w1d import validate_geometry
        validate_geometry(net, original_input, predicted_velocity)
        history = self.replay.records[-1]['prediction']
        if history is None or any(s >= net.cnt for s in history['history']['anchor_steps']):
            raise RuntimeError('Own-state scalar prediction lacks strictly past anchors')
        signature = self.deployment_signature(net)
        buffers = [(buf, buf.detach().clone()) for buf in net.buffers()]
        prior_active_exists = hasattr(net, '_w1_shadow_active')
        prior_active = getattr(net, '_w1_shadow_active', None)
        device = probe.device
        devices = [device.index if device.index is not None else torch.cuda.current_device()] if device.type == 'cuda' else []
        sync = (lambda: torch.cuda.synchronize(device)) if devices else (lambda: None)
        sync(); started = time.perf_counter()
        try:
            net._w1_shadow_active = True
            with torch.random.fork_rng(devices=devices):
                # Official approximation is evaluated before full truth, using this W1 cache and exact pinned warp.
                official = self.warp(net, self.official_hidden, net.residual_cache[branch], original_input.shape[1])
                official_velocity = net.unpatchify(net.final_layer(official, embedding, adaln_lora_B_T_3D=adaln))
                truth = probe.detach().clone()
                for block in net.blocks[net.probe_depth:]:
                    truth = block(truth, **block_kwargs)
                truth_velocity = net.unpatchify(net.final_layer(truth, embedding, adaln_lora_B_T_3D=adaln))
                truth_residual = truth-original_input
                candidates = {}
                for name, pre, hidden, velocity in [
                        ('official', self.official_hidden, official, official_velocity),
                        ('scalar', self.scalar_hidden, predicted_hidden, predicted_velocity)]:
                    candidates[name] = {
                        'prewarp_residual': tensor_error(pre-original_input, truth_residual),
                        'postwarp_residual': tensor_error(hidden-original_input, truth_residual),
                        'velocity': tensor_error(velocity, truth_velocity)}
                sync()
                if self.deployment_signature(net) != signature:
                    raise RuntimeError('Shadow modified deployment cache, anchors or replay records')
                self.records.append({'request': self.request, 'call': self.call, 'cache_counter': net.cnt,
                    'cfg_branch': branch, 'solver_pair_index_zero_based': (self.call-1)//2,
                    'actual_input_identity': dict(self.input_identity), 'shared_teacher': True,
                    'shadow_deep_blocks': len(net.blocks)-net.probe_depth,
                    'diagnostic_seconds': time.perf_counter()-started, 'candidates': candidates,
                    'scalar_prediction_history': history,
                    'scope': 'SAME_DEPLOYED_W1_STATE_FIXED_MASK; current teacher score-only, no anchor observation'})
        finally:
            for buf, saved in buffers:
                buf.copy_(saved)
            if prior_active_exists:
                net._w1_shadow_active = prior_active
            else:
                delattr(net, '_w1_shadow_active')
            self.official_hidden = self.scalar_hidden = None

    def finish(self):
        if [r['call'] for r in self.records] != sorted(self.calls):
            raise RuntimeError('Missing registered own-state observations; no narrower subset')
        self.replay.finish()
        if any(c[k]['status'] != 'OK' for r in self.records for c in r['candidates'].values()
               for k in ['prewarp_residual', 'postwarp_residual', 'velocity']):
            raise RuntimeError('Nonfinite registered own-state observation')
        for left, right in zip(self.records[::2], self.records[1::2]):
            if left['actual_input_identity'] != right['actual_input_identity']:
                raise RuntimeError('Own-state paired observation input differs')
        return self.records


def build_own_state_forward(original, replay, diagnostic):
    if diagnostic.replay is not replay:
        raise ValueError('Diagnostic belongs to another scalar replay')
    original_source = inspect.getsource(original)
    start = '        # --- Flow-Warped Scaling ---'
    end = '    else:\n        # CACHE MISS or PROBE PHASE'
    if original_source.count(start) != 1 or original_source.count(end) != 1:
        raise RuntimeError('Unsupported pinned own-state warp section')
    section = original_source.split(start, 1)[1].split(end, 1)[0]
    warp = ('def _own_warp(self, x_B_T_H_W_D, residual_x, T):\n    current_idx = self.cnt % 2\n'
            + textwrap.indent(textwrap.dedent(section).strip(), '    ') + '\n    return x_B_T_H_W_D\n')
    source = inject_source(original_source)
    prediction = '        x_B_T_H_W_D = ori_x + _w1_predict(self, current_idx, test_x - ori_x, x_B_T_H_W_D - ori_x)\n'
    edits = [
        ('    _w1_begin(self)\n', '    _own_begin(self, x_B_C_T_H_W, timesteps_B_T)\n'),
        (prediction, '        _own_official(self, x_B_T_H_W_D)\n' + prediction + '        _own_scalar(self, x_B_T_H_W_D)\n'),
        ('if self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh: # skip this step',
         'if _own_skip(self, self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh): # frozen schedule'),
        ('    # --- Final Layer & Unpatchify ---', '    _own_verify(self, skip_forward)\n    # --- Final Layer & Unpatchify ---'),
        ('    # Increment Step Counter',
         '    _own_collect(self, skipped=skip_forward, branch=current_idx, probe=test_x, original_input=ori_x,\n'
         '        predicted_hidden=x_B_T_H_W_D, predicted_velocity=x_B_C_Tt_Hp_Wp,\n'
         '        block_kwargs=block_kwargs, embedding=t_embedding_B_T_D, adaln=adaln_lora_B_T_3D)\n\n    # Increment Step Counter')]
    for anchor, replacement in edits:
        if source.count(anchor) != 1:
            raise RuntimeError('Unsupported own-state injection anchor')
        source = source.replace(anchor, replacement)
    def begin(net, latent, timestep):
        replay.begin_call(net)
        diagnostic.start_model_call(net, latent, timestep)
    namespace = dict(original.__globals__)
    exec(compile(warp, '<w1-own-state-pinned-warp>', 'exec'), namespace)
    diagnostic.warp = namespace['_own_warp']
    namespace.update(_own_begin=begin, _own_skip=replay.choose_skip, _own_verify=replay.verify_execution,
        _w1_predict=replay.predict, _w1_observe=replay.observe, _own_official=diagnostic.capture_official,
        _own_scalar=diagnostic.capture_scalar, _own_collect=diagnostic.collect)
    exec(compile(source, '<w1-own-state-shadow>', 'exec'), namespace)
    return namespace[original.__name__]
