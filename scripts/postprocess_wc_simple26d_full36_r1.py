#!/usr/bin/env python3
"""All original artifacts, full-frame LPIPS and every actual method/time."""
import argparse,hashlib,importlib.metadata,json,os,sys,time
from pathlib import Path
from statistics import mean

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.simple26d_r1 import RUN,CONFIG,sha,write,validate_contract
    from wcomr.simple26d_r1 import METHODS
    from wcomr.simple26d_r1 import matrix
    diagnostic_warm=lambda row:row['section']=='WARMUP'
    from wcomr.simple26d_r1 import audit_row
    from wcomr.h1_cost_curve_post_r1 import endpoint_identity,guided_identity
    from wcomr.simple26d_post_r1 import full_rows,summaries
    from wcomr.gpu_budget_pool_v2 import BudgetPool
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    from wcomr.gpu_budget_pool_v2 import process_identity
    assert all(process_identity(pid)['state'] in (None,'Z','X') for pid in (sup.get('pid'),sup.get('child_pid')) if pid)
    assert sup['status']=='SIMPLE26D_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    pool_before=BudgetPool(a.project).read();ledger_sha=sha(a.project/'reports/gpu-budget-v2.json')
    runner=json.loads((root/'runner.json').read_text()) if (root/'runner.json').exists() else {'runs':[]}
    if sup.get('runner_sha256'):assert sha(root/'runner.json')==sup['runner_sha256']
    validate_contract(c)
    baseline=json.loads((a.stage/c['references']['baseline']['ref']).read_text())
    assert sha(a.stage/c['references']['baseline']['ref'])==c['references']['baseline']['sha256']
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbidden(*a,**k):raise RuntimeError('N2 CPU scoring prohibits CUDA/download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    start=time.perf_counter();dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    result={'status':'SIMPLE26D_ALL36_RAW_AUDIT_RUNNING','rows':full_rows(runner['runs'],[r['name'] for r in c['requests']]),'source_revision':sup['source_revision'],
        'GPU_supervisor':sup,'scope_counts':c['scope_counts'],'budget_before_sha256':ledger_sha,
        'GPU_submissions':0,'ledger_written':False,'independent_input_confirmation':False,
        'physics_or_semantic_quality_claim':False,'stable_repeated_speed_benchmark_claim':False}
    save=lambda:write(dest,result);save()
    actual={r['id']:r for r in runner['runs']}
    assert len(actual)==len(runner['runs'])
    guided_by_id={}
    try:
        for row,planned in zip(result['rows'],matrix([r['name'] for r in c['requests']])):
            audit_row(row,planned)
            if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):save();continue
            artifact=row['final_artifact'];path=Path(artifact['path']).resolve()
            assert path.is_relative_to(root) and sha(path)==artifact['sha256'] and path.stat().st_size==artifact['bytes']
            final=torch.load(path,map_location='cpu',weights_only=True)['final_latent']
            assert tree_digest(final)==row['final_latent_sha256'] and list(final.shape)==[1,16,24,54,96] and bool(torch.isfinite(final).all())
            assert row['solver_steps']==row['guided_pairs']==36
            if diagnostic_warm(planned):
                artifact=row['warm_guided_artifact'];raw=Path(artifact['path']).resolve()
                assert raw.is_relative_to(root) and sha(raw)==artifact['sha256'] and raw.stat().st_size==artifact['bytes']
                guides=torch.load(raw,map_location='cpu',weights_only=True)['guided']
                assert len(guides)==36 and all(list(x.shape)==[1,16,24,54,96] and bool(torch.isfinite(x).all()) for x in guides)
                assert tree_digest(guides)==row['warm_guided_tree_sha256']
                guided_by_id[row['id']]=guides
            assert row['core_seconds']>0 and row['write_deferred_after_main_timer']
            actions=row.get('actions');hist=row.get('source_history',[])
            if hist:
                assert len(hist)==36 and [h['action'] for h in hist]==actions
                for h in hist:
                    assert h['teacher_calls']==0 and not h['P_updates_true_D_or_zero_risk_RA_anchor']
                    if h['action']!='DD':assert h['true_D_before']==h['true_D_after']
                    if h['action']=='PP':
                        assert all(s['kind']=='P' and not s['RA_zero_risk_reset_allowed'] for s in h['working_sources'])
                        assert h['source_policy']['creation_floor_proxy_after']>0
                row['counts']={'DD':actions.count('DD'),'PP':actions.count('PP'),
                    'C_plain':sum(h['action']=='CC' and h['A_readout']['shared_alpha']==0 for h in hist),
                    'A':sum(h['action']=='CC' and h['A_readout']['shared_alpha']>0 for h in hist),
                    'C_or_A_after_P':sum(h['action']=='CC' and h['working_sources'][0]['kind']=='P' for h in hist)}
            if row['status']=='VIDEO_REJECTED':row['endpoint_audit']='PASS_REJECTED_VIDEO_RETAINED';save();continue
            video=Path(row['video_path']).resolve();assert video.is_relative_to(root)
            metadata=probe_video(video);digest=hashlib.sha256();count=0
            with decoded_video(video) as frames:
                for f,pts,tbase in frames:digest.update(f.tobytes());count+=1
            assert count==93 and metadata['HWC']==[432,768,3]
            row.update(video_artifact={'path':str(video),'sha256':sha(video),'bytes':video.stat().st_size},
                decoded_video={'frames':count,'probe':metadata,'RGB_sha256':digest.hexdigest()},endpoint_audit='PASS')
            save()
        done=[r for r in result['rows'] if r.get('endpoint_audit')=='PASS']
        timed=[r for r in done if r['section']=='TIMED']
        rejected=[r for r in result['rows'] if r['status'] in ('VIDEO_REJECTED','TEXT_REJECTED')]
        result.update(accepted_paths=len(done),accepted_scientific_paths=len(timed),rejected_paths=len(rejected))
        resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
        result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4' and Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for param in metric.parameters():param.requires_grad_(False)
        for reference in baseline['rows']:
            if reference['method']!='NATIVE':continue
            meta=probe_video(reference['video_artifact']['path']);digest=hashlib.sha256();n=0
            assert sha(reference['video_artifact']['path'])==reference['video_artifact']['sha256']
            with decoded_video(reference['video_artifact']['path']) as frames:
                for f,pts,tbase in frames:digest.update(f.tobytes());n+=1
            assert n==93 and meta['HWC']==[432,768,3] and digest.hexdigest()==reference['decoded_video']['RGB_sha256']
        for row in timed:
            reference=next((r for r in baseline['rows'] if r['scene']==row['scene'] and r['method']=='NATIVE'),None)
            if reference is None:row['LPIPS_missing_reason']='SAME_INPUT_NATIVE_NOT_ACCEPTED';save();continue
            with decoded_video(reference['video_artifact']['path']) as left,decoded_video(row['video_path']) as right:
                row['LPIPS']=score_pair(left,right,metric,
                    reference_sha256=reference['video_artifact']['sha256'],candidate_sha256=row['video_artifact']['sha256'])
            save()
        warm_controls=[]
        for method in METHODS:
            pairs=[r for r in done if r['section']=='WARMUP' and r['method']==method]
            if len(pairs)==2:
                assert pairs[0]['final_latent_sha256']==pairs[1]['final_latent_sha256']
                assert pairs[0]['actions']==pairs[1]['actions']
                assert pairs[0]['decoded_video']['RGB_sha256']==pairs[1]['decoded_video']['RGB_sha256']
                formal=next((r for r in timed if r['method']==method and r['scene']==pairs[0]['scene']),None)
                if formal is not None:
                    assert formal['final_latent_sha256']==pairs[0]['final_latent_sha256'] and formal['actions']==pairs[0]['actions']
                    assert formal['decoded_video']['RGB_sha256']==pairs[0]['decoded_video']['RGB_sha256']
                warm_controls.append({'method':method,'warm_repeats_outputs_actions_RGB_equal':True,'same_scene_formal_repeat_equal':formal is not None})
        baseline_controls=[]
        for binding in baseline['rows']:
            if binding['method']=='NATIVE':continue
            row=next((r for r in timed if r['scene']==binding['scene'] and r['method']==binding['method']),None)
            if row is None:
                baseline_controls.append(dict(scene=binding['scene'],method=binding['method'],status='MISSING_OR_REJECTED_RETAINED'));continue
            endpoint_identity(row,binding)
            baseline_controls.append(dict(scene=binding['scene'],method=binding['method'],status='PASS_ORIGINAL420_FINAL_ACTIONS_FULL93RGB_EQUAL'))
        guided_controls=[]
        for method in METHODS:
            keys=[f'warm_{r}_{method}' for r in (1,2)]
            if not all(k in guided_by_id for k in keys):
                guided_controls.append(dict(method=method,status='MISSING_FULL36_RETAINED'));continue
            guided_identity(guided_by_id[keys[0]],guided_by_id[keys[1]])
            guided_controls.append(dict(method=method,status='PASS_ALL36_WARM_REPEAT_EQUAL',outputs_per_arm=36))
        scored=[r for r in timed if 'LPIPS' in r]
        result.update(summaries(result['rows'],[r['name'] for r in c['requests']]))
        complete=(len(scored)==24 and len(done)==36 and len(warm_controls)==6
                  and len(baseline_controls)==8 and all(x['status'].startswith('PASS') for x in guided_controls+baseline_controls)
                  and sup['child_exit_code']==0 and len(runner['runs'])==36)
        result.update(status='SIMPLE26D_FULL24_SCIENCE_ALL36_AUDITED_93FRAME_SCORED' if complete
                      else 'SIMPLE26D_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED',
            scored_scientific_paths=len(scored),warm_repeat_controls=warm_controls,
            original_baseline_controls=baseline_controls,warm_guided_controls=guided_controls,
            independent_input_confirmation=False,stable_repeated_speed_benchmark_claim=False,
            CPU_wall_seconds=time.perf_counter()-start,CUDA_initialized=False,
            budget_after_sha256=sha(a.project/'reports/gpu-budget-v2.json'),pool_before=pool_before,pool_after=BudgetPool(a.project).read())
        assert result['pool_after']['jobs'][RUN]==pool_before['jobs'][RUN];save()
    except BaseException as e:
        result.update(status='SIMPLE26D_CPU_AUDIT_TECH_FAILED_FULL24_RETAINED',error_type=type(e).__name__,error=str(e));save();raise

def copy_row(row):return json.loads(json.dumps(row,allow_nan=False))
if __name__=='__main__':main()
