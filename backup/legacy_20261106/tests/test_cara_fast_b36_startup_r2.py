"""Real CPU children plus simulated Docker/GPU I/O; no GPU or metric execution."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_fast_b36_execution_r1 as execution
from wcomr import history104_storage_r2 as storage_module
from wcomr import wc73_exclusive_r1 as exclusive
from wcomr.cara_fast_b36_capture_r1 import capture_terminal,file_sha
from wcomr.cara_fast_b36_terminal_r1 import settle_original,released_terminal,record
from wcomr.gpu_budget_pool_v2 import DeviceLease
from test_cara_fast_b36_execution_r1 import real_binding,script
from test_cara_fast_b36_post_r1 import fixture,write


class StartupTests(unittest.TestCase):
    def exercise(self,scenario):
        guardian=script('cara_fast_b36_host_guardian_r1')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,_,pool,stage,output,docker=fixture(project)
            authority=execution.read(stage/'pg-GPU-authorization.json')
            registration=execution.read(stage/'registration.json')
            _,bound=real_binding()
            launch=execution.read(stage/'GPU-launch.json')
            # Remove only this temporary metadata fixture's old runtime records.
            for name in ('pg-host-guardian.json','B-billing.json','B-supervisor-start.json','B-runner-intent.json',
                         'B-runner-start.json','pg-runner-context-ready.json','pg-runner-context-granted.json',
                         'B-terminal-capture.json','B-terminal-capture-intent.json'):
                (stage/name).unlink(missing_ok=True)
            for path in output.glob('B-*.json'):path.unlink()
            mode=['Default']
            changes=[]
            children=[]
            saved_popen=subprocess.Popen
            def launch_child(command,**kwargs):
                child=saved_popen(command,**kwargs)
                children.append(child)
                if scenario!='budget':return child
                class BudgetChild:
                    pid=child.pid
                    first=True
                    def poll(self):return child.poll()
                    def wait(self,timeout=None):
                        if self.first:
                            self.first=False
                            raise subprocess.TimeoutExpired(command,timeout)
                        return child.wait(timeout=timeout)
                return BudgetChild()
            def observe(uuid):
                return dict(gpu_uuid=uuid,compute_mode=mode[0],mps_processes=[],observed_unix=__import__('time').time(),
                    compute_apps=[dict(pid=987654,uid=os.getuid()+1)] if scenario=='busy' else [])
            def change(uuid,target,password):
                self.assertEqual(uuid,authority['gpu_uuid'])
                changes.append(target)
                mode[0]={'EXCLUSIVE_PROCESS':'Exclusive_Process','DEFAULT':'Default'}[target]
            def inspect(*args):
                if scenario=='unknown':raise RuntimeError('DECLARED_DOCKER_OBSERVATION_UNKNOWN')
                actual=copy.deepcopy(docker)
                running=bool(children and children[0].poll() is None)
                actual['State'].update(Running=running,Status='running' if running else 'exited',
                                      Pid=children[0].pid if running else 0)
                return actual
            def docker_stop(command,**kwargs):
                self.assertEqual(command,['docker','stop','--time','30',stage.name+'-gpu'])
                os.killpg(children[0].pid,15)
                children[0].wait(timeout=10)
                return subprocess.CompletedProcess(command,0)
            class Journal:
                records={}
                def write(self,key,value):self.records[key]=copy.deepcopy(value)
            class Storage:
                journal=Journal()
                def check(self):return {}
                def persist(self,key,path,value,writer):
                    self.journal.write(key,value);writer(path,value)
            storage=Storage()
            command=([str(stage/'NO_SUCH_EXECUTABLE')] if scenario=='spawn_failure' else
                [sys.executable,'-c','import time;time.sleep(60)' if scenario=='budget' else 'raise SystemExit(7)'])
            args=type('Arguments',(),dict(project=project,stage=stage))()
            with patch.object(execution,'validate',return_value=(card,registration,authority,bound)),\
                 patch.object(storage_module,'storage_for',return_value=storage),\
                 patch.object(exclusive,'observe',side_effect=observe),\
                 patch.object(guardian,'set_selected_mode',side_effect=change),\
                 patch.object(guardian,'inspect_original',side_effect=inspect),\
                 patch.object(guardian,'container_arguments',return_value=command),\
                 patch.object(guardian.os,'sched_getaffinity',return_value={24,25,27}),\
                 patch.object(guardian.subprocess,'Popen',side_effect=launch_child),\
                 patch.object(guardian.subprocess,'run',side_effect=docker_stop):
                if scenario in ('busy','spawn_failure','unknown','budget','missing_credential'):
                    with self.assertRaises((ValueError,OSError,RuntimeError,subprocess.TimeoutExpired)):
                        guardian.run(args,None if scenario=='missing_credential' else 'CPU_ONLY_DUMMY_SECRET')
                else:guardian.run(args,'CPU_ONLY_DUMMY_SECRET')
            bill=execution.read(stage/'B-billing.json')
            state=execution.read(stage/'pg-host-guardian.json')
            self.assertEqual(bill['billing_clock_owner'],'HOST_GUARDIAN')
            self.assertGreater(bill['wall_seconds'],0)
            self.assertEqual(bill['wall_seconds'],bill['ended_monotonic']-bill['started_monotonic'])
            self.assertEqual(bill['actual_GPUh'],bill['wall_seconds']/3600)
            self.assertEqual(storage.journal.records['billing'],bill)
            self.assertEqual(mode[0],'Default')
            if scenario in ('busy','missing_credential'):self.assertEqual(changes,[])
            else:self.assertEqual(changes,['EXCLUSIVE_PROCESS','DEFAULT'])
            self.assertTrue(all(child.poll() is not None for child in children))
            self.assertFalse((output/'B-billing.json').exists())
            launch['guardian_identity']=state['identity']
            write(stage/'GPU-launch.json',launch)
            before=pool.path.read_bytes()
            # Current PID liveness and GPU/engine I/O are simulated metadata boundaries.
            actual_sha=file_sha
            def controlled_sha(path):
                path=Path(path)
                if project/'runtime' in path.parents:return bound['A_runtime_source_sha256'][str(path.relative_to(project/'runtime'))]
                return actual_sha(path)
            inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
            with patch('wcomr.cara_fast_b36_capture_r1.same_live_process',return_value=False),\
                 patch('wcomr.cara_fast_b36_capture_r1.subprocess.run',return_value=inspected),\
                 patch('wcomr.cara_fast_b36_capture_r1.observe',side_effect=observe),\
                 patch('wcomr.cara_fast_b36_capture_r1.file_sha',side_effect=controlled_sha):
                captured=capture_terminal(project,stage,file_sha(stage/'GPU-launch.json'))
            if scenario=='unknown':
                self.assertFalse(bill['wall_interval_complete'])
                self.assertFalse(captured['scientific_rows_returned'])
                self.assertNotIn('files',captured)
                self.assertEqual(pool.path.read_bytes(),before)
            else:
                settled=settle_original(pool,captured,card)
                self.assertEqual(settled['central_after']['reserved_gpu_hours'],16.5)
                self.assertEqual(settled['central_after']['jobs'][execution.RUN]['actual_GPUh'],bill['actual_GPUh'])
                released=released_terminal(captured,card,settled)
                self.assertTrue(released['cost_settled'])
                self.assertFalse(released['technical_accepted'])
                self.assertFalse(captured['files']['runner_intent']['exists'])
                if scenario in ('busy','spawn_failure','missing_credential'):
                    self.assertIsNone(captured['container'])
                    self.assertTrue(released['GPU_released'])
                repeated=settle_original(pool,captured,card)
                self.assertEqual(repeated['central_before'],repeated['central_after'])
            with DeviceLease(project,authority['gpu_uuid']):pass
            with patch.object(execution,'validate',return_value=(card,registration,authority,bound)),\
                 patch.object(storage_module,'storage_for',return_value=storage),\
                 patch.object(guardian.os,'sched_getaffinity',return_value={24,25,27}),self.assertRaises(AssertionError):
                guardian.run(args,'CPU_ONLY_DUMMY_SECRET')

    @unittest.skipUnless(Path('/proc/self').exists(),'Linux guardian PID and real child controls')
    def test_pre_worker_failures_budget_stop_and_unknown_keep_one_measured_bill(self):
        for scenario in ('container_failure','busy','spawn_failure','budget','unknown','missing_credential'):
            with self.subTest(scenario=scenario):self.exercise(scenario)

    def test_engine_unknown_and_wrong_manifest_cannot_be_treated_as_absent_or_stopped(self):
        guardian=script('cara_fast_b36_host_guardian_r1')
        stage=Path('/CPU_ONLY/cara-fast-f19-b36-fixture')
        for message,allowed in [('Error: No such object: '+stage.name+'-gpu',True),('Cannot connect to Docker daemon',False)]:
            inspected=subprocess.CompletedProcess(['docker'],1,stdout='',stderr=message)
            with patch.object(guardian.subprocess,'run',return_value=inspected):
                if allowed:self.assertIsNone(guardian.inspect_original(stage,'a'*64,'GPU-CPU'))
                else:
                    with self.assertRaises(RuntimeError):guardian.inspect_original(stage,'a'*64,'GPU-CPU')
        wrong=dict(Config=dict(Labels={'wcomr.manifest':'WRONG'}),HostConfig=dict(DeviceRequests=[dict(DeviceIDs=['GPU-CPU'])]))
        inspected=subprocess.CompletedProcess(['docker'],0,stdout=json.dumps([wrong]))
        with patch.object(guardian.subprocess,'run',return_value=inspected) as observed,self.assertRaises(ValueError):
            guardian.inspect_original(stage,'a'*64,'GPU-CPU')
        self.assertEqual(observed.call_count,1)


if __name__=='__main__':
    unittest.main()
