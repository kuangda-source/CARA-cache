import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr.cara_fast_execution_r2 import Pool,RUN,check_complete_A
from wcomr.gpu_budget_pool_v2 import SCHEMA

ROOT=Path(__file__).resolve().parents[1]


def script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def complete_fixture():
    from test_cara_fast_freeze_r2 import FrozenSelectionTests
    card,state,_,_=FrozenSelectionTests().fixture()
    for row in state['rows']:
        row['result'].update(slot_id=row['slot']['id'],scope_sha256=card['scope_sha256'],T_request=450.)
    return card,state


class ExecutionTests(unittest.TestCase):
    def ledger(self,root,cap=226):
        path=root/'reports/gpu-budget-v2.json'
        path.parent.mkdir()
        jobs={}
        for index in range(2):
            key='old-uncertainty-'+str(index)
            jobs[key]=dict(job_id=key,status='RESERVED_OR_RUNNING',billed_limit_GPUh=8.25,
                gpu_uuid='GPU-OLD-UNCONFIRMED',kind='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD',
                confirmed_GPU_submission=False,actual_cost_unknown=True,
                launch_id='NOT_A_CONFIRMED_GPU_SUBMISSION',supervisor_pid=None,supervisor_start_ticks=None)
        value=dict(schema=SCHEMA,cap_gpu_hours=cap,origin_used_gpu_hours=175.8058597668662,
                   origin_gpu_jobs_launched=0,jobs=jobs,events=[])
        value.update(Pool.accounting(value))
        path.write_text(json.dumps(value))
        return Pool(root)

    def job(self,host='two_card'):
        return dict(job_id=RUN,run_id=RUN,phase='A',host=host,gpu_uuid='GPU-CPU-CONTROL',
                    forecast_GPUh=4.95,billed_limit_GPUh=5,launch_id='CPU-UNIT-ONLY')

    def gpu(self):
        return dict(uuid='GPU-CPU-CONTROL',name='NVIDIA RTX A6000',compute_cap='8.6',
                    pids=[],utilization_percent=0,memory_used_mib=24,unix=time.time())

    def test_current226_cap_fits_A32_and_preserves_original_liability(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            pool=self.ledger(root)
            before=pool.read()
            after=pool.reserve(self.job(),self.gpu())
            self.assertEqual(after['reserved_gpu_hours'],21.5)
            self.assertEqual(after['cap_gpu_hours'],226)
            self.assertGreaterEqual(after['available_gpu_hours'],0)
            self.assertEqual(after['jobs']['old-uncertainty-0'],before['jobs']['old-uncertainty-0'])
            with self.assertRaises(ValueError):
                pool.reserve(self.job('four_card'),dict(self.gpu(),name='NVIDIA RTX 6000 Ada',compute_cap='8.9'))
            settled=pool.settle(RUN,.01,'a'*64)
            self.assertEqual(settled['reserved_gpu_hours'],16.5)
            self.assertAlmostEqual(settled['used_gpu_hours'],before['used_gpu_hours']+.01)
            self.assertEqual(pool.settle(RUN,.01,'a'*64),settled)

    def test_insufficient_funds_busy_gpu_and_stale_probe_refuse_without_mutation(self):
        for cap,gpu in [(196,self.gpu()),(226,dict(self.gpu(),pids=[123])),
                        (226,dict(self.gpu(),utilization_percent=1)),
                        (226,dict(self.gpu(),unix=time.time()-61))]:
            with self.subTest(cap=cap,gpu=gpu),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                pool=self.ledger(root,cap)
                before=pool.path.read_bytes()
                with self.assertRaises(ValueError):
                    pool.reserve(self.job(),gpu)
                self.assertEqual(pool.path.read_bytes(),before)

    def test_whole_A32_denominator_and_clean_GPU_boundary(self):
        card,state=complete_fixture()
        self.assertEqual(len(check_complete_A(card,state)),64)
        for change in ('partial','CPU','dirty','gate'):
            bad=copy.deepcopy(state)
            if change=='partial':
                bad['rows'].pop()
            elif change=='CPU':
                bad['rows'][0]['result']['CPU_fixture']=True
            elif change=='gate':
                bad['diagnostic_gate']['actual_roles']=['NATIVE35','ALLD']
            else:
                next(r for r in bad['rows'] if r['slot']['eligible_clean_time'])['result']['in_timing_guided_copies']=1
            with self.subTest(change=change),self.assertRaises(ValueError):
                check_complete_A(card,bad)

    def test_thermal_trigger_is_durable_before_raise(self):
        worker=script('cara_fast_worker_r2')
        class Journal:
            value=None
            def write(self,key,value):
                self.value=(key,value)
        journal=Journal()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'telemetry.jsonl'
            sample=dict(thermal={'temperature.gpu':'90','fan.speed':'87',
                                 'clocks_event_reasons.active':'0x0'})
            with self.assertRaises(RuntimeError):
                worker.persist_sample(path,journal,sample)
            self.assertEqual(journal.value,('telemetry',sample))
            self.assertEqual(json.loads(path.read_text()),sample)

    def test_container_arguments_keep_context_visible_only_to_runner(self):
        guardian=script('cara_fast_host_guardian_r2')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            stage=project/'.sync/A32-fixture'
            storage=type('Storage',(),dict(output=project/'outputs'/RUN,
                journal=type('Journal',(),dict(path=project/'reports/A32-control.journal'))(),
                config=dict(image_path=str(project/'image.img'))))()
            command=guardian.container_arguments(project,stage,storage,'a'*64,'24,25',os.getuid(),os.getgid(),'GPU-CPU-CONTROL')
            self.assertEqual(command[command.index('--gpus')+1],'device=GPU-CPU-CONTROL')
            self.assertEqual(command[command.index('--memory')+1],'48g')
            self.assertEqual(command[command.index('--network')+1],'none')
            self.assertIn('CUDA_VISIBLE_DEVICES=',command)
            self.assertIn('NVIDIA_VISIBLE_DEVICES=GPU-CPU-CONTROL',command)
            self.assertIn('TORCHINDUCTOR_COMPILE_THREADS=1',command)
            self.assertIn(str(stage/'scripts/cara_fast_worker_r2.py'),command)
            for name in ('reports','outputs','.sync'):
                self.assertNotIn(str(project/name)+':'+str(project/name)+':rw',command)
            for path in (stage,storage.output,storage.journal.path,project/'.sync/gpu-locks'):
                self.assertIn(str(path)+':'+str(path)+':rw',command)
            bounded=guardian.container_arguments(project,stage,storage,'a'*64,'24,25',os.getuid(),os.getgid(),'GPU-CPU-CONTROL',40)
            self.assertEqual(bounded[bounded.index('--memory')+1],'40g')
            self.assertEqual(bounded[bounded.index('--memory-swap')+1],'40g')


class SupervisorTests(unittest.TestCase):
    def exercise(self,scenario):
        worker=script('cara_fast_worker_r2')
        from wcomr import cara_fast_execution_r2 as execution
        from wcomr import wc73_exclusive_r1 as exclusive
        from wcomr import history104_storage_r2 as storage_module
        card,collection=complete_fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            stage=project/'.sync/CPU-execution-fixture'
            output=project/'outputs'/RUN
            (stage/'scripts').mkdir(parents=True)
            output.mkdir(parents=True)
            quote=dict(host_quotes={'two_card':dict(phases={'A':dict(forecast_GPUh=4.95,stop_release_margin_seconds=180)})})
            quote_path=stage/execution.QUOTE
            quote_path.parent.mkdir(parents=True)
            quote_path.write_text(json.dumps(quote))
            (stage/'fixture-collection.json').write_text(json.dumps(collection))
            runner_source='''import json,os,time
from pathlib import Path
stage=Path(__file__).resolve().parents[1];project=stage.parents[1]
assert str(os.getppid())==os.environ['WC_SUPERVISOR_PID']
lock=Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()
assert lock==project/'.sync/gpu-locks/GPU-CPU-CONTROL.lock'
if __SCENARIO__=='runner_failure':raise SystemExit(7)
from wcomr.gpu_budget_pool_v2 import process_identity
ident={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};ident['uid']=os.getuid()
(stage/'pg-runner-context-ready.json').write_text(json.dumps(dict(identity=ident)))
while not (stage/'pg-runner-context-granted.json').exists():time.sleep(.02)
if __SCENARIO__=='thermal':time.sleep(60)
out=project/'outputs'/__RUN__
(out/'A-collection.json').write_text((stage/'fixture-collection.json').read_text())
'''.replace('__SCENARIO__',repr(scenario)).replace('__RUN__',repr(RUN))
            (stage/'scripts/run_cara_fast_r2.py').write_text(runner_source)
            class Journal:
                records={}
                def write(self,key,value):
                    self.records[key]=copy.deepcopy(value)
            class Storage:
                journal=Journal()
                def check(self):
                    return {}
                def persist(self,key,path,value,writer):
                    self.journal.write(key,value)
                    writer(path,value)
            storage=Storage()
            storage.output=output
            authority=dict(host='two_card',gpu_uuid='GPU-CPU-CONTROL',launch_id='CPU-SUPERVISOR-CONTROL')
            registration=dict(source_revision='CPU_FIXTURE_NOT_A_GPU_AUTHORIZATION')
            def observe(uuid):
                ready=stage/'pg-runner-context-ready.json'
                apps=[]
                if ready.exists():
                    ident=json.loads(ready.read_text())['identity']
                    if Path('/proc/'+str(ident['pid'])).exists():
                        apps=[dict(ident,gpu_uuid=uuid,memory_MiB=1)]
                return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,
                            mps_processes=[],observed_unix=time.time())
            args=type('Arguments',(),dict(project=project,stage=stage))()
            thermal={'temperature.gpu':'90' if scenario=='thermal' else '50',
                     'fan.speed':'80','clocks_event_reasons.active':'0x0'}
            patches=[patch.object(execution,'validate',return_value=(card,registration,authority)),
                     patch.object(storage_module,'storage_for',return_value=storage),
                     patch.object(exclusive,'observe',side_effect=observe),
                     patch.object(worker,'read_thermal',return_value=thermal)]
            with patches[0],patches[1],patches[2],patches[3]:
                if scenario=='complete':
                    worker.supervise(args)
                else:
                    with self.assertRaises((RuntimeError,ValueError)):
                        worker.supervise(args)
            bill=json.loads((output/'A-billing.json').read_text())
            release=json.loads((output/'A-release-pending-central.json').read_text())
            self.assertGreater(bill['actual_GPUh'],0)
            self.assertLess(bill['actual_GPUh'],5)
            self.assertFalse(release['cost_settled'])
            self.assertTrue(release['original_process_exited'])
            self.assertTrue(release['GPU_released'])
            self.assertEqual(release['technical_accepted'],scenario=='complete')
            self.assertEqual(storage.journal.records['billing'],bill)
            if scenario=='thermal':
                self.assertEqual(storage.journal.records['telemetry']['thermal']['temperature.gpu'],'90')
            # The real supervisor and its child both used this inherited lock FD.
            from wcomr.gpu_budget_pool_v2 import DeviceLease
            with DeviceLease(project,'GPU-CPU-CONTROL'):
                pass
            with patch.object(execution,'validate',return_value=(card,registration,authority)),\
                    patch.object(storage_module,'storage_for',return_value=storage):
                with self.assertRaises(ValueError):
                    worker.supervise(args)

    @unittest.skipUnless(Path('/proc/self').exists(),'Linux inherited-FD lifecycle control')
    def test_success_child_failure_and_thermal_keep_bills_and_no_replay(self):
        for scenario in ('complete','runner_failure','thermal'):
            with self.subTest(scenario=scenario):
                self.exercise(scenario)


if __name__=='__main__':
    unittest.main()
