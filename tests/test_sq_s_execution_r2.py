"""Full S source, grant, once-only finance and retained-failure CPU controls.

Every grant, ledger and GPU header here is synthetic. No asset is hashed or
deserialized and these fixtures cannot constitute actual GPU evidence.
"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json,sha
from wcomr import sq_s_execution_r2 as execution
from wcomr.sq_s_spec_r2 import (RUN,SCOPE,PROFILE,IDENTITY,RESOURCE,ASSETS,MODE,RISK,HISTORY,PHYSICAL,QUOTES,
    LIMITS,COUNTS,IDENTITY_SHA,RESOURCE_SHA,OTHER_A6000,EXECUTION_CRITICAL,stage_path)

ROOT=Path(__file__).resolve().parents[1]


def script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def ledger(project):
    jobs={}
    for index in range(2):
        key='original-unknown-'+str(index)
        jobs[key]=dict(job_id=key,status='RESERVED_OR_RUNNING',billed_limit_GPUh=8.25,
            gpu_uuid='GPU-OLD-UNCONFIRMED',kind='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD',
            confirmed_GPU_submission=False,actual_cost_unknown=True,launch_id='NOT_A_CONFIRMED_GPU_SUBMISSION',
            supervisor_pid=None,supervisor_start_ticks=None)
    value=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=176.,origin_gpu_jobs_launched=0,jobs=jobs,events=[])
    value.update(execution.Pool.accounting(value));atomic_json(project/'reports/gpu-budget-v2.json',value)
    return execution.Pool(project)


def fixture(project,host='two_card'):
    stage=stage_path(project,host);identity=execution.read(ROOT/IDENTITY)
    quote=execution.read(ROOT/QUOTES[host])
    paths=set(EXECUTION_CRITICAL)|{SCOPE,PROFILE,IDENTITY,RESOURCE,ASSETS,MODE,RISK,HISTORY,PHYSICAL[host],QUOTES[host]}
    rule=execution.read(ROOT/RISK)
    paths.update(rule['legacy_source_ref'].values());paths.update((rule['method_ref'],rule['support_ref']))
    paths.update(quote['source_evidence_sha256']);paths.update(identity['numerical_source_sha256'])
    for name in paths:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    (project/'runtime').symlink_to(ROOT/'cache/runtime',target_is_directory=True)
    profile=execution.read(stage/PROFILE);profile['hosts'][host]['output_mount']=str(project/'outputs'/RUN)
    atomic_json(stage/PROFILE,profile)
    reg=dict(namespace='SQ_S_COMPLETE_EXECUTION_R2',host=host,stage=str(stage),native_hostname=socket.gethostname(),
        source_revision='SYNTHETIC_CPU_CONTROL_NOT_A_GPU_AUTHORIZATION',
        payload_sha256={name:sha(stage/name) for name in sorted(paths)},
        runtime_source_sha256=identity['runtime_source_sha256'])
    atomic_json(stage/'registration.json',reg)
    proof=dict(passed=True,GPU_submissions=0,host=host,source_revision=reg['source_revision'],
        actual_platform=dict(system='Linux'),skipped=0,full_S_entry_CPU_accepted=True,native_parser_accepted=True,
        payload_sha256=reg['payload_sha256'],
        critical_source_sha256={name:sha(stage/name) for name in EXECUTION_CRITICAL},CPU_fixture=True)
    atomic_json(stage/'execution-CPU-proof.json',proof)
    selected=profile['hosts'][host]
    atomic_json(stage/'history104-storage.json',dict(run_id=RUN,output_mount=selected['output_mount'],
        image_path=selected['image_path'],journal_path=selected['journal_path'],image_bytes=32*2**30,journal_bytes=48*2**20,
        minimum_output_free_bytes=512*2**20,minimum_host_free_bytes=4*2**30,minimum_free_inodes=1024))
    atomic_json(stage/'S-asset-verification.json',dict(CPU_fixture=True,actual_assets_hashed=False))
    physical=execution.read(stage/PHYSICAL[host])
    auth=dict(direct_user_authorization=True,user_quote='SYNTHETIC UNIT INPUT ONLY, NO HUMAN GPU GRANT',
        authorizes_S_collection=True,authorizes_Q1_collection=False,authorizes_retry=False,
        whole_quote_frozen_by_this_approval=True,engineering_allowances_accepted_for_this_card=True,
        run_id=RUN,host=host,scope_counts=COUNTS,whole_GPUh=LIMITS[host],scope_sha256=sha(stage/SCOPE),
        physical_scope_sha256=physical['physical_scope_sha256'],execution_identity_sha256=IDENTITY_SHA,
        S_resource_contract_sha256=RESOURCE_SHA,source_revision=reg['source_revision'],
        registration_sha256=sha(stage/'registration.json'),quote_sha256=sha(stage/QUOTES[host]),
        CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),asset_proof_sha256=sha(stage/'S-asset-verification.json'),
        storage_contract_sha256=sha(stage/'history104-storage.json'),
        gpu_uuid=OTHER_A6000 if host=='two_card' else 'GPU-ADA-SYNTHETIC',launch_id='CPU_ONLY_S_NO_GPU_LAUNCH')
    atomic_json(stage/'pg-GPU-authorization.json',auth)
    job=dict(job_id=RUN,status='RESERVED_OR_RUNNING',billed_limit_GPUh=LIMITS[host],
        forecast_GPUh=quote['forecast_complete_GPUh'],authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        **{key:auth[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256',
            'physical_scope_sha256','scope_counts','registration_sha256')})
    atomic_json(stage/'central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=job))
    atomic_json(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json')))
    return stage,auth,reg,job


def validate_fixture(project,stage):
    with patch.object(execution,'assets_current',return_value=True):return execution.validate(project,stage)


class SourceAndAuthorityTests(unittest.TestCase):
    def test_both_registered_hosts_keep_full_ten_role_108_row_scope(self):
        for host in LIMITS:
            with self.subTest(host=host),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,auth,_,_=fixture(project,host)
                bundle,_,_=validate_fixture(project,stage)
                self.assertEqual(bundle['physical']['counts'],COUNTS)
                self.assertEqual(len(bundle['physical']['physical_slots']),10)
                self.assertEqual(auth['whole_GPUh'],LIMITS[host])

    def test_source_validator_imports_and_runs_with_Torch_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,_,_=fixture(project)
            code=("import sys;sys.path.insert(0,"+repr(str(ROOT/'src'))+");sys.modules['torch']=None;"
                "from wcomr.sq_s_execution_r2 import validate_source;validate_source("+repr(str(project))+","+repr(str(stage))+")")
            subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,check=True)

    def test_changed_model_entry_source_cannot_be_rebound_by_old_CPU_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,_,_=fixture(project)
            (stage/'src/wcomr/sq_s_model_entry_r1.py').write_text('# changed entry\n')
            with self.assertRaisesRegex(ValueError,'Staged S source differs'):validate_fixture(project,stage)

    def test_old_nine_new_plus_reused_OFF_is_not_this_alternative(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,reg,_=fixture(project)
            target=stage/PHYSICAL['two_card']
            target.write_bytes((ROOT/'plans/cara_next_stage_20261028/sq/S_PHYSICAL_TWO_CARD_R1.json').read_bytes())
            reg['payload_sha256'][PHYSICAL['two_card']]=sha(target);atomic_json(stage/'registration.json',reg)
            with self.assertRaisesRegex(ValueError,'ten-role'):execution.validate_source(project,stage)

    def test_missing_original_runtime_identity_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,reg,_=fixture(project)
            reg['runtime_source_sha256']=dict(reg['runtime_source_sha256']);reg['runtime_source_sha256'].pop('cosmos_predict2/config.py')
            atomic_json(stage/'registration.json',reg)
            with self.assertRaisesRegex(ValueError,'incomplete'):execution.validate_source(project,stage)

    def test_incomplete_candidate_history_support_is_refused_before_GPU_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,reg,_=fixture(project)
            proof=execution.read(stage/HISTORY);proof['supported_C_histories'].pop();atomic_json(stage/HISTORY,proof)
            reg['payload_sha256'][HISTORY]=sha(stage/HISTORY);atomic_json(stage/'registration.json',reg)
            with self.assertRaisesRegex(ValueError,'history-slot support'):execution.validate_source(project,stage)

    def refuse_auth(self,mutate):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,_,_=fixture(project);mutate(auth)
            atomic_json(stage/'pg-GPU-authorization.json',auth)
            with self.assertRaises(ValueError):validate_fixture(project,stage)

    def test_Q1_grant_cannot_load_S(self):
        self.refuse_auth(lambda auth:auth.update(authorizes_S_collection=False,authorizes_Q1_collection=True,whole_GPUh=1.25))

    def test_partial_S_scope_is_refused(self):
        self.refuse_auth(lambda auth:auth.update(scope_counts=dict(COUNTS,moment_rows=12)))

    def test_wrong_A6000_UUID_is_refused(self):self.refuse_auth(lambda auth:auth.update(gpu_uuid='GPU-FOREIGN'))
    def test_retry_grant_is_refused(self):self.refuse_auth(lambda auth:auth.update(authorizes_retry=True))
    def test_unfrozen_complete_quote_is_refused(self):
        self.refuse_auth(lambda auth:auth.update(whole_quote_frozen_by_this_approval=False))

    def test_source_exact_native_CPU_and_parser_proofs_are_required(self):
        for changes in (dict(host='four_card'),dict(skipped=1),dict(native_parser_accepted=False),
            dict(full_S_entry_CPU_accepted=False),dict(actual_platform=dict(system='Darwin'))):
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,auth,_,_=fixture(project)
                proof=execution.read(stage/'execution-CPU-proof.json');proof.update(changes)
                atomic_json(stage/'execution-CPU-proof.json',proof)
                auth['CPU_proof_sha256']=sha(stage/'execution-CPU-proof.json');atomic_json(stage/'pg-GPU-authorization.json',auth)
                with self.assertRaisesRegex(ValueError,'CPU proof'):validate_fixture(project,stage)


def financial_fixture(auth):
    common={key:auth[key] for key in ('run_id','launch_id','host','gpu_uuid','source_revision','scope_sha256')}
    guardian=dict(common,status='SQ_S_HOST_GUARDIAN_TERMINAL',billing_clock_owner='HOST_GUARDIAN',
        started_monotonic=10.,ended_monotonic=110.,started_unix=1000.,ended_unix=1100.,billing_sha256='b'*64,
        mode_restoration=dict(restored=True),container_terminal_witness=dict(complete=True,kind='NO_CONTAINER_DISPATCH'))
    billing=dict(common,status='SQ_S_ORIGINAL_WALL_BILL',billing_clock_owner='HOST_GUARDIAN',
        started_monotonic=10.,ended_monotonic=110.,started_unix=1000.,ended_unix=1100.,wall_seconds=100.,
        actual_GPUh=100/3600,billed_limit_GPUh=auth['whole_GPUh'],wall_interval_complete=True,
        supervisor_bill_is_diagnostic_only=True)
    release=dict(common,billing_sha256='b'*64,GPU_released=True,original_process_exited=True,
        allocation_release_accepted=True,mode_restoration=guardian['mode_restoration'],
        container_terminal_witness=guardian['container_terminal_witness'],cost_settled=False,authorizes_retry=False,
        technical_accepted=False)
    return billing,release,guardian


class EnvelopeAndBillTests(unittest.TestCase):
    def test_halfway_and_terminal_checks_use_actual_guardian_start_without_creating_a_scheduler(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);_,auth,_,_=fixture(project)
            guardian=dict(auth,billing_clock_owner='HOST_GUARDIAN',started_unix=10000.,started_monotonic=1234.)
            schedule=execution.make_check_schedule(auth,guardian,dict(host='two_card',forecast_complete_GPUh=2.),
                dict(CPU_post_wall_seconds_max=3600))
            self.assertEqual(schedule['halfway_unix'],13600.)
            self.assertEqual(schedule['expected_GPU_terminal_unix'],17200.)
            self.assertEqual(schedule['expected_terminal_unix'],20800.)
            self.assertEqual(schedule['hard_GPU_terminal_unix'],60400.)
            self.assertFalse(schedule['scheduler_created']);self.assertFalse(schedule['authorizes_retry'])
            guardian['launch_id']='FOREIGN'
            with self.assertRaisesRegex(ValueError,'guardian identity'):
                execution.make_check_schedule(auth,guardian,dict(host='two_card',forecast_complete_GPUh=2.),
                    dict(CPU_post_wall_seconds_max=3600))

    def test_either_host_has_one_complete_envelope_and_failure_cost_is_settled(self):
        for host in LIMITS:
            with self.subTest(host=host),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,auth,_,job=fixture(project,host)
                ledger(project);pool=execution.Pool(project)
                gpu=dict(uuid=auth['gpu_uuid'],name='NVIDIA RTX A6000' if host=='two_card' else 'NVIDIA RTX 6000 Ada',
                    compute_cap='8.6' if host=='two_card' else '8.9',pids=[],utilization_percent=0,
                    memory_used_mib=0,temperature_C=42.,unix=time.time())
                before=pool.read();pool.reserve(job,gpu)
                self.assertEqual(pool.read()['reserved_gpu_hours'],16.5+LIMITS[host])
                with self.assertRaisesRegex(ValueError,'recover only'):pool.reserve(job,gpu)
                bill,release,guardian=financial_fixture(auth)
                settled=execution.settle_central(pool,auth,bill,release,guardian,billing_sha256='b'*64)
                self.assertEqual(settled['actual_GPUh'],100/3600)
                self.assertEqual(pool.read()['reserved_gpu_hours'],16.5)
                self.assertFalse(settled['scientific_acceptance_implied'])
                self.assertEqual({k:v for k,v in pool.read()['jobs'].items() if k!=RUN},before['jobs'])

    def test_same_host_busy_refuses_even_when_another_physical_card_is_idle(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);_,auth,_,job=fixture(project);ledger(project);pool=execution.Pool(project)
            value=pool.read();value['jobs']['BUSY']=dict(job_id='BUSY',status='RESERVED_OR_RUNNING',
                host='two_card',gpu_uuid='GPU-OTHER-BUSY',billed_limit_GPUh=1.)
            value.update(pool.accounting(value));atomic_json(pool.path,value);original=pool.path.read_bytes()
            gpu=dict(uuid=auth['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',pids=[],
                utilization_percent=0,memory_used_mib=0,temperature_C=42.,unix=time.time())
            with self.assertRaisesRegex(ValueError,'already has'):pool.reserve(job,gpu)
            self.assertEqual(pool.path.read_bytes(),original)

    def test_stale_or_hot_idle_snapshot_cannot_reserve(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);_,auth,_,job=fixture(project);pool=ledger(project);before=pool.path.read_bytes()
            gpu=dict(uuid=auth['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',pids=[],
                utilization_percent=0,memory_used_mib=0,temperature_C=70.,unix=time.time())
            with self.assertRaisesRegex(ValueError,'Fresh selected'):pool.reserve(job,gpu)
            gpu.update(temperature_C=42.,unix=time.time()-61)
            with self.assertRaisesRegex(ValueError,'Fresh selected'):pool.reserve(job,gpu)
            self.assertEqual(pool.path.read_bytes(),before)

    def test_incomplete_release_or_inner_bill_never_settles(self):
        for mutate in (lambda b,r,g:r.update(allocation_release_accepted=False),
            lambda b,r,g:g['mode_restoration'].update(restored=False),
            lambda b,r,g:b.update(billing_clock_owner='SUPERVISOR_DIAGNOSTIC'),
            lambda b,r,g:b.update(wall_seconds=1.),lambda b,r,g:b.update(status='SQ_Q1_ORIGINAL_WALL_BILL')):
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);_,auth,_,_=fixture(project)
                billing,release,guardian=financial_fixture(auth);mutate(billing,release,guardian)
                with self.assertRaises(ValueError):
                    execution.check_host_bill(auth,billing,release,guardian,billing_sha256='b'*64)


if __name__=='__main__':unittest.main()
