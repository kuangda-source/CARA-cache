"""Actual guarded H1 eight-parent entry; CPU inspection never loads weights."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for name in ('project','stage'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cpu-check',action='store_true')
    parser.add_argument('--source-revision');parser.add_argument('--gpu-uuid')
    parser.add_argument('--authorization',type=Path)
    a=parser.parse_args()
    # Fail before importing Torch/native modules when no new concrete card
    # permission exists. An old generic budget file cannot select this run.
    sys.path.insert(0,str(a.stage/'src'))
    if not a.cpu_check:
        from wcomr.p_acr_profile528_admission_r1 import verify_permission
        from wcomr.p_acr_profile528_production_r1 import CONFIG,sha
        if a.authorization is None:raise ValueError('New GPU stopped; explicit PA12 authorization required')
        cfg=json.loads((a.stage/CONFIG).read_text())
        production=json.loads((a.stage/'production-CPU-result.json').read_text())
        registration=json.loads((a.stage/'registration.json').read_text())
        verify_permission(cfg,json.loads(a.authorization.read_text()),production,registration,
            config_sha256=sha(a.stage/CONFIG),proof_sha256=sha(a.stage/'production-CPU-result.json'))
        assert a.source_revision==registration['source_revision']
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if a.cpu_check:os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    if a.cpu_check:
        assert not torch.cuda.is_initialized()
        def forbidden(*args,**kwargs):raise RuntimeError('PA production CPU forbids CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('PA production CPU denies Triton execution: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        prior_helpers=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True
        torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        import cosmos_predict2.inference as im
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prior_helpers
    from wcomr.p_acr_profile528_production_r1 import CONFIG,RUN,MODE_REF,CPU_STATUS,sha,write,validate,matrix,validate_parent
    from wcomr.p_acr_profile528_contract_r1 import COUNTS,validate_contract,require_new_GPU_permission
    from wcomr import source_phase_absolute_h1_batch_r1 as batch
    from wcomr import clean_speed20_r1 as clean
    from wcomr.p_acr_profile20_owner_r1 import install_profile20
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    c,reg,old,inputs,values=validate(a.project,a.stage)
    calibration,specs,refs,evidence=inputs
    samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    setup=SetupArguments(**{**values['setup'],'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    table_parameters={'SOURCE_PHASE':values['H1']};previous=values['previous'];coefficients=values['coefficients']
    plan=matrix(c)
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:
            batch.execute(dummy,samples[0],'TABLE_PHASE_H1',table_parameters=table_parameters,previous_parameters=previous,
                runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=calibration,specs=specs[c['strategy']],
                inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=c['expected_real_shape'],audit=True)
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded real PA parent accepted')
        refused=[]
        for key,new in [('scope_counts',{**COUNTS,'baseline_parents':0}),('states',c['states'][:-1]),
                ('GPU_authorized',True),('source_rebase',True),('ACR_REFRESH',True),('fit_on_current_teacher',True)]:
            bad=copy.deepcopy(c);bad[key]=new
            try:validate_contract(bad)
            except ValueError:refused.append(key)
            else:raise AssertionError('Changed PA scope accepted: '+key)
        for permission in (None,{'direct_user_authorization':True,'automatic_single_job_gpu_hours':8}):
            try:require_new_GPU_permission(c,permission)
            except ValueError:pass
            else:raise AssertionError('Old budget authority authorized new GPU')
        assert len(plan)==8 and sum(x['planned_ordinary_pairs']+x['planned_diagnostic_pairs'] for x in plan)==528
        import importlib.util
        import unittest
        unit_path=a.stage/'tests/test_p_acr_profile528_post_r1.py'
        spec=importlib.util.spec_from_file_location('PA_actual_point_and_parent_post_CPU',unit_path)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        verdict=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        assert verdict.wasSuccessful() and verdict.testsRun==5
        launch_unit_path=a.stage/'tests/test_p_acr_profile528_launch_r1.py'
        launch_spec=importlib.util.spec_from_file_location('PA_actual_whole_card_launch_CPU',launch_unit_path)
        launch_tests=importlib.util.module_from_spec(launch_spec);launch_spec.loader.exec_module(launch_tests)
        launch_verdict=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(launch_tests))
        assert launch_verdict.wasSuccessful() and launch_verdict.testsRun==11
        post_path=a.stage/'scripts/postprocess_wc_p_acr_local12_profile528_cpu_r1.py'
        assert sha(post_path)==reg['payload_sha256']['scripts/postprocess_wc_p_acr_local12_profile528_cpu_r1.py']
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':CPU_STATUS,'exit_code':0,'GPU_submissions':0,
            'CUDA_initialized':False,'weights_loaded':0,'ledger_written':False,'scope_counts':COUNTS,
            'source_revision':reg['source_revision'],'config_sha256':sha(a.stage/CONFIG),
            'registration_sha256':sha(a.stage/'registration.json'),'matrix':plan,'mutations_refused':refused,
            'actual_setup_and_InferenceArguments_bound':True,'actual_inference_objects_instantiated':0,
            'original_input_evidence':evidence,'actual_full528_model_calls_executed':False,
            'numerical_profile_proof_ref':c['references']['profile_CPU'],
            'point_and_rejected_parent_post_unit_tests':5,'actual_post_script_sha256':sha(post_path),
            'full_video_post_GPU_not_executed':True,
            'launch_control_unit_tests':11,'launch_controls_accepted':True,
            'launcher_supervisor_post_paths_verified':True,'GPU_launch_permission_pending':True,
            'whole_card_launch_scripts_sha256':{name:sha(a.stage/name) for name in (
                'scripts/launch_wc_p_acr_local12_profile528_r1.py',
                'scripts/supervise_wc_p_acr_local12_profile528_r1.py',
                'scripts/watch_wc_p_acr_local12_post_cpu_r1.py',
                'tests/test_p_acr_profile528_launch_r1.py',
                'src/wcomr/p_acr_profile528_admission_r1.py')},
            'sampling_and_postprocessing_scope_are_separate':True})
        print(CPU_STATUS);return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    permission=json.loads(a.authorization.read_text()) if a.authorization is not None else None
    require_new_GPU_permission(c,permission,proof)
    assert proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert a.source_revision==reg['source_revision'] and os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid
    assert os.environ['WC_SUPERVISOR_PID']==str(os.getppid());os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN;assert output.is_dir() and not (output/'runner.json').exists()
    state={'status':'PA_LOCAL12_INITIALIZING_SINGLE_RESIDENT_MODEL','source_revision':a.source_revision,
        'pid':os.getpid(),'started_unix':time.time(),'scope_counts':COUNTS,'runs':copy.deepcopy(plan)}
    save=lambda:write(output/'runner.json',state)
    save();init_environment();init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-start
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));initial_sha=initial.fingerprint()
        versions=[(p,p._version) for p in net.parameters()];controls={}
        baseline={r['scene']:r for r in values['baseline']['rows']}
        for index,planned in enumerate(plan):
            row=state['runs'][index];row.update(status='RUNNING',started_unix=time.time());state['status']='PA_LOCAL12_ALL8_PARENTS_RUNNING';save()
            sample=next(s for s in samples if s.name==planned['scene']);directory=output/planned['id']
            initial.restore();assert initial.fingerprint()==initial_sha;verify_shared_eval(net,mode)
            common=dict(runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=calibration,
                specs=specs[c['strategy']],inference_module=im,expected_shape=c['expected_real_shape'],audit=True)
            holder={}
            def writer(step,payload):
                directory.mkdir(exist_ok=True);path=directory/('point-'+str(step)+'.pt');assert not path.exists()
                torch.save(payload,path)
                return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'tensor_sha256':tree_digest(payload)}
            if planned['kind']=='BASELINE':
                result,_=batch.execute(inference,sample,'TABLE_PHASE_H1',table_parameters=table_parameters,previous_parameters=previous,output=directory,**common)
                count=result['guided_pairs']
            else:
                points=[p for p in c['states'] if p['scene']==sample.name]
                with install_profile20(clean,batch,scheduler,states=points,config=c['checkpoint_reserves'],
                        writer=writer,coefficients=coefficients,holder=holder,quiet_observers=True):
                    result,_=batch.execute(inference,sample,'TABLE_PHASE_H1',table_parameters=table_parameters,
                        previous_parameters=previous,output=directory,**common)
                owner=holder['owner'];count=owner.actual_pair_computations
                row['diagnostic_points']=owner.records
            final=result.pop('final_latent',None);guided=result.pop('guided',None)
            row.update(result,actual_pair_computations=count,timing_boundary='INSTRUMENTED_UNCHANGED_H1_PARENT_NOT_NEW_METHOD_SPEED')
            if final is not None:
                assert guided is not None and len(guided)==36
                directory.mkdir(exist_ok=True);path=directory/'parent-vectors.pt';assert not path.exists()
                torch.save({'final_latent':final,'guided':guided},path)
                row.update(parent_vectors={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size},
                    guided_sha256=[tree_digest(g) for g in guided],final_latent_sha256=tree_digest(final),
                    old_H1_final_equal=tree_digest(final)==baseline[sample.name]['final_latent_sha256'],
                    old_H1_actions_equal=row['actions']==baseline[sample.name]['actions'])
                if not row['old_H1_final_equal'] or not row['old_H1_actions_equal']:raise ValueError('Actual H1 parent no longer matches frozen reference')
                if planned['kind']=='BASELINE':controls[sample.name]=(guided,final,row['actions'])
                else:
                    old_control=controls.get(sample.name)
                    if old_control is None:raise ValueError('No resident baseline; keep missing control, do not substitute')
                    row['all36_guided_final_actions_equal_to_resident_baseline']=(all(torch.equal(x,y) for x,y in zip(old_control[0],guided))
                        and torch.equal(old_control[1],final) and old_control[2]==row['actions'])
            row['ended_unix']=time.time();validate_parent(row,planned);save()
            assert all(p._version==version for p,version in versions)
        initial.restore();assert initial.fingerprint()==initial_sha
        actual=sum(r['actual_pair_computations'] for r in state['runs'])
        complete_labels=sum(len(r.get('diagnostic_points',[])) for r in state['runs'])
        state.update(status='PA_LOCAL12_FULL8_GPU_EXITED_RAW_CPU_PENDING' if actual==528 and complete_labels==12
            else 'PA_LOCAL12_FULL_SCOPE_REJECTIONS_OR_MISSING_LABELS_RETAINED',actual_pair_computations=actual,actual_origins=complete_labels)
        save()
    except BaseException as e:
        state.update(status='PA_LOCAL12_TECHNICAL_STOP_FULL8_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
