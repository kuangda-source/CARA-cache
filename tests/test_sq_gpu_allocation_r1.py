"""Synthetic modes/containers, actual Linux CPU processes and temporary locks."""
import copy
import importlib.util
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr.sq_gpu_allocation_r1 import SystemOperations, run_allocation

ROOT=Path(__file__).resolve().parents[1]
EVENTS=[]


class Clock:
    def __init__(self):self.offset=0
    def monotonic(self):return time.monotonic()+self.offset
    def time(self):return time.time()+self.offset


class Storage:
    def __init__(self,output):self.output=output;self.rows={}
    def check(self):return {}
    def persist(self,key,path,value,writer):
        self.rows[key]=copy.deepcopy(value);writer(path,value)


class Operations(SystemOperations):
    def __init__(self,case):
        self.case=case;self.child=None;self.mode_acquired=False;self.container_stops=0;self.clock=None
    def mode_guard(self,uuid,password,clock):
        self.clock=clock;owner=self
        class Guard:
            def acquire(self):
                clock.offset+=400 if owner.case=='deadline' else 2
                if owner.case=='admission':raise ValueError('CPU synthetic busy admission')
                owner.mode_acquired=True
                return dict(verified_snapshot=dict(CPU_SYNTHETIC=True))
            def restore(self):
                clock.offset+=3
                if owner.case=='restore':raise RuntimeError('CPU synthetic restoration unknown')
                return dict(restored=True,CPU_SYNTHETIC=True)
        return Guard()
    def spawn(self,command,log):
        if self.case=='spawn':raise OSError('CPU synthetic no exec')
        self.clock.offset+=400 if self.case=='startup_deadline' else 4
        self.child=super().spawn(command,log)
        EVENTS.append(dict(kind='CPU_CHILD',pid=self.child.pid,process=self.child))
        return self.child
    def wait(self,child,remaining):
        self.remaining=remaining
        if self.case=='timeout':raise subprocess.TimeoutExpired('CPU_STUB',remaining)
        if self.case=='interrupt':os.kill(os.getpid(),signal.SIGTERM)
        if self.case in ('unknown','foreign'):raise RuntimeError('CPU original observation control')
        return super().wait(child,remaining)
    def inspect_container(self,stage,registration_sha,uuid):
        if self.case=='unknown':raise RuntimeError('CPU Docker observation unknown')
        running=self.child is not None and self.child.poll() is None
        return dict(Id='CPU_SYNTHETIC_CONTAINER',State=dict(Status='running' if running else 'exited',
            Running=running,Pid=self.child.pid if running else 0,ExitCode=0 if running else self.child.returncode),
            Image='CPU_NO_GPU_IMAGE',Config=dict(Labels={'wcomr.manifest':'foreign' if self.case=='foreign' else registration_sha}),
            HostConfig=dict(DeviceRequests=[dict(DeviceIDs=[uuid])],ReadonlyRootfs=True,
                PidMode='host',NetworkMode='none',NanoCpus=2_000_000_000,Memory=8*2**30))
    def stop_container(self,stage):
        self.container_stops+=1
        self.stop_own_cli(self.child)


@unittest.skipUnless(Path('/proc/self').exists(),'Actual Linux process/lease controls required')
class AllocationTests(unittest.TestCase):
    def exercise(self,case='success',password='CPU_SYNTHETIC_NOT_A_CREDENTIAL'):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        project=Path(temp.name);stage=project/'.sync/CPU_ALLOCATION_ONLY';stage.mkdir(parents=True)
        output=project/'outputs/CPU_ONLY';output.mkdir(parents=True)
        atomic_json(stage/'registration.json',dict(source_revision='CPU_SYNTHETIC_NO_GPU'))
        authority=dict(direct_user_authorization=True,run_id='CPU_SYNTHETIC_NO_HUMAN_AUTHORITY',
            host='two_card',gpu_uuid='GPU-CPU-SYNTHETIC-ONLY',launch_id='CPU_ONLY',
            source_revision='CPU_SYNTHETIC_NO_GPU',scope_sha256='a'*64,whole_GPUh=.1)
        storage=Storage(output);ops=Operations(case);clock=Clock()
        code='import time; time.sleep(60)' if case in ('timeout','interrupt','unknown','foreign','startup_deadline') else 'raise SystemExit('+('7' if case=='child_failure' else '0')+')'
        command=lambda:[sys.executable,'-c',code]
        action=lambda:run_allocation(project,stage,authority,dict(source_revision=authority['source_revision']),
            storage,dict(guardian_release_margin_seconds=180),'Q1',command,password,ops=ops,clock=clock)
        return project,stage,storage,ops,action

    def test_admission_startup_and_restoration_are_in_one_bill(self):
        _,_,storage,ops,action=self.exercise();state=action();bill=storage.rows['billing']
        self.assertGreaterEqual(bill['wall_seconds'],9)
        self.assertEqual(bill['wall_seconds'],bill['ended_monotonic']-bill['started_monotonic'])
        self.assertEqual(bill['actual_GPUh'],bill['wall_seconds']/3600)
        self.assertEqual(bill['billing_clock_owner'],'HOST_GUARDIAN')
        self.assertTrue(bill['wall_interval_complete']);self.assertLess(ops.remaining,174)
        self.assertEqual(state['container_exit_code'],0)
        self.assertTrue(storage.rows['allocation_release']['allocation_release_accepted'])

    def test_missing_credential_cannot_admit_or_spawn_and_still_records_attempt(self):
        _,_,storage,ops,action=self.exercise(password=None)
        with self.assertRaisesRegex(ValueError,'Credential'):action()
        self.assertFalse(ops.mode_acquired);self.assertIsNone(ops.child)
        self.assertTrue(storage.rows['billing']['wall_interval_complete'])
        self.assertEqual(storage.rows['guardian']['container_terminal_witness']['kind'],'NO_CONTAINER_DISPATCH')

    def test_failed_admission_retains_complete_failed_attempt(self):
        _,_,storage,ops,action=self.exercise('admission')
        with self.assertRaisesRegex(ValueError,'busy admission'):action()
        self.assertIsNone(ops.child);self.assertTrue(storage.rows['billing']['wall_interval_complete'])
        self.assertGreaterEqual(storage.rows['billing']['wall_seconds'],5)

    def test_spawn_error_is_known_no_exec_with_original_bill(self):
        _,_,storage,ops,action=self.exercise('spawn')
        with self.assertRaises(OSError):action()
        self.assertIsNone(ops.child)
        self.assertEqual(storage.rows['guardian']['container_dispatch_state'],'SPAWN_FAILED_NO_EXEC')
        self.assertTrue(storage.rows['allocation_release']['allocation_release_accepted'])

    def test_child_failure_is_billed_without_scientific_acceptance(self):
        _,_,storage,_,action=self.exercise('child_failure');state=action()
        self.assertEqual(state['container_exit_code'],7)
        self.assertTrue(storage.rows['billing']['wall_interval_complete'])
        self.assertNotIn('scientific_accepted',storage.rows['allocation_release'])

    def test_timeout_stops_only_original_bound_CPU_child(self):
        for case,error in [('timeout',subprocess.TimeoutExpired),('interrupt',KeyboardInterrupt)]:
            with self.subTest(case=case):
                _,_,storage,ops,action=self.exercise(case)
                before=signal.getsignal(signal.SIGTERM)
                with self.assertRaises(error):action()
                self.assertEqual(ops.container_stops,1);self.assertIsNotNone(ops.child.poll())
                self.assertTrue(storage.rows['billing']['wall_interval_complete'])
                self.assertEqual(signal.getsignal(signal.SIGTERM),before)

    def test_unknown_or_foreign_container_cannot_be_stopped_or_settled(self):
        for case in ('unknown','foreign'):
            with self.subTest(case=case):
                _,_,storage,ops,action=self.exercise(case)
                with self.assertRaises(RuntimeError):action()
                self.assertEqual(ops.container_stops,0);self.assertIsNotNone(ops.child.poll())
                self.assertFalse(storage.rows['billing']['wall_interval_complete'])
                self.assertFalse(storage.rows['allocation_release']['allocation_release_accepted'])

    def test_restoration_failure_keeps_allocation_in_recovery(self):
        _,_,storage,_,action=self.exercise('restore')
        with self.assertRaisesRegex(ValueError,'closure unknown'):action()
        self.assertFalse(storage.rows['billing']['wall_interval_complete'])
        self.assertEqual(storage.rows['guardian']['status'],'SQ_Q1_ALLOCATION_RECOVERY_PENDING')

    def test_admission_consumes_the_same_deadline_and_cost_is_never_clamped(self):
        for case,error in [('deadline',ValueError),('startup_deadline',TimeoutError)]:
            with self.subTest(case=case):
                _,_,storage,ops,action=self.exercise(case)
                with self.assertRaisesRegex(error,'deadline reached'):action()
                if case=='deadline':self.assertIsNone(ops.child)
                else:
                    self.assertIsNotNone(ops.child.poll());self.assertEqual(ops.container_stops,1)
                self.assertGreater(storage.rows['billing']['actual_GPUh'],.1)

    def test_existing_original_guardian_cannot_restart(self):
        _,stage,storage,_,action=self.exercise();action();before=sha(storage.output/'Q1-billing.json')
        with self.assertRaisesRegex(ValueError,'recover only'):action()
        self.assertEqual(sha(storage.output/'Q1-billing.json'),before)


class PureBoundaryTests(unittest.TestCase):
    def test_missing_container_requires_exact_docker_missing_response(self):
        ops=SystemOperations();stage=Path('/CPU_ONLY_STUB')
        for error,missing in [('Error: No such object: CPU_ONLY_STUB-gpu',True),
                ('Error: No such container: CPU_ONLY_STUB-gpu',True),
                ('Error response from daemon: No such container: CPU_ONLY_STUB-gpu',True),
                ('Error response from daemon: No such container: FOREIGN-gpu',False),
                ('Cannot connect to Docker daemon',False)]:
            with patch('wcomr.sq_gpu_allocation_r1.subprocess.run',return_value=SimpleNamespace(returncode=1,stderr=error,stdout='')):
                if missing:self.assertIsNone(ops.inspect_container(stage,'x','CPU_GPU'))
                else:
                    with self.assertRaises(RuntimeError):ops.inspect_container(stage,'x','CPU_GPU')

    def test_old_incomplete_Q1_source_is_withdrawn_before_dispatch(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('CPU_Q1_GUARD',ROOT/'scripts/cara_sq_q1_control_r1.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with self.assertRaisesRegex(ValueError,'readiness withdrawn'):
            module.bound_controller('f3be7662175889c77e3719521fecb9c4d3be83af')


if __name__=='__main__':unittest.main()
