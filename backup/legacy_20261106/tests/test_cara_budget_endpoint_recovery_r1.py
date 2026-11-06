"""Real flock/process crash and immutable synthetic full-RGB recovery controls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from wcomr import cara_budget_endpoint_recovery_r1 as recovery
from wcomr import cara_budget_search_journal_r1 as journal
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_budget_rgb_objective_r1 import file_sha, save_endpoint
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, profile_from

ROOT=Path(__file__).resolve().parents[1]


def fixture(directory, *, crash=False, partial=False):
    directory=Path(directory);card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    arguments=dict(schedule=card['schedule'],profile=profile_from(card['profile']),
        config=SearchConfig(42,1),fit_members=card['FIT'],context_sha256='1'*64)
    endpoint=directory/'endpoint';endpoint.mkdir()
    binding=dict(CPU_fixture_only=True,original_scope_sha256=card['scope_sha256'],context_sha256='1'*64,
        RGB_shape=[3,93,2,2],host='CPU_LOCAL_FIXTURE',timing_enabled=False,
        evaluator_source_sha256=file_sha(ROOT/'src/wcomr/cara_budget_endpoint_requests_r1.py'))
    journal.create_record(endpoint/'binding.json',binding)
    def callback(request):
        for index,member in enumerate(card['FIT']):
            for candidate in (False,True):
                if partial and candidate and index==1:continue
                path=endpoint/(f'query-000001-FIT{index}' if candidate else f'teacher-FIT{index}');path.mkdir()
                sample=next(row for row in card['inputs'] if row['name']==member)
                identity=dict(context_sha256='1'*64,original_scope_sha256=card['scope_sha256'],member=member,
                    frozen_input_sha256=digest(sample),generation_seed=0,requested_steps=35,actual_updates=36,
                    RGB_shape=[3,93,2,2],kind='CANDIDATE' if candidate else 'NATIVE',
                    query_sha256=request['request_sha256'] if candidate else None,
                    policy_fingerprint=request['policy']['fingerprint'] if candidate else None,CPU_fixture_only=True)
                journal.create_record(path/'intent.json',identity)
                journal.create_record(path/'result.json',dict(status='COMPLETE',identity=identity,
                    solver_steps=36,guided_pairs=36,actual_D=19 if candidate else 36,
                    policy_exact_without_fallback=candidate,RGB_captures=1,CPU_fixture_only=True,
                    actual_model_weights=False,T_DD=1,T_request=2))
                rgb=np.zeros((3,93,2,2),dtype=np.float32)
                if candidate:rgb[2,92,1,1]=1
                save_endpoint(path/'endpoint',identity,rgb)
        if crash:os._exit(17)
        raise KeyboardInterrupt('Declared completed callback before durable return')
    try:journal.run_search(directory/'journal',**arguments,evaluate=callback,create=True,allow_new_queries=True)
    except KeyboardInterrupt:pass
    return card,arguments,binding


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.card,self.arguments,self.binding=fixture(self.root)
        self.search_binding=journal.read_record(self.root/'journal/binding.json')

    def recover(self,**changes):
        return recovery.recover_complete_cpu_query(self.root/'journal',self.root/'endpoint',
            **dict(card=self.card,expected_binding=self.search_binding,
                   expected_endpoint_binding=self.binding,query_id=1,**changes))

    def no_return(self):
        self.assertFalse((self.root/'journal/query-000001.return.json').exists())

    def hashes(self):
        return {str(p.relative_to(self.root)):file_sha(p) for p in self.root.rglob('*') if p.is_file()}

    def test_complete_recovery_replay_and_idempotence(self):
        before=self.hashes();result=self.recover()
        self.assertTrue(result['new_return_written']);self.assertEqual(result['new_generation_calls'],0)
        self.assertEqual(result['response']['rows'][0]['RGB_MSE'],1/(3*93*2*2))
        after=self.hashes();self.assertEqual(set(after)-set(before),{'journal/query-000001.return.json'})
        self.assertTrue(all(after[k]==v for k,v in before.items()))
        second=self.recover();self.assertFalse(second['new_return_written']);self.assertEqual(after,self.hashes())
        def forbidden(request):raise AssertionError('Generation must not be called')
        replay=journal.run_search(self.root/'journal',**self.arguments,evaluate=forbidden)
        self.assertEqual(replay['completed_cohort_evaluations'],1)
        self.assertEqual(replay['journal']['new_callback_calls'],0)
        self.assertEqual(replay['journal']['reused_callback_returns'],1)

    def test_partial_cohort_no_score_or_return(self):
        (self.root/'endpoint/query-000001-FIT1/endpoint/complete.json').unlink()
        with patch.object(recovery,'full_rgb_mse') as mse,self.assertRaises(ValueError):self.recover()
        mse.assert_not_called();self.no_return()

    def test_corrupt_rgb_and_wrong_teacher_refused(self):
        p=self.root/'endpoint/teacher-FIT1/endpoint/RGB.npy';raw=p.read_bytes();p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        with self.assertRaises(ValueError):self.recover()
        p.write_bytes(raw)
        p=self.root/'endpoint/teacher-FIT1/result.json';d=json.loads(p.read_text());d['identity']['member']='CHECK';p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.recover()
        self.no_return()

    def test_context_source_or_actual_budget_changed(self):
        original=copy.deepcopy(self.binding);self.binding['CPU_fixture_only']=False
        with self.assertRaises(ValueError):self.recover()
        self.binding=original;self.search_binding['source_sha256']['controller']='0'*64
        with self.assertRaises(ValueError):self.recover()
        self.search_binding=journal.read_record(self.root/'journal/binding.json')
        p=self.root/'endpoint/query-000001-FIT0/result.json';d=json.loads(p.read_text());d['actual_D']=36;p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.recover()
        self.no_return()

    def test_active_original_lock_refused(self):
        with journal.QueryJournal(self.root/'journal',self.search_binding):
            with self.assertRaises(BlockingIOError):self.recover()
        self.no_return()

    def test_saved_error_and_torn_return_never_overwritten(self):
        request=journal.read_record(self.root/'journal/query-000001.intent.json')
        with journal.QueryJournal(self.root/'journal',self.search_binding) as owner:
            owner.persist_return(request,dict(kind='CALLBACK_ERROR',error={'type':'OSError','message':'original'}))
        before=self.hashes()
        with self.assertRaises(ValueError):self.recover()
        self.assertEqual(before,self.hashes())
        p=self.root/'journal/query-000001.return.json';p.write_bytes(b'{')
        with self.assertRaises(ValueError):self.recover()
        self.assertEqual(p.read_bytes(),b'{')

    def test_failed_return_write_preserves_unknown(self):
        with patch.object(journal,'create_record',side_effect=OSError('declared disk full')),self.assertRaises(OSError):self.recover()
        self.no_return()
        result=self.recover();self.assertEqual(result['new_generation_calls'],0)

    def test_real_process_exit_after_all_artifacts(self):
        child_root=self.root/'child';child_root.mkdir()
        program="from test_cara_budget_endpoint_recovery_r1 import fixture;import sys;fixture(sys.argv[1],crash=True)"
        result=subprocess.run([sys.executable,'-c',program,str(child_root)],cwd=ROOT,
            env=dict(os.environ,PYTHONPATH=os.pathsep.join([str(ROOT/'src'),str(ROOT/'tests')])),
            capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,17,result.stderr)
        result=recovery.recover_complete_cpu_query(child_root/'journal',child_root/'endpoint',card=self.card,
            expected_binding=journal.read_record(child_root/'journal/binding.json'),
            expected_endpoint_binding=journal.read_record(child_root/'endpoint/binding.json'),query_id=1)
        self.assertEqual(result['status'],'ORIGINAL_COMPLETE_CPU_CALLBACK_RECOVERED')
        self.assertEqual(result['new_generation_calls'],0)

    def test_symlink_and_missing_attempt_refused(self):
        link=self.root/'linked';link.symlink_to(self.root/'endpoint',target_is_directory=True)
        with self.assertRaises(ValueError):
            recovery.recover_complete_cpu_query(self.root/'journal',link,card=self.card,
                expected_binding=self.search_binding,expected_endpoint_binding=self.binding,query_id=1)
        (self.root/'endpoint/query-000001-FIT0/intent.json').unlink()
        with self.assertRaises(ValueError):self.recover()
        self.no_return()


if __name__=='__main__':unittest.main()
