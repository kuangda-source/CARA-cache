#!/usr/bin/env python3
"""After original GPU exit, reload every real calibration tensor and full video."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cfg_guided_w1_production import validate,validate_selected,sha
    c,_=validate(args.project,args.stage)
    validate_selected(c,args.project,args.stage)
    import torch
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(2)
    def forbidden(*a,**kw):
        raise RuntimeError('Released-GPU calibration audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden
    torch.hub.download_url_to_file=forbidden
    from wcomr.cfg_guided_w1_sampling import verify_batch,audit_vectors
    from wcomr.rv0_video_reader import probe_video,decoded_video
    out=args.project/'outputs'/c['execution_run_id']
    supervisor=json.loads((out/'supervisor.json').read_text())
    assert supervisor['exit_code']==0 and supervisor['run_id']==c['execution_run_id']
    assert not any(Path('/proc/'+str(supervisor[k])).exists() for k in ('pid','child_pid'))
    source=out/'diagnostic/receipt.json'
    receipt=json.loads(source.read_text())
    state=receipt['batch']
    start=time.perf_counter()
    assert receipt['config']==c and receipt['source_revision']==supervisor['source_revision']
    assert receipt['status']=='REAL_GUIDED_W1_COLLECTION_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert state['initial_state_restored']
    verdict=verify_batch(state)
    context=json.dumps({'source_revision':receipt['source_revision'],
        'run_id':c['execution_run_id'],'config_sha256':sha(args.stage/'a-collection-config.json'),
        'raw_runner_receipt_sha256':sha(source),'model_context':receipt['model_context'],
        'requests':c['preregistration']['requests'],'solver':'UniPC-Karras-36',
        'branch_order':['conditional','negative_prompt'],'guided_weights':[8,-7]},sort_keys=True)
    raw=audit_vectors(state,out/'diagnostic',torch.load,c['expected_real_shape'])
    videos=[]
    for request in state['requests']:
        group=[]
        for row in request['paths']:
            assert all(len(point['components'])==c['expected_real_components'] for point in row['checkpoints'])
            art=row['video_artifact']
            path=Path(art['path']).resolve()
            assert path.is_relative_to((out/'diagnostic').resolve())
            assert path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
            probe=probe_video(path)
            count=0
            decoded_hash=hashlib.sha256()
            with decoded_video(path) as frames:
                for frame,pts,base in frames:
                    assert list(frame.shape)==[432,768,3]
                    decoded_hash.update(frame.tobytes())
                    count+=1
            assert count==93 and probe['fps']==16
            item={'label':row['label'],'sample_name':request['sample_name'],'path':str(path),
                'bytes':art['bytes'],'sha256':art['sha256'],'probe':probe,
                'decoded_RGB_SHA':decoded_hash.hexdigest(),'all_frames_shape':[count,432,768,3]}
            group.append(item)
            videos.append(item)
        assert len(group)==2 and all(v['sha256']==group[0]['sha256']
            and v['decoded_RGB_SHA']==group[0]['decoded_RGB_SHA'] for v in group)
    assert len(videos)==8
    assert {str(p.resolve()) for p in (out/'diagnostic').rglob('*.mp4')}=={v['path'] for v in videos}
    table={'status':'REAL_COSMOS_CAL_GUIDED_W1_SHARED_ALPHA_SELECTION_NOT_VIDEO_RESULT',
        'fingerprint_context':context,'context_sha256':hashlib.sha256(context.encode()).hexdigest(),
        'actual_same_state_teacher_and_post_RF_bundles_verified':True,
        'strictly_past_actual_D_only_history':True,'teacher_updates_deployment_anchor':False,
        'W1':raw['W1_shared_alpha_selection'],'BETA1':raw['BETA1_shared_alpha_selection'],
        'raw_tensor_files':raw['files'],'new_policy_or_quality_or_clean_latency_claim':False}
    tablepath=args.output.parent/'guided-w1-alpha-selection.json'
    assert not tablepath.exists() and not args.output.exists()
    tablepath.write_text(json.dumps(table,indent=2,allow_nan=False)+'\n')
    result={'status':'REAL_GUIDED_W1_COLLECTION_FULL_RAW_CPU_AUDIT_NOT_POLICY_QUALITY',
        'source_revision':receipt['source_revision'],'run_id':c['execution_run_id'],
        'config_sha256':sha(args.stage/'a-collection-config.json'),
        'runner_receipt_sha256':sha(source),'scope_counts':c['preregistration']['scope_counts'],
        'verdict':verdict,'actual_tensor_audit':raw,'videos':videos,
        'alpha_selection_artifact':{'path':str(tablepath),'bytes':tablepath.stat().st_size,'sha256':sha(tablepath)},
        'all_8_full93_videos_and_16_raw_vector_artifacts_verified':True,
        'full_state_components':c['expected_real_components'],
        'instrumented_parent_pipeline_costs':[{'label':row['label'],'collect':row['collect'],
            'wall_seconds':row['instrumented_parent_pipeline_wall_seconds']}
            for request in state['requests'] for row in request['paths']],
        'observed_origins':8,'W1_shared_alpha_selection':table['W1'],
        'BETA1_shared_alpha_selection':table['BETA1'],
        'actual_same_state_teacher_and_post_RF_bundles_verified':True,
        'new_policy_or_video_quality_or_clean_latency_claim':False,
        'CPU_wall_seconds':time.perf_counter()-start,'CUDA_initialized':False,'GPU_submissions':0}
    assert not torch.cuda.is_initialized()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','observed_origins','CPU_wall_seconds')}))


if __name__=='__main__':
    main()
