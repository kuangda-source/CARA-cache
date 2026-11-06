"""Read all original E5 real vectors/videos and both order repetitions, CPU only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
    args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    import torch
    torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E5 terminal reader forbids CUDA/download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.e5_head_complete24_production_r1 import RUN,validate,sha,write
    from wcomr.e5_head_complete24_sampling_r1 import ARMS,MODES,METHODS,verify_block
    from wcomr.e5_cross_version_policy_receipt_r1 import assert_policy_equivalent
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    root=args.project/'outputs'/RUN;sup=json.loads((root/'supervisor.json').read_text())
    pids=[sup['pid']]+[a['pid'] for a in sup['arms'] if 'pid' in a]
    live=[pid for pid in pids if Path('/proc/'+str(pid)).exists()]
    if live:print(json.dumps({'status':'WAIT_ORIGINAL_E5_HANDLES','pids':live}));return 2
    c,old,inputs=validate(args.project,args.stage);ledger=json.loads((args.project/'reports/budget.json').read_text())
    assert not any('inflight' in k for k in ledger)
    assert sup['budget_after']['used_gpu_hours']==sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600
    assert [a['id'] for a in sup['arms']]==[a['id'] for a in ARMS] and sup['planned_scope']==c['scope_counts']
    slots=[];files=[];videos=[];values={};rows_by_arm={};same_version_repeats=[];decoded_hashes={}
    numerical_complete=True;equalities=0;tensors=0;policies=0;seen=set()
    for arm,entry in zip(ARMS,sup['arms']):
        q=root/arm['id']/'receipt.json';record=json.loads(q.read_text()) if q.exists() else None
        if record:
            assert sha(q)==entry['receipt_sha256'] and record['pid']==entry['pid']
            assert record['source_revision']==sup['source_revision'] and record['arm']==arm
            batch=record['batch'];requests=batch.get('requests',[])
            rows=requests[0]['paths'] if requests else []
        else:rows=[];batch={}
        rows_by_arm[arm['id']]={row['collect']:row for row in rows}
        full=(record is not None and entry.get('exit_code')==0
              and record['status']=='E5_COMPLETE24_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT')
        if full:verify_block(batch,arm)
        numerical_complete &= full
        for method in arm['methods']:
            row=rows_by_arm[arm['id']].get(method)
            slot={'arm':arm['id'],'sample':arm['sample_name'],'method':method,
                'status':row['status'] if row else 'UNSTARTED_REGISTERED_PATH_RETAINED'}
            if row:
                slot.update(solver_updates=len(row.get('guided_sha256',[])),outcome=row.get('outcome'))
                art=row.get('vector_artifact')
                if art:
                    target=Path(art['path']).resolve();assert target.is_relative_to((root/arm['id']).resolve())
                    assert target not in seen and sha(target)==art['sha256'] and target.stat().st_size==art['bytes']
                    seen.add(target);x=torch.load(target,map_location='cpu',weights_only=True)
                    assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
                    assert {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
                    for t in x['guided']+[x['final_latent']]:
                        assert t.device.type=='cpu' and t.dtype==torch.float32
                        assert list(t.shape)==old['expected_real_shape'] and torch.isfinite(t).all();tensors+=1
                    assert sha(target)==art['sha256'] and target.stat().st_size==art['bytes']
                    values[(arm['id'],method)]=x;files.append({'arm':arm['id'],'method':method,**art})
                video=row.get('video_artifact')
                if video:
                    target=Path(video['path']).resolve();assert target.is_relative_to((root/arm['id']).resolve())
                    assert target.stat().st_size==video['bytes'] and sha(target)==video['sha256']
                    metadata=probe_video(target);count=0;rgb=hashlib.sha256()
                    with decoded_video(target) as stream:
                        for frame,pts,base in stream:
                            assert frame.shape==(432,768,3) and pts==metadata['pts'][count] and base==metadata['time_base']
                            rgb.update(frame.tobytes());count+=1
                    assert count==93
                    assert sha(target)==video['sha256'] and target.stat().st_size==video['bytes']
                    decoded_hashes[(arm['id'],method)]=(rgb.hexdigest(),metadata['pts'],metadata['time_base'])
                    videos.append({'arm':arm['id'],'method':method,**video,'all93_RGB_frames_decoded':True,
                        'actual_RGB_sequence_sha256':rgb.hexdigest()})
            slots.append(slot)
    pairs=[]
    if numerical_complete:
        assert len(seen)==24 and tensors==888
        for arm in ARMS:
            rows=rows_by_arm[arm['id']]
            for mode in MODES:
                methods=('LEGACY_'+mode,'FAST_'+mode)
                a,b=[values[(arm['id'],m)] for m in methods]
                assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
                equalities+=37
                l,r=[rows[m] for m in methods]
                assert ((arm['id'],methods[0]) in decoded_hashes)==((arm['id'],methods[1]) in decoded_hashes)
                if (arm['id'],methods[0]) in decoded_hashes:
                    assert decoded_hashes[(arm['id'],methods[0])]==decoded_hashes[(arm['id'],methods[1])]
                assert_policy_equivalent(l['collection_complete']['deployment']['history'],r['collection_complete']['deployment']['history'])
                policies+=36
                heads=[len(v['collection_complete']['actual_original_plus_candidate_heads']) for v in (l,r)]
                pairs.append({'arm':arm['id'],'sample':arm['sample_name'],'mode':mode,'old_new_tensor_equalities':37,
                    'actual_native_head_counts':heads,'saved_native_heads':heads[0]-heads[1],
                    'whole_instrumented_parent_seconds':[v['instrumented_parent_pipeline_wall_seconds'] for v in (l,r)]})
        for tag in ('AV','HUMAN'):
            for method in METHODS:
                a,b=[values[(tag+'_R'+str(rep),method)] for rep in (1,2)]
                assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
                l,r=[rows_by_arm[tag+'_R'+str(rep)][method] for rep in (1,2)]
                assert ((tag+'_R1',method) in decoded_hashes)==((tag+'_R2',method) in decoded_hashes)
                if (tag+'_R1',method) in decoded_hashes:
                    assert decoded_hashes[(tag+'_R1',method)]==decoded_hashes[(tag+'_R2',method)]
                for key in ('guided_sha256','final_latent_sha256','actions','solver_returns','rng_after'):
                    assert l[key]==r[key],key
                assert_policy_equivalent(l['collection_complete']['deployment']['history'],r['collection_complete']['deployment']['history'])
                same_version_repeats.append({'sample':next(a['sample_name'] for a in ARMS if a['id']==tag+'_R1'),'method':method,
                    'actual_order_repeat_tensor_equalities':37})
        assert equalities==444 and policies==432 and len(same_version_repeats)==12
    assert seen=={p.resolve() for p in root.rglob('*.pt')} and not torch.cuda.is_initialized()
    verdict={'status':'E5_WHOLE24_REAL_HEAD_EQUIVALENCE_CPU_AUDITED' if numerical_complete else 'E5_PARTIAL_REAL_ATTEMPT_RETAINED_NOT_WHOLE_ACCEPTED',
        'source_revision':sup['source_revision'],'original_PIDs_absent':pids,'original_supervisor':sup,
        'registered_paths':24,'path_slots':slots,'actual_vector_files':files,'actual_loaded_tensors':tensors,
        'actual_old_new_tensor_equalities':equalities,'actual_complete_videos':videos,
        'same_version_order_repeats':same_version_repeats,'actual_head_and_instrumented_wall_pairs':pairs,
        'billed_GPUh':sup['wall_seconds']/3600,'current_ledger':ledger,'current_ledger_sha256':sha(args.project/'reports/budget.json'),
        'rejected_outputs_retained':True,'guarded_video_acceptance_is_separate_from_numerical_equivalence':True,
        'new_GPU_submissions':0,'CUDA_initialized':False,'clean_latency_or_quality_frontier_claim':False}
    assert not args.output.exists();write(args.output,verdict)
    print(json.dumps({'status':verdict['status'],'actual_vectors':len(files),'actual_tensors':tensors,
        'old_new_equalities':equalities,'complete_videos':len(videos),'billed_GPUh':verdict['billed_GPUh']}))
    return 0


if __name__=='__main__':raise SystemExit(main())
