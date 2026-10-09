#!/usr/bin/env python3
"""Released-GPU actual full16 tensor/state/video audit, no quality proxy labels."""
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
    args=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cfg_complete_native_policy_production import validate,validate_selected,sha
    c,_=validate(args.project,args.stage);validate_selected(c,args.project,args.stage)
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('Complete native-policy CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.cfg_complete_native_policy_sampling import verify_batch,audit_vectors
    from wcomr.rv0_video_reader import probe_video,decoded_video
    out=args.project/'outputs'/c['execution_run_id'];supervisor=json.loads((out/'supervisor.json').read_text())
    assert supervisor['exit_code']==0 and supervisor['run_id']==c['execution_run_id']
    assert not any(Path('/proc/'+str(supervisor[k])).exists() for k in ('pid','child_pid'))
    source=out/'diagnostic/receipt.json';receipt=json.loads(source.read_text());state=receipt['batch'];started=time.perf_counter()
    assert receipt['config']==c and receipt['source_revision']==supervisor['source_revision']
    assert receipt['status']=='REAL_COMPLETE_NATIVE_POLICY_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    verdict=verify_batch(state);raw=audit_vectors(state,out/'diagnostic',torch.load,c['expected_real_shape'])
    videos=[]
    for request in state['requests']:
        group=[]
        for row in request['paths']:
            assert len(row['final_components'])==c['expected_real_components']
            assert all(len(point['components'])==c['expected_real_components'] for point in row['checkpoints'])
            art=row['video_artifact'];path=Path(art['path']).resolve()
            assert path.is_relative_to((out/'diagnostic').resolve()) and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
            probe=probe_video(path);count=0;decoded_hash=hashlib.sha256()
            with decoded_video(path) as frames:
                for frame,pts,base in frames:
                    assert list(frame.shape)==[432,768,3];decoded_hash.update(frame.tobytes());count+=1
            assert count==93 and probe['fps']==16
            item={'label':row['label'],'sample_name':request['sample_name'],'path':str(path),'sha256':art['sha256'],
                'bytes':art['bytes'],'probe':probe,'decoded_RGB_SHA':decoded_hash.hexdigest(),'all_frames_shape':[count,432,768,3]}
            group.append(item);videos.append(item)
        assert len(group)==8 and all(v['sha256']==group[0]['sha256'] and v['decoded_RGB_SHA']==group[0]['decoded_RGB_SHA'] for v in group)
    assert len(videos)==16 and {str(p.resolve()) for p in (out/'diagnostic').rglob('*.mp4')}=={v['path'] for v in videos}
    assert state['initial_state_restored'] and not torch.cuda.is_initialized()
    result={'status':'REAL_COMPLETE_NATIVE_POLICY_RAW_CPU_AUDIT_NOT_NEW_POLICY_OR_QUALITY',
        'source_revision':receipt['source_revision'],'run_id':c['execution_run_id'],
        'config_sha256':sha(args.stage/'native-policy-config.json'),'runner_receipt_sha256':sha(source),
        'scope_counts':c['preregistration']['scope_counts'],'verdict':verdict,'actual_tensor_audit':raw,'videos':videos,
        'all_16_full93_videos_and_actual_raw_tensors_verified':True,'full_state_components':c['expected_real_components'],
        'instrumented_pipeline_costs':[{'label':row['label'],'order':row['order'],'observers':row['observers'],
            'wall_seconds':row['instrumented_pipeline_wall_seconds']} for request in state['requests'] for row in request['paths']],
        'clean_latency_or_new_policy_or_quality_claim':False,'endpoint_labels':0,'future_cost_labels':0,
        'CPU_wall_seconds':time.perf_counter()-started,'CUDA_initialized':False,'GPU_submissions':0}
    assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','all_16_full93_videos_and_actual_raw_tensors_verified','CPU_wall_seconds')}))


if __name__=='__main__':main()
