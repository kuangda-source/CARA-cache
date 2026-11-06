import unittest
from wcomr.paper_latency_r1 import BoundaryClock, TimingBoundaryError


class ClockTests(unittest.TestCase):
    def test_class_docstring_identity_without_dedent(self):
        import tempfile, pathlib, importlib.util, hashlib
        from wcomr.paper_latency_r1 import _verified_function
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'original.py'
            p.write_text('class Model:\n    def sample(self):\n        """Docstring\n        with indentation.\n        """\n        return 1\n')
            spec=importlib.util.spec_from_file_location('original_timing_fixture',p)
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            fn,node=_verified_function(m.Model().sample,p,hashlib.sha256(p.read_bytes()).hexdigest(),'sample')
            self.assertEqual(fn(m.Model()),1)

    def clock(self, times=(10, 40)):
        values=iter(times); calls=[]
        return BoundaryClock(lambda:calls.append('sync'),lambda:next(values)),calls

    def result(self, **kw):
        return dict(status='COMPLETE',solver_steps=36,guided_pairs=36,
                    core_seconds=1.,full_request_seconds=2.,**kw)

    def test_contiguous_interval_including_gap(self):
        c,calls=self.clock();c.begin();c.loop_done();value=object()
        self.assertIs(c.decode(lambda:value),value)
        r=c.finish(self.result(),36,True)
        self.assertEqual(r['elapsed_seconds'],30e-9);self.assertEqual(calls,['sync','sync'])
        self.assertTrue(r['deployment_latency_eligible'])

    def test_refusal_has_no_fabricated_zero(self):
        c,calls=self.clock();r=c.finish(dict(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0),36,True)
        self.assertIsNone(r['elapsed_seconds']);self.assertFalse(r['deployment_latency_eligible']);self.assertFalse(calls)

    def test_video_refusal_is_not_latency_cohort(self):
        c,_=self.clock();c.begin();c.loop_done();c.decode(lambda:None)
        r=self.result();r['status']='VIDEO_REJECTED'
        self.assertFalse(c.finish(r,36,True)['deployment_latency_eligible'])

    def test_diagnostic_is_never_deployment(self):
        c,_=self.clock();c.begin();c.loop_done();c.decode(lambda:None)
        self.assertFalse(c.finish(self.result(),36,False)['deployment_latency_eligible'])

    def test_bad_boundaries(self):
        cases=('decode_before_loop','duplicate_start','duplicate_decode','missing_decode','short_solver',
               'bad_clock','negative_start','wrong_status','missing_core','outside_core','partial_refusal')
        for case in cases:
            with self.subTest(case=case),self.assertRaises(TimingBoundaryError):
                c,_=self.clock((40,10) if case=='bad_clock' else (-1,40) if case=='negative_start' else (10,40))
                if case=='decode_before_loop':c.decode(lambda:None)
                c.begin()
                if case=='duplicate_start':c.begin()
                c.loop_done()
                if case!='missing_decode':c.decode(lambda:None)
                if case=='duplicate_decode':c.decode(lambda:None)
                r=self.result()
                if case=='short_solver':r['solver_steps']=35
                if case=='wrong_status':r['status']='FAILED'
                if case=='missing_core':r.pop('core_seconds')
                if case=='outside_core':r['core_seconds']=1e-10
                if case=='partial_refusal':r.update(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0)
                c.finish(r,36,True)

    def test_decode_and_sync_failures(self):
        for where in ('start_sync','decode','end_sync'):
            c,_=self.clock()
            def fail():raise OSError(where)
            with self.subTest(where=where),self.assertRaises(OSError):
                if where=='start_sync':c.sync=fail
                c.begin();c.loop_done()
                if where=='end_sync':c.sync=fail
                c.decode(fail if where=='decode' else lambda:None)
            self.assertEqual(c.state,'INVALID')
