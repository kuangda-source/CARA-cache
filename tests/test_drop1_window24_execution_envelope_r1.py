"""Whole-card identity and CPU proof controls; explicit synthetic metadata."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from test_drop1_window24_production_r1 import contract
from wcomr import drop1_window24_cpu_acceptance_r1 as cpu
from wcomr.drop1_window24_execution_envelope_r1 import input_fingerprint, validate_authority
from wcomr.drop1_window24_production_r1 import COUNTS, RUN, PRODUCTION_CPU_STATUS, matrix
from wcomr.gpu_budget_pool_v2 import BudgetPool, DeviceLease, sha


def fixture():
    c=contract(); revision='1'*40; stage='/SYNTHETIC_CPU_ONLY/stage'; project='/SYNTHETIC_CPU_ONLY'
    payload={'tests/'+n:'a'*64 for n in cpu.PATTERNS}
    payload.update({cpu.WORKER:'b'*64,'scripts/run_wc_drop1_window24_cpu_bundle_r1.py':'c'*64,cpu.CONFIG:'f'*64})
    reg=dict(source_revision=revision,stage=stage,payload_sha256=payload,runtime_source_sha256={'synthetic.py':'d'*64})
    proof=dict(status=PRODUCTION_CPU_STATUS,exit_code=0,source_revision=revision,registration_sha256='e'*64,
        config_sha256='f'*64,numerical_CPU_capture_sha256=c['references']['numeric_capture']['sha256'],
        scope_counts=COUNTS,matrix=matrix([r['name'] for r in c['requests']]),
        mutations_refused=['scope_counts','methods','A_method','P_enabled','online_teachers','training',
            'autonomy_exclusive_upper_GPUh','cumulative_cap_GPUh','billed_limit_GPUh','timing_claim','plans'],
        input_evidence=dict(synthetic_input_control=True),CUDA_initialized=False,GPU_submissions=0,ledger_written=False)
    bundle=dict(status=cpu.BUNDLE_STATUS,exit_code=0,source_revision=revision,registration_sha256='e'*64,
        config_sha256='f'*64,production_CPU_sha256='2'*64,stage=stage,project=project,python_executable='/SYNTHETIC/python',
        control_source_sha256={'tests/'+n:payload['tests/'+n] for n in cpu.PATTERNS},
        bundle_worker_source_sha256='c'*64,wall_seconds=.5,GPU_submissions=0,model_weights_loaded=0,
        ledger_written=False,original_stage_written=False)
    commands=[[bundle['python_executable'],'-m','unittest','discover','-s',stage+'/tests','-p',n,'-v'] for n in cpu.PATTERNS]
    commands.append([bundle['python_executable'],stage+'/'+cpu.WORKER,'--project',project,'--stage',stage,'--cpu-check'])
    bundle['commands']=[dict(command=r,exit_code=0) for r in commands]
    launch=dict(source_revision=revision,stage=stage,project=project,registration_sha256='e'*64,final_not_before_unix=10.,identity=dict(pid=123,start_ticks=100))
    value=dict(status='WINDOW24_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=launch,registration=reg,
        observed_unix=11.,registration_sha256='e'*64,payload_actual_sha256=payload,
        runtime_actual_sha256=reg['runtime_source_sha256'],process=dict(pid=123,start_ticks=None,state=None),
        GPU_submissions=0,ledger_written=False,files=dict(
            bundle=dict(data=bundle,sha256='3'*64),proof=dict(data=proof,sha256='2'*64),config=dict(data=c,sha256='f'*64)))
    accepted=cpu.accept(value)
    kwargs=dict(source_revision=revision,gpu_uuid='GPU-unit-only',registration_sha256='e'*64,
        config_sha256='f'*64,proof_sha256='2'*64,accepted_sha256='4'*64)
    authority=dict(source_revision=revision,gpu_uuid=kwargs['gpu_uuid'],whole_card_run=RUN,
        registration_sha256='e'*64,config_sha256='f'*64,production_CPU_sha256='2'*64,
        independent_CPU_acceptance_sha256='4'*64,bound_input_fingerprint=input_fingerprint(c),scope_counts=COUNTS,
        forecast_complete_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
        cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,autonomy_exclusive_upper_GPUh=12,
        kind='EXISTING_PLAN_UNDER12_AUTONOMY',direct_user_authorization=True,
        user_reply_quote='SYNTHETIC_HUMAN_AUTH_UNIT_ONLY',launch_id='unit-only-launch')
    return c,reg,proof,accepted,authority,kwargs,value


class Whole24EnvelopeControls(unittest.TestCase):
    def test_complete_five_command_real_entry_contract_and_whole_authority(self):
        c,r,p,a,h,k,v=fixture();expected=validate_authority(c,r,p,a,h,**k)
        self.assertEqual(expected['scope_counts']['total_paths'],24)
        self.assertEqual(a['CPU_commands'],5);self.assertFalse(a['actual_GPU_or_video_result'])

    def test_missing_runtime_payload_or_wrong_source_is_not_CPU_acceptance(self):
        for key in ('runtime_actual_sha256','payload_actual_sha256','registration_sha256'):
            *_,v=fixture();v=copy.deepcopy(v);v[key]={} if key.endswith('sha256') and key!='registration_sha256' else '0'*64
            with self.subTest(key=key),self.assertRaises(ValueError):cpu.accept(v)

    def test_same_handle_live_waits_reused_pid_does_not_hang_original(self):
        *_,v=fixture();v['process']=dict(pid=123,start_ticks=100,state='S')
        self.assertFalse(cpu.accept(v)['CPU_accepted'])
        v['process']['start_ticks']=200
        self.assertTrue(cpu.accept(v)['CPU_accepted'])

    def test_before_ETA_and_missing_final_preserve_pending_not_success(self):
        *_,v=fixture();early=copy.deepcopy(v);early['observed_unix']=9
        with self.assertRaises(ValueError):cpu.accept(early)
        v['files']['proof']['data']=None
        self.assertFalse(cpu.accept(v)['CPU_accepted'])

    def test_omitted_or_reordered_control_and_failed_exit_refused(self):
        for mode in ('omit','reorder','source','failed','CUDA','numeric88','wall'):
            *_,v=fixture();v=copy.deepcopy(v);b=v['files']['bundle']['data'];p=v['files']['proof']['data']
            if mode=='omit':b['commands'].pop()
            elif mode=='reorder':b['commands'].reverse()
            elif mode=='source':b['bundle_worker_source_sha256']='0'*64
            elif mode=='failed':b['commands'][0]['exit_code']=1
            elif mode=='CUDA':p['CUDA_initialized']=True
            elif mode=='numeric88':p['numerical_CPU_capture_sha256']='0'*64
            else:b['wall_seconds']=float('nan')
            with self.subTest(mode=mode),self.assertRaises(ValueError):cpu.accept(v)

    def test_changed_whole_authority_never_inherits_CPU_success(self):
        for key,bad in [('scope_counts',{**COUNTS,'formal_paths':15}),('whole_card_run','old18'),
                        ('source_revision','old-source'),('gpu_uuid','GPU-other'),('config_sha256','0'*64),
                        ('production_CPU_sha256','0'*64),('independent_CPU_acceptance_sha256','0'*64),
                        ('cumulative_cap_GPUh',113),('budget_origin_used_GPUh',0),('user_reply_quote','')]:
            c,r,p,a,h,k,_=fixture();h[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):validate_authority(c,r,p,a,h,**k)

    def test_exact12_needs_specific_whole_approval_and_still_all24(self):
        c,r,p,a,h,k,_=fixture();c['forecast_complete_GPUh']=11.5;c['billed_limit_GPUh']=12
        h.update(forecast_complete_GPUh=11.5,billed_limit_GPUh=12)
        with self.assertRaises(ValueError):validate_authority(c,r,p,a,h,**k)
        h['kind']='SPECIFIC_WHOLE_CARD_APPROVAL'
        self.assertEqual(validate_authority(c,r,p,a,h,**k)['scope_counts']['total_paths'],24)


def supervisor_fixture(root):
    from test_gpu_budget_pool_v2 import legacy
    c,r,p,a,h,k,v=fixture();stage=root/'.sync/unit-only-window24';stage.mkdir(parents=True)
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
    for name in r['payload_sha256']:
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'SYNTHETIC_UNIT_ONLY_SOURCE_NOT_EXECUTED')
    write(stage/cpu.CONFIG,c)
    r['payload_sha256']={n:sha(stage/n) for n in r['payload_sha256']};r['stage']=str(stage)
    write(stage/'registration.json',r);regsha=sha(stage/'registration.json');configsha=sha(stage/cpu.CONFIG)
    p.update(registration_sha256=regsha,config_sha256=configsha);write(stage/'window24-production-CPU-result.json',p)
    proofsha=sha(stage/'window24-production-CPU-result.json')
    bundle=v['files']['bundle']['data'];bundle.update(stage=str(stage),project=str(root),python_executable=sys.executable,
        registration_sha256=regsha,config_sha256=configsha,production_CPU_sha256=proofsha,
        control_source_sha256={'tests/'+n:r['payload_sha256']['tests/'+n] for n in cpu.PATTERNS},
        bundle_worker_source_sha256=r['payload_sha256']['scripts/run_wc_drop1_window24_cpu_bundle_r1.py'])
    commands=[[sys.executable,'-m','unittest','discover','-s',str(stage/'tests'),'-p',n,'-v'] for n in cpu.PATTERNS]
    commands.append([sys.executable,str(stage/cpu.WORKER),'--project',str(root),'--stage',str(stage),'--cpu-check'])
    bundle['commands']=[dict(command=x,exit_code=0) for x in commands];write(stage/cpu.BUNDLE,bundle)
    a.update(registration_sha256=regsha,config_sha256=configsha,production_CPU_sha256=proofsha)
    ap=stage/'window24-production-CPU-independent-acceptance.json';write(ap,a)
    h.update(registration_sha256=regsha,config_sha256=configsha,production_CPU_sha256=proofsha,
        independent_CPU_acceptance_sha256=sha(ap));authority=root/'unit-only-authority.json';write(authority,h)
    pool=BudgetPool(root);pool.initialize(cap=226,origin_used=79.99637737158223,origin_jobs=0,
        authorization=dict(direct_user_authorization=True,cumulative_cap_GPUh=226,
            autonomy_exclusive_upper_GPUh=12,user_reply_quote='SYNTHETIC_UNIT_ONLY'),legacy_job=legacy())
    return c,r,stage,authority,pool


class Whole24SupervisorControls(unittest.TestCase):
    def module(self):
        path=Path(__file__).resolve().parents[1]/'scripts/supervise_wc_drop1_window24_r1.py'
        spec=importlib.util.spec_from_file_location('unit_only_window24_supervisor',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def test_owned_job_settles_and_releases_while_other_UUID_remains_reserved(self):
        from wcomr import drop1_window24_production_r1 as production
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);c,r,stage,authority,pool=supervisor_fixture(root);module=self.module()
            child=mock.Mock(pid=99999);child.poll.return_value=0;child.wait.return_value=0
            gpu=dict(uuid='GPU-unit-only',name='NVIDIA RTX A6000',memory_used_mib=0,compute_cap='8.6',pids=[])
            argv=['unit','--project',str(root),'--stage',str(stage),'--authorization',str(authority),
                '--source-revision',r['source_revision'],'--gpu-uuid',gpu['uuid']]
            identify=lambda pid:dict(pid=pid,state='R',start_ticks=pid*10,command='SYNTHETIC_UNIT_ONLY')
            with DeviceLease(root,'GPU-original'),mock.patch.object(production,'validate',return_value=(c,r,None,None,None,None)),\
                    mock.patch.object(module,'observe',return_value=gpu),mock.patch.object(module.subprocess,'Popen',return_value=child),\
                    mock.patch('wcomr.gpu_budget_pool_v2.process_identity',side_effect=identify),\
                    mock.patch.object(module.signal,'signal'),mock.patch.object(sys,'argv',argv),mock.patch.dict(os.environ):
                module.main()
                settled=pool.read();self.assertEqual(settled['jobs'][RUN]['status'],'SETTLED')
                self.assertEqual(settled['jobs']['original-W3']['status'],'RESERVED_OR_RUNNING')
                self.assertEqual(settled['reserved_gpu_hours'],12)
                with DeviceLease(root,gpu['uuid']):pass
                with self.assertRaises(BlockingIOError):DeviceLease(root,'GPU-original').acquire()
            bill=json.loads((root/'outputs'/RUN/'billing.json').read_text())
            self.assertGreaterEqual(bill['actual_GPUh'],0);self.assertEqual(bill['scope_counts']['total_paths'],24)
            sup=json.loads((root/'outputs'/RUN/'supervisor.json').read_text())
            self.assertEqual(sup['status'],'WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT')

    def test_busy_device_has_no_child_no_reservation_no_fee_and_no_restart(self):
        from wcomr import drop1_window24_production_r1 as production
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);c,r,stage,authority,pool=supervisor_fixture(root);module=self.module();before=pool.read()
            gpu=dict(uuid='GPU-unit-only',name='NVIDIA RTX A6000',memory_used_mib=48000,compute_cap='8.6',pids=[55])
            argv=['unit','--project',str(root),'--stage',str(stage),'--authorization',str(authority),
                '--source-revision',r['source_revision'],'--gpu-uuid',gpu['uuid']]
            with mock.patch.object(production,'validate',return_value=(c,r,None,None,None,None)),\
                    mock.patch.object(module,'observe',return_value=gpu),mock.patch.object(module.subprocess,'Popen') as popen,\
                    mock.patch.object(sys,'argv',argv),mock.patch.dict(os.environ),self.assertRaises(ValueError):
                module.main()
            popen.assert_not_called();self.assertEqual(pool.read(),before)
            self.assertFalse((root/'outputs'/RUN).exists())
            failure=json.loads((stage/'window24-admission-failure.json').read_text())
            self.assertFalse(failure['GPU_child_started']);self.assertEqual(failure['GPUh'],0)
            with DeviceLease(root,gpu['uuid']):pass


if __name__=='__main__':unittest.main()
