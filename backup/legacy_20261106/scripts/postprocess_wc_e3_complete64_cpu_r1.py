#!/usr/bin/env python3
"""After release, audit all64 slots and score every valid compatible complete93 pair."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def load_sources(project,scope,p):
    from wcomr.e3_complete64_production_r1 import sha
    result={}
    for name,binding in p['reuse_receipts'].items():
        path=project/binding['path']
        if sha(path)!=binding['sha256']:raise ValueError('Immutable reuse receipt changed')
        r=json.loads(path.read_text())
        if r['source_revision']!=binding['source_revision']:raise ValueError('Reuse original revision differs')
        result[name]=r
    selected={}
    for slot in scope['all64_slots']:
        if slot['disposition']!='REUSE_QUALIFIED_DEV_OUTPUT':continue
        origin='ORIGINAL64' if slot['reuse_binding']['origin']=='ORIGINAL_FAILED64_VALID_E0_PATH' else 'E1_CPU_PREFIX'
        r=result[origin];state=r['batches'][slot['strategy']] if origin=='ORIGINAL64' else r['batch']
        choices=[]
        for q in state['requests']:
            if q['sample_name']!=slot['sample_name']:continue
            for i,row in enumerate(q['paths']):
                if row['collect']==slot['method']:choices.append((q,i,row))
        if len(choices)!=1:raise ValueError('One immutable actual reuse row required')
        q,i,row=choices[0]
        selected[slot['slot']]=dict(request_record=q,method_index=i,row=row,
            model_context=r['model_context'],source_revision=r['source_revision'],
            source_receipt=p['reuse_receipts'][origin],artifact_root=str(project/p['reuse_receipts'][origin]['artifact_root']))
    return selected


def audit_slot(item,reference,source_proof,check,calibration,specs,expected_shape,torch,tree_digest,probe,decode,model_context):
    from wcomr.e3_complete64_terminal_r1 import actual_vectors,artifact_file,replay_policy,bind_pair,recorded_cost
    check(item['row'],item['strategy'])
    item['policy_replay']=replay_policy(item['row'],item['strategy'],calibration,specs)
    item['actual_vector_read']=actual_vectors(item,torch.load,expected_shape,torch,tree_digest)
    item['recorded_cost']=recorded_cost(item)
    art=item['row']['video_artifact'];path=artifact_file(art,item['artifact_root'],'.mp4')
    metadata=probe(path);h=hashlib.sha256();frames=0
    with decode(path) as values:
        for frame,pts,base in values:h.update(frame.tobytes());frames+=1
    if frames!=93:raise ValueError('Every complete candidate video must fully decode93')
    item.update(candidate=art,reference=reference['artifact'],
        decoded_video={'probe':metadata,'frames':frames,'RGB_sha256':h.hexdigest()})
    item['pairing']=bind_pair(item,reference,source_proof,model_context)
    item['compatible']=item['pairing']['compatible']
    item['status']='RAW_VALID_COMPATIBLE_READY_TO_SCORE' if item['compatible'] else 'RAW_VALID_REFERENCE_INCOMPATIBLE_RETAINED'


def score_slots(slots,model,decode,score_pair,save):
    for item in slots:
        if item['status']!='RAW_VALID_COMPATIBLE_READY_TO_SCORE':continue
        try:
            with decode(item['reference']['path']) as left,decode(item['candidate']['path']) as right:
                item['score']=score_pair(left,right,model,reference_sha256=item['reference']['sha256'],
                    candidate_sha256=item['candidate']['sha256'])
            item.update(status='SCORED_FULL93',scored=True)
        except Exception as error:
            item.update(status='SCORE_FAILED_RETAINED',score=None,scored=False,error_type=type(error).__name__,error=str(error))
        save()


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e3_complete64_production_r1 import RUN,CONFIG,sha,write,validate,validate_selected
    from wcomr.e3_complete64_execution_r1 import PROTOCOL,validate_execution,validate_post_proof,original_gone
    c,scope,old,inputs=validate(args.project,args.stage);validate_selected(c,args.stage)
    p=json.loads((args.stage/PROTOCOL).read_text());validate_execution(c,p,args.stage);validate_post_proof(c,p,args.stage)
    calibration,specs,references,evidence=inputs;native={r['sample_name']:r for r in references}
    output=args.project/'outputs'/RUN;supervisor=json.loads((output/'supervisor.json').read_text())
    original_gone(supervisor,supervisor['pid'],lambda pid:Path('/proc/'+str(pid)).exists())
    receipt_hashes={};receipts={}
    for b in supervisor['blocks']:
        path=output/b['id']/'receipt.json'
        if path.exists():
            h=sha(path)
            if b.get('receipt_sha256')!=h:raise ValueError('Actual original block receipt not bound by supervisor')
            r=json.loads(path.read_text());r.update(source_receipt={'path':str(path),'sha256':h},artifact_root=str(path.parent))
            receipts[b['id']]=r;receipt_hashes[str(path)]=h
        elif 'receipt_sha256' in b:raise ValueError('Original recorded block receipt disappeared')
    from wcomr.e3_complete64_terminal_r1 import inventory,summarize,receipt_slots
    reused=load_sources(args.project,scope,p);slots=inventory(scope,supervisor,receipts,reused)
    from wcomr.full64_partial_recovery_cpu import verifier,zero_mask_proof
    parent=args.project/c['parent_stage'];check,check_proof=verifier(parent,old['payload_sha256'])
    source_proof=zero_mask_proof(args.project/'runtime',parent,old)
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E3 released-GPU audit/score forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    model_context='Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json')
    raw_path=args.stage/'raw-audit.json';score_path=args.stage/'score-result.json'
    assert not raw_path.exists() and not score_path.exists();start=time.perf_counter()
    budget_sha=sha(args.project/'reports/budget.json');supervisor_sha=sha(output/'supervisor.json')
    raw={'status':'E3_COMPLETE64_RAW_CPU_RUNNING','slots_all64':slots,'GPU_supervisor':supervisor,
        'supervisor_sha256':supervisor_sha,'block_receipt_sha256':receipt_hashes,'source_verifier':check_proof,
        'numerical_zero_mask_source_proof':source_proof,'GPU_submissions':0,'ledger_written':False,
        'budget_before_sha256':budget_sha,'CUDA_initialized':False}
    save_raw=lambda:write(raw_path,{**raw,'slots_all64':receipt_slots(slots)})
    save_raw()
    for item in slots:
        if item['status']!='COMPLETE_REQUIRES_RAW_AUDIT':continue
        try:
            audit_slot(item,native[item['sample_name']],source_proof,check,calibration,specs,
                old['expected_real_shape'],torch,tree_digest,probe_video,decoded_video,model_context)
        except Exception as error:
            item.update(status='RAW_AUDIT_FAILED_RETAINED',error_type=type(error).__name__,error=str(error),compatible=False)
        save_raw()
    raw.update(status='E3_COMPLETE64_RAW_CPU_TERMINAL_ALL_SLOTS_RETAINED',CPU_wall_seconds=time.perf_counter()-start,
        valid_complete_paths=sum(r['status'].startswith('RAW_VALID') for r in slots))
    # Freeze raw receipt before adding metric data; the score result owns its copy.
    save_raw()
    slots=receipt_slots(slots)
    result={'status':'E3_COMPLETE64_ALL_AVAILABLE93_CPU_SCORING_RUNNING','slots_all64':slots,
        'raw_audit_sha256':sha(raw_path),'execution_protocol_sha256':sha(args.stage/PROTOCOL),'summary':None,
        'GPU_submissions':0,'ledger_written':False,'CUDA_initialized':False}
    write(score_path,result);score_start=time.perf_counter()
    try:
        from wcomr.lpips_resource_identity import audit
        resource=args.project/'.sync/wc-rv0-lpips-resource-v2'
        metric_sha=p['execution_payload_sha256'].get('src/wcomr/rv0_lpips.py',c['payload_sha256'].get('src/wcomr/rv0_lpips.py'))
        identity=audit(resource,metric_sha);sys.path.insert(0,str(resource/'site'));import lpips
        from wcomr.rv0_lpips import PROTOCOL as METRIC,score_pair
        assert METRIC==identity['protocol'] and importlib.metadata.version('lpips')=='0.1.4'
        assert Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        model=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in model.parameters():parameter.requires_grad_(False)
        result.update(resource_identity=identity,metric_protocol=METRIC)
        score_slots(slots,model,decoded_video,score_pair,lambda:write(score_path,result))
        result['summary']=summarize(slots)
        for item in slots:
            if item['scored']:
                for art in (item['reference'],item['candidate']):assert sha(art['path'])==art['sha256']
        assert audit(resource,metric_sha)==identity
        assert sha(output/'supervisor.json')==supervisor_sha
        assert all(sha(path)==h for path,h in receipt_hashes.items())
        assert sha(args.project/'reports/budget.json')==budget_sha and not torch.cuda.is_initialized()
        validate(args.project,args.stage);validate_execution(c,p,args.stage)
        result.update(status='E3_COMPLETE64_ALL_AVAILABLE93_CPU_TERMINAL_NOT_AUTOMATIC_METHOD_ACCEPTANCE',
            actual_score_failures=sum(r['status']=='SCORE_FAILED_RETAINED' for r in slots),
            whole64_all_scored=all(r['scored'] for r in slots),budget_after_sha256=budget_sha)
    except BaseException as error:
        result.update(status='E3_CPU_SCORE_GLOBAL_FAILURE_ALL64_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        result.update(CPU_score_wall_seconds=time.perf_counter()-score_start,CUDA_initialized=torch.cuda.is_initialized())
        write(score_path,result)
    print(json.dumps({k:result[k] for k in ('status','whole64_all_scored','actual_score_failures','GPU_submissions')}))


if __name__=='__main__':main()
