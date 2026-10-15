"""Profiler lifetime, failure propagation, scalar output, and device accounting."""
import gc
import types
import unittest
import weakref

from wcomr.deployment_profile_r1 import RequestProfile


class FakeEvent:
    def __init__(self, cuda):
        self.cuda = cuda
        self.at = None

    def record(self, stream):
        assert stream == 'STREAM'
        self.at = self.cuda.tick

    def elapsed_time(self, end):
        assert self.cuda.synced and self.at is not None and end.at is not None
        return end.at - self.at


class DeclaredFakeCUDA:
    def __init__(self):
        self.allocated = 100
        self.peak = 9000  # Earlier request's accumulated peak must be reset.
        self.tick = 0
        self.resets = self.syncs = 0
        self.synced = False

    def is_initialized(self): return True
    def synchronize(self, device):
        assert str(device) == 'cuda:0'
        self.syncs += 1
        self.synced = True
    def reset_peak_memory_stats(self, device):
        self.resets += 1
        self.peak = self.allocated
    def memory_allocated(self, device): return self.allocated
    def memory_reserved(self, device): return self.allocated + 20
    def max_memory_allocated(self, device): return self.peak
    def max_memory_reserved(self, device): return self.peak + 20
    def current_stream(self, device): return 'STREAM'
    def Event(self, enable_timing):
        assert enable_timing
        self.synced = False
        return FakeEvent(self)


class ProfilerControls(unittest.TestCase):
    def test_exact_return_and_restore(self):
        class Owner:
            def call(self, value): return value
        owner = Owner()
        original = owner.call
        value = object()
        with RequestProfile() as profile:
            profile.bind(owner, 'call', 'identity')
            self.assertIs(owner.call(value), value)
        self.assertNotIn('call', vars(owner))
        self.assertEqual(owner.call, original)
        self.assertEqual(profile.summary['components']['identity']['calls'], 1)
        self.assertIsNone(profile.summary['memory_after']['allocated_bytes'])
        self.assertFalse(profile.summary['peak_reset_before_request'])

    def test_exception_and_nested_intervals(self):
        class Owner:
            def call(self): raise RuntimeError('original')
        owner = Owner()
        with self.assertRaisesRegex(RuntimeError, 'original'):
            with RequestProfile() as profile:
                profile.bind(owner, 'call', 'inner')
                with profile.span('outer'):
                    owner.call()
        self.assertNotIn('call', vars(owner))
        self.assertEqual(profile.summary['status'], 'REQUEST_FAILED_PROFILE_RETAINED')
        rows = profile.summary['intervals']
        self.assertEqual(rows[1]['parent'], rows[0]['id'])
        self.assertEqual([r['outcome'] for r in rows], ['RuntimeError', 'RuntimeError'])

    def test_static_namespace_and_dynamic_weak_requirement(self):
        owner = types.SimpleNamespace(call=lambda x: x + 1)
        original = owner.call
        with RequestProfile() as profile:
            profile.bind(owner, 'call', 'static_namespace')
            self.assertEqual(owner.call(3), 4)
            with self.assertRaises(ValueError):
                profile.bind(owner, 'call', 'invalid_dynamic', require_weak=True)
        self.assertIs(owner.call, original)

    def test_static_namespace_bound_method(self):
        owner = types.SimpleNamespace()
        def decode(bound, value):
            self.assertIs(bound, owner)
            return value
        owner.decode = types.MethodType(decode, owner)
        original = owner.decode
        value = object()
        with RequestProfile() as profile:
            profile.bind(owner, 'decode', 'static_bound_method')
            self.assertIs(owner.decode(value), value)
            with self.assertRaises(ValueError):
                profile.bind(owner, 'decode', 'invalid_dynamic', require_weak=True)
        self.assertIs(owner.decode, original)

    def test_does_not_keep_ephemeral_owner_alive(self):
        class Owner:
            def call(self): return 1
        with RequestProfile() as profile:
            owner = Owner()
            reference = weakref.ref(owner)
            profile.bind(owner, 'call', 'ephemeral')
            self.assertEqual(owner.call(), 1)
            del owner
            gc.collect()
            self.assertIsNone(reference())
        self.assertFalse(profile._patches)

    def test_per_request_peak_and_deferred_events(self):
        cuda = DeclaredFakeCUDA()
        summaries = []
        for peak in (170, 130):
            with RequestProfile(device='cuda:0', cuda=cuda) as profile:
                self.assertEqual(profile.memory_before['peak_allocated_bytes'], 100)
                with profile.span('outer'):
                    cuda.peak = peak
                    cuda.tick += 3
                    with profile.span('inner'):
                        cuda.tick += 2
                self.assertEqual(cuda.syncs, 1 + 2 * len(summaries))
            summaries.append(profile.summary)
        self.assertEqual(cuda.resets, 2)
        self.assertEqual(cuda.syncs, 4)
        self.assertEqual([p['memory_after']['peak_allocated_bytes'] for p in summaries], [170, 130])
        self.assertEqual(summaries[0]['components']['outer']['inclusive_CUDA_ms'], 5)
        self.assertEqual(summaries[0]['components']['inner']['inclusive_CUDA_ms'], 2)

    def test_single_use_and_explicit_device(self):
        with self.assertRaises(ValueError): RequestProfile(device='cuda')
        profile = RequestProfile()
        with profile: pass
        with self.assertRaises(ValueError):
            with profile: pass
        with self.assertRaises(ValueError):
            with profile.span('late'): pass


if __name__ == '__main__':
    unittest.main()
