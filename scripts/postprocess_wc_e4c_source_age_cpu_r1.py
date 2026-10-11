"""Original terminal handles, whole scope, actual tensors and all93-frame videos."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage','reader-stage','output'):p.add_argument('--'+n,type=Path,required=True)
    args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    post_reg=json.loads((args.reader_stage/'postprocessor-registration.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==post_reg['postprocessor_sha256']
    root=args.project/'outputs/wc-e4c-matched-p-d-age124-offon4-suffix16-r1'
    sup=json.loads((root/'supervisor.json').read_text())
    pids=[sup['pid']]+[a['pid'] for a in sup['arms'] if 'pid' in a]
    live=[i for i in pids if Path('/proc/'+str(i)).exists()]
    if live:
        print(json.dumps({'status':'WAIT_ORIGINAL_E4C_GPU_HANDLES_NOT_TERMINAL','live_PIDs':live}));return 2
    assert sup['status']=='E4C_SOURCE_AGE_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
    assert sup['pid']==4075406 and sup['arms'][0]['pid']==4075494
    assert sup['source_revision']=='6a5910ce07dd7cb6896f57de7f8827c9583f07bc'
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((args.reader_stage/'registration.json').read_text())
    for name,h in reg['new_payload_sha256'].items():assert sha(args.reader_stage/name)==h
    proof=json.loads((args.reader_stage/'receipt.json').read_text())
    assert proof['status']=='E4C_READONLY_CPU_READER_EXIT0_NOT_GPU' and proof['exit_code']==proof['child_exit_code']==0
    assert proof['source_after_sha256']==reg['new_payload_sha256'] and proof['original_source_unchanged']
    assert sha(args.reader_stage/'result.json')==proof['result_sha256']
    cpu=json.loads((args.reader_stage/'result.json').read_text())
    assert cpu['status']=='E4C_READONLY_FULL_EXISTING_CPU_ARTIFACT_READER_PASS_NOT_NEW_GPU'
    assert (cpu['actual_files_reloaded'],cpu['actual_tensors_reloaded'],cpu['actual_direct_tensor_comparisons'],cpu['actual_points_summarized'])==(88,776,324,48)
    sys.path[:0]=[str(args.reader_stage/'src'),str(args.stage/'src')]
    import wcomr
    for source in (args.reader_stage/'src/wcomr',args.stage/'src/wcomr'):
        if str(source) not in wcomr.__path__:wcomr.__path__.append(str(source))
    import torch
    torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E4c raw CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.e4c_source_age_production_r1 import validate,validate_selected,CONFIG
    c,old,_=validate(args.project,args.stage);validate_selected(c,args.stage)
    assert sha(args.stage/CONFIG)==sup['config_sha256']
    assert len(sup['arms'])==1 and sup['planned_scope']==c['scope_counts']
    ledger=json.loads((args.project/'reports/budget.json').read_text())
    assert not any('inflight' in key for key in ledger)
    assert sup['budget_after']['used_gpu_hours']==sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600
    path=root/'model/receipt.json';receipt=json.loads(path.read_text())
    assert sha(path)==sup['arms'][0]['receipt_sha256'] and receipt['pid']==4075494
    assert receipt['source_revision']==sup['source_revision'] and receipt['run_id']==c['run_id']
    state=receipt['batch'];rows={}
    for request in state.get('requests',[]):
        for row in request['paths']:rows[(request['sample_name'],row['collect'])]=(request,row)
    slots=[];videos=[];partial=[]
    from wcomr.rv0_video_reader import decoded_video,probe_video
    from wcomr.mid_coverage import tree_digest
    for sample in [r['name'] for r in c['requests']]:
        for collect in (False,True):
            pair=rows.get((sample,collect));slot={'sample':sample,'collect':collect,'status':'UNSTARTED_REGISTERED_PARENT_RETAINED'}
            if pair:
                request,row=pair
                slot.update(status=row['status'],solver_updates=len(row.get('guided_sha256',[])),
                    events=len(row.get('origins',[])),outcome=row.get('outcome'))
                for art in [row.get('vector_artifact')]:
                    if not art:continue
                    target=Path(art['path']).resolve();assert target.is_relative_to((root/'model').resolve())
                    assert target.stat().st_size==art['bytes'] and sha(target)==art['sha256']
                    x=torch.load(target,map_location='cpu',weights_only=True)
                    assert {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
                    partial.append({'path':str(target),'sha256':art['sha256'],'guided_vectors':len(x['guided'])})
                if 'video_artifact' in row:
                    art=row['video_artifact'];target=Path(art['path']).resolve()
                    assert target.is_relative_to((root/'model').resolve()) and target.stat().st_size==art['bytes'] and sha(target)==art['sha256']
                    metadata=probe_video(target);count=0
                    with decoded_video(target) as stream:
                        for frame,pts,base in stream:
                            assert frame.shape==(432,768,3) and pts==metadata['pts'][count] and base==metadata['time_base'];count+=1
                    assert count==93
                    videos.append({'sample':sample,'collect':collect,**art,'all93_RGB_frames_decoded':True,'probe':metadata})
            slots.append(slot)
    scope=json.loads((args.stage/c['scope_ref']).read_text());raw=summary=structural=None
    completed=sup['arms'][0]['exit_code']==0 and receipt['status']=='E4C_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT'
    if completed:
        module=ast.parse((args.stage/'src/wcomr/e4c_matched_source_age_sampling_r1.py').read_text())
        fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='verify_batch')
        namespace={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<pinned-pure-verify-batch>','exec'),namespace)
        structural=namespace['verify_batch'](state,scope)
        from wcomr.e4c_source_age_tensor_audit_r2 import audit
        from wcomr.e4c_source_age_summary_r1 import summarize
        assert sha(args.stage/'src/wcomr/e4c_source_age_tensor_audit_r1.py')==reg['original_payload_sha256']['src/wcomr/e4c_source_age_tensor_audit_r1.py']
        raw=audit(state,root/'model',torch.load,old['expected_real_shape']);summary=summarize(state,raw)
        assert len(videos)==4 and len(raw['files'])==44 and raw['actual_tensors_reloaded']==388 and raw['actual_direct_tensor_comparisons']==162
    value={'status':'E4C_WHOLE_TRUE_MODEL_SOURCE_AGE_CPU_AUDITED_NOT_ENDPOINT_QUALITY' if completed else 'E4C_PARTIAL_TRUE_MODEL_SCOPE_RETAINED_NOT_WHOLE_ACCEPTANCE',
        'original_source_revision':sup['source_revision'],'reader_source_revision':proof['source_revision'],
        'registered_parent_paths':4,'registered_events':4,'registered_suffixes':16,'registered_points':24,
        'parent_slots':slots,'original_gpu_terminal':sup,'original_runner_receipt_sha256':sha(path),
        'original_runner_scope_state':state,
        'original_runner_failure':receipt.get('error'),'original_protected_capacity_failure':receipt.get('protected_capacity_failure'),
        'actual_written_parent_vectors':partial,'whole_structural_audit':structural,'whole_actual_tensor_audit':raw,
        'all_actual_videos':videos,'matched_source_age_summary':summary,'reader_CPU_receipt_sha256':sha(args.reader_stage/'receipt.json'),
        'current_ledger_sha256':sha(args.project/'reports/budget.json'),'current_ledger':ledger,
        'CUDA_initialized':torch.cuda.is_initialized(),'new_GPU_submissions':0,'endpoint_quality_or_clean_latency_claim':False}
    assert not value['CUDA_initialized'] and not args.output.exists()
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':value['status'],'parent_paths':len(slots),'videos_decoded':len(videos),
        'whole_points':len(summary['points']) if summary else 0,'billed_GPUh':sup['wall_seconds']/3600}))
    return 0


if __name__=='__main__':raise SystemExit(main())
