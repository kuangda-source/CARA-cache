#!/usr/bin/env python3
"""Released-GPU full twelve-output audit and all93-frame LPIPS comparisons."""
import argparse,hashlib,importlib.metadata,json,math,os,sys,time
from pathlib import Path
from collections import Counter
from statistics import mean


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.pi0_suffix8_production_r1 import RUN,CONFIG,COUNTS,sha,write
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbid(*a,**k):raise RuntimeError('Suffix CPU audit prohibits CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='PI0_SUFFIX8_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not Path('/proc/'+str(sup['pid'])).exists() and not Path('/proc/'+str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    before=sha(a.project/'reports/budget.json');dest=a.stage/'CPU-final-results.json';assert not dest.exists();start=time.perf_counter()
    result={'status':'PI0_SUFFIX8_RAW_AND_FRAME_CPU_RUNNING','scope_counts':COUNTS,'parents':[],'outputs':[],
        'comparisons':[],'GPU_supervisor':sup,'source_revision':sup['source_revision'],'GPU_submissions':0,'ledger_written':False,
        'budget_before_sha256':before,'four_CAL_seed0_not_unseen_confirmation':True,'instrumented_suffix_time_not_clean_latency':True}
    save=lambda:write(dest,result);save()
    bindings=json.loads((a.stage/c['baseline_ref']).read_text())['bindings']
    def load(bound):
        p=Path(bound['path']).resolve();assert p.is_relative_to(root) and sha(p)==bound['sha256'] and p.stat().st_size==bound['bytes']
        return torch.load(p,weights_only=True,map_location='cpu')
    def video(bound):
        p=Path(bound['path']).resolve();assert p.is_relative_to(root) and sha(p)==bound['sha256'] and p.stat().st_size==bound['bytes']
        h=hashlib.sha256();n=0;meta=probe_video(p)
        with decoded_video(p) as frames:
            for f,pts,tbase in frames:h.update(f.tobytes());n+=1
        assert n==93 and meta['HWC']==[432,768,3]
        return {'artifact':bound,'RGB_sha256':h.hexdigest(),'frames':n,'probe':meta}
    try:
        if sup['child_exit_code']!=0 or len(runner['runs'])!=4 or any(r['status']!='COMPLETE' for r in runner['runs']):
            result['status']='PI0_SUFFIX8_INCOMPLETE_FULL266_SCOPE_RETAINED';save();return
        for parent in runner['runs']:
            scene=parent['scene'];bind=bindings[scene];raw=load(parent['parent_vectors'])
            assert parent['original_parent_all36_guided_equal'] and parent['original_parent_final_actions_equal']
            assert tree_digest(raw['final_latent'])==bind['final_latent_sha256'] and [tree_digest(g) for g in raw['guided']]==bind['guided_sha256']
            parent_path=Path(parent['video_path']);parent_bound={'path':str(parent_path),'sha256':sha(parent_path),'bytes':parent_path.stat().st_size}
            audited=video(parent_bound);assert audited['RGB_sha256']==bind['parent_RGB_sha256']
            result['outputs'].append({'scene':scene,'label':'PARENT_PI0','video':audited,'final_latent_sha256':parent['final_latent_sha256']})
            event=parent['event'];point=parent['point'];n=point['chosen']['step']
            assert event['actual_teacher_calls']==0 and event['one_step_readout_only'] and len(event['serial_restores'])==4
            assert parent['actual_pair_computations']==36+2*(37-n)
            expected=['ALTERNATIVE','DEFAULT_PI0'] if c['mirror_order'][[r['name'] for r in c['requests']].index(scene)] else ['DEFAULT_PI0','ALTERNATIVE']
            assert [b['label'] for b in event['branches']]==expected
            for b in event['branches']:
                tensors=load(b['artifact']);assert set(tensors)=={'final_latent','guided'} and tree_digest(tensors)==b['artifact']['tensor_sha256']
                assert all(bool(torch.isfinite(t).all()) for t in [tensors['final_latent']]+tensors['guided'])
                assert len(tensors['guided'])==len(b['actions'])==len(b['source_policy_tail'])==37-n
                assert [tree_digest(g) for g in tensors['guided']]==b['guided_sha256'] and tree_digest(tensors['final_latent'])==b['final_latent_sha256']
                assert b['actions'][0]=='CC' and b['readout_actions'][0]==b['first_readout']
                assert b['source_policy_tail'][0]['source_policy']['decision']['reason']=='MATH_EVENT_SUFFIX_FIRST:'+b['first_readout']
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in b['source_policy_tail'][1:])
                first=b['source_policy_tail'][0];assert first['true_D_before']==first['true_D_after']
                for h in b['source_policy_tail']:
                    if h['action']!='DD':assert h['true_D_before']==h['true_D_after']
                    if h['action']=='PP':assert h['source_policy']['creation_floor_proxy_after']>0 and all(s['kind']=='P' and not s['RA_zero_risk_reset_allowed'] for s in h['working_sources'])
                frames=video(b['artifact']['video_artifact'])
                if b['label']=='DEFAULT_PI0':
                    assert b['actions']==parent['actions'][n-1:] and b['guided_sha256']==parent['guided_sha256'][n-1:]
                    assert torch.equal(tensors['final_latent'],raw['final_latent']) and frames['RGB_sha256']==audited['RGB_sha256']
                sample=b['instrumented_suffix_sampling_seconds'];vae=b['artifact']['VAE_and_video_guardrail_seconds']
                assert all(math.isfinite(t) and t>=0 for t in (sample,vae,b['research_endpoint_export_seconds']))
                result['outputs'].append({'scene':scene,'label':b['label'],'first_readout':b['first_readout'],'video':frames,
                    'final_latent_sha256':b['final_latent_sha256'],'instrumented_sampling_seconds':sample,'VAE_guardrail_seconds':vae,
                    'instrumented_remaining_main_seconds':sample+vae,'research_export_seconds':b['research_endpoint_export_seconds'],
                    'research_upload_seconds':b['artifact']['research_CPU_to_GPU_upload_seconds'],'video_write_seconds':b['artifact']['video_write_seconds'],
                    'actual_suffix_actions':b['actions'],'actual_suffix_counts':dict(Counter(b['actions'])),'raw_artifact':b['artifact']})
            result['parents'].append({'scene':scene,'point':point,'actual_pair_computations':parent['actual_pair_computations'],
                'all36_guided_actions_final_and93RGB_original_equal':True,'default_suffix_all_remaining_original_equal':True});save()
        assert len(result['outputs'])==12 and len(result['parents'])==4 and sum(p['actual_pair_computations'] for p in result['parents'])==266
        resource=a.project/c['LPIPS_resource'];result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        assert result['LPIPS_resource_identity']['server_receipt_sha256']==c['LPIPS_resource_receipt_sha256']
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4' and Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in metric.parameters():parameter.requires_grad_(False)
        for output in result['outputs']:
            ref=bindings[output['scene']]['native_video_artifact'];assert sha(ref['path'])==ref['sha256']
            with decoded_video(ref['path']) as left,decoded_video(output['video']['artifact']['path']) as right:
                output['LPIPS']=score_pair(left,right,metric,reference_sha256=ref['sha256'],candidate_sha256=output['video']['artifact']['sha256'])
            save()
        for scene in bindings:
            by={x['label']:x for x in result['outputs'] if x['scene']==scene};d,alt=by['DEFAULT_PI0'],by['ALTERNATIVE']
            assert d['LPIPS']['frame_distances']==by['PARENT_PI0']['LPIPS']['frame_distances']
            result['comparisons'].append({'scene':scene,'point':next(p['point'] for p in result['parents'] if p['scene']==scene),
                'Y_quality_default_minus_alternative':d['LPIPS']['mean_LPIPS']-alt['LPIPS']['mean_LPIPS'],
                'Y_instrumented_time_default_minus_alternative':d['instrumented_remaining_main_seconds']-alt['instrumented_remaining_main_seconds'],
                'default_LPIPS':d['LPIPS']['mean_LPIPS'],'alternative_LPIPS':alt['LPIPS']['mean_LPIPS'],
                'default_main_seconds':d['instrumented_remaining_main_seconds'],'alternative_main_seconds':alt['instrumented_remaining_main_seconds'],
                'default_counts':d['actual_suffix_counts'],'alternative_counts':alt['actual_suffix_counts'],
                'all93_paired_frames':True,'future_action_changes_are_intervention_outcomes':True,'single_pair_timing_NOT_repeated_clean_speed':True})
        result.update(status='PI0_SUFFIX8_ALL4_PARENTS8_SUFFIXES12_OUTPUTS_AUDITED_ALL93_SCORED',
            accepted_videos=12,scored_videos=12,CPU_wall_seconds=time.perf_counter()-start,CUDA_initialized=False,
            mean_Y_quality=mean(x['Y_quality_default_minus_alternative'] for x in result['comparisons']),
            budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert before==result['budget_after_sha256'];save()
    except BaseException as e:
        result.update(status='PI0_SUFFIX8_CPU_TECH_FAILED_FULL266_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise


if __name__=='__main__':main()
