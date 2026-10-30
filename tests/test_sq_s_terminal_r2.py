"""Synthetic complete GPU headers exercise native capture and finance only.

No fixture here is real CUDA/model evidence. PIDs, containers, monitor GPU
observations, native CPU grants and precision headers are explicitly stand-ins.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from test_sq_s_execution_r2 import fixture as entry_fixture,financial_fixture,ledger,script
from test_sq_s_data_terminal_r2 import fixture as data_fixture
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.sq_s_data_terminal_r2 import check_result
from wcomr import sq_s_capture_r2 as capture_module
from wcomr import sq_s_terminal_r2 as terminal
from wcomr.sq_s_monitor_terminal_r2 import check_monitor
from wcomr.sq_gpu_allocation_r1 import SystemOperations,container_record
from wcomr.sq_s_execution_r2 import read,Pool
from wcomr.sq_s_spec_r2 import RUN,SCOPE,PHYSICAL,IDENTITY_SHA,RESOURCE_SHA,IDENTITY


def observation(uuid,runner=None):
    return dict(gpu_uuid=uuid,observed_unix=1000.,compute_mode='Exclusive_Process',
        compute_apps=[dict(runner)] if runner else [],mps_processes=[],CPU_SYNTHETIC=True)


def sample(launch,runner,elapsed,start=12.,active=True):
    return dict(run_id=RUN,launch_id=launch['launch_id'],runner=runner,
        snapshot=observation(launch['gpu_uuid'],runner if active else None),context_granted=active,
        monotonic_elapsed=elapsed,thermal_monotonic=start+elapsed,thermal={'temperature.gpu':'42'})


def fixture(project):
    stage,auth,reg,job=entry_fixture(project);output=project/'outputs'/RUN;output.mkdir(parents=True)
    common={key:auth[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')}
    guardian_id=dict(pid=101,start_ticks=1,uid=os.getuid());runner=dict(pid=104,start_ticks=4,uid=os.getuid())
    launch=dict(auth,stage=str(stage),container=stage.name+'-gpu',guardian_identity=guardian_id,
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'))
    atomic_json(stage/'GPU-launch.json',launch)
    state=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False)
    container=dict(Id='CPU_SYNTHETIC_NOT_A_REAL_CONTAINER',State=state,Image=terminal.IMAGE,
        Config=dict(Labels={'wcomr.manifest':auth['registration_sha256']}),
        HostConfig=dict(DeviceRequests=[dict(DeviceIDs=[auth['gpu_uuid']])],ReadonlyRootfs=True,
            PidMode='host',NetworkMode='none',NanoCpus=2_000_000_000,Memory=40*2**30,
            MemorySwap=40*2**30,CpusetCpus='24,25'))
    billing,allocation,guardian=financial_fixture(auth);atomic_json(output/'S-billing.json',billing)
    bill_sha=sha(output/'S-billing.json')
    for key in ('GPU_released','original_process_exited','technical_accepted'):allocation.pop(key)
    witness=dict(complete=True,kind='BOUND_CONTAINER_TERMINAL',container_id=container['Id'],
        container=container_record(container),manifest_sha256=auth['registration_sha256'])
    guardian.update(identity=guardian_id,billing_sha256=bill_sha,container_dispatch_state='STARTED',mode_owner_fenced=True,
        container_cli_identity=dict(pid=102,start_ticks=2),container_terminal_witness=witness,container_exit_code=0,
        mode_admission=dict(verified_snapshot=observation(auth['gpu_uuid'])))
    allocation.update(billing_sha256=bill_sha,container_terminal_witness=witness)
    atomic_json(output/'S-allocation-release.json',allocation);atomic_json(stage/'pg-host-guardian.json',guardian)
    collection,*_=data_fixture();upper=read(stage/SCOPE);physical=read(stage/PHYSICAL[auth['host']]);identity=read(stage/IDENTITY)
    collection.update(common,CPU_fixture=False,actual_CUDA=True,upper_scope_sha256=upper['scope_sha256'],
        physical_scope_sha256=physical['physical_scope_sha256'],execution_identity_sha256=IDENTITY_SHA,
        resource_contract_sha256=RESOURCE_SHA,SYNTHETIC_GPU_HEADERS_NOT_ACTUAL_CUDA=True)
    collection['matrix']['scope_sha256']=upper['scope_sha256'];collection['matrix']['physical_execution']['scope']=physical
    for row in collection['resource_checks']:row['contract_sha256']=RESOURCE_SHA
    model=collection['model_entry'];model.update(CPU_fixture=False,execution_identity_sha256=IDENTITY_SHA,
        physical_scope_sha256=physical['physical_scope_sha256'])
    model['precision'].update(model_precision='torch.bfloat16',blocks=28,parameter_tensors=569,
        parameter_dtypes={'torch.bfloat16':569},parameter_devices={'cuda:0':569})
    for record in collection['matrix']['rows']:
        value=record['result'];value['CPU_fixture']=False
        for tensor in value['guided']+[value['final_latent']]:tensor['shape']=identity['expected_real_shape']
        value['pre_encoding_RGB'].update(shape=[93,432,768,3],dtype='uint8')
        value['encoded_video']['path']=str(output/'paths'/record['slot']['id']/'SYNTHETIC.mp4')
    classification=check_result(collection,upper,physical,identity_sha256=IDENTITY_SHA,resource_contract_sha256=RESOURCE_SHA,
        expected_shape=identity['expected_real_shape'],new_output_root=str(output/'paths'))
    atomic_json(output/'S-collection.json',collection)
    inner=dict(common,billing_clock_owner='SUPERVISOR_DIAGNOSTIC',diagnostic_only=True,chargeable=False,
        started_monotonic=12.,ended_monotonic=108.,wall_seconds=96.,allocation_started_monotonic=10.)
    atomic_json(output/'S-supervisor-billing-diagnostic.json',inner)
    supervisor=dict(common,supervisor_identity=dict(pid=103,start_ticks=3),child_identity=runner,
        allocation_started_monotonic=10.,started_monotonic=12.,ended_monotonic=108.,diagnostic_wall_seconds=96.,
        observations=6,child_exit_code=0,exclusive_monitor_accepted=True,
        collection_sha256=sha(output/'S-collection.json'),collection_classification=classification,
        supervisor_billing_sha256=sha(output/'S-supervisor-billing-diagnostic.json'))
    atomic_json(output/'S-supervisor.json',supervisor)
    diagnostic=dict(common,diagnostic_only=True,technical_accepted=True,GPU_released=True,original_process_exited=True,
        collection_sha256=sha(output/'S-collection.json'),collection_classification=classification,
        final_snapshot=observation(auth['gpu_uuid']),billing_sha256=sha(output/'S-supervisor-billing-diagnostic.json'))
    atomic_json(output/'S-supervisor-release-diagnostic.json',diagnostic)
    ready=dict(identity=runner,GPU_context_held=True,source_revision=auth['source_revision'])
    grant=dict(runner=runner,gpu_uuid=auth['gpu_uuid'],source_revision=auth['source_revision'])
    atomic_json(stage/'pg-runner-context-ready.json',ready);atomic_json(stage/'pg-runner-context-granted.json',grant)
    with (output/'S-exclusive-monitor.jsonl').open('w') as stream:
        for elapsed in (1.,20.,40.,60.,80.,95.):stream.write(json.dumps(sample(launch,runner,elapsed,active=elapsed>1))+'\n')
    for suffix in ('.lock','.mode-owner.lock'):
        path=project/'.sync/gpu-locks'/(auth['gpu_uuid']+suffix);path.parent.mkdir(exist_ok=True);path.touch()
    from test_sq_gpu_allocation_r1 import Storage
    script('cara_sq_s_guardian_r2').pending_release(stage,Storage(output))
    def capture():
        with patch.object(capture_module,'same_live_process',return_value=False),\
                patch.object(SystemOperations,'inspect_container',return_value=container):
            return capture_module.capture(project,stage,sha(stage/'GPU-launch.json'))
    return stage,auth,job,capture,container


class TerminalTests(unittest.TestCase):
    def test_original_capture_technical_data_and_central_settlement_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,job,capture,_=fixture(project);value=capture();scope=read(stage/SCOPE)
            self.assertEqual(value['status'],'SQ_S_TERMINAL_CAPTURE_R2')
            self.assertFalse(value['monitor_witness']['raw_monitor_transferred'])
            technical=terminal.technical_terminal(value,scope)
            self.assertEqual(technical['same_state_rows'],108);self.assertFalse(technical['scientific_S_effect_established'])
            pool=ledger(project);gpu=dict(uuid=auth['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',
                pids=[],utilization_percent=0,memory_used_mib=0,temperature_C=42.,unix=time.time())
            pool.reserve(job,gpu);settled=terminal.settle_original(pool,value,scope)
            self.assertEqual(terminal.audit_settlement(value,scope,settled)['actual_GPUh'],100/3600)
            self.assertEqual(pool.read()['reserved_gpu_hours'],16.5)

    def test_missing_collection_cannot_be_accepted_but_original_bill_can_settle(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,auth,job,capture,_=fixture(project)
            (project/'outputs'/RUN/'S-collection.json').unlink();value=capture();scope=read(stage/SCOPE)
            with self.assertRaises((ValueError,KeyError)):terminal.technical_terminal(value,scope)
            pool=ledger(project);gpu=dict(uuid=auth['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',
                pids=[],utilization_percent=0,memory_used_mib=0,temperature_C=42.,unix=time.time())
            pool.reserve(job,gpu);settled=terminal.settle_original(pool,value,scope)
            self.assertTrue(settled['cost_settled']);self.assertFalse(settled['scientific_acceptance_implied'])

    def test_live_capture_returns_only_operational_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,_,_,container=fixture(project)
            container['State'].update(Running=True,Pid=104,Status='running')
            atomic_json(project/'outputs'/RUN/'S-health.json',dict(status='RUNNING',matrix_health=dict(
                attempted_new_role_ids=['r1','r2'],S_rows=['PRIVATE_PARTIAL_SCIENCE'])))
            with patch.object(capture_module,'same_live_process',return_value=True),\
                    patch.object(SystemOperations,'inspect_container',return_value=container):
                value=capture_module.capture(project,stage,sha(stage/'GPU-launch.json'))
            self.assertFalse(value['scientific_rows_returned']);self.assertNotIn('files',value)
            self.assertEqual(value['health']['attempted_new_paths'],2)
            self.assertNotIn('PRIVATE_PARTIAL_SCIENCE',json.dumps(value))

    def test_unknown_original_container_cannot_form_a_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage,_,_,_,_=fixture(project)
            with patch.object(capture_module,'same_live_process',return_value=False),\
                    patch.object(SystemOperations,'inspect_container',side_effect=RuntimeError('CPU UNKNOWN')):
                value=capture_module.capture(project,stage,sha(stage/'GPU-launch.json'))
            self.assertEqual(value['status'],'SQ_S_ORIGINAL_CONTAINER_UNKNOWN_RECOVER_ONLY')
            self.assertFalse(value['scientific_rows_returned'])

    def test_changed_or_foreign_monitor_witness_cannot_accept_technical_data(self):
        for case in ('identity','temperature','grant'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage,_,_,capture,_=fixture(project);value=capture()
                if case=='identity':value['monitor_witness']['launch_id']='FOREIGN'
                elif case=='temperature':value['monitor_witness']['max_temperature_C']=90.
                else:value['monitor_witness']['input_sha256']['grant']='f'*64
                with self.assertRaisesRegex(ValueError,'streamed S monitor'):terminal.technical_terminal(value,read(stage/SCOPE))


class MonitorTests(unittest.TestCase):
    def exercise(self,path,rows):
        runner=dict(pid=11,start_ticks=22,uid=33)
        launch=dict(run_id=RUN,gpu_uuid='GPU_CPU_ONLY',launch_id='CPU_LONG_MONITOR',source_revision='CPU_ONLY')
        ready=dict(identity=runner,GPU_context_held=True,source_revision='CPU_ONLY')
        grant=dict(runner=runner,gpu_uuid='GPU_CPU_ONLY',source_revision='CPU_ONLY')
        with path.open('w') as stream:
            for row in rows(launch,runner):stream.write(json.dumps(row)+'\n')
        return launch,dict(child_identity=runner,observations=300),dict(started_monotonic=12.,wall_seconds=601.),ready,grant

    def test_monitor_over_old16MiB_limit_is_streamed_without_raw_transfer(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'CPU-monitor.jsonl'
            def rows(launch,runner):
                for i in range(1,301):yield dict(sample(launch,runner,2.*i),CPU_padding='x'*60000)
            args=self.exercise(path,rows)
            self.assertGreater(path.stat().st_size,16*2**20)
            value=check_monitor(path,*args,maximum_bytes=512*2**20)
            self.assertEqual(value['samples'],300);self.assertFalse(value['raw_monitor_transferred'])

    def test_gap_stale_thermal_foreign_context_and_hot_sample_are_refused(self):
        for case in ('gap','stale','foreign','hot','incomplete'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'CPU-monitor.jsonl'
                def rows(launch,runner):
                    for i in range(1,301):
                        row=sample(launch,runner,2.*i)
                        if i==1:
                            if case=='gap':row['monotonic_elapsed']=60.
                            if case=='stale':row['thermal_monotonic']=-100.
                            if case=='foreign':row['snapshot']['compute_apps'][0]['pid']=999
                            if case=='hot':row['thermal']['temperature.gpu']='90'
                        yield row
                args=self.exercise(path,rows)
                if case=='incomplete':path.write_bytes(path.read_bytes()[:-1])
                with self.assertRaises(ValueError):check_monitor(path,*args,maximum_bytes=512*2**20)


if __name__=='__main__':unittest.main()
