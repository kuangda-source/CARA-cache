#!/usr/bin/env python3
"""Released-GPU independent CPU video audit, full93-frame fidelity and every timing."""
import argparse,hashlib,importlib.metadata,json,os,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    # This process imports no actual model/attention runtime or GPU adapters.
    from wcomr.e1_diag8_production_r2 import sha,write
    from wcomr.clean_speed20_r1 import RUN,METHODS,SCENES,matrix
    c=json.loads((a.stage/'configs/wc_clean_speed20_r1_20261012.json').read_text());reg=json.loads((a.stage/'registration.json').read_text())
    for n,h in reg['payload_sha256'].items():assert sha(a.stage/n)==h
    output=a.project/'outputs'/RUN;sp=output/'supervisor.json';supervisor=json.loads(sp.read_text())
    assert not Path('/proc/'+str(supervisor['pid'])).exists()
    if supervisor.get('child_pid'):assert not Path('/proc/'+str(supervisor['child_pid'])).exists()
    assert supervisor['status']=='CLEAN_SPEED20_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    budgetsha=sha(a.project/'reports/budget.json');budget=json.loads((a.project/'reports/budget.json').read_text());assert not any('inflight' in k for k in budget)
    runner=json.loads((output/'runner.json').read_text());assert supervisor['runner_sha256']==sha(output/'runner.json')
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('CPU audit/score forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    start=time.perf_counter();rows={r['id']:dict(r) for r in runner['runs']}
    result={'status':'CLEAN_SPEED20_CPU_AUDIT_RUNNING','scope':matrix(),'rows':[],'score_rows':[],
        'source_revision':supervisor['source_revision'],'runner_sha256':sha(output/'runner.json'),'supervisor_sha256':sha(sp),'budget_before_sha256':budgetsha,
        'GPU_supervisor':supervisor,'load_seconds':runner.get('load_seconds'),'GPU_submissions':0,'ledger_written':False}
    dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    save=lambda:write(dest,result)
    save()
    try:
        for planned in matrix():
            r=rows.get(planned['id'],{**planned,'status':'NOT_REACHED_FULL_SCOPE_RETAINED'})
            result['rows'].append(r)
            if r['status']!='COMPLETE':save();continue
            assert all(r[k]==v for k,v in planned.items())
            path=(output/r['id']/'final-latent.pt').resolve();assert path.is_relative_to(output.resolve())
            raw=torch.load(path,map_location='cpu',weights_only=True);tensor=raw['final_latent']
            assert list(tensor.shape)==[1,16,24,54,96] and bool(torch.isfinite(tensor).all())
            assert tree_digest(tensor)==r['final_latent_sha256']==r['expected_old_endpoint_sha256']
            assert r['old_audit_endpoint_equal'] and r['old_actions_equal']
            assert r['solver_steps']==r['guided_pairs']==36 and r['in_timing_guided_copies']==r['in_timing_hashes']==r['research_checkpoints']==0
            assert r['core_seconds']>0 and r['write_deferred_after_main_timer']
            video=Path(r['video_path']).resolve();assert video.is_relative_to(output.resolve())
            metadata=probe_video(video);h=hashlib.sha256();count=0
            with decoded_video(video) as frames:
                for f,pts,tbase in frames:h.update(f.tobytes());count+=1
            assert count==93
            bind=c['old_audit_endpoint_and_action_bindings'][r['scene']+':'+r['method']]
            oldvideo=bind.get('video_artifact') or bind.get('artifact');assert oldvideo is not None
            assert sha(oldvideo['path'])==oldvideo['sha256']
            oldhash=hashlib.sha256()
            with decoded_video(oldvideo['path']) as frames:
                for f,pts,tbase in frames:oldhash.update(f.tobytes())
            r.update(raw_final_artifact={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size},video_artifact={'path':str(video),'sha256':sha(video),'bytes':video.stat().st_size},decoded_video={'probe':metadata,'frames':count,'RGB_sha256':h.hexdigest()},old_decoded_RGB_equal=h.hexdigest()==oldhash.hexdigest())
            assert r['old_decoded_RGB_equal'],'Clean output decode differs from old audit endpoint'
            r['raw_audit']='PASS';save()
        complete=[r for r in result['rows'] if r.get('raw_audit')=='PASS'];timed=[r for r in complete if r['section']=='TIMED']
        result.update(complete_paths=len(complete),timed_paths=len(timed),warmup_paths=len(complete)-len(timed))
        if len(complete)!=40 or len(timed)!=20 or supervisor['child_exit_code']!=0:
            result['status']='INCOMPLETE_TECHNICAL_SCOPE_RETAINED_NOT_SPEED20_RESULT';save();return
        resource=a.project/'.sync/wc-rv0-lpips-resource-v2';result['metric_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4' and Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for param in model.parameters():param.requires_grad_(False)
        for r in timed:
            ref=next(x for x in timed if x['scene']==r['scene'] and x['round']==r['round'] and x['method']=='NATIVE')
            with decoded_video(ref['video_path']) as left,decoded_video(r['video_path']) as right:
                score=score_pair(left,right,model,reference_sha256=ref['video_artifact']['sha256'],candidate_sha256=r['video_artifact']['sha256'])
            r['LPIPS']=score;save()
        compare=[]
        for r in timed:
            lookup={x['method']:x for x in timed if x['scene']==r['scene'] and x['round']==r['round']}
            compare.append({'scene':r['scene'],'method':r['method'],'round':r['round'],'core_seconds':r['core_seconds'],
                'speedup_vs_Native':lookup['NATIVE']['core_seconds']/r['core_seconds'],
                'speedup_vs_WC':lookup['WC']['core_seconds']/r['core_seconds'],
                'speedup_vs_RA':lookup['RA']['core_seconds']/r['core_seconds'],
                'LPIPS_mean':r['LPIPS']['mean_LPIPS']})
        variation=[];increment=[]
        for scene in SCENES:
            for method in METHODS:
                rr=sorted([r for r in timed if r['scene']==scene and r['method']==method],key=lambda r:r['round']);a1,b=rr
                variation.append({'scene':scene,'method':method,'round1_seconds':a1['core_seconds'],'round2_seconds':b['core_seconds'],
                    'range_seconds':abs(b['core_seconds']-a1['core_seconds']),'range_percent_of_mean':abs(b['core_seconds']-a1['core_seconds'])/((b['core_seconds']+a1['core_seconds'])/2)*100,
                    'rounds_RGB_equal':a1['decoded_video']['RGB_sha256']==b['decoded_video']['RGB_sha256']})
            for rep in (1,2):
                nop=next(r for r in timed if r['scene']==scene and r['round']==rep and r['method']=='A_NO_P')
                pp=next(r for r in timed if r['scene']==scene and r['round']==rep and r['method']=='KEEP_A_P')
                increment.append({'scene':scene,'round':rep,'A_NO_P_seconds':nop['core_seconds'],'KEEP_A_P_seconds':pp['core_seconds'],'P_speedup':nop['core_seconds']/pp['core_seconds'],
                    'P_seconds_saved':nop['core_seconds']-pp['core_seconds'],'LPIPS_NO_P':nop['LPIPS']['mean_LPIPS'],'LPIPS_P':pp['LPIPS']['mean_LPIPS'],
                    'LPIPS_loss_reduction':nop['LPIPS']['mean_LPIPS']-pp['LPIPS']['mean_LPIPS'],
                    'P_action_count':(pp['actions'] or []).count('PP')})
        result.update(status='CLEAN_SPEED20_COMPLETE40_ALL20_TIMINGS_AND93_FRAME_SCORES_AUDITED',comparisons_all20=compare,variation_all10=variation,P_increment_all4=increment,
            CPU_wall_seconds=time.perf_counter()-start,budget_after_sha256=sha(a.project/'reports/budget.json'),CUDA_initialized=torch.cuda.is_initialized())
        assert result['budget_after_sha256']==budgetsha and not result['CUDA_initialized'];save()
    except BaseException as e:
        result.update(status='CPU_AUDIT_OR_SCORE_TECH_FAILED_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e),CPU_wall_seconds=time.perf_counter()-start);save();raise
if __name__=='__main__':main()
