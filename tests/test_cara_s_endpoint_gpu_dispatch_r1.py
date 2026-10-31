"""Temporary metadata and injected process controls; no actual GPU admission."""
import copy
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import tempfile
from test_cara_s_endpoint_runner_binding_r1 import Fixture
from wcomr import cara_budget_dispatch_r1 as admission
from wcomr import cara_s_endpoint_gpu_dispatch_r1 as dispatch
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.wc73_execution_r1 import Pool,hold
from wcomr.cara_budget_search_journal_r1 import read_record
import cara_s_endpoint_host_entry_r1 as guardian_entry


class DispatchTests(unittest.TestCase):
    def write(self,name,value):self.f.write(name,value)

    def write_all(self):
        self.f.write_all();self.launch=self.f.launch

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(self.temp.name,endpoint7=getattr(self,'endpoint7',False))
        for key in ('project','stage','auth','launch','reg','proof','quote','card'):
            setattr(self,key,getattr(self.f,key))
        for name in dispatch.REQUIRED:
            target=self.stage/name;target.parent.mkdir(parents=True,exist_ok=True)
            source=ROOT/('reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json' if name==dispatch.ORIGINAL_SCORES else name)
            target.write_bytes(source.read_bytes());self.reg['payload_sha256'][name]=sha(target)
        output=self.project/'outputs'/self.auth['run_id'];journal=self.project/'reports/fixture.journal'
        self.storage=SimpleNamespace(output=output,journal=SimpleNamespace(path=journal),check=lambda:None,
            config=dict(output_mount=str(output),image_path=str(self.project/'image.ext4'),image_bytes=64*2**30,
                journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=self.f.profile['storage']['minimum_output_free_bytes'],
                minimum_host_free_bytes=self.f.profile['storage']['minimum_host_free_bytes'],minimum_free_inodes=1024))
        self.identity=dict(pid=333,start_ticks=100,host_view=dict(boot_id='a'*36,pid_namespace_inode=9),
            original_command_sha256='c'*64)
        self.refresh()

    def refresh(self):
        self.write_all();(self.stage/'GPU-launch.json').unlink()
        self.job=read_record(self.stage/'central-reservation.json')['job']
        packet=read_record(ROOT/'reports/cara_fast_B36_actual_central_reservation_r1_20261029.json')
        before=copy.deepcopy(packet['central_envelope']['central_before'])
        self.old_keys=[k for k,v in before['jobs'].items() if hold(v)]
        before.update(Pool.accounting(before));after=copy.deepcopy(before)
        after['jobs'][self.auth['run_id']]=self.job;after.update(Pool.accounting(after))
        self.write('central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,
            job=self.job,central_before=before,central_after=after))
        self.snapshot=dict(central_ledger_host='four_card',observed_unix=time.time(),ledger=after)

    def invoke_dispatch(self,spawn=None):
        child=SimpleNamespace(pid=333,stdin=io.BytesIO())
        with patch.object(dispatch,'fresh_resources',return_value=(self.storage,{'CPU_metadata_fixture':True})),\
             patch.object(dispatch,'bind_original_process',return_value=self.identity),\
             patch.object(dispatch.subprocess,'Popen',side_effect=spawn or (lambda *a,**k:child)) as popen:
            result=dispatch.dispatch(self.project,self.stage,self.snapshot,'private-fixture-credential')
        return result,popen

    def publish(self,identity=None):
        with patch.object(dispatch,'bind_original_process',return_value=identity or self.identity),\
             patch.object(dispatch,'storage_for',return_value=self.storage):
            return dispatch.publish_launch(self.project,self.stage)

    def test_prelaunch_requires_current_two_card_policy_and_refuses_four_card(self):
        self.assertEqual(dispatch.ready_inputs(self.project,self.stage)[4]['host'],'two_card')
        self.assertEqual(dispatch.central_binding(self.stage,self.auth,self.snapshot)['job']['host'],'two_card')
        self.assertFalse((self.stage/'GPU-launch.json').exists())
        self.auth['execution_host_policy_sha256']='0'*64;self.refresh()
        with self.assertRaisesRegex(ValueError,'two-card policy'):dispatch.ready_inputs(self.project,self.stage)
        self.auth['execution_host_policy_sha256']=admission.POLICY_SHA256
        self.auth['host']=self.launch['host']=self.reg['host']=self.proof['host']='four_card'
        self.quote['host_quotes']['four_card']=self.quote['host_quotes']['two_card'];self.refresh()
        with self.assertRaisesRegex(ValueError,'two-card policy'):dispatch.ready_inputs(self.project,self.stage)

    def test_resource_gate_checks_selected_GPU_MPS_memory_affinity_and_exact_absence(self):
        from wcomr import cara_budget_lifecycle_capture_r1 as capture
        profile=read_record(self.stage/dispatch.PROFILE)
        self.write('fresh-admission.json',dict(registration_sha256=sha(self.stage/'registration.json'),
            authorization_sha256=sha(self.stage/'GPU-authorization.json'),asset_spec_sha256=sha(self.stage/dispatch.ASSETS),assets=[]))
        gpu=dict(uuid=self.auth['gpu_uuid'],compute_cap='8.6',utilization_percent=0,pids=[],memory_used_mib=0,
            temperature_C=30,compute_mode='Default')
        observation=dict(gpu_uuid=self.auth['gpu_uuid'],compute_apps=[],mps_processes=[])
        def check(gpu_override=None,hardware=None,memory=48,affinity=(24,25),container=None):
            with patch.object(admission,'storage_for',return_value=self.storage),\
                 patch.object(admission,'assets_unchanged'),patch.object(admission,'english_resources'),\
                 patch.object(admission.subprocess,'check_output',return_value=json.dumps([{'Id':self.reg['container_image']}])),\
                 patch.object(capture,'inspect_container',return_value=container),\
                 patch.object(admission,'selected_gpu',return_value=gpu_override or gpu),\
                 patch.object(admission,'observe',return_value=hardware or observation),\
                 patch.object(Path,'read_text',return_value='MemAvailable: '+str(memory*2**20)+' kB\n'),\
                 patch.object(os,'sched_getaffinity',return_value=set(affinity),create=True):
                return admission.fresh_resources(self.project,self.stage,self.auth,profile)
        self.assertEqual(check()[1]['MemAvailable_bytes'],48*2**30)
        failures=[dict(gpu_override=dict(gpu,temperature_C=90)),dict(gpu_override=dict(gpu,pids=[999])),
            dict(gpu_override=dict(gpu,compute_cap='8.9')),dict(gpu_override=dict(gpu,memory_used_mib=1025)),
            dict(hardware=dict(observation,mps_processes=None)),dict(hardware=dict(observation,compute_apps=[{}])),
            dict(memory=43),dict(affinity=(0,1)),dict(container={'unrelated':'existing'})]
        for arguments in failures:
            with self.subTest(arguments=arguments),self.assertRaises(ValueError):check(**arguments)

    def test_private_credential_pipe_failure_is_recover_only(self):
        class ClosedPipe(io.BytesIO):
            def write(self,value):raise BrokenPipeError('Fixture credential delivery lost')
        child=SimpleNamespace(pid=333,stdin=ClosedPipe())
        with self.assertRaises(BrokenPipeError):self.invoke_dispatch(lambda *a,**k:child)
        self.assertTrue(child.stdin.closed)
        with patch.object(admission,'observe_original_process',return_value=dict(original_live=None)):
            result,popen=self.invoke_dispatch()
        popen.assert_not_called();self.assertFalse(result['authorizes_retry'])

    def test_other_live_job_on_same_host_refused_and_unrelated_host_allowed(self):
        other=dict(status='RESERVED_OR_RUNNING',host='two_card',gpu_uuid='GPU-other',billed_limit_GPUh=1)
        self.snapshot['ledger']['jobs']['other']=other
        self.snapshot['ledger'].update(Pool.accounting(self.snapshot['ledger']))
        with self.assertRaisesRegex(ValueError,'already has an owned GPU job'):
            dispatch.central_binding(self.stage,self.auth,self.snapshot)
        other['host']='four_card'
        self.assertEqual(dispatch.central_binding(self.stage,self.auth,self.snapshot)['job'],self.job)

    def test_original_guardian_publication_binds_frozen_commands_and_runner_context(self):
        result,popen=self.invoke_dispatch();popen.assert_called_once()
        launch,_=self.publish()
        self.assertEqual(result['guardian_identity'],launch['guardian_identity'])
        for key in dispatch.ENDPOINT_IDENTITY:self.assertEqual(launch[key],self.auth[key])
        self.assertEqual(launch['commands']['runner'][0],str(self.project/'envs/wc-cosmos-py310-cu128-r3/bin/python'))
        self.assertEqual(dispatch.validate(self.project,self.stage)[-1]['launch_sha256'],sha(self.stage/'GPU-launch.json'))
        with self.assertRaises(FileExistsError):self.publish()
        self.assertNotIn('private-fixture-credential',(self.stage/'GPU-intent.json').read_text())
        self.assertNotIn('private-fixture-credential',(self.stage/'GPU-dispatch.json').read_text())
        from wcomr.cara_s_endpoint_guardian_journal_r1 import GuardianJournal,encoded_sha
        from wcomr.gpu_budget_pool_v2 import atomic_json
        self.assertEqual(encoded_sha(launch),sha(self.stage/'GPU-launch.json'))
        self.storage.journal.path.parent.mkdir(parents=True,exist_ok=True)
        with self.storage.journal.path.open('wb') as stream:stream.truncate(48*2**20)
        self.storage.persist=lambda key,path,value,writer:writer(path,value)
        journal=GuardianJournal(self.stage,launch,read_record(self.stage/'registration.json'),self.storage)
        self.assertFalse(any(journal.state['allocation_attempts'].values()))
        self.assertEqual(read_record(self.stage/'guardian-intent.json')['launch_sha256'],sha(self.stage/'GPU-launch.json'))

    def test_second_call_recovers_before_admission_or_spawn_even_with_dead_or_unknown_guardian(self):
        self.invoke_dispatch()
        for live in (True,False,None):
            with patch.object(admission,'observe_original_process',return_value=dict(original_live=live)),\
                 patch.object(dispatch,'ready_inputs',side_effect=AssertionError('Must recover first')),\
                 patch.object(dispatch.subprocess,'Popen',side_effect=AssertionError('No replay')):
                result=dispatch.dispatch(self.project,self.stage,{},None)
            self.assertIs(result['guardian_observation']['original_live'],live)
            self.assertEqual(result['GPU_submissions'],0)

    def test_spawn_failure_leaves_intent_and_forbids_retry(self):
        with self.assertRaises(OSError):self.invoke_dispatch(lambda *a,**k:(_ for _ in ()).throw(OSError('Fixture spawn failure')))
        self.assertTrue((self.stage/'GPU-intent.json').exists())
        result,popen=self.invoke_dispatch();popen.assert_not_called()
        self.assertEqual(result['status'],'ORIGINAL_DISPATCH_RECOVER_ONLY')

    def test_failure_to_bind_spawned_child_retains_unknown_without_retry(self):
        child=SimpleNamespace(pid=333,stdin=io.BytesIO())
        with patch.object(dispatch,'fresh_resources',return_value=(self.storage,{})),\
             patch.object(dispatch,'bind_original_process',side_effect=[self.identity,ValueError('Unknown child')]),\
             patch.object(dispatch.subprocess,'Popen',return_value=child):
            with self.assertRaisesRegex(ValueError,'Unknown child'):
                dispatch.dispatch(self.project,self.stage,self.snapshot,'fixture')
        self.assertTrue(child.stdin.closed)
        result,popen=self.invoke_dispatch();popen.assert_not_called();self.assertIsNone(result['guardian_observation'])

    def test_write_failure_never_submits(self):
        with patch.object(dispatch,'create_record',side_effect=OSError('No durable intent')),\
             patch.object(dispatch,'fresh_resources',return_value=(self.storage,{})),\
             patch.object(dispatch,'bind_original_process',return_value=self.identity),\
             patch.object(dispatch.subprocess,'Popen') as popen:
            with self.assertRaises(OSError):dispatch.dispatch(self.project,self.stage,self.snapshot,'fixture')
            popen.assert_not_called()

    def test_admission_failure_does_not_write_intent(self):
        with patch.object(dispatch,'fresh_resources',side_effect=ValueError('Busy or stale resource')),\
             patch.object(dispatch.subprocess,'Popen') as popen:
            with self.assertRaises(ValueError):dispatch.dispatch(self.project,self.stage,self.snapshot,'fixture')
        popen.assert_not_called();self.assertFalse((self.stage/'GPU-intent.json').exists())

    def test_changed_source_incomplete_CPU_and_partial_quote_refused(self):
        self.proof['whole_card_CPU_accepted']=False;self.refresh()
        with self.assertRaisesRegex(ValueError,'CPU acceptance'):dispatch.ready_inputs(self.project,self.stage)
        self.proof['whole_card_CPU_accepted']=True
        del self.quote['host_quotes']['two_card']['components_seconds']['path_artifacts'];self.refresh()
        with self.assertRaisesRegex(ValueError,'allocation costs'):dispatch.ready_inputs(self.project,self.stage)
        (self.stage/dispatch.GUARDIAN).write_text('# Different source\n')
        with self.assertRaisesRegex(ValueError,'source/runtime'):dispatch.ready_inputs(self.project,self.stage)

    def test_missing_approval_refused_before_intent(self):
        self.auth['direct_user_authorization']=False;self.refresh()
        with self.assertRaises(ValueError):self.invoke_dispatch()
        self.assertFalse((self.stage/'GPU-intent.json').exists())

    def test_stale_or_changed_central_original_refused(self):
        for fault in ('stale','other_host','liability','cap','funds'):
            self.refresh()
            if fault=='stale':self.snapshot['observed_unix']-=61
            if fault=='other_host':self.snapshot['ledger']['jobs'][self.auth['run_id']]['host']='four_card'
            if fault=='liability':self.snapshot['ledger']['jobs'][self.old_keys[0]]['billed_limit_GPUh']=15
            if fault=='cap':self.snapshot['ledger']['cap_gpu_hours']=250
            if fault=='funds':self.snapshot['ledger']['available_gpu_hours']=100
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                dispatch.central_binding(self.stage,self.auth,self.snapshot)

    def test_wrong_guardian_or_mutated_command_cannot_publish(self):
        self.invoke_dispatch()
        with self.assertRaisesRegex(ValueError,'original registered guardian'):
            self.publish(dict(self.identity,start_ticks=101))
        intent=read_record(self.stage/'GPU-intent.json');intent['commands']['runner'].append('--changed')
        self.write('GPU-intent.json',intent)
        record=read_record(self.stage/'GPU-dispatch.json');record['intent_sha256']=sha(self.stage/'GPU-intent.json')
        self.write('GPU-dispatch.json',record)
        with self.assertRaisesRegex(ValueError,'commands changed'):self.publish()

    def test_endpoint_scope_mutation_cannot_publish(self):
        self.invoke_dispatch()
        intent=read_record(self.stage/'GPU-intent.json');intent['physical_paths']=25
        self.write('GPU-intent.json',intent)
        record=read_record(self.stage/'GPU-dispatch.json');record['intent_sha256']=sha(self.stage/'GPU-intent.json')
        self.write('GPU-dispatch.json',record)
        with self.assertRaisesRegex(ValueError,'original registered guardian'):self.publish()

    def test_credential_loss_reaches_original_never_attempted_guardian_accounting(self):
        self.invoke_dispatch()
        from wcomr import cara_s_endpoint_host_guardian_r1 as allocation
        for incoming in ('','not-json','{}','{"sudo_password": ""}'):
            with patch.object(sys,'argv',['entry','--project',str(self.project),'--stage',str(self.stage)]),\
                 patch.object(sys,'stdin',io.StringIO(incoming)),\
                 patch.object(dispatch,'publish_launch',return_value=({},self.storage)),\
                 patch.object(allocation,'allocate') as allocate:
                guardian_entry.main()
            allocate.assert_called_once_with(self.project,self.stage,self.storage,None)


if __name__=='__main__':unittest.main()
