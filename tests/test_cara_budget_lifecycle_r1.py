"""Synthetic lifecycle packets and real temporary-ledger I/O; never GPU access."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from wcomr import cara_budget_lifecycle_r1 as lifecycle
from wcomr.cara_budget_original_handles_r1 import ROLES
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA, sha
from wcomr.policy_price_terminal_r1 import record


def put(capture, name, value):
    raw = json.dumps(value, indent=2) + '\n'
    capture['files'][name] = dict(exists=True, raw_utf8=raw, bytes=len(raw.encode()),
                                sha256=hashlib.sha256(raw.encode()).hexdigest())
    return capture['files'][name]['sha256']


def fixture(*,host='four_card',gpu_uuid='GPU-CPU-FIXTURE'):
    view = dict(boot_id='12345678-1234-1234-1234-123456789abc', pid_namespace_inode=123)
    handles = {role:dict(pid=100+i, start_ticks=1000+i, host_view=view) for i,role in enumerate(ROLES)}
    capture = dict(files={}, payload_actual_sha256={lifecycle.SOURCE:sha(lifecycle.__file__)},
                   runtime_actual_sha256={'runtime.py':'a'*64}, own_UUID_lock_free=True, mode_owner_lock_free=True)
    identity = dict(run_id='CPU-FIXTURE-CALIBRATION',launch_id='CPU-FIXTURE-UNIQUE-LAUNCH',
        host=host,gpu_uuid=gpu_uuid,stage='/CPU-FIXTURE/original-stage',
        source_revision='f'*40,scope_sha256='d'*64,billed_limit_GPUh=2.)
    registration = dict(host=identity['host'],stage=identity['stage'],source_revision=identity['source_revision'],
        payload_sha256=capture['payload_actual_sha256'],runtime_source_sha256=capture['runtime_actual_sha256'],
        container_image='sha256:'+'e'*64)
    reg_sha = put(capture,'registration',registration)
    auth_sha = put(capture,'authorization',dict(identity,execution_authorized=True,
        authorizes_replay=False,CPU_fixture_only=True))
    job = dict(identity,job_id=identity['run_id'],status='RESERVED_OR_RUNNING',
               registration_sha256=reg_sha,authorization_sha256=auth_sha)
    envelope_sha = put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
    launch = dict(identity,registration_sha256=reg_sha,authorization_sha256=auth_sha,
        central_reservation_sha256=envelope_sha,container='CPU-FIXTURE-original-container',
        guardian_identity=handles['guardian'],CPU_fixture_only=True)
    expected_sha = put(capture,'launch',launch)
    container = dict(id='c'*64,name=launch['container'],image=registration['container_image'],
        manifest_sha256=reg_sha,device_ids=[identity['gpu_uuid']],
        state=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False))
    capture['container'] = container
    final = dict(gpu_uuid=identity['gpu_uuid'],compute_mode='Exclusive_Process',compute_apps=[],
                 mps_processes=[],observed_unix=100.)
    put(capture,'pending_release',dict(identity,final_snapshot=final))
    for role in ('supervisor','runner'):
        put(capture,role+'_start',dict(identity=handles[role]))
    put(capture,'runner_intent',dict(launch_id=launch['launch_id']))
    bill = dict(identity,started_monotonic=20.,ended_monotonic=200.,wall_seconds=180.,actual_GPUh=.05,
                billing_clock_owner='HOST_GUARDIAN',wall_interval_complete=True)
    bill_sha = put(capture,'billing',bill)
    guardian = dict(identity,status='BUDGET_CALIBRATION_GUARDIAN_TERMINAL',original_handles=handles,
        container_dispatch_state='STARTED',container_terminal_witness=dict(kind='BOUND_CONTAINER_TERMINAL',
            complete=True,container_id=container['id'],container=container),
        started_monotonic=20.,ended_monotonic=200.,billing_sha256=bill_sha,container_exit_code=0,
        mode_restoration=dict(restored=True,snapshot=dict(final,compute_mode='Default')),GPU_mode_change_attempted=True)
    put(capture,'guardian',guardian)
    capture['process_observations']={role:dict(original_pid=h['pid'],original_start_ticks=h['start_ticks'],
        observed_host_view=view,original_live=False,status='ORIGINAL_NOT_LIVE',reason='ORIGINAL_PROC_ABSENT',
        observed_process=dict(pid=h['pid'],state=None,start_ticks=None)) for role,h in handles.items()}
    return capture,expected_sha,job


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.capture,self.expected,self.job=fixture()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.pool=BudgetPool(self.temp.name)
        value=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
            jobs={'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5),
                  self.job['job_id']:self.job},events=[])
        value.update(self.pool.accounting(value));self.pool.path.parent.mkdir(parents=True)
        self.pool.path.write_text(json.dumps(value))

    def finance(self):
        return lifecycle.financial_terminal(self.capture,self.expected,cpu_validation=True)

    def settle(self):
        launch,bill=self.finance();before=self.pool.read()
        after=self.pool.settle(launch['run_id'],bill['actual_GPUh'],self.capture['files']['billing']['sha256'])
        return dict(central_ledger_host='four_card',launch_id=launch['launch_id'],
            billing_sha256=self.capture['files']['billing']['sha256'],central_before=before,central_after=after)

    def release(self,settlement=None):
        return lifecycle.released_lifecycle(self.capture,self.expected,settlement or self.settle(),cpu_validation=True)

    def change_guardian(self,fn):
        guardian=record(self.capture,'guardian');fn(guardian);put(self.capture,'guardian',guardian)

    def test_complete_release_and_exact_idempotent_temporary_settlement(self):
        first=self.settle();second=self.settle()
        self.assertEqual(first['central_after'],second['central_after'])
        self.assertEqual(second['central_after']['reserved_gpu_hours'],16.5)
        for receipt in (first,second):
            result=self.release(receipt)
            self.assertTrue(result['GPU_released']);self.assertTrue(result['container_exit_success'])
            self.assertFalse(result['complete_search_accepted']);self.assertFalse(result['dispatch_allowed'])
            self.assertFalse(result['ledger_written'])
        with self.assertRaises(ValueError):self.pool.settle(self.job['job_id'],.06,'a'*64)

    def test_real_central_liability_layout_accepts_same_UUID_without_altering_old_holds(self):
        from wcomr.wc73_execution_r1 import Pool,hold
        root=Path(__file__).resolve().parents[1]
        packet=json.loads((root/'reports/cara_fast_B36_actual_central_reservation_r1_20261029.json').read_text())
        value=copy.deepcopy(packet['central_envelope']['central_before'])
        old={k:v for k,v in value['jobs'].items() if hold(v)}
        self.assertEqual(sorted(v['billed_limit_GPUh'] for v in old.values()),[4.5,12.])
        self.capture,self.expected,self.job=fixture(host='two_card',gpu_uuid=next(iter(old.values()))['gpu_uuid'])
        value['jobs'][self.job['job_id']]=self.job;value.update(Pool.accounting(value))
        self.pool=Pool(self.temp.name);self.pool.path.write_text(json.dumps(value))
        first=self.settle();second=self.settle()
        for receipt in (first,second):
            self.assertTrue(self.release(receipt)['cost_settled'])
            self.assertTrue(self.release(json.loads(json.dumps(receipt,sort_keys=True)))['cost_settled'])
            self.assertEqual(receipt['central_after']['reserved_gpu_hours'],16.5)
            self.assertEqual({k:receipt['central_after']['jobs'][k] for k in old},old)
        self.assertEqual(first['central_after'],second['central_after'])

    def test_fixture_refused_without_explicit_CPU_mode(self):
        with self.assertRaises(ValueError):lifecycle.financial_terminal(self.capture,self.expected)

    def test_wrong_launch_source_and_authority_refused(self):
        original=copy.deepcopy(self.capture)
        for change in ('launch','source','authority','runtime','reservation'):
            self.capture=copy.deepcopy(original)
            if change=='launch':
                launch=record(self.capture,'launch');launch['launch_id']='other';put(self.capture,'launch',launch)
            elif change=='source':self.capture['payload_actual_sha256']={}
            elif change=='runtime':self.capture['runtime_actual_sha256']={}
            elif change=='reservation':
                envelope=record(self.capture,'central_reservation');envelope['central_ledger_host']='two_card'
                put(self.capture,'central_reservation',envelope)
            else:
                authority=record(self.capture,'authorization');authority['authorizes_replay']=True
                put(self.capture,'authorization',authority)
            with self.subTest(change=change),self.assertRaises(ValueError):self.finance()

    def test_live_unknown_wrong_view_and_fake_exit_refused(self):
        original=copy.deepcopy(self.capture)
        for change in ('live','unknown','view','unproven'):
            self.capture=copy.deepcopy(original);row=self.capture['process_observations']['runner']
            if change=='live':row['original_live']=True
            elif change=='unknown':row['original_live']=None
            elif change=='view':row['observed_host_view']=dict(row['observed_host_view'],pid_namespace_inode=9)
            else:row['observed_process']['state']='S'
            with self.subTest(change=change),self.assertRaises(ValueError):self.finance()

    def test_reused_pid_is_not_original_live_process(self):
        row=self.capture['process_observations']['runner']
        row.update(reason='PID_REUSED_ORIGINAL_PROCESS_EXITED',observed_process=dict(pid=103,state='S',start_ticks=9000))
        self.assertEqual(self.finance()[1]['actual_GPUh'],.05)

    def test_wrong_or_live_container_and_unknown_locks_refused(self):
        original=copy.deepcopy(self.capture)
        for change in ('id','manifest','device','running','lock','mode_lock'):
            self.capture=copy.deepcopy(original)
            if change=='lock':self.capture['own_UUID_lock_free']=False
            elif change=='mode_lock':self.capture['mode_owner_lock_free']=None
            else:
                container=self.capture['container']
                if change=='running':container['state']['Running']=True
                elif change=='id':container['id']='z'*64
                elif change=='manifest':container['manifest_sha256']='0'*64
                else:container['device_ids']=['GPU-OTHER']
            with self.subTest(change=change),self.assertRaises(ValueError):self.finance()

    def test_failed_container_still_charged_but_not_successful(self):
        self.capture['container']['state'].update(ExitCode=137,OOMKilled=True)
        self.change_guardian(lambda g:g.update(container_exit_code=137,error_type='GPUWorkerFailure',
            container_terminal_witness=dict(g['container_terminal_witness'],container=self.capture['container'])))
        result=self.release()
        self.assertTrue(result['cost_settled']);self.assertFalse(result['container_exit_success'])
        self.assertEqual(result['actual_GPUh'],.05)

    def test_missing_release_or_unrestored_mode_does_not_erase_bill(self):
        self.capture['files']['pending_release']={'exists':False}
        self.change_guardian(lambda g:g.update(mode_restoration={'restored':False}))
        result=self.release()
        self.assertTrue(result['cost_settled']);self.assertFalse(result['GPU_released'])
        self.assertFalse(result['mode_restored']);self.assertFalse(result['container_exit_success'])

    def test_original_release_survives_later_foreign_GPU_activity(self):
        self.capture['current_GPU_snapshot']={'compute_apps':[{'pid':9999}],'observation_unavailable':False}
        self.assertTrue(self.release()['GPU_released'])

    def test_wrong_worker_start_and_other_launch_release_refused(self):
        start=record(self.capture,'runner_start');start['identity']['start_ticks']+=1
        put(self.capture,'runner_start',start)
        with self.assertRaises(ValueError):self.finance()
        self.capture,self.expected,_=fixture()
        pending=record(self.capture,'pending_release');pending['launch_id']='OTHER-LAUNCH'
        put(self.capture,'pending_release',pending)
        with self.assertRaises(ValueError):self.release()

    def test_precontainer_failure_and_missing_runner_intent(self):
        for kind in ('NO_CONTAINER_DISPATCH','ORIGINAL_CONTAINER_NEVER_CREATED','BOUND_CONTAINER_TERMINAL'):
            self.capture,self.expected,_=fixture()
            for key in ('supervisor_start','runner_start','runner_intent'):self.capture['files'][key]={'exists':False}
            guardian=record(self.capture,'guardian')
            for role in ('supervisor','runner'):
                guardian['original_handles'][role]=None;self.capture['process_observations'][role]=None
            if kind!='BOUND_CONTAINER_TERMINAL':
                self.capture['container']=None
                guardian['container_terminal_witness']={'kind':kind,'complete':True}
            else:
                self.capture['container']['state']['ExitCode']=1
                guardian['container_terminal_witness']['container']=self.capture['container']
            if kind=='NO_CONTAINER_DISPATCH':
                guardian.update(container_dispatch_state='NOT_ATTEMPTED',GPU_mode_change_attempted=False)
                guardian['original_handles']['container_cli']=None;self.capture['process_observations']['container_cli']=None
            put(self.capture,'guardian',guardian)
            with self.subTest(kind=kind):self.assertEqual(self.finance()[1]['actual_GPUh'],.05)
        self.capture['files']['runner_intent']={'exists':True}
        with self.assertRaises(ValueError):self.finance()

    def test_incomplete_or_estimated_bill_refused(self):
        original=copy.deepcopy(self.capture)
        for key,value in [('wall_interval_complete',False),('wall_seconds',179.),('actual_GPUh',0.),
                          ('billing_clock_owner','SUPERVISOR'),('ended_monotonic',float('nan'))]:
            self.capture=copy.deepcopy(original);bill=record(self.capture,'billing');bill[key]=value
            bill_sha=put(self.capture,'billing',bill)
            self.change_guardian(lambda g:g.update(billing_sha256=bill_sha))
            with self.subTest(key=key),self.assertRaises(ValueError):self.finance()

    def test_hard_overrun_settled_actual_and_never_successful(self):
        bill=record(self.capture,'billing');bill.update(ended_monotonic=10820.,wall_seconds=10800.,actual_GPUh=3.)
        bill_sha=put(self.capture,'billing',bill)
        self.change_guardian(lambda g:g.update(ended_monotonic=10820.,billing_sha256=bill_sha))
        result=self.release();self.assertTrue(result['hard_limit_exceeded']);self.assertFalse(result['container_exit_success'])
        self.assertEqual(result['actual_GPUh'],3.);self.assertTrue(self.pool.read()['budget_overrun_recorded'])

    def test_altered_old_liability_or_added_settlement_event_refused(self):
        receipt=self.settle()
        for change in ('liability','event','job'):
            altered=copy.deepcopy(receipt);after=altered['central_after']
            if change=='liability':
                after['jobs']['old-unknown-16.5']['billed_limit_GPUh']=1.
                after.update(self.pool.accounting(after))
            elif change=='event':after['events'].append(copy.deepcopy(after['events'][-1]))
            else:after['jobs'][self.job['job_id']]['authorization_sha256']='0'*64
            with self.subTest(change=change),self.assertRaises(ValueError):self.release(altered)

    def test_proven_preallocation_failure_can_settle_without_owning_resource_locks(self):
        self.capture['container']=None
        for key in ('supervisor_start','runner_start','runner_intent'):self.capture['files'][key]={'exists':False}
        guardian=record(self.capture,'guardian')
        for role in ('container_cli','supervisor','runner'):
            guardian['original_handles'][role]=None;self.capture['process_observations'][role]=None
        guardian.update(container_terminal_witness=dict(kind='NO_CONTAINER_DISPATCH',complete=True),
            container_dispatch_state='NOT_ATTEMPTED',GPU_mode_change_attempted=False,mode_owner_fenced=False,
            error_type='CredentialUnavailable',mode_restoration=dict(restored=True,status='PRIOR_MODE_UNCHANGED'),
            allocation_never_attempted_witness=dict(mode_lock_attempted=False,device_lease_attempted=False,
                mode_change_attempted=False,container_dispatch_attempted=False))
        put(self.capture,'guardian',guardian)
        for lock_state in (None,False):
            self.capture['own_UUID_lock_free']=self.capture['mode_owner_lock_free']=lock_state
            result=self.release();self.assertTrue(result['cost_settled']);self.assertFalse(result['container_exit_success'])
        valid=copy.deepcopy(self.capture)
        for fault in ('missing','mode_lock_attempted','device_lease_attempted','mode_change_attempted',
                      'container_dispatch_attempted','mode_changed','fenced','no_error'):
            self.capture=copy.deepcopy(valid);g=record(self.capture,'guardian')
            if fault=='missing':g.pop('allocation_never_attempted_witness')
            elif fault=='mode_changed':g['GPU_mode_change_attempted']=True
            elif fault=='fenced':g['mode_owner_fenced']=True
            elif fault=='no_error':g.pop('error_type')
            else:g['allocation_never_attempted_witness'][fault]=True
            put(self.capture,'guardian',g)
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.finance()


if __name__=='__main__':unittest.main()
