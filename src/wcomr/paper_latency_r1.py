"""Opt-in continuous solver-loop-to-decode wall clock; no upstream file edits.

The original complete-request clock remains authoritative. This instrumentation
adds two CUDA synchronizations per generated request, not per step. CPU checks
establish boundaries and cleanup, never GPU latency or scientific acceptance.
"""
import ast
import contextlib
import copy
import hashlib
import inspect
import math
from pathlib import Path
import time
import types

SAMPLER_PATH = 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py'
SAMPLER_SHA = 'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'
PIPE_PATH = 'cosmos_predict2/_src/predict2/inference/video2world.py'
PIPE_SHA = '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95'
BOUNDARY = 'SOLVER_LOOP_START_THROUGH_MODEL_DECODE_COMPLETION_WALL_R1'
HOSTS = {'four_card': (8, 9), 'two_card': (8, 6)}


class TimingBoundaryError(ValueError):
    pass


def _require(ok, message):
    if not ok:
        raise TimingBoundaryError(message)


def _ast_function(source, name):
    found = [n for n in ast.walk(ast.parse(source))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    _require(len(found) == 1, 'Exactly one supported source function required: '+name)
    return found[0]


def _verified_function(bound, path, digest, name):
    _require(inspect.ismethod(bound), 'Bound production method required: '+name)
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == digest, 'Pinned source SHA differs: '+name)
    expected = _ast_function(raw, name)
    fn = inspect.unwrap(bound.__func__)
    source = inspect.getsource(fn)
    # Do not dedent multiline string literals: that changes the docstring AST
    # even for an untouched class method. A suite preserves the original bytes.
    if source[0].isspace(): source = 'if True:\n'+source
    actual = _ast_function(source, name)
    _require(ast.dump(actual) == ast.dump(expected), 'Live callable differs from pinned source: '+name)
    _require(not fn.__closure__, 'Unsupported closure-bound sampler/pipeline')
    return fn, expected


class BoundaryClock:
    def __init__(self, synchronize, now_ns=time.perf_counter_ns):
        self.sync, self.now = synchronize, now_ns
        self.state = 'NEW'
        self.start_ns = self.end_ns = None
        self.sync_calls = 0

    def _fail(self, message):
        self.state = 'INVALID'
        raise TimingBoundaryError(message)

    def begin(self):
        if self.state != 'NEW': self._fail('Duplicate or out-of-order solver loop')
        self.state = 'STARTING'
        try:
            self.sync(); self.sync_calls += 1
            self.start_ns = self.now()
            _require(type(self.start_ns) is int and self.start_ns >= 0, 'Invalid monotonic start')
        except BaseException:
            self.state = 'INVALID'; raise
        self.state = 'LOOP'

    def loop_done(self):
        if self.state != 'LOOP': self._fail('Unexpected solver loop completion')
        self.state = 'AFTER_LOOP'

    def decode(self, call, *args, **kwargs):
        if self.state != 'AFTER_LOOP': self._fail('Decode before complete loop or duplicate decode')
        self.state = 'DECODING'
        try:
            value = call(*args, **kwargs)
            self.sync(); self.sync_calls += 1
            self.end_ns = self.now()
            _require(type(self.end_ns) is int and self.end_ns > self.start_ns, 'Invalid monotonic end')
        except BaseException:
            self.state = 'INVALID'; raise
        self.state = 'DONE'
        return value

    def finish(self, result, expected_updates, deployment_eligible):
        status = result.get('status')
        steps, pairs = result.get('solver_steps'), result.get('guided_pairs')
        if status == 'TEXT_REJECTED':
            _require(self.state == 'NEW' and steps == pairs == 0, 'Refusal contains partial generation')
        elif status in ('COMPLETE', 'VIDEO_REJECTED'):
            _require(self.state == 'DONE' and steps == pairs == expected_updates, 'Incomplete timed request')
        else:
            self._fail('Failed/unknown request cannot yield an accepted latency')
        seconds = (self.end_ns-self.start_ns)/1e9 if self.state == 'DONE' else None
        if seconds is not None:
            core, full = result.get('core_seconds'), result.get('full_request_seconds')
            _require(all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in (core, full)),
                     'Original core and full clocks required')
            _require(0 < seconds <= core <= full, 'Nested timing boundaries differ')
        eligible = status == 'COMPLETE' and deployment_eligible
        return dict(boundary=BOUNDARY, state=self.state, start_monotonic_ns=self.start_ns,
                    end_monotonic_ns=self.end_ns, elapsed_seconds=seconds,
                    synchronization_calls=self.sync_calls, expected_updates=expected_updates,
                    request_status=status, deployment_latency_eligible=eligible,
                    diagnostic_only=not deployment_eligible,
                    budget_clock='full_request_seconds', replaces_original_clock=False)


def _compile_sampler(fn, node, clock):
    original = copy.deepcopy(node)
    node = copy.deepcopy(node)
    matches = [i for i, n in enumerate(node.body) if isinstance(n, ast.For)
               and ast.dump(n.iter) == ast.dump(ast.parse('enumerate(timesteps_iter)', mode='eval').body)]
    _require(len(matches) == 1, 'Unsupported solver loop structure')
    i = matches[0]
    for reserved in ('_cara_paper_begin_r1', '_cara_paper_done_r1'):
        _require(reserved not in fn.__globals__ and reserved not in ast.unparse(node), 'Timing hook name collision')
    node.body[i:i+1] = [ast.parse('_cara_paper_begin_r1()').body[0], node.body[i],
                        ast.parse('_cara_paper_done_r1()').body[0]]
    inverse = copy.deepcopy(node)
    inverse.body[i:i+3] = [inverse.body[i+1]]
    _require(ast.dump(inverse) == ast.dump(original), 'Instrumentation inverse changed sampler AST')
    module = ast.Module(body=[ast.ImportFrom(module='__future__',
        names=[ast.alias(name='annotations')], level=0), node], type_ignores=[])
    ns = dict(fn.__globals__, _cara_paper_begin_r1=clock.begin, _cara_paper_done_r1=clock.loop_done)
    exec(compile(ast.fix_missing_locations(module), '<CARA-paper-latency-r1>', 'exec'), ns)
    return ns[node.name]


@contextlib.contextmanager
def _patch(owner, name, value):
    own, old = name in vars(owner), getattr(owner, name)
    setattr(owner, name, value)
    try:
        yield
    finally:
        if own: setattr(owner, name, old)
        else: delattr(owner, name)


@contextlib.contextmanager
def measure(inference, *, runtime, host, expected_updates, cpu_validation=False, _clock_factory=None):
    """Patch only this request's instances; absent/changed sources fail closed.

    A CPU receipt explicitly declares CPU validation. No compute capability
    assertion is made from CPU execution; production must match the chosen GPU.
    """
    import torch
    _require(host in HOSTS, 'Unknown registered host')
    _require(type(expected_updates) is int and expected_updates > 0, 'Actual scheduler update count required')
    if cpu_validation:
        _require(not torch.cuda.is_initialized(), 'CPU validation cannot run with a CUDA context')
        sync = lambda: None
    else:
        _require(_clock_factory is None, 'Injected clock prohibited in production')
        _require(torch.cuda.is_initialized(), 'Production requires the admitted existing CUDA context')
        _require(tuple(torch.cuda.get_device_capability()) == HOSTS[host], 'Host/GPU capability mismatch')
        sync = torch.cuda.synchronize
    model, pipe = inference.pipe.model, inference.pipe
    _require('_cara_paper_timing_active_r1' not in vars(model), 'Nested/concurrent request timing prohibited')
    runtime = Path(runtime)
    fn, node = _verified_function(model.generate_samples_from_batch,
                                 runtime/SAMPLER_PATH, SAMPLER_SHA, 'generate_samples_from_batch')
    _verified_function(pipe.generate_vid2world, runtime/PIPE_PATH, PIPE_SHA, 'generate_vid2world')
    clock = _clock_factory(sync) if _clock_factory else BoundaryClock(sync)
    compiled = _compile_sampler(fn, node, clock)
    decode = model.decode
    def timed_decode(*args, **kwargs): return clock.decode(decode, *args, **kwargs)
    with contextlib.ExitStack() as stack:
        # A sentinel prevents reentrant timing on this model, without global patches.
        setattr(model, '_cara_paper_timing_active_r1', True)
        stack.callback(delattr, model, '_cara_paper_timing_active_r1')
        stack.enter_context(_patch(model, 'generate_samples_from_batch', types.MethodType(compiled, model)))
        stack.enter_context(_patch(model, 'decode', timed_decode))
        yield clock


def execute_with_timing(execute, inference, sample, *args, runtime, host, expected_updates,
                        cpu_validation=False, diagnostic=False, **kwargs):
    """Future method-card call site. Keep legacy request fields bit-for-bit intact."""
    from .policy_generator_r1.production_sampling import complete_request_seconds
    setup = time.perf_counter()
    with measure(inference, runtime=runtime, host=host, expected_updates=expected_updates,
                 cpu_validation=cpu_validation) as clock:
        setup_seconds = time.perf_counter()-setup
        result = execute(inference, sample, *args, runtime=runtime, **kwargs)
        if result.get('core_seconds'):
            full = complete_request_seconds(result)
            if 'full_request_seconds' in result:
                _require(result['full_request_seconds'] == full, 'Original full-request clock changed')
            else:
                result['full_request_seconds'] = full
        else:
            _require(result.get('status') == 'TEXT_REJECTED', 'Missing original generation clock')
            result.setdefault('full_request_seconds', None)
        # Observer/audit paths cannot accidentally advertise deployment speed.
        diagnostic = bool(diagnostic or kwargs.get('audit') or kwargs.get('enabled')
                          or result.get('audit') or result.get('scout_enabled')
                          or result.get('in_timing_guided_copies') or result.get('in_timing_hashes')
                          or result.get('research_checkpoints'))
        receipt = clock.finish(result, expected_updates, not diagnostic and not cpu_validation)
        receipt.update(host=host, supported_capability=list(HOSTS[host]), cpu_validation=cpu_validation,
                       sampler_sha256=SAMPLER_SHA, pipeline_sha256=PIPE_SHA,
                       sampler_inverse_AST_equal=True,
                       adapter_setup_seconds_excluded_from_request_included_in_job=setup_seconds,
                       real_GPU_timing=not cpu_validation)
        result['paper_timing'] = receipt
        result['paper_denoise_decode_seconds'] = receipt['elapsed_seconds']
        return result
