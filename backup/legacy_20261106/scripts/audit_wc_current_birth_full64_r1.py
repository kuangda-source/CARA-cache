#!/usr/bin/env python3
"""Full64 original-byte/tensor/video/Native pairing CPU audit, no scoring."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for name in ('project','stage','runner','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    assert not args.output.exists()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime')]
    import torch
    torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('Full64 raw CPU forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    assert not torch.cuda.is_initialized()
    from wcomr.current_birth_real_production_r1 import validate,COUNTS,RUN
    from wcomr.source_aware_current_birth_sampling_r2 import audit_vectors,STRATEGIES,METHODS
    from wcomr.current_birth_real_inputs_r1 import sha
    from wcomr.native_video_compatibility_r1 import assess
    from wcomr.rv0_video_reader import decoded_video
    started=time.perf_counter();before=sha(args.project/'reports/budget.json')
    result={'status':'CURRENT_BIRTH_FULL64_RAW_CPU_RUNNING_NOT_SCORE','planned_scope':COUNTS,
        'source_revision':args.source_revision,'runner_sha256':sha(args.runner),
        'raw_audits':{},'pairing':{},'decoded_videos':[],'GPU_submissions':0,'budget_written':False}
    try:
        c,inputs=validate(args.project,args.stage);_,_,references,evidence=inputs
        runner=json.loads(args.runner.read_text());root=args.project/'outputs'/RUN/'diagnostic'
        if (runner['status']!='CURRENT_BIRTH_REAL_FULL64_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
            or runner['source_revision']!=args.source_revision or runner['config']!=c
            or runner['planned_scope']!=COUNTS or runner['completed_strategies']!=list(STRATEGIES)
            or runner['input_evidence']!=evidence or runner['matched_Native_metadata']!=references):
            raise ValueError('Complete actual whole64 GPU source and fixed input receipt required')
        for strategy in STRATEGIES:
            batch=runner['batches'][strategy]
            result['raw_audits'][strategy]=audit_vectors(batch,root/strategy,torch.load,c['expected_real_shape'])
            result['pairing'][strategy]=assess(batch,references,METHODS)
            for request in batch['requests']:
                for row in request['paths']:
                    if row['collect']=='DENSE_CONTROL' and row['actions']!=['DD']*36:
                        raise ValueError('Declared dense ordering control did not execute full computation')
                    artifact=row['video_artifact'];path=Path(artifact['path']).resolve()
                    if (not path.is_relative_to((root/strategy).resolve())
                        or path.stat().st_size!=artifact['bytes'] or sha(path)!=artifact['sha256']):
                        raise ValueError('Bound new full video bytes changed')
                    with decoded_video(path) as frames:
                        count=sum(1 for _ in frames)
                    if count!=93:raise ValueError('Original all93 video decode required')
                    result['decoded_videos'].append({'strategy':strategy,'sample_name':request['sample_name'],
                        'method':row['collect'],'artifact':artifact,'frames':count})
        for reference in references:
            artifact=reference['artifact'];path=Path(artifact['path'])
            if sha(path)!=artifact['sha256'] or path.stat().st_size!=artifact['bytes']:
                raise ValueError('Original reused Native video bytes changed')
            with decoded_video(path) as frames:count=sum(1 for _ in frames)
            if count!=93:raise ValueError('Reused Native all93 frame decode required')
        assert len(result['decoded_videos'])==64 and not torch.cuda.is_initialized()
        assert before==sha(args.project/'reports/budget.json')
        result.update(status='CURRENT_BIRTH_FULL64_RAW_CPU_PASS_NOT_FIDELITY_SCORE',exit_code=0,
            actual_all_guided_tensors_reloaded=2304,actual_all_final_latents_reloaded=64,
            accepted_new_videos=64,Native_videos_rechecked=4,
            compatible_pairs=sum(r['compatible_pairs'] for r in result['pairing'].values()),
            incompatible_pairs=sum(r['incompatible_pairs'] for r in result['pairing'].values()),
            no_P_RA_and_OFF_exact_and_full_GEMM_reference_verified=True,
            all_unpaired_slots_retained=True,clean_speed_or_physics_or_new_fidelity_claim=False)
    except BaseException as error:
        result.update(status='CURRENT_BIRTH_FULL64_RAW_CPU_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        result.update(CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=torch.cuda.is_initialized(),
            budget_before_sha256=before,budget_after_sha256=sha(args.project/'reports/budget.json'))
        args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','exit_code','CPU_wall_seconds','GPU_submissions')}))
    return result['exit_code']


if __name__=='__main__':raise SystemExit(main())
