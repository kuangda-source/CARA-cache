"""Receipt parser and post-release selection controls using tiny CPU tensors."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_sq_q1_execution_r1 import (ROOT,authority_fixture,ledger,gpu,raw_fixture,numeric_failure)
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.sq_q1_spec_r1 import RUN,SCOPE,PROFILE,QUOTES
from wcomr.sq_q1_terminal_r1 import (settle_original,analyse_released,technical_terminal)


def captured(value):
    raw=json.dumps(value,indent=2,allow_nan=False)+'\n';data=raw.encode()
    return dict(exists=True,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),raw_utf8=raw)


def fixture(project,failed_numeric=False,stage_name='Q1_SYNTHETIC_AUTHORITY_CONTROL_ONLY'):
    stage,authority,registration,job=authority_fixture(project,stage_name=stage_name)
    pool=ledger(project);envelope=pool.reserve(job,gpu())
    reservation=dict(central_ledger_host='four_card',new_reservation=True,job=envelope['jobs'][RUN])
    atomic_json(stage/'central-reservation.json',reservation)
    atomic_json(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json')))
    scope=json.loads((stage/SCOPE).read_text())
    launch=dict(authority,stage=str(stage),container=stage.name+'-gpu',authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        guardian_identity=dict(pid=123,start_ticks=456))
    identity={key:authority[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')}
    collection=copy.deepcopy(raw_fixture())
    if failed_numeric:collection=numeric_failure(collection)
    collection.update(identity)
    from wcomr.sq_q1_execution_r1 import check_collection
    classification=check_collection(scope,collection)
    bill=dict(identity,status='SQ_Q1_ORIGINAL_WALL_BILL',wall_seconds=10.,actual_GPUh=10/3600,
        billed_limit_GPUh=authority['whole_GPUh'])
    runner=dict(pid=321,start_ticks=654,uid=1000)
    idle=dict(gpu_uuid=authority['gpu_uuid'],compute_mode='Exclusive_Process',compute_apps=[],
        mps_processes=[],observed_unix=100.)
    active=dict(idle,compute_apps=[dict(runner,gpu_uuid=authority['gpu_uuid'],memory_MiB=1)])
    supervisor=dict(identity,child_exit_code=0,exclusive_monitor_accepted=True,
        collection_sha256=captured(collection)['sha256'],collection_classification=classification,
        child_identity=runner,supervisor_identity=dict(pid=125,start_ticks=458),observations=2)
    guardian=dict(run_id=RUN,launch_id=authority['launch_id'],gpu_uuid=authority['gpu_uuid'],
        source_revision=authority['source_revision'],identity=launch['guardian_identity'],
        status='SQ_Q1_HOST_GUARDIAN_TERMINAL',container_exit_code=0,
        container_cli_identity=dict(pid=124,start_ticks=457),
        mode_restoration=dict(restored=True),mode_admission=dict(verified_snapshot=idle))
    pending=dict(identity,billing_sha256=captured(bill)['sha256'],GPU_released=True,
        original_process_exited=True,technical_accepted=True,cost_settled=False,
        collection_sha256=captured(collection)['sha256'],collection_classification=classification,final_snapshot=idle)
    values=dict(launch=launch,registration=registration,authorization=authority,central_reservation=reservation,
        launch_binding=json.loads((stage/'launch-binding.json').read_text()),
        CPU_acceptance=json.loads((stage/'execution-CPU-proof.json').read_text()),scope=scope,
        storage=json.loads((stage/'history104-storage.json').read_text()),
        profile=json.loads((stage/PROFILE).read_text()),quote=json.loads((stage/QUOTES['two_card']).read_text()),
        billing=bill,pending_release=pending,supervisor=supervisor,guardian=guardian,collection=collection,
        ready=dict(identity=runner,GPU_context_held=True,source_revision=authority['source_revision']),
        grant=dict(runner=runner,gpu_uuid=authority['gpu_uuid'],source_revision=authority['source_revision']))
    rows=[]
    for elapsed,granted,snapshot in ((1.,False,idle),(3.,True,active)):
        rows.append(dict(monotonic_elapsed=elapsed,context_granted=granted,snapshot=snapshot,
            thermal={'temperature.gpu':'50'},runner=runner,run_id=RUN,launch_id=authority['launch_id']))
    raw=''.join(json.dumps(row)+'\n' for row in rows)
    capture=dict(status='SQ_Q1_TERMINAL_CAPTURE_R1',files={key:captured(value) for key,value in values.items()},
        original_live_handles={key:False for key in ('guardian','container_cli','supervisor','runner')},
        own_UUID_lock_free=True,mode_owner_lock_free=True,
        payload_actual_sha256=registration['payload_sha256'],runtime_actual_sha256=registration['runtime_source_sha256'],
        terminal_validator_sha256=registration['payload_sha256']['src/wcomr/sq_q1_terminal_r1.py'],
        monitor_raw_utf8=raw,monitor_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        container=dict(state=dict(Status='exited',Running=False,ExitCode=0,OOMKilled=False),
            image='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
            manifest_sha256=authority['registration_sha256'],device_requests=[dict(DeviceIDs=[authority['gpu_uuid']])],
            readonly_root=True,pid_mode='host',network='none',cpus=2,memory_GiB=16,memory_swap_GiB=16,cpuset_cpus='24,25'))
    for key,name in (('scope',SCOPE),('profile',PROFILE),('quote',QUOTES['two_card'])):
        raw=(stage/name).read_bytes()
        capture['files'][key]=dict(exists=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                                  raw_utf8=raw.decode())
    # All wrappers are byte-identical to the actual staged synthetic receipts.
    return capture,scope,pool


class TerminalTests(unittest.TestCase):
    def test_original_bill_settles_once_before_complete_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            capture,scope,pool=fixture(Path(directory));before=pool.read()
            settlement=settle_original(pool,capture,scope)
            self.assertEqual(pool.read()['reserved_gpu_hours'],16.5)
            self.assertEqual(pool.read()['jobs']['original-unknown-0'],before['jobs']['original-unknown-0'])
            repeated=settle_original(pool,capture,scope)
            self.assertEqual(settlement['job'],repeated['job'])
            result=analyse_released(capture,scope,settlement)
            self.assertEqual(len(result['codec_selection']['selections']),8)
            self.assertFalse(result['endpoint_benefit_established'])

    def test_numeric_failure_is_billed_and_never_selects_codecs(self):
        with tempfile.TemporaryDirectory() as directory:
            capture,scope,pool=fixture(Path(directory),True)
            settlement=settle_original(pool,capture,scope)
            with patch('wcomr.sq_q1_readout_r1.select_shared_codecs',side_effect=AssertionError('Must not select')):
                result=analyse_released(capture,scope,settlement)
            self.assertIsNone(result['codec_selection'])
            self.assertEqual(result['status'],'Q1_NUMERIC_DIAGNOSTIC_TERMINAL_NO_CODEC_SELECTION')

    def test_tampered_bill_live_runner_and_unreleased_mode_cannot_settle(self):
        for case in ('bill','runner','mode'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                capture,scope,pool=fixture(Path(directory));before=pool.path.read_bytes()
                if case=='bill':capture['files']['billing']['raw_utf8']+=' '
                if case=='runner':capture['original_live_handles']['runner']=True
                if case=='mode':
                    value=json.loads(capture['files']['guardian']['raw_utf8'])
                    value['mode_restoration']['restored']=False;capture['files']['guardian']=captured(value)
                with self.assertRaises(ValueError):settle_original(pool,capture,scope)
                self.assertEqual(pool.path.read_bytes(),before)

    def test_technical_failure_keeps_charge_but_cannot_reach_analysis(self):
        for case in ('exit','thermal','foreign_context','collection','settlement'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                capture,scope,pool=fixture(Path(directory))
                settlement=settle_original(pool,capture,scope)
                if case=='exit':capture['container']['state']['ExitCode']=7
                elif case in ('thermal','foreign_context'):
                    rows=[json.loads(line) for line in capture['monitor_raw_utf8'].splitlines()]
                    if case=='thermal':rows[-1]['thermal']['temperature.gpu']='90'
                    else:rows[-1]['snapshot']['compute_apps'][0]['pid']+=1
                    raw=''.join(json.dumps(row)+'\n' for row in rows)
                    capture.update(monitor_raw_utf8=raw,monitor_sha256=hashlib.sha256(raw.encode()).hexdigest())
                elif case=='collection':capture['files']['collection']['raw_utf8']+=' '
                else:settlement['job']['billing_sha256']='f'*64
                with patch('wcomr.sq_q1_readout_r1.select_shared_codecs',side_effect=AssertionError('Must not select')):
                    with self.assertRaises(ValueError):analyse_released(capture,scope,settlement)


if __name__=='__main__':unittest.main()
