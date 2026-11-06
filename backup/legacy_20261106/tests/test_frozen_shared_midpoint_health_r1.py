"""Original local launch binding and synthetic health/transport controls only."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from wcomr import frozen_shared_health_r1 as H

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'scripts/capture_wc_paper_N07_midpoint_health_r1.py'
spec=importlib.util.spec_from_file_location('N07_midpoint_collector',path)
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)


def packet(expected):
    return dict(status='N07_MIDPOINT_READONLY_TECHNICAL_HEALTH',expected=expected,
        observed_unix=expected['health_not_before_unix']+1,
        original_processes={k:dict(v,match='ORIGINAL_PROCESS_LIVE') for k,v in expected['processes'].items()},
        supervisor=dict(child_exit_code=None),own_budget_job=dict(status='RESERVED_OR_RUNNING'),
        bounded_technical_logs={},identity_mismatches=[],read_errors=[],CPU_post_exit={},
        final_scientific_results_read=False,no_quality_or_method_latency_readout=True,
        GPU_submissions=0,ledger_written=False)


class MidpointHealthControls(unittest.TestCase):
    def test_real_original_process_binding_and_unchanged_two_times(self):
        expected=C.expected_binding(ROOT)
        self.assertEqual(expected['run_id'],H.RUN);self.assertEqual(expected['scope_counts']['total_paths'],180)
        self.assertEqual(expected['processes']['runner'],dict(pid=1115898,start_ticks=542330755))
        self.assertEqual(expected['health_not_before_unix'],1792157400.)
        self.assertEqual(expected['final_not_before_unix'],1792185964.2521062)
        ast.parse(H.remote_code(expected))

    def test_before_midpoint_and_after_final_never_SSH_or_create_attempt(self):
        expected=C.expected_binding(ROOT);called=[]
        def forbidden(*a,**k):called.append(True);raise AssertionError('No premature remote observation')
        for now in (expected['health_not_before_unix']-1,expected['final_not_before_unix']):
            with tempfile.TemporaryDirectory() as folder:
                output=Path(folder)/'health.json'
                with self.assertRaises(ValueError):C.collect(expected,output,now=now,execute=forbidden)
                self.assertFalse(output.exists());self.assertFalse(list(Path(folder).glob('*.attempt')))
        self.assertFalse(called)

    def test_one_observation_and_cached_receipt_never_duplicate_query(self):
        expected=C.expected_binding(ROOT);value=packet(expected);called=[]
        def execute(command,**kw):
            called.append(command);self.assertEqual(kw['timeout'],45)
            self.assertEqual(command[:2],['ssh','-o'])
            return SimpleNamespace(returncode=0,stdout=json.dumps(value).encode(),stderr=b'')
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'health.json'
            first,queried=C.collect(expected,output,now=expected['health_not_before_unix'],execute=execute)
            second,repeated=C.collect(expected,output,now=expected['health_not_before_unix']+2,execute=execute)
            self.assertTrue(queried);self.assertFalse(repeated);self.assertEqual(first,second);self.assertEqual(len(called),1)
            self.assertTrue(output.with_name(output.name+'.attempt').exists())

    def test_transport_timeout_is_unknown_not_task_terminal_and_fence_prevents_race(self):
        expected=C.expected_binding(ROOT);called=[]
        def timeout(command,**kw):called.append(True);raise subprocess.TimeoutExpired('SYNTHETIC_SSH_NO_REMOTE_TASK_RESTART',45)
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'health.json'
            value,_=C.collect(expected,output,now=expected['health_not_before_unix'],execute=timeout)
            self.assertFalse(value['original_task_terminal']);self.assertFalse(value['final_scientific_results_read'])
            self.assertIn('UNKNOWN',value['status']);C.collect(expected,output,execute=timeout);self.assertEqual(len(called),1)
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'health.json';output.with_name(output.name+'.attempt').write_text('SYNTHETIC_OWN_QUERY_IN_PROGRESS')
            with self.assertRaises(FileExistsError):C.collect(expected,output,now=expected['health_not_before_unix'],execute=timeout)
        self.assertEqual(len(called),1)

    def test_progress_counts_running_separately_and_never_returns_private_science_fields(self):
        secret='LPIPS_PRIVATE_SENTINEL_0.123456'
        data=dict(status='N07_SHARED180_RUNNING',LPIPS=secret,runs=[
            dict(section='WARMUP',status='COMPLETE',core_seconds=secret),
            dict(section='WARMUP',status='TEXT_REJECTED',quality=secret),
            dict(section='WARMUP',status='RUNNING',video_path=secret),
            dict(section='TIMED',status='TECH_FAILED',MSE=secret),
            dict(section='TIMED',status=secret)])
        value=H.technical_progress(data)
        self.assertEqual(value['observed_positions'],5);self.assertEqual(value['terminal_request_outcomes'],2)
        self.assertEqual(value['not_reached'],175);self.assertEqual(value['sections']['WARMUP']['running'],1)
        self.assertEqual(value['sections']['TIMED']['technical_failures'],1);self.assertNotIn(secret,json.dumps(value))
        self.assertEqual(H.error_labels('LPIPS_PRIVATE 0.12\nTraceback (most recent call last)\nRuntimeError: CUDA out of memory'),
            {'out of memory':1,'traceback (most recent call last)':1,'runtimeerror':1})

    def test_original_handle_missing_reused_and_post_failure_are_distinct(self):
        expected=dict(pid=1,start_ticks=7)
        self.assertEqual(H.process_match(dict(state=None),expected),'ORIGINAL_HANDLE_MISSING')
        self.assertEqual(H.process_match(dict(state='S',start_ticks=8),expected),'PID_REUSED_ORIGINAL_HANDLE_MISSING')
        self.assertEqual(H.process_match(dict(read_error='PermissionError'),expected),'UNKNOWN_READ_ERROR')
        value=packet(C.expected_binding(ROOT));self.assertEqual(H.classify(value),'ORIGINAL_GPU_JOB_ACTIVE')
        failed=copy.deepcopy(value);failed['technical_progress']=dict(generation_status_counts=dict(TECH_FAILED=1))
        self.assertEqual(H.classify(failed),'TECHNICAL_SIGNAL_NEEDS_DIAGNOSIS')
        for role in ('supervisor','runner'):value['original_processes'][role]['match']='ORIGINAL_HANDLE_MISSING'
        value['own_budget_job']['status']='SETTLED'
        self.assertEqual(H.classify(value),'ORIGINAL_GPU_STAGE_FINISHED_CPU_POST_ACTIVE')
        value['CPU_post_exit']=dict(exit_code=1)
        self.assertEqual(H.classify(value),'TECHNICAL_SIGNAL_NEEDS_DIAGNOSIS')


if __name__=='__main__':unittest.main()
