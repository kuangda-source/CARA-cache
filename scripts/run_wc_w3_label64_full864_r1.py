"""One resident guarded H1 model, eighteen original W3 label parents.

The CPU entry inspects actual imports/assets and full contracts only. GPU mode
requires distinct new human authority and a fresh whole-card supervisor/lock.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid')
    p.add_argument('--authorization',type=Path);a=p.parse_args()
    sys.path.insert(0,str(a.stage/'src'))
    if not a.cpu_check:
        if a.authorization is None:raise ValueError('New GPU stopped; distinct full W3 authorization required')
        from wcomr.w3_label64_production_contract_r1 import SCOPE,sha
        from wcomr.w3_label64_admission_r1 import verify_permission
        scope=json.loads((a.stage/SCOPE).read_text());proof=json.loads((a.stage/'production-CPU-result.json').read_text())
        registration=json.loads((a.stage/'registration.json').read_text())
        assert registration['source_revision']==a.source_revision
        verify_permission(scope,json.loads(a.authorization.read_text()),proof,registration,
            scope_sha256=sha(a.stage/SCOPE),proof_sha256=sha(a.stage/'production-CPU-result.json'))
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if a.cpu_check:os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path[:0]=[str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    original_tensor_load=torch.load
    if a.cpu_check:
        assert not torch.cuda.is_initialized()
        def forbidden(*args,**kwargs):raise RuntimeError('W3 production CPU forbids CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('W3 CPU denies Triton execution: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        previous=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        import cosmos_predict2.inference as im
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=previous
    from wcomr.w3_label64_production_r1 import validate_assets,write,sha,RUN,CPU_STATUS,MODE_REF
    from wcomr.w3_label64_production_contract_r1 import require_new_permission,SCOPE,validate
    from wcomr.w3_label64_h1_owner_r1 import install_w3_labels
    from wcomr.w3_label64_fullpost_r1 import check_row
    from wcomr import source_phase_absolute_h1_batch_r1 as batch
    from wcomr import clean_speed20_r1 as clean
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.runtime_config import install_core_inference_registration
    scope,reg,base,old,inputs,values,requests,plan,numeric,cost=validate_assets(a.project,a.stage)
    counts=scope['scope_counts'];calibration,specs,refs,evidence=inputs
    samples=[InferenceArguments(**r) for r in requests]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,requests))
    setup=SetupArguments(**{**values['setup'],'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    parameters={'SOURCE_PHASE':values['H1']};previous_parameters=values['previous']
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:batch.execute(dummy,samples[0],'TABLE_PHASE_H1',table_parameters=parameters,previous_parameters=previous_parameters,
            runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=calibration,specs=specs[base['strategy']],
            inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=base['expected_real_shape'],audit=True)
        except ValueError as error:assert str(error)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded W3 actual parent accepted')
        import importlib.util
        import unittest
        # Only the explicit synthetic temporary-folder raw fixture may restore
        # its saved tensors during this exiting CPU process. Real weights stay forbidden.
        import tempfile
        original_temporary=tempfile.TemporaryDirectory;owned_temporary_roots=[]
        def owned_temporary(*args,**kwargs):
            temporary=original_temporary(*args,**kwargs)
            owned_temporary_roots.append(Path(temporary.name).resolve());return temporary
        def synthetic_loader(path,**kwargs):
            path=Path(path).resolve()
            assert any(path.is_relative_to(root) for root in owned_temporary_roots)
            assert path.suffix=='.pt' and kwargs=={'weights_only':True,'map_location':'cpu'}
            return original_tensor_load(path,**kwargs)
        tempfile.TemporaryDirectory=owned_temporary;torch.load=synthetic_loader
        verdicts={}
        try:
            for filename,count in (('test_w3_label64_production_contract_r1.py',4),('test_w3_label64_fullpost_r1.py',7),
                    ('test_w3_label64_launch_r1.py',12)):
                spec=importlib.util.spec_from_file_location('W3_actual_CPU_'+filename,a.stage/'tests'/filename)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(module))
                assert result.wasSuccessful() and result.testsRun==count;verdicts[filename]=count
        finally:tempfile.TemporaryDirectory=original_temporary;torch.load=forbidden
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':CPU_STATUS,'source_revision':reg['source_revision'],'exit_code':0,
            'registration_sha256':sha(a.stage/'registration.json'),'scope_sha256':sha(a.stage/SCOPE),
            'scope_counts':counts,'matrix':plan,'GPU_submissions':0,'weights_loaded':0,'CUDA_initialized':False,
            'full72_collector_CPU_accepted':True,'collector_proof':numeric,'full90_post_CPU_controls_accepted':True,
            'full90_saved_synthetic_files1242_tensors':True,'actual_models_instantiated':0,'actual864_model_calls_executed':False,
            'actual_setup_and_eight_InferenceArguments_bound':True,'H1_fingerprint':values['H1']['fingerprint'],
            'original_H1_assets_and_inputs_preserved':True,'unit_tests':verdicts,
            'cost_status':'PROVISIONAL_COMPLETE_COST_NOT_CURRENT_MEASURED','forecast_complete_GPUh':cost['provisional_forecast_complete_GPUh'],
            'new_GPU_permission_pending':True,'supervisor_and_fresh_admission_CPU_pending':False,
            'whole_card_supervisor_CPU_accepted':True,'launch_controls_accepted':True,'launcher_supervisor_post_paths_verified':True,
            'whole_card_launch_scripts_sha256':{name:sha(a.stage/name) for name in (
                'scripts/launch_wc_w3_label64_full864_r1.py','scripts/supervise_wc_w3_label64_full864_r1.py',
                'scripts/watch_wc_w3_label64_post_cpu_r1.py','scripts/postprocess_wc_w3_label64_full864_cpu_r1.py',
                'src/wcomr/w3_label64_admission_r1.py','tests/test_w3_label64_launch_r1.py')},
            'full_parent_videos_and_real_labels_not_yet_audited':True})
        print(CPU_STATUS);return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    require_new_permission(scope,json.loads(a.authorization.read_text()),proof,
        source_revision=a.source_revision,scope_sha256=sha(a.stage/SCOPE))
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and a.source_revision==reg['source_revision']
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    held=os.fstat(int(os.environ['WC_LOCK_FD']));actual_lock=(a.project/'.sync/f1.lock').stat()
    assert (held.st_dev,held.st_ino)==(actual_lock.st_dev,actual_lock.st_ino)
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN;assert output.is_dir() and not (output/'runner.json').exists()
    state={'status':'W3_LABEL64_INITIALIZING_ONE_RESIDENT_H1','source_revision':a.source_revision,
        'scope_counts':counts,'runs':copy.deepcopy(plan),'pid':os.getpid(),'started_unix':time.time()}
    save=lambda:write(output/'runner.json',state)
    save();init_environment();init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-start
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));initial_sha=initial.fingerprint()
        versions=[(p,p._version) for p in net.parameters()];controls={}
        for index,planned in enumerate(plan):
            row=state['runs'][index];row.update(status='RUNNING',started_unix=time.time());save()
            sample=next(s for s in samples if s.name==planned['scene']);directory=(output/planned['id']).resolve()
            initial.restore();assert initial.fingerprint()==initial_sha;verify_shared_eval(net,mode)
            common=dict(runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=calibration,
                specs=specs[base['strategy']],inference_module=im,expected_shape=base['expected_real_shape'],audit=True)
            holder={}
            def writer(step,payload):
                directory.mkdir(exist_ok=True);path=directory/('point-'+str(step)+'.pt');assert not path.exists()
                torch.save(payload,path)
                asset={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'tensor_sha256':tree_digest(payload)}
                row.setdefault('raw_point_artifacts',[]).append({'step':step,'artifact':asset});save()
                return asset
            try:
                if planned['kind']=='DIAGNOSTIC':
                    with install_w3_labels(clean,batch,scheduler,config=base['checkpoint_reserves'],writer=writer,
                            holder=holder,label_provenance='REAL_SAME_STATE_POST_RF'):
                        result,_=batch.execute(inference,sample,'TABLE_PHASE_H1',table_parameters=parameters,
                            previous_parameters=previous_parameters,output=directory,**common)
                    owner=holder['owner'];count=owner.actual_pair_computations
                    row.update(diagnostic_points=owner.records,feature_rows=owner.feature_rows)
                else:
                    result,_=batch.execute(inference,sample,'TABLE_PHASE_H1',table_parameters=parameters,
                        previous_parameters=previous_parameters,output=directory,**common);count=result['guided_pairs']
            except BaseException:
                owner=holder.get('owner')
                if owner is not None:row.update(diagnostic_points=owner.records,feature_rows=owner.feature_rows,
                    actual_pair_computations=owner.actual_pair_computations,source_history=owner.history)
                row['status']='TECHNICAL_FAILURE';save();raise
            final=result.pop('final_latent',None);guided=result.pop('guided',None)
            row.update(result,actual_pair_computations=count,timing_boundary='INSTRUMENTED_ORIGINAL_H1_LABEL_PARENT_NOT_METHOD_LATENCY')
            if final is not None:
                path=directory/'parent-vectors.pt';assert not path.exists();torch.save({'guided':guided,'final_latent':final},path)
                row.update(parent_vectors={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size},
                    guided_sha256=[tree_digest(t) for t in guided],final_latent_sha256=tree_digest(final))
                key=(planned['section'],planned['scene'])
                if planned['kind']=='BASELINE':controls[key]=(guided,final,row['actions'],row['A_history'])
                else:
                    control=controls.get(key)
                    if (control is None or any(not torch.equal(a,b) for a,b in zip(control[0],guided))
                            or not torch.equal(control[1],final) or control[2]!=row['actions'] or control[3]!=row['A_history']):
                        raise ValueError('W3 shadow collection changed the complete original H1 parent')
                    row['all36_parent_guided_actions_Ahistory_final_equal']=True
            if row['status']=='COMPLETE':
                video=Path(row['video_path']).resolve();row['video_artifact']={'path':str(video),'sha256':sha(video),'bytes':video.stat().st_size}
            check_row(row,planned);row['ended_unix']=time.time();save()
            assert all(p._version==version for p,version in versions)
        initial.restore();assert initial.fingerprint()==initial_sha
        state.update(status='W3_LABEL64_FULL18_GPU_EXITED_FULL_RAW_CPU_PENDING',actual_pairs=sum(r.get('actual_pair_computations',0) for r in state['runs']))
        save()
    except BaseException as error:
        state.update(status='W3_LABEL64_TECHNICAL_STOP_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
