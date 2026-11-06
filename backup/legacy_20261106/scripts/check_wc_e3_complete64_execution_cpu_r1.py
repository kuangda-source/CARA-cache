#!/usr/bin/env python3
"""Affected terminal/selection CPU plus real ten reusable artifact readers."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e3_complete64_production_r1 import CONFIG,sha,write,binding,validate
    from wcomr.e3_complete64_execution_r1 import PROTOCOL,validate_execution
    c=json.loads((args.stage/CONFIG).read_text());p=json.loads((args.stage/PROTOCOL).read_text())
    assert not c['GPU_execution_selected'];validate_execution(c,p,args.stage)
    target=args.stage/'execution-CPU-receipt.json';assert not target.exists();start=time.perf_counter()
    r={'status':'E3_COMPLETE64_POST_SELECTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.source_revision,'started_unix':time.time(),'method_binding_sha256':binding(c),
        'protocol_sha256':sha(args.stage/PROTOCOL),'budget_before_sha256':sha(args.project/'reports/budget.json'),
        'GPU_submissions':0,'ledger_written':False}
    write(target,r)
    try:
        c,scope,old,inputs=validate(args.project,args.stage);calibration,specs,references,evidence=inputs
        import torch
        assert not torch.cuda.is_initialized();torch.set_num_threads(2)
        def forbidden(*a,**k):raise RuntimeError('E3 post/selection CPU forbids CUDA/downloads')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        from wcomr.mid_coverage import tree_digest
        from wcomr.full64_partial_recovery_cpu import verifier,zero_mask_proof
        from wcomr.e3_complete64_terminal_r1 import actual_vectors,bind_pair,recorded_cost
        from wcomr.rv0_video_reader import probe_video,decoded_video
        def load(name,filename):
            s=importlib.util.spec_from_file_location(name,args.stage/filename)
            v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
        post=load('E3_actual_post','scripts/postprocess_wc_e3_complete64_cpu_r1.py')
        reused=post.load_sources(args.project,scope,p)
        tests=load('E3_affected_terminal_tests','tests/check_e3_complete64_terminal_cpu_r1.py')
        r['affected_complete64_reporter_and_launch_wrapper_CPU_controls']=tests.run(args.stage,c,scope,reused)
        parent=args.project/c['parent_stage'];check,source=verifier(parent,old['payload_sha256'])
        proof=zero_mask_proof(args.project/'runtime',parent,old)
        native={n['sample_name']:n for n in references};real=[]
        context='Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json')
        for declared in scope['all64_slots']:
            if declared['slot'] not in reused:continue
            item={**declared,**reused[declared['slot']],'source_kind':'QUALIFIED_REUSED_DEV'}
            post.audit_slot(item,native[item['sample_name']],proof,check,calibration,specs,old['expected_real_shape'],
                torch,tree_digest,probe_video,decoded_video,context)
            assert item['compatible']
            real.append({k:item[k] for k in ('slot','strategy','sample_name','method','actual_vector_read',
                'policy_replay','pairing','decoded_video','recorded_cost')})
        assert len(real)==10 and sum(v['actual_vector_read']['actual_tensors_reloaded'] for v in real)==370
        # Actual serialization/loader boundary controls on small CPU tensors.
        controls=[]
        with tempfile.TemporaryDirectory(prefix='E3_FILE_READER_CPU_') as folder:
            root=Path(folder);path=root/'vectors.pt'
            good={'guided':[torch.tensor([1.],dtype=torch.float32) for _ in range(36)],'final_latent':torch.tensor([2.],dtype=torch.float32)}
            def item_for(values):
                torch.save(values,path)
                art={'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),
                    'tensor_sha256':{k:tree_digest(v) for k,v in good.items()}}
                return {'artifact_root':str(root),'row':{'vector_artifact':art,
                    'guided_sha256':[tree_digest(x) for x in good['guided']],
                    'guided_list_sha256':tree_digest(good['guided']),'final_latent_sha256':tree_digest(good['final_latent'])}}
            item=item_for(good);assert actual_vectors(item,torch.load,[1],torch,tree_digest)['actual_tensors_reloaded']==37
            variants={'short_guided':{**good,'guided':good['guided'][:-1]},
                'dtype':{**good,'final_latent':good['final_latent'].double()},
                'shape':{**good,'final_latent':torch.tensor([2.,3.])},
                'nonfinite':{**good,'final_latent':torch.tensor([float('nan')])},
                'wrong_final_content':{**good,'final_latent':torch.tensor([3.])}}
            for name,values in variants.items():
                item=item_for(values)
                try:actual_vectors(item,torch.load,[1],torch,tree_digest)
                except ValueError:controls.append(name)
                else:raise AssertionError('Affected file reader admitted '+name)
            item=item_for(good);path.write_bytes(path.read_bytes()[:100])
            try:actual_vectors(item,torch.load,[1],torch,tree_digest)
            except ValueError:controls.append('actual_truncation')
            else:raise AssertionError('Truncated actual file admitted')
            item=item_for(good);item['artifact_root']=str(root/'foreign')
            try:actual_vectors(item,torch.load,[1],torch,tree_digest)
            except ValueError:controls.append('foreign_path')
            else:raise AssertionError('Foreign actual file admitted')
        # Native compatibility stays causal: no missing prepare or active changes repaired.
        item={**next(s for s in scope['all64_slots'] if s['slot'] in reused),**reused[0]}
        ref=native[item['sample_name']];assert bind_pair(item,ref,proof,context)['compatible']
        pairing_refusals=[]
        for name in ('missing_prepare','active_mask','active_condition','different_model','first_guided'):
            x=copy.deepcopy(item)
            if name=='missing_prepare':x['request_record']['prepared_input_calls']=[]
            elif name=='active_mask':
                x['row']['actual_condition_masks'][0]['nonzero_elements']=1
                x['row']['condition_fields_before'][0]['gt_frames']='CHANGED_ACTIVE'
            elif name=='active_condition':x['row']['condition_fields_before'][0]['t5_text_embeddings']='CHANGED_ACTIVE'
            elif name=='different_model':x['model_context']='FOREIGN'
            else:x['row']['guided_sha256'][0]='BAD'
            assert not bind_pair(x,ref,proof,context)['compatible'];pairing_refusals.append(name)
        from wcomr.lpips_resource_identity import audit
        metric_sha=p['execution_payload_sha256']['src/wcomr/rv0_lpips.py']
        resource_identity=audit(args.project/'.sync/wc-rv0-lpips-resource-v2',metric_sha)
        assert not torch.cuda.is_initialized()
        r.update(status='E3_COMPLETE64_POST_SELECTION_ACTUAL_CPU_PASS_NOT_GPU',exit_code=0,CUDA_initialized=False,
            actual_reuse_reader={'validated_original_paths':10,'actual_tensors_reloaded':370,
                'actual_fully_decoded_videos':10,'actual_decoded_frames':930,'per_path':real},
            file_reader_actual_refusals=controls,Native_pairing_refusals=pairing_refusals,
            actual_original_input_evidence=evidence,original_row_source_verifier=source,
            unchanged_original_metric_resource_identity=resource_identity,
            original_sampling_and_full20_production_CPU_reused_not_rerun=True,
            no_new_metric_values_generated=True,no_authorization_or_selected_stage_created=True)
    except BaseException as error:
        r.update(status='E3_POST_SELECTION_ACTUAL_CPU_FAILED_NOT_GPU',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            method_payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']},
            execution_payload_after_sha256={n:sha(args.stage/n) for n in p['execution_payload_sha256']},
            budget_after_sha256=sha(args.project/'reports/budget.json'))
        if (r['method_payload_after_sha256']!=c['payload_sha256'] or r['execution_payload_after_sha256']!=p['execution_payload_sha256']
                or r['budget_after_sha256']!=r['budget_before_sha256']):
            r.update(status='E3_POST_SELECTION_CPU_IDENTITY_FAILED',exit_code=1)
        write(target,r)
    print(json.dumps({k:r[k] for k in ('status','exit_code','CPU_wall_seconds','GPU_submissions')}))
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
