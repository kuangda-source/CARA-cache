"""Safety and recovery controls for the actual deployment tool boundaries."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
import four_card_bank24_execution_tools_r1 as tools
from four_card_bank24_gpu_port_r1 import generate,sha,require_full_CPU,accept_capture
from four_card_bank24_execution_adapter_r1 import LIFECYCLE_SOURCE
from wc_four_card_bank24_execution_cpu_r1 import SETUP,CAPTURE


class ExecutionToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.project=Path(self.temp.name);self.stage=self.project/'.sync/test-stage';self.stage.mkdir(parents=True)
        self.launch=dict(source_revision='UNIT_CPU_FIXTURE',launch_id='unit-once',project=str(self.project),stage=str(self.stage),
            run_id='unit-full24',gpu_uuid='GPU-CPU-UNIT',scope_counts={'total_paths':24},forecast_GPUh=6.974166666666667,billed_limit_GPUh=8.75,
            supervisor_identity=None,post_watcher_identity=None)
    def tearDown(self):self.temp.cleanup()

    def file(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path

    def settled(self):
        out=self.project/'outputs'/self.launch['run_id'];out.mkdir(parents=True)
        bill=dict((k,self.launch[k]) for k in ['launch_id','run_id','source_revision','gpu_uuid','scope_counts'])
        bill.update(wall_seconds=1.,actual_GPUh=1./3600,CPU_FIXTURE_ONLY=True)
        bp=self.file(out/'billing.json',bill)
        self.file(out/'supervisor.json',dict(status='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',owned_container_exit_verified=True,
            supervisor_identity=None,child_identity=None,billing_sha256=sha(bp)))
        self.file(self.project/'reports/gpu-budget-v2.json',dict(jobs={self.launch['run_id']:dict(status='SETTLED',billing_sha256=sha(bp),actual_GPUh=bill['actual_GPUh'])}))
        p=self.project/'.sync/gpu-locks'/('GPU-CPU-UNIT.lock');p.parent.mkdir();p.touch()
        return out

    def test_once_dispatch_and_original_restore_no_second_Popen(self):
        with patch.object(tools.subprocess,'Popen') as popen,patch.object(tools,'identity',side_effect=lambda pid:dict(pid=pid,start_ticks=pid)):
            popen.side_effect=[Mock(pid=101),Mock(pid=102)]
            first=tools.spawn_once(self.stage,self.launch,['CPU_ONLY_1'],['CPU_ONLY_2'])
            again=tools.spawn_once(self.stage,self.launch,['MUST_NOT_START'],['MUST_NOT_START'])
        self.assertEqual(popen.call_count,2);self.assertEqual(first,again);self.assertEqual(tools.restore_only(self.stage),first)

    def test_Popen_unknown_retains_fence_and_refuses_replay(self):
        with patch.object(tools.subprocess,'Popen',side_effect=OSError('CPU_TEST_FAILURE')) as popen:
            with self.assertRaises(OSError):tools.spawn_once(self.stage,self.launch,['CPU_ONLY'],['CPU_ONLY'])
            old=tools.spawn_once(self.stage,self.launch,['MUST_NOT_START'],['MUST_NOT_START'])
        self.assertEqual(popen.call_count,1);self.assertTrue(old['no_GPU_relaunch_authority']);self.assertTrue((self.stage/tools.GPU_INTENT).exists())

    def test_fence_without_launch_is_unknown_restore_only(self):
        self.file(self.stage/tools.GPU_INTENT,dict(source_revision='CPU_TEST',launch_id='original'))
        value=tools.restore_only(self.stage)
        self.assertEqual(value['status'],'DISPATCH_FENCE_PRESENT_UNKNOWN_RESTORE_ONLY')

    def test_post_accepts_only_settled_exited_fixture(self):
        self.settled()
        with patch.object(tools,'alive',return_value=False):
            self.assertEqual(tools.post_conditions(self.project,self.stage,self.launch,'ABSENT')['status'],'SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT')

    def test_post_refuses_live_parent(self):
        with patch.object(tools,'alive',return_value=True):
            with self.assertRaises(ValueError):tools.post_conditions(self.project,self.stage,self.launch,'ABSENT')

    def test_post_refuses_unknown_and_running_container(self):
        self.settled()
        for name in ['UNKNOWN','RUNNING']:
            with self.subTest(name=name),patch.object(tools,'alive',return_value=False):
                with self.assertRaises(ValueError):tools.post_conditions(self.project,self.stage,self.launch,name)

    def test_post_refuses_unsettled_reservation(self):
        self.settled();p=self.project/'reports/gpu-budget-v2.json';x=json.loads(p.read_text());x['jobs'][self.launch['run_id']]['status']='RESERVED_OR_RUNNING';self.file(p,x)
        with patch.object(tools,'alive',return_value=False):
            with self.assertRaises(ValueError):tools.post_conditions(self.project,self.stage,self.launch,'EXITED')

    def test_post_refuses_changed_bill(self):
        out=self.settled();p=out/'billing.json';x=json.loads(p.read_text());x['actual_GPUh']=100;self.file(p,x)
        with patch.object(tools,'alive',return_value=False):
            with self.assertRaises(ValueError):tools.post_conditions(self.project,self.stage,self.launch,'ABSENT')

    def test_post_refuses_foreign_launch_even_with_updated_hash(self):
        out=self.settled();p=out/'billing.json';x=json.loads(p.read_text());x['launch_id']='FOREIGN';self.file(p,x)
        s=json.loads((out/'supervisor.json').read_text());s['billing_sha256']=sha(p);self.file(out/'supervisor.json',s)
        pool=json.loads((self.project/'reports/gpu-budget-v2.json').read_text());pool['jobs'][self.launch['run_id']]['billing_sha256']=sha(p);self.file(self.project/'reports/gpu-budget-v2.json',pool)
        with patch.object(tools,'alive',return_value=False):
            with self.assertRaises(ValueError):tools.post_conditions(self.project,self.stage,self.launch,'ABSENT')

    def test_post_refuses_held_original_lease(self):
        import fcntl
        self.settled()
        with (self.project/'.sync/gpu-locks/GPU-CPU-UNIT.lock').open('r') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.object(tools,'alive',return_value=False):
                with self.assertRaises(BlockingIOError):tools.post_conditions(self.project,self.stage,self.launch,'ABSENT')

    def test_live_terminal_capture_does_not_start_CPU_or_read_science(self):
        value=dict(original_live_handles={'runner':True},mode='terminal',status='IN_PROGRESS')
        with patch.object(tools,'capture_host',return_value=value),patch.object(tools,'cpu_container',side_effect=AssertionError('MUST_NOT_START')) as cpu:
            result=tools.collect_once(self.project,self.stage,self.launch,'terminal',self.stage/'obs')
        self.assertFalse(cpu.called);self.assertEqual(result,value)

    def test_technical_capture_one_injected_telemetry_no_raw(self):
        self.file(self.project/'reports/gpu-budget-v2.json',dict(jobs={}))
        self.file(self.stage/'registration.json',dict(CPU_FIXTURE_ONLY=True))
        (self.stage/'CPU-final-results.json').write_text('INVALID_MUST_NOT_READ')
        out=self.project/'outputs'/self.launch['run_id'];out.mkdir(parents=True);(out/'runner.json').write_text('INVALID_MUST_NOT_READ')
        telemetry=Mock(return_value={'GPU_telemetry_calls':1})
        with patch.object(tools,'verify_registration',return_value={}):
            value=tools.capture_host(self.project,self.stage,self.launch,'halfway',telemetry)
        self.assertEqual(telemetry.call_count,1);self.assertFalse(value['scientific_partial_read']);self.assertNotIn('final',value);self.assertNotIn('runner',value)

    def test_GPU_namespace_refuses_test_fixture_before_ledger_read(self):
        target=self.project/'.sync'/tools.TARGET_STAGE;target.mkdir();self.file(target/'CPU-TEST-ONLY.json',{'CPU_FIXTURE_ONLY':True})
        with patch.object(tools,'ROOT',str(self.project)):
            with self.assertRaisesRegex(ValueError,'fixture'):tools.validate_authorization(self.project,target,{})
        self.assertFalse((self.project/'reports/gpu-budget-v2.json').exists())

    def test_missing_authority_fails_before_GPU_observation(self):
        with patch.object(tools,'validate_authorization',side_effect=ValueError('missing handoff')),patch.object(tools,'module',side_effect=AssertionError('MUST_NOT_OBSERVE')) as mod:
            with self.assertRaisesRegex(ValueError,'handoff'):tools.dispatch(self.project,self.stage,{})
        self.assertFalse(mod.called);self.assertFalse((self.stage/tools.GPU_INTENT).exists())

    def test_registration_refuses_matching_hash_symlink(self):
        target=self.project/'outside.py';target.write_text('CPU_TEST_ONLY')
        (self.stage/'alias.py').symlink_to(target)
        self.file(self.stage/'registration.json',dict(namespace='BANK24_FOURCARD_GPU_PORT_R1',payload_sha256={'alias.py':sha(target)}))
        with self.assertRaises(ValueError):tools.verify_registration(self.stage)

    def test_registration_refuses_mutated_source(self):
        p=self.stage/'code.py';p.write_text('original')
        self.file(self.stage/'registration.json',dict(namespace='BANK24_FOURCARD_GPU_PORT_R1',payload_sha256={'code.py':sha(p)}))
        p.write_text('modified')
        with self.assertRaises(ValueError):tools.verify_registration(self.stage)

    def test_incomplete_component_receipt_cannot_grant_full_CPU(self):
        self.file(self.stage/'scout-lifecycle-CPU-independent-acceptance.json',dict(status='BANK24_REAL_CROSS_CONTAINER_LIFECYCLE_CPU_INDEPENDENTLY_ACCEPTED',full_new_host_scope_production_CPU_accepted=False))
        with self.assertRaises(ValueError):require_full_CPU(self.stage,'CPU_TEST')

    def test_generated_GPU_branch_requires_actual_full_CPU_without_old_proof(self):
        for name in ['scripts/run_wc_drop1_full18_r1.py','scripts/postprocess_wc_scout_gpu_r1.py','src/wcomr/scout_gpu_lifecycle_r1.py','src/wcomr/gpu_budget_pool_v2.py']:
            p=self.project/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+name],cwd=ROOT))
        sources,binding=generate(self.project);body=sources['bank24-fourcard-runner.py']
        self.assertIn('proof=require_full_CPU(a.stage,a.source_revision)',body)
        self.assertNotIn("proof=json.loads((a.stage/'scout-entry-production-CPU-result.json').read_text())",body)
        self.assertTrue(binding['GPU_branch_uses_actual_full_new_host_CPU_acceptance_without_fabricating_legacy_entry_proof'])
        self.assertIn('torch.cuda.get_device_capability()==(8,9)',body)

    def test_original_inner_live_handle_blocks_offline_acceptance(self):
        launch=dict(next_check_not_before_unix=0)
        capture=dict(launch=launch,mode='terminal',observed_unix=1,original_live_handles={'inner':True})
        self.assertFalse(accept_capture(capture,launch,self.project)['full_protocol_accepted'])

    def test_host_CPU_templates_compile_without_GPU_probe(self):
        compile(SETUP,'<CPU-setup>','exec');compile(CAPTURE,'<CPU-capture>','exec')
        self.assertNotIn('nvidia-smi',SETUP+CAPTURE);self.assertNotIn('.is_relative_to(',SETUP+CAPTURE)
        self.assertIn('EXISTING_STAGE_RESTORE_ONLY',SETUP)


if __name__=='__main__':unittest.main()
