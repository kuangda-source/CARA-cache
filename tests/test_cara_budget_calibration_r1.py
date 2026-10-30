import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import numpy as np

from wcomr.cara_budget_calibration_r1 import Calibration
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_budget_search_journal_r1 import OriginalQueryUnknown
from wcomr.cara_fast_binding_r2 import load_card

ROOT=Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'run';self.calls=[];self.fault=None
        self.card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        self.config=SearchConfig(42,4,sa_iterations=1,hc_iterations=1,hc_neighbors=2)

    def execute(self,slot,policy,output):
        self.calls.append(slot['id'])
        if self.fault==slot['id']:raise OSError('Declared physical request failure')
        policy=policy or self.card['roles'][slot['role']].get('policy')
        offset=.1 if policy else 0.
        rgb=np.full((3,93,2,2),.5+offset,dtype=np.float32)
        if self.fault=='parity' and slot['id']=='native-ON-FIT0':rgb[0,0,0,0]=.1
        result=dict(status='COMPLETE',solver_steps=36,guided_pairs=36,CPU_fixture=True,T_DD=None,T_request=1.)
        if policy:result['semantic_history']=[dict(actual=a,fallback_reason=None) for a in policy['actions']]
        if self.fault=='fallback' and slot['role']=='SEARCH_CANDIDATE':result['semantic_history'][0]['fallback_reason']='injected'
        return result,rgb,'a'*64

    def entry(self,create=False,config=None):
        return Calibration(root=self.root,card=self.card,config=config or self.config,context_sha256='b'*64,
            RGB_shape=[3,93,2,2],execute=self.execute,cpu_validation=True,create=create)

    def test_complete_physical_scope_and_readonly_recovery(self):
        result=self.entry(True).run(allow_new=True)
        self.assertTrue(result['complete']);self.assertEqual(result['complete_physical_paths'],18)
        self.assertEqual(len(self.calls),18)
        recovered=self.entry().run()
        self.assertTrue(recovered['complete']);self.assertEqual(recovered['new_physical_calls'],0)
        self.assertEqual(len(self.calls),18);self.assertEqual(recovered['search']['journal']['new_callback_calls'],0)

    def test_full_proposed51_query_scope(self):
        config=SearchConfig(42,51,sa_iterations=30,hc_iterations=1)
        result=self.entry(True,config).run(allow_new=True)
        self.assertTrue(result['complete']);self.assertEqual(len(self.calls),112)
        self.assertEqual(result['search']['HC_iterations_completed'],1)

    def test_original_control_failure_no_retry(self):
        self.fault='allD-ON-FIT0'
        with self.assertRaises(OSError):self.entry(True).run(allow_new=True)
        before=list(self.calls)
        with self.assertRaises(OriginalQueryUnknown):self.entry().run(allow_new=True)
        self.assertEqual(self.calls,before)

    def test_output_parity_failure_stops_before_search(self):
        self.fault='parity'
        with self.assertRaises(ValueError):self.entry(True).run(allow_new=True)
        self.assertFalse((self.root/'queries').exists())

    def test_failed_second_FIT_and_policy_fallback_never_complete(self):
        for fault in ('query-000001-FIT1','fallback'):
            self.root=Path(self.temp.name)/fault;self.calls=[];self.fault=fault
            result=self.entry(True).run(allow_new=True)
            self.assertFalse(result['complete']);self.assertEqual(result['search']['completed_cohort_evaluations'],0)
            before=list(self.calls);recovered=self.entry().run(allow_new=True)
            self.assertFalse(recovered['complete']);self.assertEqual(self.calls,before)

    def test_partial_or_changed_binding_and_unbound_GPU_refused(self):
        with self.assertRaises(ValueError):self.entry(True,replace(self.config,max_evaluations=3))
        self.entry(True)
        with self.assertRaises(ValueError):self.entry(config=replace(self.config,seed=43))
        with self.assertRaises(ValueError):Calibration(root=self.root,card=self.card,config=self.config,
            context_sha256='b'*64,RGB_shape=[3,93,2,2],execute=self.execute,cpu_validation=False)

    def test_damaged_saved_RGB_and_unknown_query_return_do_not_repeat(self):
        self.entry(True).run(allow_new=True);before=list(self.calls)
        path=self.root/'query-000004-FIT1/endpoint/RGB.npy'
        raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        with self.assertRaises(ValueError):self.entry().run()
        self.assertEqual(self.calls,before)
        path.write_bytes(raw)
        (self.root/'queries/query-000004.return.json').unlink()
        result=self.entry().run(allow_new=True)
        self.assertFalse(result['complete']);self.assertEqual(result['search']['termination'],'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH')
        self.assertEqual(self.calls,before)


if __name__=='__main__':unittest.main()
