"""Audit all50 originals, score all compatible40 videos/full93 on CPU."""
import argparse,hashlib,importlib.metadata,json,os,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.source_conditional_confirmation_production_r1 import CONFIG,RUN,sha,write,validate_contract
    from wcomr.source_confirmation_post_r1 import planned_rows,validate_matrix_rows,aggregate
    from wcomr.source_conditional_confirmation_batch_r1 import METHODS
    c=json.loads((a.stage/CONFIG).read_text());validate_contract(c)
    reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert not Path('/proc/'+str(sup['pid'])).exists() and not Path('/proc/'+str(sup['child_pid'])).exists()
    assert sup['status']=='SOURCE_CONFIRMATION_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert sup['source_revision']==reg['source_revision']
    ledger_sha=sha(a.project/'reports/budget.json');runner=json.loads((root/'runner.json').read_text())
    assert sha(root/'runner.json')==sup['runner_sha256']
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbidden(*args,**kw):raise RuntimeError('Confirmation CPU scoring prohibits CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    start=time.perf_counter();dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    result={'status':'SOURCE_CONFIRMATION_ALL50_RAW_AUDIT_RUNNING','rows':[],
        'source_revision':sup['source_revision'],'scope_counts':c['scope_counts'],
        'budget_before_sha256':ledger_sha,'candidate_freeze_sha256':c['candidate_freeze_sha256'],
        'GPU_submissions':0,'ledger_written':False,'confirmation_input_prompt_count':4,
        'physics_or_semantic_quality_claim':False,'stable_repeated_speed_benchmark_claim':False}
    save=lambda:write(dest,result);save()
    actual={r['id']:r for r in runner['runs']}
    try:
        for planned in planned_rows(c):
            row=json.loads(json.dumps(actual.get(planned['id'],{**planned,'status':'NOT_REACHED_FULL_SCOPE_RETAINED'})))
            result['rows'].append(row);assert all(row[k]==v for k,v in planned.items())
            if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):save();continue
            artifact=row['final_artifact'];path=Path(artifact['path']).resolve()
            assert path.is_relative_to(root) and sha(path)==artifact['sha256'] and path.stat().st_size==artifact['bytes']
            final=torch.load(path,map_location='cpu',weights_only=True)['final_latent']
            assert tree_digest(final)==row['final_latent_sha256'] and list(final.shape)==[1,16,24,54,96]
            assert bool(torch.isfinite(final).all()) and row['solver_steps']==row['guided_pairs']==36
            assert row['core_seconds']>0 and row['write_deferred_after_main_timer']
            assert row['actual_request_seed']==planned['seed']
            hist=row.get('source_history',[]);actions=row.get('actions')
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
                for frame,pts,tbase in frames:digest.update(frame.tobytes());count+=1
            assert count==93 and metadata['HWC']==[432,768,3]
            row.update(video_artifact={'path':str(video),'sha256':sha(video),'bytes':video.stat().st_size},
                decoded_video={'frames':count,'probe':metadata,'RGB_sha256':digest.hexdigest()},endpoint_audit='PASS')
            save()
        done=[r for r in result['rows'] if r.get('endpoint_audit')=='PASS'];timed=[r for r in done if r['section']=='TIMED']
        result.update(accepted_paths=len(done),accepted_scientific_paths=len(timed),
            rejected_paths=sum(r['status'] in ('VIDEO_REJECTED','TEXT_REJECTED') for r in result['rows']))
        if sup['child_exit_code']!=0 or len(runner['runs'])!=50:
            result['status']='SOURCE_CONFIRMATION_INCOMPLETE_TECHNICAL_ALL50_SCOPE_RETAINED';save();return
        validate_matrix_rows(c,result['rows'])
        resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
        result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4'
        assert Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for param in metric.parameters():param.requires_grad_(False)
        for row in timed:
            native=next((r for r in timed if r['scene']==row['scene'] and r['method']=='NATIVE'),None)
            if native is None:row['LPIPS_missing_reason']='SAME_INPUT_AND_SEED_NATIVE_NOT_ACCEPTED';save();continue
            with decoded_video(native['video_path']) as left,decoded_video(row['video_path']) as right:
                row['LPIPS']=score_pair(left,right,metric,reference_sha256=native['video_artifact']['sha256'],candidate_sha256=row['video_artifact']['sha256'])
            save()
        warm=[];old_controls=[];baseline=json.loads((a.stage/c['warmup_baseline_ref']).read_text())
        for method in METHODS:
            pair=[r for r in done if r['section']=='WARMUP' and r['method']==method]
            if len(pair)!=2:
                warm.append({'method':method,'status':'REJECTED_WARMUP_RETAINED'});continue
            assert pair[0]['final_latent_sha256']==pair[1]['final_latent_sha256'] and pair[0]['actions']==pair[1]['actions']
            assert pair[0]['decoded_video']['RGB_sha256']==pair[1]['decoded_video']['RGB_sha256']
            warm.append({'method':method,'status':'PASS_REPEATED_FINAL_ACTIONS_FULL93RGB_EQUAL'})
            old=next(r for r in baseline['rows'] if r['method']==method)
            assert old['final_latent_sha256']==pair[0]['final_latent_sha256'] and old['actions']==pair[0]['actions']
            assert old['decoded_video']['RGB_sha256']==pair[0]['decoded_video']['RGB_sha256']
            old_controls.append({'method':method,'status':'PASS_COMPLETE_H1_CAL_CONTROL_EQUAL'})
        result.update(aggregate(c,result['rows']))
        result.update(status='SOURCE_CONFIRMATION_FULL40_SCIENCE_ALL50_AUDITED_93FRAME_SCORED'
            if len(done)==50 and result['scored_formal_videos']==40 and len(old_controls)==5
            else 'SOURCE_CONFIRMATION_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED',
            warm_repeat_controls=warm,original_CAL_controls=old_controls,CPU_wall_seconds=time.perf_counter()-start,
            CUDA_initialized=False,budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert result['budget_after_sha256']==ledger_sha;save()
    except BaseException as error:
        result.update(status='SOURCE_CONFIRMATION_CPU_AUDIT_TECH_FAILED_ALL50_RETAINED',error_type=type(error).__name__,error=str(error));save();raise


if __name__=='__main__':main()
