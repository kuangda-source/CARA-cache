"""Optional request profiling, kept separate from clean latency measurements.

No tensor arguments or outputs are saved. CUDA events are read only after the
request's final synchronization; nested component intervals are inclusive and
must not be added to infer total latency. This module submits no GPU work.
"""
from contextlib import contextmanager
from functools import wraps
import inspect
import time
import weakref

import torch

from . import clean_speed20_r1 as clean
from . import paper_baseline_grid_r1 as grid
from . import simple26d_memory_r2 as memory


class RequestProfile:
    def __init__(self, *, device=None, cuda=None, clock=time.perf_counter):
        self.device = torch.device(device or 'cpu')
        if self.device.type not in ('cpu', 'cuda'):
            raise ValueError('Explicit CPU control or resident CUDA device required')
        if self.device.type == 'cuda' and self.device.index is None:
            raise ValueError('Bind profiling to an explicit visible CUDA device index')
        self.cuda = torch.cuda if cuda is None else cuda
        self.clock = clock
        self.rows, self._stack, self._patches = [], [], []
        self._started = self._finished = False
        self.memory_before = self.memory_after = None
        self.summary = None

    @property
    def CUDA(self):
        return self.device.type == 'cuda'

    def _memory(self):
        if not self.CUDA:
            return dict(available=False, allocated_bytes=None, reserved_bytes=None,
                        peak_allocated_bytes=None, peak_reserved_bytes=None)
        return dict(available=True,
            allocated_bytes=self.cuda.memory_allocated(self.device),
            reserved_bytes=self.cuda.memory_reserved(self.device),
            peak_allocated_bytes=self.cuda.max_memory_allocated(self.device),
            peak_reserved_bytes=self.cuda.max_memory_reserved(self.device))

    def __enter__(self):
        if self._started:
            raise ValueError('A profiler belongs to exactly one complete request')
        if self.CUDA:
            if not self.cuda.is_initialized():
                raise ValueError('Load the resident model before starting the request profile')
            self.cuda.synchronize(self.device)
            self.cuda.reset_peak_memory_stats(self.device)
        self.memory_before = self._memory()
        self._started = True
        self.started = self.clock()
        return self

    @contextmanager
    def span(self, component):
        if not self._started or self._finished or not isinstance(component, str) or not component:
            raise ValueError('Named span inside one active request required')
        row = dict(id=len(self.rows), parent=self._stack[-1] if self._stack else None,
                   component=component, CPU_start=self.clock(), outcome='RUNNING')
        events = None
        if self.CUDA:
            events = (self.cuda.Event(enable_timing=True), self.cuda.Event(enable_timing=True))
            events[0].record(self.cuda.current_stream(self.device))
        self.rows.append((row, events))
        self._stack.append(row['id'])
        try:
            yield
        except BaseException as error:
            row['outcome'] = type(error).__name__
            raise
        else:
            row['outcome'] = 'RETURNED'
        finally:
            if events:
                events[1].record(self.cuda.current_stream(self.device))
            row['CPU_seconds'] = self.clock() - row.pop('CPU_start')
            assert self._stack.pop() == row['id']

    def bind(self, owner, name, component, *, require_weak=False):
        """Weak restoration entries do not keep short-lived algorithm owners alive."""
        original = getattr(owner, name)
        if not callable(original):
            return False
        owned = name in vars(owner)
        previous = weakref.WeakMethod(original) if inspect.ismethod(original) else weakref.ref(original)
        try:
            owner_ref = weakref.ref(owner)
        except TypeError:
            if require_weak:
                raise ValueError('Dynamic algorithm components require weak restoration entries')
            # Static fixture namespaces/pipe boundaries live for the whole request.
            owner_ref = lambda: owner

        @wraps(original)
        def measured(*args, **kwargs):
            with self.span(component):
                return original(*args, **kwargs)

        setattr(owner, name, measured)
        self._patches.append((owner_ref, name, owned, previous, weakref.ref(measured)))
        return True

    def _restore(self):
        for owner_ref, name, owned, previous, measured in reversed(self._patches):
            owner = owner_ref()
            if owner is None or getattr(owner, name, None) is not measured():
                continue
            if owned:
                original = previous()
                if original is None:
                    raise ValueError('Live profiled callable lost its original identity')
                setattr(owner, name, original)
            else:
                delattr(owner, name)
        self._patches.clear()

    def __exit__(self, kind, error, traceback):
        try:
            self._restore()
        finally:
            if self.CUDA:
                self.cuda.synchronize(self.device)
            self.memory_after = self._memory()
            self._finished = True
        assert not self._stack
        components = {}
        plain = []
        for row, events in self.rows:
            item = {**row, 'CUDA_elapsed_ms': events[0].elapsed_time(events[1]) if events else None}
            plain.append(item)
            group = components.setdefault(item['component'], dict(calls=0, inclusive_CPU_seconds=0.,
                inclusive_CUDA_ms=0. if self.CUDA else None, exceptions=0))
            group['calls'] += 1
            group['inclusive_CPU_seconds'] += item['CPU_seconds']
            if events:
                group['inclusive_CUDA_ms'] += item['CUDA_elapsed_ms']
            group['exceptions'] += item['outcome'] != 'RETURNED'
        self.rows.clear()  # Release CUDA event handles, retain only plain scalar metadata.
        self.summary = dict(status='PROFILE_COMPLETE' if kind is None else 'REQUEST_FAILED_PROFILE_RETAINED',
            device=str(self.device), request_profile_wall_seconds=self.clock() - self.started,
            memory_before=self.memory_before, memory_after=self.memory_after,
            peak_reset_before_request=self.CUDA, components=components, intervals=plain,
            interval_semantics='INCLUSIVE_CURRENT_STREAM_INTERVALS_NOT_ADDITIVE_PURE_KERNEL_COSTS',
            multi_stream_work_not_attributed=True, no_inner_profiler_synchronize=True,
            scalar_records_only=True, timing_claim='INSTRUMENTED_PROFILE_NOT_CLEAN_LATENCY',
            no_direct_post_probe_action_price_claim=True)
        return False


@contextmanager
def profile_execution(inference, *, inference_module, probe_depth, device=None):
    """Observe existing components without replacing execution or action selection.

The dynamic install observer runs after accepted compilers construct their
readouts. Callable identity guards and physical C/A/P/D decisions stay intact.
The input-preparation span includes its original conditioning operations; it
is not reported as isolated text-encoder cost. P remains a legal existing action.
"""
    model = inference.pipe.model
    net = model.net
    if type(probe_depth) is not int or not 0 < probe_depth < len(net.blocks):
        raise ValueError('Use the existing explicit probe boundary, without retuning it')
    with RequestProfile(device=device) as profile:
        for index, block in enumerate(net.blocks):
            label = 'shallow_block' if index < probe_depth else 'deep_block'
            profile.bind(block, 'forward', label)
        profile.bind(net.final_layer, 'forward', 'output_head')
        profile.bind(model.sample_scheduler, 'step', 'solver_update')
        profile.bind(model, 'decode', 'VAE_decode')
        profile.bind(inference.pipe, '_get_data_batch_input', 'input_preparation_inclusive')
        profile.bind(inference_module, 'save_img_or_video', 'video_write')
        profile.bind(memory, 'collect_boundary', 'request_boundary_GC')
        profile.bind(grid, 'collect_boundary', 'request_boundary_GC')
        original_install = clean.install

        def observed_install(*args, **kwargs):
            with profile.span('method_install_inclusive'):
                values = original_install(*args, **kwargs)
            if int(net.probe_depth) != probe_depth:
                raise ValueError('Profile labels differ from the installed probe boundary')
            owner, executor, readout = values[1:]
            controller = getattr(owner, 'controller', None) or getattr(executor, 'controller', None)
            if controller is not None:
                for name in ('decide', 'commit', 'commit_protected_dense'):
                    if hasattr(controller, name):
                        profile.bind(controller, name, 'policy_' + name, require_weak=True)
            if readout is not None:
                for name in ('warp', 'to_velocity'):
                    if getattr(readout, name, None) is not None:
                        profile.bind(readout, name, 'correction_' + name, require_weak=True)
            return values

        # Restored before profiling ends; no new compiler/source rewriting.
        with clean.patched(clean, 'install', observed_install):
            with profile.span('complete_request_inclusive'):
                yield profile
