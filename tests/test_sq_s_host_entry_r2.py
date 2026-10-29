"""S container resources, once-only transport, journal and long-monitor limits."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_sq_s_execution_r2 import fixture,financial_fixture,script
from test_sq_gpu_allocation_r1 import Storage,Operations,Clock
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr import sq_s_execution_r2 as execution
from wcomr import sq_s_stage_r2 as staging
from wcomr.sq_s_spec_r2 import RUN,PROFILE


class HostEntryTests(unittest.TestCase):
    def test_container_uses_one_GPU_40GiB_no_swap_and_only_original_writable_mounts(self):
        guardian=script('cara_sq_s_guardian_r2')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=project/'.sync/S_CPU_ONLY';stage.mkdir(parents=True)
            output=project/'outputs'/RUN
            journal=SimpleNamespace(path=project/'reports/S.journal')
            image=str(project/'private/S.img');storage=SimpleNamespace(output=output,journal=journal,config=dict(image_path=image))
            command=guardian.container_arguments(project,stage,storage,'c'*64,'24,25',501,20,'GPU-S-CPU-ONLY')
            self.assertEqual(command[command.index('--memory')+1],'40g')
            self.assertEqual(command[command.index('--memory-swap')+1],'40g')
            self.assertEqual(command[command.index('--cpus')+1],'2')
            self.assertEqual(command[command.index('--cpuset-cpus')+1],'24,25')
            self.assertEqual(command[command.index('--gpus')+1],'device=GPU-S-CPU-ONLY')
            self.assertIn('fsize=2147483648:2147483648',command)
            self.assertIn(str(stage/'scripts/cara_sq_s_worker_r2.py'),command)
            mounts=[command[i+1] for i,arg in enumerate(command) if arg=='-v']
            writable={value.rsplit(':',1)[0] for value in mounts if value.endswith(':rw')}
            self.assertEqual(writable,{str(path)+':'+str(path) for path in
                (stage,output,journal.path,project/'.sync/gpu-locks')})
            self.assertIn(str(project)+':'+str(project)+':ro',mounts)
            self.assertIn(image+':'+image+':ro',mounts)

    def test_S_intent_is_consumed_once_without_touching_the_central_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,_,_=fixture(project)
            for name in ('pg-GPU-authorization.json','central-reservation.json','launch-binding.json'):(stage/name).unlink()
            with patch.object(execution,'assets_current',return_value=True):
                result=staging.prepare_intent(project,auth['host'],auth)
            original=(stage/'GPU-intent.json').read_bytes()
            self.assertEqual(result['intent']['run_id'],RUN)
            with self.assertRaisesRegex(ValueError,'recover only'):staging.prepare_intent(project,auth['host'],auth)
            self.assertEqual((stage/'GPU-intent.json').read_bytes(),original)
            self.assertFalse((project/'reports/gpu-budget-v2.json').exists())

    def test_ambiguous_child_publication_cannot_dispatch_again(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,reg,job=fixture(project)
            envelope=execution.read(stage/'central-reservation.json')
            for name in ('central-reservation.json','launch-binding.json'):(stage/name).unlink()
            staging.create(stage/'GPU-intent.json',dict(launch_id=auth['launch_id']))
            digest=sha(stage/'GPU-intent.json')
            child=SimpleNamespace(stdin=io.BytesIO(),pid=999999,poll=lambda:7)
            with patch.object(staging,'validate',return_value=({},reg,auth)),\
                    patch.object(staging.subprocess,'Popen',return_value=child) as spawn,\
                    patch.object(staging,'process_identity',return_value=dict(pid=999999,start_ticks=None)):
                result=staging.dispatch(project,auth['host'],envelope,digest,'CPU_NON_SECRET')
                self.assertIn('RECOVER_ONLY',result['status']);self.assertEqual(spawn.call_count,1)
                with self.assertRaisesRegex(ValueError,'recover only'):
                    staging.dispatch(project,auth['host'],envelope,digest,'CPU_NON_SECRET')
                self.assertEqual(spawn.call_count,1)

    def test_pending_release_retains_host_bill_and_rejects_foreign_inner_diagnostics(self):
        guardian=script('cara_sq_s_guardian_r2')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,_,_=fixture(project);output=project/'outputs'/RUN;output.mkdir(parents=True)
            billing,release,state=financial_fixture(auth)
            for key in ('GPU_released','original_process_exited','technical_accepted'):release.pop(key)
            atomic_json(output/'S-billing.json',billing);atomic_json(output/'S-allocation-release.json',release)
            inner=dict(auth,diagnostic_only=True,run_id='FOREIGN',technical_accepted=True,
                GPU_released=True,original_process_exited=True)
            atomic_json(output/'S-supervisor-release-diagnostic.json',inner)
            before=sha(output/'S-billing.json');guardian.pending_release(stage,Storage(output))
            pending=execution.read(output/'S-release-pending-central.json')
            self.assertTrue(pending['GPU_released']);self.assertFalse(pending['technical_accepted'])
            self.assertEqual(before,sha(output/'S-billing.json'))

    def test_monitor_byte_boundary_retains_trigger_in_journal_without_truncating_history(self):
        worker=script('cara_sq_s_worker_r2');records=[]
        journal=SimpleNamespace(write=lambda key,value:records.append((key,copy.deepcopy(value))))
        sample=dict(thermal={'temperature.gpu':'42'},original='first')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'monitor.jsonl';worker.persist_sample(path,journal,sample,4096)
            before=path.read_bytes();sample['original']='trigger'
            with self.assertRaisesRegex(OSError,'triggering journal retained'):
                worker.persist_sample(path,journal,sample,len(before))
            self.assertEqual(path.read_bytes(),before);self.assertEqual(records[-1][1]['original'],'trigger')

    def test_monitor_thermal_stop_records_triggering_sample(self):
        worker=script('cara_sq_s_worker_r2');records=[]
        journal=SimpleNamespace(write=lambda key,value:records.append(value))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'monitor.jsonl';sample=dict(thermal={'temperature.gpu':'90'})
            with self.assertRaisesRegex(RuntimeError,'Thermal stop'):worker.persist_sample(path,journal,sample,4096)
            self.assertEqual(json.loads(path.read_text()),sample);self.assertEqual(records,[sample])

    def test_invalid_temperature_also_stops_after_durable_trigger(self):
        worker=script('cara_sq_s_worker_r2');records=[]
        journal=SimpleNamespace(write=lambda key,value:records.append(value))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'monitor.jsonl';sample=dict(thermal={'temperature.gpu':'nan'})
            with self.assertRaisesRegex(RuntimeError,'Invalid S temperature'):worker.persist_sample(path,journal,sample,4096)
            self.assertEqual(json.loads(path.read_text()),sample);self.assertEqual(records,[sample])


@unittest.skipUnless(Path('/proc/self').exists(),'Actual Linux S allocation child/lease acceptance required')
class LinuxAllocationTests(unittest.TestCase):
    def test_S_wrapper_retains_original_bill_on_pre_worker_failures_and_UNKNOWN(self):
        guardian=script('cara_sq_s_guardian_r2')
        from wcomr import sq_control_storage_r1 as storage_module
        for case in ('credential','admission','RAM','spawn','child_failure','timeout','unknown','restore'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,auth,_,_=fixture(project)
                output=project/'outputs'/RUN;output.mkdir(parents=True);storage=Storage(output)
                ops=Operations(case);clock=Clock()
                code='import time;time.sleep(60)' if case in ('timeout','unknown') else 'raise SystemExit(7)'
                with patch.object(execution,'assets_current',return_value=True),\
                        patch.object(storage_module,'storage_for',return_value=storage),\
                        patch.object(guardian.os,'sched_getaffinity',return_value={24,25}),\
                        patch.object(guardian,'available_memory_bytes',return_value=0 if case=='RAM' else 64*2**30),\
                        patch.object(guardian,'container_arguments',return_value=[sys.executable,'-c',code]):
                    if case=='child_failure':guardian.run(SimpleNamespace(project=project,stage=stage),'CPU_NON_SECRET',ops=ops,clock=clock)
                    else:
                        with self.assertRaises((ValueError,RuntimeError,OSError,subprocess.TimeoutExpired)):
                            guardian.run(SimpleNamespace(project=project,stage=stage),
                                None if case=='credential' else 'CPU_NON_SECRET',ops=ops,clock=clock)
                if ops.child is not None:self.assertIsNotNone(ops.child.poll())
                bill=execution.read(output/'S-billing.json')
                self.assertEqual(bill['billing_clock_owner'],'HOST_GUARDIAN')
                self.assertGreaterEqual(bill['wall_seconds'],3)
                pending=execution.read(output/'S-release-pending-central.json')
                self.assertEqual(pending['allocation_release_accepted'],case not in ('unknown','restore'))
                self.assertFalse(pending['technical_accepted'])


if __name__=='__main__':unittest.main()
