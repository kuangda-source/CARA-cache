"""Synthetic whole24 post receipts; no generated tensors, videos, or GPU calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from test_drop1_window24_execution_envelope_r1 import fixture as CPU_fixture
from test_gpu_budget_pool_v2 import legacy
from wcomr.drop1_window24_acceptance_r1 import accept, original_matrix
from wcomr.drop1_window_original_controls_r1 import expected_plans
from wcomr.drop1_window24_production_r1 import COUNTS, RUN
from wcomr.gpu_budget_pool_v2 import BudgetPool

ROOT=Path(__file__).resolve().parents[1]
H=lambda text:hashlib.sha256(text.encode()).hexdigest()


def fixture(root):
    c,reg,proof,CPU,auth,kw,cpu_capture=CPU_fixture();scenes=[r['name'] for r in c['requests']]
    launch=dict(status='WINDOW24_COMPLETE24_DISPATCHED_ADMISSION_PENDING',run_id=RUN,source_revision=reg['source_revision'],
        launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],stage=reg['stage'],project=cpu_capture['launch']['project'],
        scope_counts=COUNTS,registration_sha256='e'*64,config_sha256='f'*64,production_CPU_sha256='2'*64,
        independent_CPU_acceptance_sha256='4'*64,authorization_sha256='5'*64,bound_input_fingerprint=auth['bound_input_fingerprint'],
        supervisor_pid=101,supervisor_identity=dict(pid=101,start_ticks=1000),
        post_watcher_pid=102,post_watcher_identity=dict(pid=102,start_ticks=2000),next_check_not_before_unix=100.)
    pool=BudgetPool(root);pool.initialize(cap=226,origin_used=79.99637737158223,origin_jobs=0,
        authorization=dict(direct_user_authorization=True,cumulative_cap_GPUh=226,autonomy_exclusive_upper_GPUh=12,user_reply_quote='SYNTHETIC_UNIT_ONLY'),legacy_job=legacy())
    job=dict(job_id=RUN,source_revision=launch['source_revision'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],
        config_sha256=launch['config_sha256'],scope_counts=COUNTS,production_CPU_sha256='2'*64,
        authorization_sha256='5'*64,bound_input_fingerprint=launch['bound_input_fingerprint'],
        forecast_GPUh=2.,billed_limit_GPUh=2.5,supervisor_pid=101,supervisor_start_ticks=1000)
    pool.reserve(job,dict(uuid=launch['gpu_uuid'],name='NVIDIA RTX A6000',memory_used_mib=0,compute_cap='8.6',pids=[]));pool.settle(RUN,1.,'9'*64)
    matrix=original_matrix(scenes);rows=[]
    for planned in matrix:
        method=planned['method'];scene=planned['scene'];mask=expected_plans()[method];history=[];last=0
        for step,action in enumerate(mask,1):
            before=last
            if action=='D':last=step
            history.append(dict(teacher_calls=0,true_D_before=before,true_D_after=last,
                P_updates_true_D_or_zero_risk_RA_anchor=False,
                A_readout=dict(readout_action=action,teacher_calls=0,extra_deep_blocks=0,
                    shared_alpha=0 if action=='C' else 1,extra_heads=2 if action=='A' else 0)))
        row=dict(planned,status='COMPLETE',semantic_plan=mask,actions=['DD' if a=='D' else 'CC' for a in mask],
            A_history=[copy.deepcopy(h['A_readout']) for h in history],source_history=history,
            solver_steps=36,guided_pairs=36,online_teacher_calls=0,in_timing_hashes=0,research_checkpoints=0,
            in_timing_guided_copies=36 if planned['section']=='WARMUP' else 0,audit=planned['section']=='WARMUP',
            core_seconds=dict(zip(('S26-C','S25-C','S25-A1','S25-A3'),(200.,196.,197.,198.)))[method],
            write_deferred_after_main_timer=True,final_latent_sha256=H(scene+method+'latent'),
            decoded_video=dict(frames=93,probe=dict(HWC=[432,768,3]),RGB_sha256=H(scene+method+'RGB')),
            endpoint_audit='PASS',counts=dict(DD=mask.count('D'),PP=0,C_plain=mask.count('C'),A=mask.count('A'),C_or_A_after_P=0))
        if planned['section']=='WARMUP':row.update(warm_guided_outputs=36,warm_guided_tree_sha256=H(scene+method+'guides'))
        else:
            loss={'S26-C':.1,'S25-C':.14,'S25-A1':.12,'S25-A3':[.11,.13,.12,.15][scenes.index(scene)]}[method]
            row['LPIPS']=dict(frames=93,frame_distances=[loss]*93,mean_LPIPS=loss,pts=list(range(93)),reference_sha256=H(scene+'Native'))
        rows.append(row)
    before=[{k:copy.deepcopy(v) for k,v in r.items() if k not in ('LPIPS','endpoint_audit','decoded_video','counts')} for r in rows]
    memory=[dict(id=r['id'],observed_owners=1,owners_alive_after=0) for r in rows]
    runner=dict(source_revision=launch['source_revision'],config_sha256='f'*64,scope_counts=COUNTS,matrix=matrix,runs=before,request_memory_records=memory)
    sup=dict(status='WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',source_revision=launch['source_revision'],
        config_sha256='f'*64,scope_counts=COUNTS,child_exit_code=0,child_pid=103,child_identity=dict(pid=103,start_ticks=3000),
        billing_sha256='9'*64,runner_sha256='6'*64)
    final=dict(status='WINDOW24_FULL16_SCIENCE_ALL24_AUDITED_93FRAME_SCORED',source_revision=launch['source_revision'],
        scope_counts=COUNTS,GPU_supervisor=copy.deepcopy(sup),rows=rows,request_memory_records=memory,
        warm_guided_controls=[dict(method=m,status='PASS_ALL36_WARM_REPEAT_EQUAL',outputs_per_arm=36) for m in expected_plans()],
        warm_common_prefix_controls=[dict(round=r,status='PASS_ALL21_COMMON_PREFIX',compared_outputs=21) for r in (1,2)],
        original_baseline_controls=[dict(scene=s,method=m,status='PASS_OLD12') for s in scenes for m in ('S26-C','S25-C','S25-A1')],
        warm_repeat_controls=[dict(method=m,warm_repeats_outputs_actions_RGB_equal=True,same_scene_formal_repeat_equal=True) for m in expected_plans()])
    bindings=[dict(scene=r['scene'],window_method=r['method'],original_row=copy.deepcopy(r)) for r in rows if r['section']=='TIMED' and r['method']!='S25-A3']
    value=dict(status='WINDOW24_ORIGINAL_ONCE_CAPTURE',mode='terminal',launch=launch,observed_unix=101.,
        registration_sha256='e'*64,registration=reg,payload_actual_sha256=reg['payload_sha256'],runtime_actual_sha256=reg['runtime_source_sha256'],
        config=c,config_sha256='f'*64,production_CPU=proof,production_CPU_sha256='2'*64,
        CPU_bundle=cpu_capture['files']['bundle']['data'],CPU_independent=CPU,CPU_independent_sha256='4'*64,
        CPU_launch=dict(identity=CPU['original_CPU_identity'],source_revision=launch['source_revision']),
        authorization=auth,authorization_sha256='5'*64,runner=runner,runner_sha256='6'*64,supervisor=sup,
        final=final,final_sha256='8'*64,post_exit=dict(status='WINDOW24_POST_CPU_TERMINAL',exit_code=0,
            original_supervisor=launch['supervisor_identity'],source_revision=launch['source_revision'],config_sha256='f'*64,final_result_sha256='8'*64),
        old_controls=dict(rows=bindings),old_controls_sha256=c['references']['old_controls']['sha256'],
        baseline=dict(rows=[dict(scene=s,method='NATIVE',video_artifact=dict(sha256=H(s+'Native'))) for s in scenes]),
        baseline_sha256=c['references']['baseline']['sha256'],
        billing=dict(run_id=RUN,source_revision=launch['source_revision'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],
            scope_counts=COUNTS,actual_GPUh=1.,wall_seconds=3600.,billed_limit_GPUh=2.5),billing_sha256='9'*64,
        pool=pool.read(),own_UUID_lock_exists=True,own_UUID_lock_free=True,own_GPU=launch['gpu_uuid']+', NVIDIA RTX A6000, 0',compute_apps='',
        original_processes={k:dict(pid=i,state=None,start_ticks=None) for k,i in [('supervisor',101),('post',102),('runner',103)]},
        unit_fixture_only=True,GPU_submissions=0,ledger_written=False)
    return value,launch


class Whole24FinalAcceptanceControls(unittest.TestCase):
    def test_complete_valid_negative_method_result_is_accepted_as_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder));result=accept(value,launch)
            self.assertTrue(result['scientific_accepted'],result['errors']);self.assertTrue(result['full_protocol_accepted'],result['finance'])
            self.assertEqual((result['registered_paths'],result['scored_scientific_paths'],len(result['contrasts'])),(24,16,6))
            self.assertGreater(result['contrasts'][0]['complete_four_scene_relative_mean_change_percent'],0)

    def test_lost_frame_or_reference_is_not_zero_or_full_quality(self):
        for mode in ('frame','reference'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                value,launch=fixture(Path(folder));row=next(r for r in value['final']['rows'] if r['section']=='TIMED' and r['method']=='S25-A3')
                if mode=='frame':row['LPIPS']['frame_distances'].pop()
                else:row['LPIPS']['reference_sha256']='0'*64
                result=accept(value,launch);self.assertFalse(result['scientific_accepted']);self.assertEqual(result['scored_scientific_paths'],15)
                self.assertIsNone(result['contrasts'][0]['complete_four_scene_relative_mean_change_percent'])

    def test_rejection_preserves_all24_and_sixteen_denominator(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder));key=next(r['id'] for r in value['final']['rows'] if r['section']=='TIMED' and r['method']=='S25-A3')
            for group in (value['final']['rows'],value['runner']['runs']):next(r for r in group if r['id']==key)['status']='VIDEO_REJECTED'
            result=accept(value,launch);self.assertFalse(result['scientific_accepted'])
            self.assertEqual((result['registered_paths'],result['formal_denominator'],result['outcomes']['VIDEO_REJECTED']),(24,16,1))

    def test_duplicate_old_control_and_short_prefix_are_rejected(self):
        for mode in ('duplicate','prefix','old_endpoint'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                value,launch=fixture(Path(folder))
                if mode=='duplicate':value['final']['original_baseline_controls'][-1]=copy.deepcopy(value['final']['original_baseline_controls'][0])
                elif mode=='prefix':value['final']['warm_common_prefix_controls'][0]['compared_outputs']=20
                else:value['old_controls']['rows'][0]['original_row']['final_latent_sha256']='0'*64
                self.assertFalse(accept(value,launch)['scientific_accepted'])

    def test_other_account_after_release_does_not_erase_valid_own_release(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder));value['compute_apps']=launch['gpu_uuid']+', 998877'
            self.assertTrue(accept(value,launch)['finance']['finance_accepted'])

    def test_wrong_bill_keeps_science_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder));value['pool']['jobs'][RUN]['billing_sha256']='0'*64
            result=accept(value,launch);self.assertTrue(result['scientific_accepted']);self.assertFalse(result['full_protocol_accepted'])

    def test_recorded_actual_overrun_is_visible_and_not_full_protocol_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder))
            value['billing'].update(actual_GPUh=3.,wall_seconds=10800.)
            value['pool']['jobs'][RUN]['actual_GPUh']=3.
            value['pool']['budget_overrun_recorded']=True
            value['pool'].update(BudgetPool.accounting(value['pool']))
            result=accept(value,launch)
            self.assertTrue(result['scientific_accepted'])
            self.assertTrue(result['finance']['finance_accepted'],result['finance']['errors'])
            self.assertFalse(result['finance']['billed_limit_respected'])
            self.assertFalse(result['full_protocol_accepted'])

    def test_original_running_handle_is_pending_and_early_final_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder));value['original_processes']['runner']=dict(pid=103,start_ticks=3000,state='S')
            self.assertFalse(accept(value,launch)['scientific_accepted'])
            value['observed_unix']=99
            with self.assertRaises(ValueError):accept(value,launch)

    def test_launcher_uses_real_CPU_hash_and_requires_whole12_approval(self):
        path=ROOT/'scripts/launch_wc_drop1_window24_r1.py';spec=importlib.util.spec_from_file_location('unit_window24_launcher',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        c,r,p,a,h,k,value=CPU_fixture();auth=module.authority_for(value,a,'GPU-unit-only','new-unit-launch',accepted_sha256='7'*64)
        self.assertEqual(auth['independent_CPU_acceptance_sha256'],'7'*64)
        c['forecast_complete_GPUh']=11.5;c['billed_limit_GPUh']=12
        with self.assertRaises(ValueError):module.authority_for(value,a,'GPU-unit-only','new-unit-launch',accepted_sha256='7'*64)


if __name__=='__main__':unittest.main()
