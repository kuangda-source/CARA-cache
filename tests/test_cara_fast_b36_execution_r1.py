"""New B boundaries only: real A metadata, temporary ledgers and real CPU children."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr import cara_fast_b36_execution_r1 as execution
from wcomr.cara_fast_b36_r1 import COMMON_SOURCES
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.gpu_budget_pool_v2 import DeviceLease, sha

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def real_binding():
    card = load_card(ROOT, execution.SPEC)
    profile = execution.read(ROOT/execution.PROFILE)
    return card, execution.load_handoff(ROOT, card, profile)


def complete_fixture(card, binding):
    rows = []
    schedules = {row['requested_steps']: row['actual_updates'] for row in card['schedules']}
    for slot in card['physical_matrix']:
        if slot['phase'] != 'B':
            continue
        role = card['roles'][slot['role']]
        name = binding['frozen']['selected'][role['family']]['candidate'] if role['kind']=='selection' else slot['role']
        updates = schedules[card['roles'][name]['requested_steps']]
        result = dict(slot_id=slot['id'], role=slot['role'], concrete_role=name,
            scope_sha256=card['scope_sha256'], CPU_fixture=False, solver_steps=updates,
            guided_pairs=updates, audit_enabled=False, in_timing_guided_copies=0,
            in_timing_hashes=0, research_checkpoints=0, T_DD=120., T_request=180.)
        rows.append(dict(slot=slot, result=result, status='COMPLETE'))
    return dict(phase='B', scope_sha256=card['scope_sha256'], status='TERMINAL', rows=rows,
                CPU_METADATA_FIXTURE_ONLY_NO_MODEL_EXECUTION=True)


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card, cls.bound = real_binding()

    def fixture(self, root):
        """Synthetic authority/envelope files; never operational GPU authority."""
        stage = root/'.sync/B36-UNIT-ONLY'
        names = set(COMMON_SOURCES) | set(execution.EXECUTION_SOURCES) | {
            execution.SPEC, execution.QUOTE, 'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json'}
        for name in names:
            path = stage/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT/name).read_bytes())
        registration = dict(source_revision='CPU_FIXTURE_NOT_GPU_AUTHORITY',
            payload_sha256={name: sha(stage/name) for name in names}, runtime_source_sha256={})
        write = lambda name, value: (stage/name).write_text(json.dumps(value))
        write('registration.json', registration)
        bound = dict(self.bound, A_runtime_source_sha256={})
        proof = dict(passed=True, critical_source_sha256={name: sha(stage/name) for name in execution.EXECUTION_SOURCES},
            receipts={'two_card': dict(runtime_source_sha256={})}, CPU_METADATA_FIXTURE_ONLY=True)
        for name in ('B36-core-CPU-proof.json', 'execution-CPU-proof.json'):
            write(name, proof)
        authority = dict(direct_user_authorization=True, user_quote='SYNTHETIC CPU UNIT INPUT ONLY',
            new_B36_authorization=True, authorizes_replay=False, run_id=execution.RUN, phase='B',
            physical_paths=36, whole_GPUh=5.5, host=bound['host'], gpu_uuid=bound['gpu_uuid'],
            A_launch_id=bound['A_launch_id'], frozen_file_sha256=bound['frozen_file_sha256'],
            scope_sha256=self.card['scope_sha256'], source_revision=registration['source_revision'],
            registration_sha256=sha(stage/'registration.json'), launch_id='B36-CPU-UNIT-NO-GPU',
            CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),
            core_CPU_proof_sha256=sha(stage/'B36-core-CPU-proof.json'))
        write('pg-GPU-authorization.json', authority)
        job = dict(authority, job_id=execution.RUN, stage=str(stage), billed_limit_GPUh=5.5,
            forecast_GPUh=5.022, status='RESERVED_OR_RUNNING', authorization_sha256=sha(stage/'pg-GPU-authorization.json'))
        write('central-reservation.json', dict(central_ledger_host='four_card', new_reservation=True, job=job))
        write('launch-binding.json', dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
            central_reservation_sha256=sha(stage/'central-reservation.json'),
            A_handoff_package_sha256=bound['package_sha256']))
        return stage, authority, job, bound

    def test_real_A_chain_unchanged_and_no_B_authority(self):
        self.assertFalse(self.bound['CPU_fixture_only'])
        self.assertFalse(self.bound['authorizes_phase_B'])
        self.assertEqual(self.bound['frozen_file_sha256'], '56e1eb84fed0a459ae8fdeb6598680009226dced9529052cabc57cf11cef2be8')
        self.assertEqual(self.bound['A_precision']['net_parameter_dtypes'], {'torch.bfloat16': 569})
        self.assertEqual({k: v['time_match'] for k,v in self.bound['frozen']['selected'].items()},
                         {'WC': 'UNMATCHED', 'RA': 'UNMATCHED', 'NATIVE_K': 'MATCHED'})

    def test_separate_authority_and_single_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage, authority, _, bound = self.fixture(root)
            with patch.object(execution, 'load_handoff', return_value=bound):
                self.assertEqual(execution.validate(root, stage)[2], authority)

    def test_wrong_phase_parent_frozen_host_proof_source_and_envelope_refused(self):
        for changed in ('no_authority','A_phase','partial','parent','frozen','host','same_launch','proof','source','replica','bill','binding'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                stage, authority, job, bound = self.fixture(root)
                if changed=='no_authority': authority['new_B36_authorization']=False
                elif changed=='A_phase': authority['phase']='A'
                elif changed=='partial': authority['physical_paths']=24
                elif changed=='parent': authority['A_launch_id']='WRONG-A'
                elif changed=='frozen': authority['frozen_file_sha256']='0'*64
                elif changed=='host': authority['host']='four_card'
                elif changed=='same_launch': authority['launch_id']=bound['A_launch_id']
                elif changed=='proof': authority['CPU_proof_sha256']='0'*64
                elif changed=='source': (stage/execution.EXECUTION_SOURCES[0]).write_text('changed')
                elif changed=='replica':
                    envelope=execution.read(stage/'central-reservation.json')
                    envelope['central_ledger_host']='two_card'
                    (stage/'central-reservation.json').write_text(json.dumps(envelope))
                elif changed=='bill':
                    job['billed_limit_GPUh']=5
                    (stage/'central-reservation.json').write_text(json.dumps(dict(central_ledger_host='four_card',new_reservation=True,job=job)))
                elif changed=='binding': (stage/'launch-binding.json').write_text('{}')
                (stage/'pg-GPU-authorization.json').write_text(json.dumps(authority))
                with patch.object(execution, 'load_handoff', return_value=bound), self.assertRaises((ValueError, KeyError)):
                    execution.validate(root, stage)

    def pool(self, root):
        value = execution.read(ROOT/'reports/cara_fast_A6000_central_settlement_20261029_0052.json')['central_after']
        path = root/'reports/gpu-budget-v2.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(value))
        return execution.Pool(root)

    def job(self):
        return dict(job_id=execution.RUN,run_id=execution.RUN,phase='B',physical_paths=36,host=self.bound['host'],
            gpu_uuid=self.bound['gpu_uuid'],A_launch_id=self.bound['A_launch_id'],
            frozen_file_sha256=self.bound['frozen_file_sha256'],scope_sha256=self.card['scope_sha256'],
            launch_id='CPU-ONLY-B-RESERVE',billed_limit_GPUh=5.5,forecast_GPUh=5.022)

    def gpu(self):
        return dict(uuid=self.bound['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',
                    pids=[],utilization_percent=0,memory_used_mib=24,unix=time.time())

    def test_reserve_whole_B_settle_once_preserve_A_and_16point5(self):
        with tempfile.TemporaryDirectory() as directory:
            pool = self.pool(Path(directory))
            before = pool.read()
            held = pool.reserve(self.job(), self.gpu(), self.bound)
            self.assertEqual(held['cap_gpu_hours'], 226)
            self.assertEqual(held['reserved_gpu_hours'], 22.)
            settled = pool.settle(execution.RUN, .05, 'b'*64)
            self.assertEqual(settled['reserved_gpu_hours'], 16.5)
            for key, value in before['jobs'].items(): self.assertEqual(settled['jobs'][key], value)
            self.assertEqual(pool.settle(execution.RUN,.05,'b'*64), settled)
            with self.assertRaises(ValueError): pool.reserve(self.job(), self.gpu(), self.bound)
            with self.assertRaises(ValueError): pool.settle(execution.RUN,.06,'b'*64)

    def test_unsettled_A_no_funds_busy_stale_migration_overlap_and_fixture_refuse_without_write(self):
        for changed in ('unsettled','A_bill','funds','busy','stale','migration','overlap','fixture'):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as directory:
                pool = self.pool(Path(directory))
                value, job, gpu, bound = pool.read(),self.job(),self.gpu(),copy.deepcopy(self.bound)
                if changed=='unsettled': value['jobs'][execution.A_RUN]['status']='RESERVED_OR_RUNNING'
                elif changed=='A_bill': value['jobs'][execution.A_RUN]['billing_sha256']='0'*64
                elif changed=='funds': value['cap_gpu_hours']=197
                elif changed=='busy': gpu['pids']=[123]
                elif changed=='stale': gpu['unix']=time.time()-61
                elif changed=='migration': job['host']='four_card'
                elif changed=='overlap':
                    value['jobs']['another-CPU-fixture']=dict(status='RESERVED_OR_RUNNING',host='two_card',
                        billed_limit_GPUh=.1,gpu_uuid='GPU-DIFFERENT',kind='V2')
                elif changed=='fixture': bound['CPU_fixture_only']=True
                value.update(pool.accounting(value))
                pool.path.write_text(json.dumps(value))
                before=pool.path.read_bytes()
                with self.assertRaises(ValueError): pool.reserve(job,gpu,bound)
                self.assertEqual(before,pool.path.read_bytes())

    def test_container_has_private_B_paths_and_unchanged_40GiB_no_swap(self):
        guardian = script('cara_fast_b36_host_guardian_r1')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root/'.sync/B36-CPU-fixture'
            storage=type('Storage',(),dict(output=root/'outputs'/execution.RUN,
                journal=type('Journal',(),dict(path=root/'reports/B36-control.journal'))(),
                config=dict(image_path=str(root/'B36.img'))))()
            command=guardian.container_arguments(root,stage,storage,'a'*64,'24,25',1004,998,self.bound['gpu_uuid'],40)
            for option,value in [('--memory','40g'),('--memory-swap','40g'),('--cpus','2'),
                                 ('--cpuset-cpus','24,25'),('--network','none'),('--pid','host')]:
                self.assertEqual(command[command.index(option)+1],value)
            self.assertIn(str(stage/'scripts/cara_fast_b36_worker_r1.py'),command)
            self.assertIn('CUDA_VISIBLE_DEVICES=',command)
            for name in ('outputs','reports','.sync'):
                self.assertNotIn(str(root/name)+':'+str(root/name)+':rw',command)
            self.assertNotIn('cara-fast-cal-a32-r2-20261028:rw',' '.join(command))


class SupervisorTests(unittest.TestCase):
    def exercise(self, scenario):
        worker = script('cara_fast_b36_worker_r1')
        from wcomr import wc73_exclusive_r1 as exclusive
        from wcomr import history104_storage_r2 as storage_module
        card, bound = real_binding()
        collection = complete_fixture(card,bound)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root/'.sync/B36-CPU-child'
            output = root/'outputs'/execution.RUN
            (stage/'scripts').mkdir(parents=True)
            output.mkdir(parents=True)
            margin = 5.5*3600-.2 if scenario=='budget' else 180
            quote = dict(host_quotes={'two_card':dict(phases={'B':dict(forecast_GPUh=5.022,stop_release_margin_seconds=margin)})})
            path = stage/execution.QUOTE
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(quote))
            if scenario=='partial': collection['rows'].pop()
            (stage/'fixture-collection.json').write_text(json.dumps(collection))
            source = '''import json,os,time
from pathlib import Path
from wcomr.gpu_budget_pool_v2 import process_identity
stage=Path(__file__).resolve().parents[1];project=stage.parents[1]
assert str(os.getppid())==os.environ['WC_SUPERVISOR_PID']
assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==project/'.sync/gpu-locks'/(__UUID__+'.lock')
if __SCENARIO__=='runner_failure':raise SystemExit(7)
identity={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
(stage/'pg-runner-context-ready.json').write_text(json.dumps(dict(identity=identity)))
while not (stage/'pg-runner-context-granted.json').exists():time.sleep(.02)
if __SCENARIO__ in ('thermal','budget','foreign_context'):time.sleep(60)
(project/'outputs'/__RUN__/'B-collection.json').write_text((stage/'fixture-collection.json').read_text())
'''.replace('__UUID__',repr(bound['gpu_uuid'])).replace('__SCENARIO__',repr(scenario)).replace('__RUN__',repr(execution.RUN))
            (stage/'scripts/run_cara_fast_b36_r1.py').write_text(source)
            class Journal:
                records={}
                def write(self,key,value): self.records[key]=copy.deepcopy(value)
            class Storage:
                journal=Journal()
                def check(self): return {}
                def persist(self,key,path,value,writer):
                    self.journal.write(key,value)
                    writer(path,value)
            storage=Storage();storage.output=output
            authority=dict(host='two_card',gpu_uuid=bound['gpu_uuid'],launch_id='B36-CPU-CHILD',whole_GPUh=5.5)
            registration=dict(source_revision='CPU_FIXTURE_NOT_GPU_AUTHORITY')
            def observe(uuid):
                apps=[]
                ready=stage/'pg-runner-context-ready.json'
                if ready.exists():
                    identity=json.loads(ready.read_text())['identity']
                    if Path('/proc/'+str(identity['pid'])).exists():
                        apps=[dict(identity,gpu_uuid=uuid,memory_MiB=1)]
                        if scenario=='foreign_context':apps.append(dict(identity,pid=os.getpid(),memory_MiB=1,gpu_uuid=uuid))
                return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,mps_processes=[],observed_unix=time.time())
            args=type('Arguments',(),dict(project=root,stage=stage))()
            thermal={'temperature.gpu':'90' if scenario=='thermal' else '50','fan.speed':'80','clocks_event_reasons.active':'0x0'}
            with patch.object(execution,'validate',return_value=(card,registration,authority,bound)),\
                 patch.object(storage_module,'storage_for',return_value=storage),\
                 patch.object(exclusive,'observe',side_effect=observe),patch.object(worker,'read_thermal',return_value=thermal):
                if scenario=='complete':worker.supervise(args)
                else:
                    with self.assertRaises((ValueError,RuntimeError,TimeoutError)):worker.supervise(args)
            bill=execution.read(output/'B-billing.json')
            release=execution.read(output/'B-release-pending-central.json')
            self.assertGreater(bill['actual_GPUh'],0)
            self.assertEqual(bill['actual_GPUh'],bill['wall_seconds']/3600)
            self.assertTrue(release['original_process_exited'] and release['GPU_released'])
            self.assertEqual(release['technical_accepted'],scenario=='complete')
            self.assertFalse(release['cost_settled'])
            self.assertEqual(storage.journal.records['billing'],bill)
            if scenario=='thermal':self.assertEqual(storage.journal.records['telemetry']['thermal']['temperature.gpu'],'90')
            with DeviceLease(root,bound['gpu_uuid']):pass
            with patch.object(execution,'validate',return_value=(card,registration,authority,bound)),\
                 patch.object(storage_module,'storage_for',return_value=storage),self.assertRaises(ValueError):worker.supervise(args)
            schedule=execution.read(output/'B-check-schedule.json')
            state=execution.read(output/'B-supervisor.json')
            self.assertAlmostEqual(schedule['halfway_unix']-state['started_unix'],5.022*1800,places=5)
            self.assertEqual(schedule['hard_terminal_unix']-state['started_unix'],5.5*3600)

    @unittest.skipUnless(Path('/proc/self').exists(),'Linux inherited-FD child/process-group control')
    def test_normal_failure_partial_thermal_budget_foreign_context(self):
        for scenario in ('complete','runner_failure','partial','thermal','budget','foreign_context'):
            with self.subTest(scenario=scenario):self.exercise(scenario)


if __name__=='__main__':
    unittest.main()
