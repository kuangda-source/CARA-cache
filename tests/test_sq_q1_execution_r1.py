"""CPU boundary controls. Synthetic CUDA headers are never GPU evidence."""
import copy
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json,sha,DeviceLease
from wcomr.sq_q1_execution_r1 import Pool,validate,check_collection
from wcomr.sq_q1_spec_r1 import (RUN,SCOPE,PROFILE,QUOTES,COUNTS,STATE_KEYS,LIMITS,
    CHECKPOINT_SHA,MANIFEST_SHA,EXECUTION_CRITICAL,RUNTIME_REQUIRED)
from wcomr.sq_q1_terminal_r1 import settle_original,analyse_released,technical_terminal

ROOT=Path(__file__).resolve().parents[1]


def script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def ledger(root,remaining=33.694140233133794):
    jobs={}
    for index in range(2):
        key='original-unknown-'+str(index)
        jobs[key]=dict(job_id=key,status='RESERVED_OR_RUNNING',billed_limit_GPUh=8.25,
            gpu_uuid='GPU-OLD-UNCONFIRMED',kind='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD',
            confirmed_GPU_submission=False,actual_cost_unknown=True,
            launch_id='NOT_A_CONFIRMED_GPU_SUBMISSION',supervisor_pid=None,supervisor_start_ticks=None)
    value=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=226-16.5-remaining,
        origin_gpu_jobs_launched=0,jobs=jobs,events=[])
    value.update(Pool.accounting(value));atomic_json(root/'reports/gpu-budget-v2.json',value)
    return Pool(root)


def gpu(host='two_card'):
    return dict(uuid='GPU-Q1-CPU-CONTROL',name='NVIDIA RTX A6000' if host=='two_card' else 'NVIDIA RTX 6000 Ada',
        compute_cap='8.6' if host=='two_card' else '8.9',pids=[],utilization_percent=0,memory_used_mib=24,unix=time.time())


def job(host='two_card'):
    return dict(job_id=RUN,run_id=RUN,scope_counts=COUNTS,host=host,gpu_uuid=gpu()['uuid'],
        forecast_GPUh=json.loads((ROOT/QUOTES[host]).read_text())['forecast_complete_GPUh'],
        billed_limit_GPUh=LIMITS[host],launch_id='CPU_CONTROL_NO_GPU_LAUNCH')


@functools.lru_cache(None)
def raw_fixture():
    from test_sq_q1_collection_r1 import fixture_cohort
    from wcomr.sq_q1_collection_r1 import collect_saved_q1
    kernel,schema,values=fixture_cohort()
    result=collect_saved_q1(kernel,[dict(prompt=p,step=t) for p,t in STATE_KEYS],
        lambda row:values[row['prompt'],row['step']],schema,device='cpu',
        max_copy_bytes=128*2**20,save_health=lambda value:None)
    # Headers exercise the independent terminal parser only. The fixture's
    # provenance is explicitly synthetic; no test changes CUDA availability.
    result.update(CPU_fixture=False,actual_CUDA=True,
        input_evidence=dict(checkpoint_sha256=CHECKPOINT_SHA,manifest_sha256=MANIFEST_SHA,
            original_B1_files_verified=32,condition_schema='ACTUAL_RUNTIME_MODULE'))
    return result


def authority_fixture(project,host='two_card',stage_name='Q1_SYNTHETIC_AUTHORITY_CONTROL_ONLY'):
    stage=project/'.sync'/stage_name
    paths=set(EXECUTION_CRITICAL)|{SCOPE,PROFILE,QUOTES[host]}
    for name in paths:
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((ROOT/name).read_bytes())
    (project/'runtime').symlink_to(ROOT/'cache/runtime',target_is_directory=True)
    registration=dict(namespace='SQ_Q1_EXECUTION_R1',host=host,stage=str(stage),
        source_revision='CPU_UNIT_INPUT_NOT_A_REAL_GPU_AUTHORIZATION',
        payload_sha256={name:sha(stage/name) for name in sorted(paths)},
        runtime_source_sha256={name:sha(project/'runtime'/name) for name in RUNTIME_REQUIRED})
    atomic_json(stage/'registration.json',registration)
    proof=dict(passed=True,GPU_submissions=0,
        critical_source_sha256={name:sha(stage/name) for name in EXECUTION_CRITICAL})
    atomic_json(stage/'execution-CPU-proof.json',proof)
    profile=json.loads((stage/PROFILE).read_text())
    atomic_json(stage/'history104-storage.json',dict(run_id=RUN,output_mount=str(project/'outputs'/RUN),
        image_path=profile['hosts'][host]['image_path'],journal_path=profile['hosts'][host]['journal_path'],image_bytes=2**30))
    authority=dict(direct_user_authorization=True,
        user_quote='SYNTHETIC UNIT INPUT ONLY, NOT A HUMAN GPU AUTHORIZATION',run_id=RUN,
        scope_counts=COUNTS,whole_GPUh=LIMITS[host],host=host,
        authorizes_retry=False,authorizes_S_collection=False,scope_sha256=sha(stage/SCOPE),
        source_revision=registration['source_revision'],registration_sha256=sha(stage/'registration.json'),
        CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),quote_sha256=sha(stage/QUOTES[host]),
        gpu_uuid=gpu(host)['uuid'],launch_id='CPU_CONTROL_NO_GPU_LAUNCH')
    authority['storage_contract_sha256']=sha(stage/'history104-storage.json')
    atomic_json(stage/'pg-GPU-authorization.json',authority)
    envelope_job=dict(job(host),**{key:authority[key] for key in (
        'scope_sha256','source_revision','registration_sha256')},
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'),status='RESERVED_OR_RUNNING')
    atomic_json(stage/'central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=envelope_job))
    atomic_json(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json')))
    return stage,authority,registration,envelope_job


def numeric_failure(result,completed=0,kind='ORIGINAL_C_AND_DENSE_HEAD'):
    value=copy.deepcopy(result);value['states']=value['states'][:completed]
    formal=16*completed+(2 if kind=='FORMAL_ORIGINAL_C' else 0)
    value.update(status='Q1_ORIGINAL_PARITY_NOT_ACCEPTED_NO_CODEC_SELECTION',
        complete_Q1_cohort=False,completed_states=completed,
        failure=dict(prompt=STATE_KEYS[completed][0],step=STATE_KEYS[completed][1],kind=kind),
        head_calls={k:dict(started=n,completed=n) for k,n in (
            ('warm',4),('controls',4+2*completed),('formal',formal))})
    return value


class ExecutionTests(unittest.TestCase):
    def test_both_host_prices_keep_one_envelope_and_unknown_reserve(self):
        for host in LIMITS:
            with self.subTest(host=host),tempfile.TemporaryDirectory() as directory:
                pool=ledger(Path(directory));before=pool.read()
                after=pool.reserve(job(host),gpu(host))
                self.assertEqual(after['reserved_gpu_hours'],16.5+LIMITS[host])
                self.assertEqual(after['jobs']['original-unknown-0'],before['jobs']['original-unknown-0'])
                with self.assertRaises(ValueError):pool.reserve(job(),gpu())

    def test_busy_stale_funds_wrong_scope_and_same_host_overlap_do_not_mutate(self):
        for case in ('busy','stale','funds','scope','overlap'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                pool=ledger(Path(directory),remaining=.1 if case=='funds' else 33.)
                selected=gpu();new_job=job()
                if case=='busy':selected['pids']=[999]
                if case=='stale':selected['unix']-=61
                if case=='scope':new_job['scope_counts']=dict(COUNTS,complete_head_calls=192)
                if case=='overlap':
                    value=pool.read();value['jobs']['other']=dict(job_id='other',host='two_card',kind='V2',
                        status='RESERVED_OR_RUNNING',billed_limit_GPUh=1,gpu_uuid='GPU-OTHER')
                    value.update(Pool.accounting(value));atomic_json(pool.path,value)
                before=pool.path.read_bytes()
                with self.assertRaises(ValueError):pool.reserve(new_job,selected)
                self.assertEqual(pool.path.read_bytes(),before)

    def test_authority_source_and_lifecycle_proof_are_bound_on_both_hosts(self):
        for host in LIMITS:
            with tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,authority,_,_=authority_fixture(project,host)
                self.assertEqual(validate(project,stage)[2],authority)
                proof=json.loads((stage/'execution-CPU-proof.json').read_text())
                proof['critical_source_sha256'].pop(EXECUTION_CRITICAL[0])
                atomic_json(stage/'execution-CPU-proof.json',proof)
                authority['CPU_proof_sha256']=sha(stage/'execution-CPU-proof.json')
                atomic_json(stage/'pg-GPU-authorization.json',authority)
                with self.assertRaisesRegex(ValueError,'Untested'):validate(project,stage)

    def test_no_authority_retry_S_scope_and_foreign_envelope_refuse(self):
        for case in ('authority','retry','S','bill','source'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,authority,_,envelope=authority_fixture(project)
                if case=='authority':authority['direct_user_authorization']=False
                if case=='retry':authority['authorizes_retry']=True
                if case=='S':authority['authorizes_S_collection']=True
                if case=='bill':envelope['billed_limit_GPUh']=2.
                if case=='source':(stage/EXECUTION_CRITICAL[0]).write_text('UNTESTED CHANGE')
                atomic_json(stage/'pg-GPU-authorization.json',authority)
                atomic_json(stage/'central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=envelope))
                with self.assertRaises(ValueError):validate(project,stage)

    def test_complete_and_all_original_gate_stops_have_exact_denominators(self):
        scope=json.loads((ROOT/SCOPE).read_text());full=copy.deepcopy(raw_fixture())
        self.assertTrue(check_collection(scope,full)['complete'])
        for count,kind in ((0,'ORIGINAL_C_AND_DENSE_HEAD'),(3,'STORED_DENSE_HIDDEN_HEAD'),(7,'FORMAL_ORIGINAL_C')):
            value=numeric_failure(full,count,kind)
            self.assertFalse(check_collection(scope,value)['selection_allowed_after_release'])
            value['head_calls']['formal']['completed']+=2
            value['head_calls']['formal']['started']+=2
            with self.assertRaises(ValueError):check_collection(scope,value)
        for case in ('CPU','selection','partial','deep'):
            value=copy.deepcopy(full)
            if case=='CPU':value['CPU_fixture']=True
            if case=='selection':value['selections']={}
            if case=='partial':value['states'].pop()
            if case=='deep':value['new_deep_pairs']=1
            with self.subTest(case=case),self.assertRaises(ValueError):check_collection(scope,value)

    def test_gpu_container_exposes_only_own_writes_and_registered_16GiB(self):
        guardian=script('cara_sq_q1_guardian_r1')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=project/'.sync/CPU_COMMAND_ONLY'
            storage=type('Storage',(),dict(output=project/'outputs'/RUN,
                journal=type('Journal',(),dict(path=project/'reports/Q1.journal'))(),
                config=dict(image_path=str(project/'image.img'))))()
            command=guardian.container_arguments(project,stage,storage,'a'*64,'24,25',1000,1000,gpu()['uuid'])
            self.assertEqual(command[command.index('--memory')+1],'16g')
            self.assertEqual(command[command.index('--memory-swap')+1],'16g')
            self.assertEqual(command[command.index('--gpus')+1],'device='+gpu()['uuid'])
            self.assertIn('CUDA_VISIBLE_DEVICES=',command)
            self.assertIn(str(stage/'scripts/cara_sq_q1_worker_r1.py'),command)
            for name in ('reports','outputs','.sync'):
                self.assertNotIn(str(project/name)+':'+str(project/name)+':rw',command)


class SupervisorTests(unittest.TestCase):
    @unittest.skipUnless(Path('/proc/self').exists(),'Requires real Linux PID/startticks/inherited FD')
    def test_original_success_numeric_failure_runner_failure_thermal_and_timeout(self):
        for scenario in ('complete','numeric_failure','runner_failure','thermal','timeout'):
            with self.subTest(scenario=scenario):self.exercise(scenario)

    def exercise(self,scenario):
        worker=script('cara_sq_q1_worker_r1')
        from wcomr import sq_q1_execution_r1 as execution,sq_q1_spec_r1 as spec
        from wcomr import wc73_exclusive_r1 as exclusive,history104_storage_r2 as storage_module
        scope=json.loads((ROOT/SCOPE).read_text());collection=copy.deepcopy(raw_fixture())
        if scenario=='numeric_failure':collection=numeric_failure(collection)
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=project/'.sync/CPU_Q1_REAL_SUBPROCESS_ONLY'
            output=project/'outputs'/RUN;(stage/'scripts').mkdir(parents=True);output.mkdir(parents=True)
            for path,value in ((QUOTES['two_card'],dict(forecast_complete_GPUh=.01)),
                (PROFILE,dict(stop_release_margin_seconds=0,CPU_post_wall_seconds_max=300))):
                atomic_json(stage/path,value)
            atomic_json(stage/'fixture-collection.json',collection)
            source='''import json,os,time
from pathlib import Path
from wcomr.gpu_budget_pool_v2 import process_identity
stage=Path(__file__).resolve().parents[1];project=stage.parents[1]
assert str(os.getppid())==os.environ['WC_SUPERVISOR_PID']
assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==project/'.sync/gpu-locks/GPU-Q1-CPU-CONTROL.lock'
if __CASE__=='runner_failure':raise SystemExit(7)
ident={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};ident['uid']=os.getuid()
(stage/'pg-runner-context-ready.json').write_text(json.dumps(dict(identity=ident)))
while not (stage/'pg-runner-context-granted.json').exists():time.sleep(.02)
if __CASE__ in ('thermal','timeout'):time.sleep(60)
(project/'outputs'/__RUN__/'Q1-collection.json').write_text((stage/'fixture-collection.json').read_text())
'''.replace('__CASE__',repr(scenario)).replace('__RUN__',repr(RUN))
            (stage/'scripts/run_cara_sq_q1_r1.py').write_text(source)
            class Journal:
                def __init__(self):self.records={}
                def write(self,key,value):self.records[key]=copy.deepcopy(value)
            class Storage:
                journal=Journal()
                def check(self):return {}
                def persist(self,key,path,value,writer):self.journal.write(key,value);writer(path,value)
            storage=Storage();storage.output=output
            authority=dict(host='two_card',gpu_uuid=gpu()['uuid'],launch_id='CPU_NO_GPU_LAUNCH',scope_sha256='a'*64)
            registration=dict(source_revision='CPU_REAL_SUBPROCESS_CONTROL')
            def observe(uuid):
                ready=stage/'pg-runner-context-ready.json';apps=[]
                if ready.exists():
                    ident=json.loads(ready.read_text())['identity']
                    if Path('/proc',str(ident['pid'])).exists():apps=[dict(ident,gpu_uuid=uuid,memory_MiB=1)]
                return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,
                    mps_processes=[],observed_unix=time.time())
            args=type('Arguments',(),dict(project=project,stage=stage))()
            thermal={'temperature.gpu':'90' if scenario=='thermal' else '50'}
            limits=dict(LIMITS,two_card=1/3600 if scenario=='timeout' else 1.25)
            with patch.object(execution,'validate',return_value=(scope,registration,authority)),\
                    patch.object(storage_module,'storage_for',return_value=storage),\
                    patch.object(exclusive,'observe',side_effect=observe),\
                    patch.object(worker,'read_thermal',return_value=thermal),patch.object(spec,'LIMITS',limits):
                if scenario in ('complete','numeric_failure'):worker.supervise(args)
                else:
                    with self.assertRaises((RuntimeError,ValueError,TimeoutError)):worker.supervise(args)
            bill=json.loads((output/'Q1-billing.json').read_text())
            release=json.loads((output/'Q1-release-pending-central.json').read_text())
            self.assertGreater(bill['actual_GPUh'],0)
            self.assertTrue(release['GPU_released'] and release['original_process_exited'])
            self.assertFalse(release['cost_settled'])
            self.assertEqual(release['technical_accepted'],scenario in ('complete','numeric_failure'))
            self.assertEqual(storage.journal.records['billing'],bill)
            if scenario=='thermal':self.assertEqual(storage.journal.records['telemetry']['thermal']['temperature.gpu'],'90')
            with DeviceLease(project,gpu()['uuid']):pass
            with patch.object(execution,'validate',return_value=(scope,registration,authority)),\
                    patch.object(storage_module,'storage_for',return_value=storage):
                with self.assertRaises(ValueError):worker.supervise(args)


if __name__=='__main__':unittest.main()
