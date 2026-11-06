"""Actual saved CPU evidence and mocked network; no new task or GPU process."""
import copy
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from wcomr import frozen_repair_gpu_r2 as gpu
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA

ROOT=Path(__file__).resolve().parents[1]
CPU=ROOT/'reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_independent_acceptance_20261016.json'


def fixture():
    accepted,raw=gpu.accepted_CPU(CPU);config=raw['files']['config']['data']
    authority=dict(source_revision=accepted['source_revision'],config_sha256=accepted['config_sha256'],
        production_CPU_sha256=accepted['production_CPU_sha256'],bound_input_fingerprint=accepted['bound_input_fingerprint'],
        scope_counts=accepted['scope_counts'],whole_card_run=gpu.RUN,gpu_uuid='GPU-SYNTHETIC-NOT-A-DEVICE',
        forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'],budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True,user_reply_quote='SYNTHETIC ONLY, NO HUMAN APPROVAL',
        launch_id='SYNTHETIC_METADATA_NO_GPU_LAUNCH',kind='SPECIFIC_WHOLE_CARD_APPROVAL')
    start=1000.;delay=config['first_collection_delay_seconds']
    launch=dict(run_id=gpu.RUN,source_revision=authority['source_revision'],launch_id=authority['launch_id'],
        gpu_uuid=authority['gpu_uuid'],scope_counts=accepted['scope_counts'],config_sha256=accepted['config_sha256'],
        registration_sha256=accepted['registration_sha256'],production_CPU_sha256=accepted['production_CPU_sha256'],
        bound_input_fingerprint=accepted['bound_input_fingerprint'],project=raw['files']['bundle']['data']['project'],
        stage=raw['launch']['stage'],supervisor_identity=dict(pid=1001,start_ticks=10010),
        post_watcher_identity=dict(pid=1002,start_ticks=10020),started_unix=start,
        midpoint_check_not_before_unix=start+delay/2,next_check_not_before_unix=start+delay,
        forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
        authorization_sha256='8'*64)
    relative='.sync/'+Path(launch['stage']).name
    return authority,launch,relative,raw


class RepairGPUControls(unittest.TestCase):
    def test_original_launch_paths_fence_midpoint_and_stdlib_observer_are_exact(self):
        for kind in ('launch','capture'):
            ns,proof=gpu.script_namespace(ROOT,kind);self.assertTrue(proof['inverse_bytes_and_AST_equal'])
            self.assertFalse(proof['original_source_written'])
        ns,_=gpu.script_namespace(ROOT,'launch');text=ns['remote_code']('.sync/SYNTHETIC',{})
        self.assertIn("fence=stage/'GPU-launch-request.json'",text)
        self.assertIn("with fence.open('x')",text)
        self.assertIn('midpoint_check_not_before_unix=now+delay/2',text)
        self.assertIn('supervise_wc_paper_N07_refusal_repair180_r2.py',text)
        ns,_=gpu.script_namespace(ROOT,'capture');text=ns['remote_code']({},'admission')
        self.assertNotIn('from wcomr.frozen_repair180_r2 import',text)
        self.assertIn("CONFIG='"+gpu.CONFIG+"'",text)

    def test_real_original_CPU_preflight_rejects_wrong_stage_old_card_or_under12_authority(self):
        authority,launch,stage,_=fixture();accepted=gpu.preflight_launch(stage,authority,CPU)
        self.assertEqual(accepted['CPU_commands'],9)
        for changed in (dict(whole_card_run='wc-paper-n07-frozen-shared180-r1'),dict(kind='STANDING_STRICT_UNDER12'),
                        dict(production_CPU_sha256='0'*64),dict(source_revision='ANOTHER_SOURCE')):
            with self.subTest(changed=changed),self.assertRaises(ValueError):gpu.preflight_launch(stage,{**authority,**changed},CPU)
        with self.assertRaises(ValueError):gpu.preflight_launch('.sync/ANOTHER_STAGE',authority,CPU)

    def test_one_mocked_dispatch_timeout_and_unparsed_reply_never_authorize_retry(self):
        authority,launch,stage,_=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);send=Mock(return_value=subprocess.CompletedProcess([],0,
                stdout=json.dumps(launch).encode(),stderr=b''))
            result=gpu.launch_once(ROOT,stage,authority,CPU,root/'launch.json',execute=send)
            self.assertEqual(result['dispatch'],launch);self.assertEqual(send.call_count,1)
            with self.assertRaises(FileExistsError):gpu.launch_once(ROOT,stage,authority,CPU,root/'launch.json',execute=send)
            self.assertEqual(send.call_count,1)
            timeout=Mock(side_effect=subprocess.TimeoutExpired('SYNTHETIC_NO_SSH',180))
            result=gpu.launch_once(ROOT,stage,authority,CPU,root/'timeout.json',execute=timeout)
            self.assertFalse(result['GPU_retry_authorized']);self.assertFalse(result['original_task_terminal'])
            self.assertEqual(timeout.call_count,1)
            bad=Mock(return_value=subprocess.CompletedProcess([],0,stdout=b'partial response',stderr=b''))
            result=gpu.launch_once(ROOT,stage,authority,CPU,root/'unparsed.json',execute=bad)
            self.assertNotIn('dispatch',result);self.assertFalse(result['GPU_retry_authorized'])

    def test_both_time_gates_fail_before_SSH_or_attempt_file(self):
        _,launch,_,_=fixture()
        with tempfile.TemporaryDirectory() as directory:
            for mode,time in (('health',launch['midpoint_check_not_before_unix']-1),
                              ('health',launch['next_check_not_before_unix']),('terminal',launch['next_check_not_before_unix']-1)):
                out=Path(directory)/(mode+str(time)+'.json');send=Mock()
                with self.assertRaises(ValueError):gpu.collect_once(ROOT,launch,mode,CPU,out,now=time,execute=send)
                send.assert_not_called();self.assertFalse(out.exists());self.assertFalse(out.with_name(out.name+'.attempt').exists())
            bad=copy.deepcopy(launch);bad['next_check_not_before_unix']-=60
            with self.assertRaises(ValueError):gpu.bind_launch(bad,CPU)

    def test_health_exact_run_config_identities_and_saved_reply_deduplication(self):
        _,launch,_,raw=fixture()
        sup={**{k:launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','config_sha256')},
             'child_identity':dict(pid=1003,start_ticks=10030)}
        admission=dict(mode='admission',launch=launch,registration_sha256=launch['registration_sha256'],
            payload_verified={n:True for n in raw['registration']['payload_sha256']},supervisor=sup)
        expected=gpu.health_expected(launch,admission,CPU);code=gpu.health_code(expected)
        self.assertIn("assert EXPECTED['run_id']=='"+gpu.RUN+"'",code)
        self.assertIn("stage/'"+gpu.CONFIG+"'",code)
        self.assertEqual(expected['processes']['runner'],dict(pid=1003,start_ticks=10030))
        reply=dict(status='N07_MIDPOINT_READONLY_TECHNICAL_HEALTH',expected=expected,
            final_scientific_results_read=False,no_quality_or_method_latency_readout=True,
            original_processes=expected['processes'],observed_unix=launch['midpoint_check_not_before_unix'])
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'health.json';send=Mock(return_value=subprocess.CompletedProcess([],0,
                stdout=json.dumps(reply).encode(),stderr=b''))
            result,queried=gpu.collect_once(ROOT,launch,'health',CPU,out,admission=admission,
                now=launch['midpoint_check_not_before_unix'],execute=send)
            self.assertTrue(queried);self.assertEqual(result,reply)
            _,queried=gpu.collect_once(ROOT,launch,'health',CPU,out,admission=admission,execute=send)
            self.assertFalse(queried);self.assertEqual(send.call_count,1)

    def test_observation_timeout_is_saved_unknown_and_never_restarted(self):
        _,launch,_,_=fixture()
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'final.json.gz';send=Mock(side_effect=subprocess.TimeoutExpired('NO_SSH',150))
            result,queried=gpu.collect_once(ROOT,launch,'terminal',CPU,out,
                now=launch['next_check_not_before_unix'],execute=send)
            self.assertTrue(queried);self.assertFalse(result['original_task_terminal'])
            self.assertEqual(result['status'],'N07_REPAIR_ORIGINAL_OBSERVATION_UNKNOWN_NO_RESTART')
            _,queried=gpu.collect_once(ROOT,launch,'terminal',CPU,out,execute=send)
            self.assertFalse(queried);self.assertEqual(send.call_count,1)

    def test_admission_checks_original_reservation_handles_and_own_UUID(self):
        authority,launch,_,raw=fixture();config=raw['files']['config']['data']
        sup=dict(status='N07_SHARED180_GPU_RUNNING',child_identity=dict(pid=1003,start_ticks=10030),
            **{k:launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','config_sha256','registration_sha256','scope_counts')})
        ids={'supervisor_pid':launch['supervisor_identity'],'post_watcher_pid':launch['post_watcher_identity'],
            'child_pid':sup['child_identity']}
        job=dict(status='RESERVED_OR_RUNNING',kind='V2_SPECIFIC_WHOLE_CARD_APPROVAL',
            billed_limit_GPUh=config['billed_limit_GPUh'],forecast_GPUh=config['forecast_complete_GPUh'],
            **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','scope_counts',
                'production_CPU_sha256','bound_input_fingerprint','authorization_sha256')})
        pool=dict(schema=SCHEMA,cap_gpu_hours=config['cumulative_cap_GPUh'],origin_used_gpu_hours=config['budget_origin_used_GPUh'],
            origin_gpu_jobs_launched=100,jobs={gpu.RUN:job},events=[]);pool.update(BudgetPool.accounting(pool))
        value=dict(mode='admission',launch=launch,registration=raw['registration'],registration_sha256=launch['registration_sha256'],
            payload_verified={n:True for n in raw['registration']['payload_sha256']},supervisor=sup,
            original_processes={k:{**v,'state':'S'} for k,v in ids.items()},pool=pool,
            own_UUID_lock_free=False,own_GPU=launch['gpu_uuid']+', NVIDIA RTX A6000, 24')
        result=gpu.accept_admission(value,launch,CPU);self.assertTrue(result['GPU_admitted'])
        self.assertFalse(result['scientific_results_read'])
        bad=copy.deepcopy(value);bad['own_UUID_lock_free']=True
        with self.assertRaises(ValueError):gpu.accept_admission(bad,launch,CPU)
        pending=copy.deepcopy(value);del pending['supervisor']
        self.assertFalse(gpu.accept_admission(pending,launch,CPU)['GPU_admitted'])
        dead=copy.deepcopy(value);dead['supervisor']['status']='N07_SHARED180_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
        self.assertIn('TECHNICALLY_TERMINAL',gpu.accept_admission(dead,launch,CPU)['status'])


if __name__=='__main__':unittest.main()
