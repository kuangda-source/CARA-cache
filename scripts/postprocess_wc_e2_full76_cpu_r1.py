#!/usr/bin/env python3
"""After GPU release, audit every full76 artifact and score all valid93 pairs."""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import RUN,sha,write,validate_execution
    from wcomr.e2_confirmation_production_r1 import validate,validate_selected
    c,inputs,*_=validate(args.project,args.stage);validate_selected(c,args.project,args.stage)
    protocol=json.loads((args.stage/'execution-protocol.json').read_text());validate_execution(c,protocol,args.stage)
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E2 released-GPU CPU audit/score forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.e2_confirmation_timing_sampling_r1 import verify_matrix,audit_vectors
    from wcomr.e2_full76_reports_r1 import bind_pairs,summarize
    from wcomr.rv0_video_reader import probe_video,decoded_video
    out=args.project/'outputs'/RUN;supervisor=json.loads((out/'supervisor.json').read_text())
    pids=[supervisor['pid'],supervisor['child_pid']]
    assert supervisor['exit_code']==0 and not any(Path('/proc/'+str(p)).exists() for p in pids)
    source=out/'diagnostic/receipt.json';runner=json.loads(source.read_text());state=runner['matrix']
    assert runner['status']=='E2_GPU_COMPLETE_REQUIRES_RAW_AUDIT_AND_93FRAME_CPU_SCORE'
    assert runner['config']==c and runner['source_revision']==supervisor['source_revision']
    verdict=verify_matrix(state,inputs);start=time.perf_counter()
    raw=audit_vectors(state,inputs,out/'diagnostic',torch.load,c['expected_real_shape'])
    old_capture=json.loads((args.stage/protocol['old_capture_ref']).read_text());old={}
    assert old_capture['GPU_exit_code']==old_capture['CPU_exit_code']==0 and old_capture['independent_checks']['success']
    for name,ref in [('runner',protocol['old_runner_ref']),('CPU_result',protocol['old_raw_ref'])]:
        data=gzip.decompress((args.stage/ref).read_bytes());info=old_capture['files'][name]
        assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'];old[name]=json.loads(data)
    assert old['CPU_result']['runner_receipt_sha256']==old_capture['files']['runner']['sha256']
    assert old['CPU_result']['all_accepted_complete93_videos_and_raw_vector_artifacts_verified']
    for key in ('historical_wc_settings','sampling_protocol','expected_real_shape'):
        assert old['runner']['config'][key]==c[key]
    pairs=bind_pairs(state['slots'],old['runner'],old['CPU_result'],runner['model_context'])
    videos={}
    for row in state['slots']:
        art=row.get('video_artifact')
        if art:
            assert Path(art['path']).resolve().is_relative_to((out/'diagnostic').resolve())
            videos[art['path']]=art
    assert {str(p.resolve()) for p in (out/'diagnostic').rglob('*.mp4')}=={str(Path(n).resolve()) for n in videos}
    for pair in pairs:
        if pair['status']=='PAIRED':
            reference=pair['reference'];path=Path(reference['path']).resolve()
            if pair['reference_source']!='CURRENT_MATCHED_NATIVE':
                assert path.is_relative_to((args.project/'outputs/wc-ra-plus-a-full-video-r1/diagnostic').resolve())
            videos[reference['path']]=reference
    decoded=[]
    for name,art in videos.items():
        path=Path(name);assert path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
        metadata=probe_video(path);count=0;rgb=hashlib.sha256()
        with decoded_video(path) as frames:
            for frame,pts,base in frames:count+=1;rgb.update(frame.tobytes())
        assert count==93;decoded.append({**art,'probe':metadata,'decoded_RGB_sha256':rgb.hexdigest()})
    memory=[json.loads(s) for s in (out/'diagnostic/memory-boundaries.jsonl').read_text().splitlines() if s]
    assert len(memory)==152
    for row in state['slots']:
        events=[r for r in memory if r['id']==row['id']];assert [r['event'] for r in events]==['BEGIN','END']
        assert all(r['method']==row['method'] and r['section']==row['section'] for r in events)
    raw_result={'status':'E2_COMPLETE76_RAW_CPU_AUDIT_NOT_QUALITY','source_revision':runner['source_revision'],
        'original_PIDs_absent':pids,'runner_receipt_sha256':sha(source),'config_sha256':sha(args.stage/'e2-config.json'),
        'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),'verdict':verdict,
        'actual_vectors':raw,'videos':decoded,'pairs_all68':pairs,'memory_all76':memory,
        'CPU_wall_seconds':time.perf_counter()-start,'CUDA_initialized':False,'GPU_submissions':0,'ledger_written':False}
    target=args.stage/'raw-audit.json';assert not target.exists();write(target,raw_result)
    from wcomr.lpips_resource_identity import audit
    metric_sha=protocol['execution_payload_sha256']['src/wcomr/rv0_lpips.py']
    resource=args.project/'.sync/wc-rv0-lpips-resource-v2';identity=audit(resource,metric_sha)
    sys.path.insert(0,str(resource/'site'));import lpips
    from wcomr.rv0_lpips import PROTOCOL,score_pair
    assert PROTOCOL==identity['protocol'] and importlib.metadata.version('lpips')=='0.1.4'
    assert Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
    model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
    for parameter in model.parameters():parameter.requires_grad_(False)
    result={'status':'E2_FULL76_ALL_AVAILABLE93_CPU_SCORING_RUNNING','pairs_all68':pairs,
        'raw_audit_sha256':sha(target),'runner_receipt_sha256':sha(source),'resource_identity':identity,
        'protocol':{k:v for k,v in PROTOCOL.items() if k not in ('benefit','policy')},
        'GPU_submissions':0,'ledger_written':False,'CUDA_initialized':False,'summary':None}
    target=args.stage/'score-result.json';assert not target.exists();write(target,result);score_start=time.perf_counter()
    try:
        for pair in pairs:
            if pair['status']!='PAIRED':continue
            reference,candidate=pair['reference'],pair['candidate']
            with decoded_video(reference['path']) as left,decoded_video(candidate['path']) as right:
                pair['score']=score_pair(left,right,model,reference_sha256=reference['sha256'],candidate_sha256=candidate['sha256'])
            write(target,result);print(json.dumps({'id':pair['id'],'mean_LPIPS':pair['score']['mean_LPIPS']}),flush=True)
        result['summary']=summarize(state['slots'],pairs,inputs)
        for art in videos.values():assert sha(art['path'])==art['sha256']
        assert sha(source)==result['runner_receipt_sha256'] and audit(resource,metric_sha)==identity
        assert not torch.cuda.is_initialized()
        result['status']='E2_FULL76_ALL_AVAILABLE93_CPU_SCORE_COMPLETE_NOT_AUTOMATIC_METHOD_ACCEPTANCE'
    except BaseException as error:
        result.update(status='E2_CPU_SCORE_FAILED_ALL68_PAIR_SLOTS_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        result.update(CPU_score_wall_seconds=time.perf_counter()-score_start,CUDA_initialized=torch.cuda.is_initialized());write(target,result)
    print(json.dumps({'status':result['status'],'scored_pairs':result['summary']['scored_pairs']}))


if __name__=='__main__':main()
