#!/usr/bin/env python3
"""Audit every original position and score all compatible93-frame outputs."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.paper_baseline_production_r1 import CONFIG,RUN,DEFAULTS,sha,write,validate_contract,diagnostic_warm,audit_row,matrix
    from wcomr.paper_baseline_post_r1 import full_rows,summaries
    from wcomr.h1_cost_curve_post_r1 import endpoint_identity,guided_identity
    from wcomr.gpu_budget_pool_v2 import process_identity
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    validate_contract(c)
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve()
    supervisor=json.loads((root/'supervisor.json').read_text())
    assert supervisor['status']=='N05_CORE66_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert all(process_identity(n)['state'] in (None,'Z','X') for n in (supervisor.get('pid'),supervisor.get('child_pid')) if n)
    runner=json.loads((root/'runner.json').read_text()) if (root/'runner.json').exists() else {'runs':[]}
    if supervisor.get('runner_sha256'):assert sha(root/'runner.json')==supervisor['runner_sha256']
    import torch
    torch.set_num_threads(2)
    def forbidden(*args,**kw):raise RuntimeError('N05 CPU audit forbids CUDA/downloads')
    assert not torch.cuda.is_initialized()
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    start=time.time();destination=a.stage/'CPU-final-results.json';assert not destination.exists()
    scenes=[r['name'] for r in c['requests']]
    value=dict(status='N05_CORE66_RAW_AUDIT_RUNNING',source_revision=supervisor['source_revision'],
        GPU_supervisor=supervisor,scope_counts=c['scope_counts'],rows=full_rows(runner['runs'],scenes),
        audit_failures=[],GPU_submissions=0,ledger_written=False,independent_input_confirmation=False,
        stable_repeated_speed_benchmark_claim=False,direct_corrected_neighbor_comparison_complete=False)
    save=lambda:write(destination,value)
    save();guide_paths={}

    def tensor_file(info,key):
        path=Path(info['path']).resolve()
        assert path.is_relative_to(root) and sha(path)==info['sha256'] and path.stat().st_size==info['bytes']
        return torch.load(path,map_location='cpu',weights_only=True)[key]

    def failure(kind,row,error):
        value['audit_failures'].append(dict(kind=kind,id=row.get('id'),error_type=type(error).__name__,error=str(error)))

    try:
        for row,planned in zip(value['rows'],matrix(scenes)):
            try:
                audit_row(row,planned)
                if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):save();continue
                final=tensor_file(row['final_artifact'],'final_latent')
                assert list(final.shape)==[1,16,24,54,96] and bool(torch.isfinite(final).all())
                assert tree_digest(final)==row['final_latent_sha256']
                del final
                if diagnostic_warm(planned):
                    guides=tensor_file(row['warm_guided_artifact'],'guided')
                    assert len(guides)==36 and tree_digest(guides)==row['warm_guided_tree_sha256']
                    assert all(list(t.shape)==[1,16,24,54,96] and bool(torch.isfinite(t).all()) for t in guides)
                    guide_paths[row['id']]=row['warm_guided_artifact'];del guides
                row['raw_model_audit']='PASS'
                if row['status']=='VIDEO_REJECTED':
                    row['endpoint_audit']='PASS_REJECTED_VIDEO_RETAINED';save();continue
                path=Path(row['video_path']).resolve();assert path.is_relative_to(root)
                meta=probe_video(path);digest=hashlib.sha256();count=0
                with decoded_video(path) as frames:
                    for rgb,pts,base in frames:digest.update(rgb.tobytes());count+=1
                assert count==93 and meta['HWC']==[432,768,3] and meta['fps']==16
                row.update(video_artifact=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size),
                    decoded_video=dict(frames=93,probe=meta,RGB_sha256=digest.hexdigest()),endpoint_audit='PASS')
            except Exception as error:
                row['endpoint_audit']='AUDIT_FAILURE_RETAINED'
                failure('RAW_OR_VIDEO',row,error)
            save()
        done=[r for r in value['rows'] if r.get('endpoint_audit')=='PASS']
        timed=[r for r in done if r['section']=='TIMED']
        resource=a.project/'.sync/wc-rv0-lpips-resource-v2'
        value['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4'
        assert Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in metric.parameters():parameter.requires_grad_(False)
        for row in timed:
            reference=next((r for r in timed if r['scene']==row['scene'] and r['method']=='NATIVE35'),None)
            if reference is None:
                row['LPIPS_missing_reason']='MATCHED_FRESH_NATIVE35_NOT_ACCEPTED';save();continue
            try:
                with decoded_video(reference['video_path']) as left,decoded_video(row['video_path']) as right:
                    row['LPIPS']=score_pair(left,right,metric,
                        reference_sha256=reference['video_artifact']['sha256'],candidate_sha256=row['video_artifact']['sha256'])
            except Exception as error:failure('LPIPS',row,error)
            save()
        warm=[];guided=[]
        for method in c['methods']:
            arms=[next((r for r in done if r['id']==f'warm_{repeat}_{method}'),None) for repeat in (1,2)]
            if any(r is None for r in arms):
                warm.append(dict(method=method,status='MISSING_OR_REJECTED_RETAINED'));continue
            try:
                endpoint_identity(*arms)
                assert arms[0].get('A_history')==arms[1].get('A_history')
                formal=next((r for r in timed if r['method']==method and r['scene']==arms[0]['scene']),None)
                if formal is not None:
                    endpoint_identity(formal,arms[0]);assert formal.get('A_history')==arms[0].get('A_history')
                warm.append(dict(method=method,status='PASS',same_scene_formal_equal=formal is not None))
            except Exception as error:failure('WARM_REPEAT',arms[0],error)
        for method in DEFAULTS:
            keys=[f'warm_{i}_{method}' for i in (1,2)]
            if any(k not in guide_paths for k in keys):
                guided.append(dict(method=method,status='MISSING_OR_REJECTED_RETAINED'));continue
            try:
                left=tensor_file(guide_paths[keys[0]],'guided');right=tensor_file(guide_paths[keys[1]],'guided')
                guided_identity(left,right);del left,right
                guided.append(dict(method=method,status='PASS_ALL36_GUIDED_EQUAL',outputs_per_arm=36))
            except Exception as error:failure('WARM_GUIDED',{'id':method},error)
        binding=c['references']['default20'];assert sha(a.stage/binding['ref'])==binding['sha256']
        controls=[]
        for prior in json.loads((a.stage/binding['ref']).read_text())['rows']:
            row=next((r for r in timed if (r['scene'],r['method'])==(prior['scene'],prior['method'])),None)
            if row is None:
                controls.append(dict(scene=prior['scene'],method=prior['method'],status='MISSING_OR_REJECTED_RETAINED'));continue
            try:
                for name in ('final_artifact','video_artifact'):
                    asset=prior[name];assert sha(asset['path'])==asset['sha256'] and Path(asset['path']).stat().st_size==asset['bytes']
                endpoint_identity(row,prior);assert row.get('A_history')==prior.get('A_history')
                controls.append(dict(scene=row['scene'],method=row['method'],status='PASS_ORIGINAL420_ENDPOINT_EQUAL'))
            except Exception as error:failure('ORIGINAL420_DEFAULT',row,error)
        value.update(summaries(value['rows'],scenes))
        value.update(warm_repeat_controls=warm,warm_guided_controls=guided,original420_default_controls=controls,
            artifact_inventory=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
                for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.pt','.mp4')],
            accepted_scientific_videos=len(timed),scored_scientific_videos=sum('LPIPS' in r for r in timed),
            original_runner_paths=len(runner['runs']),CPU_wall_seconds=time.time()-start,CUDA_initialized=False)
        incomplete=supervisor.get('child_exit_code')!=0 or len(runner['runs'])!=66
        complete=(not incomplete and not value['audit_failures'] and len(done)==66
            and value['scored_scientific_videos']==44 and len(warm)==11 and len(guided)==5 and len(controls)==20
            and all(r['status'].startswith('PASS') for r in warm+guided+controls))
        value['status']=('N05_CORE66_COMPLETE44_AUDITED_93FRAME_SCORED' if complete else
            'N05_CORE66_AUDIT_FAILURE_FULL_SCOPE_RETAINED' if value['audit_failures'] else
            'N05_CORE66_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED' if incomplete else
            'N05_CORE66_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCES_RETAINED')
        save()
        if value['audit_failures']:raise RuntimeError('N05 audit failures retained in complete result')
    except BaseException as error:
        value.update(CPU_terminal_error_type=type(error).__name__,CPU_terminal_error=str(error),CPU_wall_seconds=time.time()-start)
        if not value['status'].startswith('N05_CORE66_AUDIT_FAILURE'):
            value['status']='N05_CORE66_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        save();raise

if __name__=='__main__':main()
