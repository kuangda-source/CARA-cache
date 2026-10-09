#!/usr/bin/env python3
"""Reload the complete comparison's real vectors and every accepted full video."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.cfg_ra_comparison_production import validate,validate_selected,sha,bound_prior
    c,_=validate(a.project,a.stage);validate_selected(c,a.project,a.stage)
    import torch
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('Released-GPU comparison audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.cfg_ra_baseline_with_references import verify_comparison,audit_comparison_vectors
    from wcomr.rv0_video_reader import probe_video,decoded_video
    out=a.project/'outputs'/c['execution_run_id']
    supervisor=json.loads((out/'supervisor.json').read_text())
    assert supervisor['exit_code']==0 and not any(Path('/proc/'+str(supervisor[k])).exists() for k in ('pid','child_pid'))
    source=out/'diagnostic/receipt.json';receipt=json.loads(source.read_text());state=receipt['comparison']
    assert receipt['config']==c and receipt['source_revision']==supervisor['source_revision']
    assert receipt['status']=='REAL_RA_COMPARISON_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert state['reference_initial_state_restored'] and state['batch']['initial_state_restored']
    start=time.perf_counter();verdict=verify_comparison(state)
    prior,threshold=bound_prior(c,a.stage)
    assert receipt['actual_initial_threshold']==threshold
    assert state['batch']['calibration_fingerprint']==prior.fingerprint and state['batch']['RA_threshold']==threshold['threshold']
    raw=audit_comparison_vectors(state,out/'diagnostic',torch.load,c['expected_real_shape'])
    videos=[];costs=[];matched=[]
    for request,ref in zip(state['batch']['requests'],state['references']):
        group=[]
        for row in request['paths']:
            assert all(len(x['components'])==c['expected_real_components'] for x in row['checkpoints'])
            group.append((row['method'],row['video_artifact']))
            costs.append({'sample_name':request['sample_name'],'method':row['method'],
                'actions':row['actions'],'complete_branch_calls':sum(x.count('D') for x in row['actions']),
                'instrumented_pipeline_wall_seconds':row['instrumented_pipeline_wall_seconds']})
        if ref['outcome']=='ACCEPTED':group.append(('NATIVE',ref['artifact']))
        costs.append({'sample_name':request['sample_name'],'method':'NATIVE','outcome':ref['outcome'],
            'complete_branch_calls':ref['block_counts']['full_calls'],
            'instrumented_pipeline_wall_seconds':ref['pipeline_wall_seconds']})
        probes={}
        for method,art in group:
            path=Path(art['path']).resolve()
            assert path.is_relative_to((out/'diagnostic').resolve())
            assert path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
            probe=probe_video(path);count=0;decoded=hashlib.sha256()
            with decoded_video(path) as frames:
                for frame,pts,base in frames:
                    assert list(frame.shape)==[432,768,3]
                    count+=1;decoded.update(frame.tobytes())
            assert count==93 and probe['fps']==16
            item={'sample_name':request['sample_name'],'method':method,'path':str(path),
                  'bytes':art['bytes'],'sha256':art['sha256'],'probe':probe,
                  'decoded_RGB_SHA':decoded.hexdigest(),'all_frames_shape':[count,432,768,3]}
            probes[method]=item;videos.append(item)
        if 'NATIVE' in probes:
            for method in ('WC','JOINT_NATIVE','RA'):
                assert probes[method]['probe']==probes['NATIVE']['probe']
                matched.append({'sample_name':request['sample_name'],'method':method,
                    'candidate':probes[method],'reference':probes['NATIVE']})
    accepted=verdict['accepted_reference_slots']
    assert len(videos)==6+accepted and len(matched)==3*accepted
    assert {str(x.resolve()) for x in (out/'diagnostic').rglob('*.mp4')}=={x['path'] for x in videos}
    result={'status':'REAL_RA_COMPARISON_FULL_RAW_CPU_AUDIT_NOT_QUALITY_OR_CLEAN_LATENCY',
        'source_revision':receipt['source_revision'],'run_id':c['execution_run_id'],
        'config_sha256':sha(a.stage/'ra-comparison-config.json'),'runner_receipt_sha256':sha(source),
        'scope_counts':c['preregistration']['scope_counts'],'verdict':verdict,'actual_tensor_audit':raw,
        'actual_total_guided_reloaded':216+36*accepted,'actual_total_latents_reloaded':6+accepted,
        'videos':videos,'matched_fidelity_pairs':matched,'actual_method_actions_and_costs':costs,
        'actual_real_prior_and_initial_threshold_verified':threshold,
        'all_accepted_complete93_videos_and_raw_vector_artifacts_verified':True,
        'reference_rejections_preserved_without_replacement':True,
        'quality_metrics_pending_uniform_full_frame_scoring':True,'clean_latency_claim':False,
        'CPU_wall_seconds':time.perf_counter()-start,'CUDA_initialized':False,'GPU_submissions':0}
    assert not a.output.exists() and not torch.cuda.is_initialized()
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','actual_total_guided_reloaded','actual_total_latents_reloaded','CPU_wall_seconds','GPU_submissions')}))


if __name__=='__main__':main()
