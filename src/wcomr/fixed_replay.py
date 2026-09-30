"""Frozen official-schedule replay; diagnostic, not an online scheduling policy."""
import inspect
from .calibration import ResidualCalibrator
from .integration import inject_source


class FixedReplay:
    def __init__(self, trace, mode='official', calibration_params=None):
        if mode not in {'official', 'scalar', 'shrink'}:
            raise ValueError('Unknown approximation mode')
        self.trace = [{key: row[key] for key in ['call', 'cache_counter_before', 'deep_executed']} for row in trace]
        if not self.trace or any(row['call'] != i+1 or type(row['deep_executed']) is not bool
            or type(row['cache_counter_before']) is not int or row['cache_counter_before'] < 0
            for i, row in enumerate(self.trace)):
            raise ValueError('Malformed or empty frozen trace')
        self.mode = mode
        self.params = dict(calibration_params or {})
        ResidualCalibrator(**self.params)  # Validate even before any generation.
        self.request = None

    def begin_request(self, identity):
        if identity is None:
            raise ValueError('Explicit replay request required')
        self.request = identity
        self.call = 0
        self.records = []
        self.calibrators = None
        self.cycle = 0
        self.model_identity = None

    def begin_call(self, net):
        if self.request is None or self.call >= len(self.trace):
            raise RuntimeError('Replay request missing or trace exhausted')
        planned = self.trace[self.call]
        if net.cnt != planned['cache_counter_before']:
            raise RuntimeError('Replay cache counter differs from frozen trace')
        identity = (id(net), getattr(net, '_w1_expert_key', None))
        if self.model_identity is not None and identity != self.model_identity:
            raise RuntimeError('Replay model/expert changed within frozen request')
        self.model_identity = identity
        if net.cnt == 0 or self.calibrators is None:
            self.cycle += 1
            self.calibrators = [ResidualCalibrator(**self.params), ResidualCalibrator(**self.params)]
            for branch, cal in enumerate(self.calibrators):
                cal.reset(self.context(net, branch))
        self.call += 1
        self.records.append({'call': self.call, 'cache_counter_before': net.cnt,
            'planned_full': planned['deep_executed'], 'natural_skip': None,
            'prediction': None, 'execution_verified': False})

    def context(self, net, branch):
        return (self.request, self.cycle, id(net), branch, getattr(net, '_w1_expert_key', None))

    def choose_skip(self, net, natural_skip):
        record = self.records[-1]
        record['natural_skip'] = bool(natural_skip)
        return not record['planned_full']

    def predict(self, net, branch, probe, official):
        cal = self.calibrators[branch]
        history = cal.receipt()
        value, reason = cal.predict(context=self.context(net, branch), step=net.cnt,
                                   probe=probe, official=official, mode=self.mode)
        if cal.receipt() != history:
            raise RuntimeError('Replay prediction modified full-anchor history')
        beta = None
        if reason == 'scalar':
            beta = max(-cal.clip, min(cal.clip, cal.numerator/(cal.denominator+cal.ridge)))
        self.records[-1]['prediction'] = {'reason': reason, 'history': history, 'beta': beta}
        return value

    def observe(self, net, branch, probe, residual):
        if not self.records[-1]['planned_full']:
            raise RuntimeError('Attempted to observe an unplanned full anchor')
        self.calibrators[branch].observe_full(context=self.context(net, branch),
            step=net.cnt, probe=probe, residual=residual)

    def verify_execution(self, net, skipped):
        record = self.records[-1]
        if bool(skipped) == record['planned_full']:
            raise RuntimeError('Execution differs from frozen full/skip schedule')
        record['execution_verified'] = True

    def finish(self):
        if self.call != len(self.trace) or not all(r['execution_verified'] for r in self.records):
            raise RuntimeError('Frozen replay request incomplete')
        return {'request': self.request, 'mode': self.mode, 'calibration_params': self.params,
                'records': self.records, 'scope': 'FROZEN_OFFICIAL_SCHEDULE_DIAGNOSTIC; own current latent and true full anchors; no shadow truth observed'}


def build_replay_forward(original, replay, diagnostic=None):
    """Caller must hash-gate the original module and frozen trace provenance."""
    source = inspect.getsource(original)
    if replay.mode != 'official':
        source = inject_source(source)
        source = source.replace('    _w1_begin(self)\n', '    _replay_begin(self)\n')
    else:
        anchor = '    current_idx = self.cnt % 2'
        if source.count(anchor) != 1:
            raise RuntimeError('Unsupported replay call-entry anchor')
        source = source.replace(anchor, '    _replay_begin(self)\n'+anchor)
    anchor = 'if self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh: # skip this step'
    if source.count(anchor) != 1:
        raise RuntimeError('Unsupported replay decision anchor')
    source = source.replace(anchor,
        'if _replay_skip(self, self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh): # frozen schedule')
    anchor = '    # --- Final Layer & Unpatchify ---'
    if source.count(anchor) != 1:
        raise RuntimeError('Unsupported replay execution-verification anchor')
    source = source.replace(anchor, '    _replay_verify(self, skip_forward)\n'+anchor)
    if diagnostic is not None:
        anchor = '    # Increment Step Counter'
        if source.count(anchor) != 1:
            raise RuntimeError('Unsupported replay shadow anchor')
        source = source.replace(anchor, '''    _replay_shadow(self, skipped=skip_forward, branch=current_idx,
        probe=test_x, original_input=ori_x,
        predicted_hidden=x_B_T_H_W_D, predicted_velocity=x_B_C_Tt_Hp_Wp,
        block_kwargs=block_kwargs, embedding=t_embedding_B_T_D, adaln=adaln_lora_B_T_3D)

'''+anchor)
    def begin(net):
        if diagnostic is not None and diagnostic.request != replay.request:
            raise RuntimeError('Replay/shadow request identities differ')
        replay.begin_call(net)
        if diagnostic is not None:
            diagnostic.start_call()
    namespace = dict(original.__globals__)
    namespace.update(_replay_begin=begin, _replay_skip=replay.choose_skip,
                     _replay_verify=replay.verify_execution, _w1_predict=replay.predict,
                     _w1_observe=replay.observe)
    if diagnostic is not None:
        namespace['_replay_shadow'] = diagnostic.collect
    exec(compile(source, '<w1-frozen-official-schedule>', 'exec'), namespace)
    return namespace[original.__name__]
