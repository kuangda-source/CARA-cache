#!/usr/bin/env python3
"""One model; four ordinary P_OFF controls and four isolated F/B parents."""
import argparse,copy,json,os,subprocess,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid');a=p.parse_args()
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    if a.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        def forbidden(*a,**k):raise RuntimeError('Production CPU forbids CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('No CPU Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        prev=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.fb_probe_production_r1 import CONFIG,RUN,UUID,MODE_REF,COUNTS,STRATEGY,sha,write,validate,validate_contract,CPU_STATUS,PRODUCTION_CPU_STATUS
    from wcomr import clean_speed20_r1 as clean
    from wcomr.math_n2_batch_r1 import execute
    from wcomr.fb_probe_r1 import fb_install
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prev
    c,reg,old,inputs,params,baseline=validate(a.project,a.stage,require_CPU=not a.cpu_check)
    if a.cpu_check:
        check=[sys.executable,str(a.stage/'scripts/check_wc_fb_probe_cpu_r1.py'),'--stage',str(a.stage),
            '--runtime',str(a.project/'runtime'),'--output',str(a.stage/'sampling-CPU-result.json')]
        with (a.stage/'sampling-CPU.log').open('x') as log:
            subprocess.run(check,stdout=log,stderr=subprocess.STDOUT,check=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
        sample_proof=json.loads((a.stage/'sampling-CPU-result.json').read_text())
        assert sample_proof['status']==CPU_STATUS and sample_proof['actual_CPU_paths']==16
        assert sample_proof['natural_points']==32 and sample_proof['B_trials']==288
        assert not sample_proof['CUDA_initialized'] and sample_proof['GPU_submissions']==0
        for n,h in reg['payload_sha256'].items():assert sha(a.stage/n)==h
        sample_proof['payload_sha256']=reg['payload_sha256']
        sample_proof['actual_checker_command']=check
        write(a.stage/'sampling-CPU-result.json',sample_proof)
        validate(a.project,a.stage)
    c['_runtime_old_points']={(p['selection']['scene'],p['selection']['chosen']['step']):p for p in c['old_points']}
    old392=json.loads((a.stage/c['old_labels_capture_ref']).read_text())
    old392_parents={v['scene']:v for v in old392['runner']['runs'] if v['kind']=='BASELINE'}
    assert len(old392_parents)==4
    cal,specs,refs,evidence=inputs;samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    if a.cpu_check:
        from importlib.util import spec_from_file_location,module_from_spec
        from types import SimpleNamespace
        sp=spec_from_file_location('fb_probe_supervisor',a.stage/'scripts/supervise_wc_fb_probe_r1.py');m=module_from_spec(sp);sp.loader.exec_module(m)
        cmd=m.child_command(SimpleNamespace(project=a.project,stage=a.stage,source_revision=reg['source_revision']),UUID)
        assert Path(cmd[2])==a.stage/'scripts/run_wc_fb_probe_r1.py' and sha(Path(cmd[2]))==reg['payload_sha256']['scripts/run_wc_fb_probe_r1.py']
        assert cmd[3:]==['--project',str(a.project),'--stage',str(a.stage),'--source-revision',reg['source_revision'],'--gpu-uuid',UUID]
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:execute(dummy,samples[0],'P_OFF',parameters=params,runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=cal,specs=specs[STRATEGY],inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded production accepted')
        mutations={'scope_counts':{**COUNTS,'baseline_parents':0},'states':c['states'][:-1],
            'head_elision':True,'training':True,'fit_in_parent':True,'online_teacher_deployment':True,
            'isolated_exploration':False,'mainline_F_B_enabled':True,'F_labels_reused_only_after_exact_replay':False,
            'automatic_single_job_GPUh':4,'cumulative_cap_GPUh':77.89524658965853,'forecast_complete_GPUh':9.}
        for k,v in mutations.items():
            bad=copy.deepcopy(c);bad[k]=v
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed complete contract accepted: '+k)
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':'FB_PROBE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','exit_code':0,
            'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False,'scope_counts':COUNTS,
            'source_revision':reg['source_revision'],'config_sha256':sha(a.stage/CONFIG),'registration_sha256':sha(a.stage/'registration.json'),
            'sampling_CPU_sha256':sha(a.stage/'sampling-CPU-result.json'),'mutations_refused':list(mutations),'input_evidence':evidence})
        print('FB_PROBE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU');return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['sampling_CPU_sha256']==sha(a.stage/'sampling-CPU-result.json')
    assert proof['status']=='FB_PROBE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert a.source_revision==reg['source_revision'] and os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid==UUID and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    root=a.project/'outputs'/RUN;assert root.is_dir() and not (root/'runner.json').exists()
    state={'status':'FB_PROBE_INITIALIZING','pid':os.getpid(),'runs':[],'source_revision':a.source_revision,
        'scope_counts':COUNTS,'parameters_fingerprint':params['fingerprint'],'started_unix':time.time()}
    save=lambda:write(root/'runner.json',state);save();init_environment();init_output_dir(root,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inf=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-start
        model=inf.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint();versions=[(p,p._version) for p in net.parameters()]
        for i,sample in enumerate(samples):
            common=dict(runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs[STRATEGY],inference_module=im,expected_shape=old['expected_real_shape'],audit=True)
            controls={}
            for kind in ('BASELINE','DIAGNOSTIC'):
                initial.restore();assert initial.fingerprint()==fp;verify_shared_eval(net,mode)
                directory=root/(str(i)+'_'+kind);row={'scene':sample.name,'kind':kind,'status':'RUNNING','started_unix':time.time()}
                state['runs'].append(row);state['status']='FB_PROBE_ALL8_FULL_PATHS_RUNNING';save()
                holder={}
                def writer(scene,step,payload):
                    assert scene==sample.name
                    directory.mkdir(exist_ok=True);path=directory/('point-'+str(step)+'.pt');assert not path.exists();torch.save(payload,path)
                    return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'tensor_sha256':tree_digest(payload)}
                if kind=='BASELINE':result,_=execute(inf,sample,'P_OFF',parameters=params,output=directory,**common)
                else:
                    points=[s for s in c['states'] if s['scene']==sample.name]
                    with fb_install(clean,scheduler,points,c,writer,params,holder):
                        result=clean.execute(inf,sample,'KEEP_A_P',output=directory,**common)
                final=result.pop('final_latent',None);guided=result.pop('guided',None)
                assert final is not None and guided is not None and len(guided)==36 and result['status']=='COMPLETE'
                vectors=directory/'parent-vectors.pt';assert not vectors.exists();torch.save({'final_latent':final,'guided':guided},vectors)
                bind=baseline['bindings'][sample.name]
                row.update(result,parent_vectors={'path':str(vectors),'sha256':sha(vectors),'bytes':vectors.stat().st_size},
                    final_latent_sha256=tree_digest(final),guided_sha256=[tree_digest(g) for g in guided],
                    old_final_equal=tree_digest(final)==bind['final_latent_sha256'],old_actions_equal=result['actions']==bind['actions'],ended_unix=time.time())
                assert row['old_final_equal'] and row['old_actions_equal']
                original392=old392_parents[sample.name]
                assert row['guided_sha256']==original392['guided_sha256']
                assert row['final_latent_sha256']==original392['final_latent_sha256'] and row['actions']==original392['actions']
                row['all36_guided_final_actions_equal_original392']=True
                if kind=='BASELINE':controls={'final':final,'guided':guided,'actions':result['actions']};row['actual_pair_computations']=36
                else:
                    owner=holder['owner'];row.update(diagnostic_points=owner.records,actual_pair_computations=owner.actual_pair_computations,
                        all36_guided_final_actions_equal=all(torch.equal(x,y) for x,y in zip(controls['guided'],guided))
                            and torch.equal(controls['final'],final) and controls['actions']==result['actions'])
                    expected=36+36*sum(v['scene']==sample.name for v in c['b_points'])
                    assert len(owner.records)==4 and owner.actual_pair_computations==expected and row['all36_guided_final_actions_equal']
                    for point in row['diagnostic_points']:
                        oldpoint=c['_runtime_old_points'][(point['scene'],point['step'])]
                        assert point['input_sha256']==oldpoint['input_sha256']
                        assert list(point['parent_pre_action'])==oldpoint['parent_pre_action']
                        point.update(raw_label_artifact=oldpoint['raw_artifact'],parent_control_pass=True)
                save();assert all(p._version==v for p,v in versions)
        initial.restore();assert initial.fingerprint()==fp
        assert len(state['runs'])==8 and sum(r['actual_pair_computations'] for r in state['runs'])==432
        state['status']='FB_PROBE_ALL8_PARENTS16_F4_B432_PAIRS_GPU_COMPLETE_RAW_CPU_PENDING';save()
    except BaseException as e:state.update(status='FB_PROBE_TECHNICAL_STOP_FULL_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
