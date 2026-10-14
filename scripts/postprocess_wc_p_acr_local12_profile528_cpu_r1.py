"""Audit all original parents/point tensors after GPU release, on CPU only."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2',TORCH_HOME='/home/gaokuangda/.cache/torch')
    sys.path.insert(0,str(a.stage/'src'))
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    from wcomr.p_acr_profile528_production_r1 import CONFIG,RUN,COUNTS,sha,write,matrix,validate_parent
    from wcomr.p_acr_profile528_post_r1 import audit_point
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    import hashlib
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='PA_LOCAL12_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not Path('/proc/'+str(sup['pid'])).exists() and not Path('/proc/'+str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    before=sha(a.project/'reports/budget.json');dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    result={'status':'PA_LOCAL12_RAW_CPU_AUDIT_RUNNING','scope_counts':COUNTS,'parents':[],'points':[],
        'source_revision':reg['source_revision'],'GPU_submissions':0,'budget_before_sha256':before,
        'method_endpoint_or_net_speed_claim':False,'GPU_supervisor':sup}
    save=lambda:write(dest,result);save();start=time.perf_counter()
    coeff=json.loads((a.stage/c['references']['coefficients']['ref']).read_text())
    base={r['scene']:r for r in json.loads((a.stage/c['references']['baseline']['ref']).read_text())['rows']}
    controls={};raw_paths=set();raw_tensors=0
    def load(asset):
        path=Path(asset['path']).resolve()
        assert path.is_relative_to(root) and sha(path)==asset['sha256'] and path.stat().st_size==asset['bytes']
        raw_paths.add(str(path));return torch.load(path,weights_only=True,map_location='cpu')
    def rgb(path):
        probe=probe_video(path);assert probe['HWC']==[432,768,3]
        h=hashlib.sha256();n=0
        with decoded_video(path) as frames:
            for frame,pts,tbase in frames:h.update(frame.tobytes());n+=1
        assert n==93;return h.hexdigest()
    try:
        assert len(runner['runs'])==8
        if sup['child_exit_code']!=0:
            result.update(status='PA_LOCAL12_TECHNICAL_STOP_FULL_SCOPE_RETAINED',runner_status=runner['status']);save();return
        for row,planned in zip(runner['runs'],matrix(c)):
            validate_parent(row,planned)
            parent={'id':planned['id'],'scene':row['scene'],'kind':row['kind'],'status':row['status']}
            if row['status']=='TEXT_REJECTED':
                parent['missing_points']=[s for s in c['states'] if s['scene']==row['scene']] if row['kind']=='DIAGNOSTIC' else []
                result['parents'].append(parent);save();continue
            raw=load(row['parent_vectors']);assert set(raw)=={'guided','final_latent'} and len(raw['guided'])==36
            assert [tree_digest(g) for g in raw['guided']]==row['guided_sha256']
            assert tree_digest(raw['final_latent'])==row['final_latent_sha256']==base[row['scene']]['final_latent_sha256']
            assert row['old_H1_final_equal'] and row['old_H1_actions_equal'] and row['actions']==base[row['scene']]['actions']
            raw_tensors+=37
            if row['kind']=='BASELINE':controls[row['scene']]=raw
            else:
                old=controls[row['scene']]
                assert all(torch.equal(x,y) for x,y in zip(old['guided'],raw['guided'])) and torch.equal(old['final_latent'],raw['final_latent'])
                for record in row['diagnostic_points']:
                    payload=load(record['artifact']);assert tree_digest(payload)==record['artifact']['tensor_sha256']
                    report=audit_point(payload,record,c,coeff,row['source_history'][record['point']['step']-1],c['expected_real_shape'])
                    report['raw_artifact']=record['artifact'];result['points'].append(report);raw_tensors+=40
            if row['status']=='COMPLETE':
                video=Path(row['video_path']).resolve();assert video.is_relative_to(root)
                h=rgb(video);assert h==base[row['scene']]['decoded_video']['RGB_sha256']
                parent.update(complete93_RGB_equal_to_original_H1=True,RGB_sha256=h,
                    video_artifact={'path':str(video),'sha256':sha(video),'bytes':video.stat().st_size})
            else:parent['video_rejection_retained']=True
            parent['actual_pair_computations']=row['actual_pair_computations'];result['parents'].append(parent);save()
        actual=sum(r.get('actual_pair_computations',0) for r in result['parents'])
        # These are unchanged H1 parent videos. Full-frame Native distance is
        # a parent-control result, not the endpoint of an ACR policy.
        from wcomr.lpips_resource_identity import audit
        from wcomr.rv0_lpips import score_pair
        native_ref='manifests/wc_source_phase_h1_four_controls_bindings_r1_20261013.json'
        assert sha(a.stage/native_ref)==reg['payload_sha256'][native_ref]
        natives={r['scene']:r for r in json.loads((a.stage/native_ref).read_text())['rows'] if r['method']=='NATIVE'}
        assert set(natives)=={r['name'] for r in c['requests']}
        resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
        result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'))
        import lpips
        import importlib.metadata
        assert importlib.metadata.version('lpips')=='0.1.4' and Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in metric.parameters():parameter.requires_grad_(False)
        for parent in result['parents']:
            if parent['status']!='COMPLETE':continue
            row=next(r for r in runner['runs'] if r['id']==parent['id']);reference=natives[parent['scene']]['video_artifact']
            assert sha(reference['path'])==reference['sha256']
            assert sha(row['video_path'])==parent['video_artifact']['sha256']
            with decoded_video(reference['path']) as left,decoded_video(row['video_path']) as right:
                parent['LPIPS_to_original_matching_Native']=score_pair(left,right,metric,
                    reference_sha256=reference['sha256'],candidate_sha256=sha(row['video_path']))
            save()
        complete=actual==528 and len(result['points'])==12 and len(raw_paths)==20 and raw_tensors==776
        result.update(status='PA_LOCAL12_ALL8_PARENTS12_POINTS528_PAIRS776_TENSORS_CPU_AUDITED' if complete
            else 'PA_LOCAL12_FULL_SCOPE_REJECTIONS_OR_MISSING_LABELS_RETAINED',actual_pairs=actual,raw_files=len(raw_paths),raw_tensors=raw_tensors,
            video_rejections=sum(r['status']!='COMPLETE' for r in result['parents']),CPU_wall_seconds=time.perf_counter()-start,
            budget_after_sha256=sha(a.project/'reports/budget.json'),CUDA_initialized=False)
        assert result['budget_after_sha256']==before;save()
    except BaseException as e:
        result.update(status='PA_LOCAL12_RAW_CPU_TECH_FAILURE_FULL_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise


if __name__=='__main__':main()
