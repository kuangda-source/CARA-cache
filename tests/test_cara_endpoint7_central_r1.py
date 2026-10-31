"""Real temporary-ledger transactions with simulated complete host admission."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr import cara_endpoint7_central_r1 as central
from wcomr.cara_s_endpoint_lifecycle_r1 import IDENTITY,audit_settlement,SOURCE as LIFECYCLE_SOURCE
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import sha
from test_cara_budget_lifecycle_r1 import fixture,put
from wcomr.policy_price_terminal_r1 import record

ROOT=Path(__file__).resolve().parents[1]


class CentralTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.pool=central.Pool(self.project)
        packet=read_record(ROOT/'reports/cara_fast_B36_actual_central_reservation_r1_20261029.json')
        self.before=copy.deepcopy(packet['central_envelope']['central_before'])
        self.pool.path.parent.mkdir(parents=True);self.pool.path.write_text(json.dumps(self.before))
        self.auth=dict(run_id=central.RUN,launch_id='f'*32,source_revision='e'*40,scope_sha256='d'*64,
            host='two_card',gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
            stage=str(self.project/'.sync'/central.STAGES['two_card']),billed_limit_GPUh=7,
            CPU_fixture_only=False,execution_authorized=True,direct_user_authorization=True,
            user_quote='Synthetic metadata for temporary ledger only',authorizes_replay=False,
            central_transaction_authorized=True,central_user_quote='CPU fixture central exception',new_endpoint_authorization=True,physical_paths=46,
            execution_host_policy_sha256=central.POLICY_SHA256)
        self.observations={host:dict(host=host,stage=str(self.project/'.sync'/stage),run_id=central.RUN,
            observation_complete=True,observed_unix=time.time(),dispatch_records=[],container=None)
            for host,stage in central.STAGES.items()}
        self.admission=dict(authorization=self.auth,registration_sha256='c'*64,forecast_GPUh=6.040146520925272,
            status='ENDPOINT7_COMPLETE_FRESH_ADMISSION_NO_GPU',required_host_whole_card_CPU_accepted=True,
            required_hosts=['two_card'],execution_host_policy_sha256=central.POLICY_SHA256,
            central_operator_sha256=sha(central.__file__),physical_paths=46,new_scoring_pairs=16,observed_unix=time.time(),
            resources=dict(gpu=dict(uuid=self.auth['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',
                utilization_percent=0,pids=[],memory_used_mib=0,temperature_C=35,unix=time.time())))
        self.refresh_authority()

    def refresh_authority(self):
        raw=json.dumps(self.auth);self.admission.update(authorization_raw_utf8=raw,
            authorization_sha256=hashlib.sha256(raw.encode()).hexdigest())

    def reserve(self):return central.reserve(self.project,self.admission,self.observations)

    def test_whole_reservation_idempotence_and_original_liabilities(self):
        first=self.reserve();after=self.pool.read();second=self.reserve()
        self.assertEqual(first,second);self.assertEqual(after,self.pool.read())
        self.assertEqual(after['reserved_gpu_hours'],23.5)
        self.assertEqual(after['jobs'][central.RUN]['billed_limit_GPUh'],7)
        self.assertEqual({k:after['jobs'][k] for k in self.before['jobs']},self.before['jobs'])
        self.assertEqual(len(after['events']),len(self.before['events'])+1)

    def test_persisted_reservation_recovers_original_atomic_write_only(self):
        with patch.object(central,'atomic_json',side_effect=OSError('Interrupted before ledger replacement')):
            with self.assertRaises(OSError):self.reserve()
        self.assertEqual(self.pool.read(),self.before)
        saved=read_record(self.project/'reports'/(central.RUN+'.central-reservation.json'))
        self.assertEqual(self.reserve(),saved);self.assertEqual(self.pool.read(),saved['central_after'])

    def test_receipt_failure_never_changes_ledger(self):
        with patch.object(central,'create',side_effect=OSError('Receipt unavailable')):
            with self.assertRaises(OSError):self.reserve()
        self.assertEqual(self.pool.read(),self.before)

    def test_original_other_host_intent_unknown_or_stale_refuses(self):
        original=self.observations.pop('two_card')
        with self.assertRaisesRegex(ValueError,'required original handles'):self.reserve()
        self.observations['two_card']=original
        for field,value in [('dispatch_records',['GPU-intent.json']),('observation_complete',False),
                            ('container',{'Running':False}),('observed_unix',time.time()-61)]:
            original=self.observations['two_card'][field];self.observations['two_card'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.reserve()
            self.observations['two_card'][field]=original
        self.assertEqual(self.pool.read(),self.before)

    def test_no_approval_incomplete_or_stale_admission_and_wrong_source_refuse(self):
        self.auth['direct_user_authorization']=False;self.refresh_authority()
        with self.assertRaises(ValueError):self.reserve()
        self.auth['direct_user_authorization']=True;self.refresh_authority()
        for key,value in [('physical_paths',45),('new_scoring_pairs',15),('forecast_GPUh',15),
                          ('observed_unix',time.time()-61),('required_host_whole_card_CPU_accepted',False),
                          ('required_hosts',['four_card']),('execution_host_policy_sha256','0'*64),
                          ('central_operator_sha256','0'*64)]:
            original=self.admission[key];self.admission[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.reserve()
            self.admission[key]=original
        self.assertEqual(self.pool.read(),self.before)

    def test_new_endpoint_preserves_failed_original_and_refuses_its_approval(self):
        old_run = 'cara-budget-calibration-14gpuh-r1-20261030'
        old_job = dict(job_id=old_run, run_id=old_run, kind='V2', status='SETTLED',
                       host='two_card', billed_limit_GPUh=7, actual_GPUh=0.002315298004800247,
                       launch_id='2b8058a77c7248f181acffddd399c257')
        self.before['jobs'][old_run] = old_job
        self.before.update(self.pool.accounting(self.before))
        self.pool.path.write_text(json.dumps(self.before))
        self.auth['run_id'] = old_run
        self.refresh_authority()
        with self.assertRaises(ValueError):
            self.reserve()
        self.assertEqual(self.pool.read(), self.before)
        self.auth['run_id'] = central.RUN
        self.refresh_authority()
        self.reserve()
        self.assertEqual(self.pool.read()['jobs'][old_run], old_job)

    def test_central_exception_must_be_direct(self):
        self.auth['central_transaction_authorized']=False;self.refresh_authority()
        with self.assertRaises(ValueError):self.reserve()
        self.assertEqual(self.pool.read(),self.before)

    def test_existing_reservation_cannot_migrate_or_replay(self):
        self.reserve();before=self.pool.read();self.auth['launch_id']='0'*32;self.refresh_authority()
        with self.assertRaisesRegex(ValueError,'Original reservation differs'):self.reserve()
        self.assertEqual(self.pool.read(),before)

    def test_insufficient_funds_or_same_host_job_refuse(self):
        for fault in ('funds','host'):
            value=copy.deepcopy(self.before)
            if fault=='funds':value['origin_used_gpu_hours']=210
            else:value['jobs']['other']=dict(status='RESERVED_OR_RUNNING',billed_limit_GPUh=1,host='two_card',gpu_uuid='GPU-other')
            value.update(central.Pool.accounting(value));self.pool.path.write_text(json.dumps(value))
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.reserve()
            self.assertEqual(self.pool.read(),value)

    def financial_fixture(self):
        capture,expected,job=fixture(run_id=central.RUN,billed_limit_GPUh=7,host='two_card',
            gpu_uuid=self.auth['gpu_uuid'],extra_sources={central.SOURCE:sha(central.__file__),LIFECYCLE_SOURCE:sha(ROOT/LIFECYCLE_SOURCE)})
        guardian=record(capture,'guardian');guardian['status']='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1';put(capture,'guardian',guardian)
        authority=record(capture,'authorization');authority.update(central_transaction_authorized=True,central_user_quote='CPU fixture only')
        auth_sha=put(capture,'authorization',authority);job['authorization_sha256']=auth_sha
        reserve_sha=put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
        launch=record(capture,'launch');launch.update(authorization_sha256=auth_sha,central_reservation_sha256=reserve_sha)
        expected=put(capture,'launch',launch)
        value=copy.deepcopy(self.before);value['jobs'][central.RUN]=job;value.update(self.pool.accounting(value))
        self.pool.path.write_text(json.dumps(value));return capture,expected

    def test_original_bill_settles_once_with_old_same_UUID_liability(self):
        capture,expected=self.financial_fixture()
        first=central.settle(self.project,capture,expected,cpu_validation=True)
        second=central.settle(self.project,capture,expected,cpu_validation=True)
        self.assertEqual(first,second);self.assertEqual(first['central_after'],self.pool.read())
        self.assertEqual(self.pool.read()['reserved_gpu_hours'],16.5)
        audit_settlement(capture,expected,first,cpu_validation=True)

    def test_original_settlement_recovery_after_receipt_before_ledger(self):
        capture,expected=self.financial_fixture();before=self.pool.read()
        with patch.object(central,'atomic_json',side_effect=OSError('Original ledger replacement interrupted')):
            with self.assertRaises(OSError):central.settle(self.project,capture,expected,cpu_validation=True)
        self.assertEqual(self.pool.read(),before)
        result=central.settle(self.project,capture,expected,cpu_validation=True)
        self.assertEqual(self.pool.read(),result['central_after'])

    def test_unknown_original_or_CPU_packet_cannot_settle_production(self):
        capture,expected=self.financial_fixture();before=self.pool.read()
        with self.assertRaises(ValueError):central.settle(self.project,capture,expected)
        capture['process_observations']['runner']['original_live']=None
        with self.assertRaises(ValueError):central.settle(self.project,capture,expected,cpu_validation=True)
        self.assertEqual(self.pool.read(),before)

    def test_failed_and_over_limit_original_cost_kept(self):
        capture,expected=self.financial_fixture()
        billing=record(capture,'billing');billing.update(ended_monotonic=20+15*3600,wall_seconds=15*3600,actual_GPUh=15)
        billsha=put(capture,'billing',billing)
        guardian=record(capture,'guardian');guardian.update(ended_monotonic=billing['ended_monotonic'],billing_sha256=billsha,
            error_type='TimeoutError',container_exit_code=1)
        capture['container']['state']['ExitCode']=1
        guardian['container_terminal_witness']['container']=capture['container'];put(capture,'guardian',guardian)
        result=central.settle(self.project,capture,expected,cpu_validation=True)
        self.assertEqual(result['central_after']['jobs'][central.RUN]['actual_GPUh'],15)
        self.assertTrue(result['central_after']['budget_overrun_recorded'])
        self.assertEqual(result['central_after']['reserved_gpu_hours'],16.5)


if __name__=='__main__':unittest.main()
