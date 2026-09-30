"""Offline repeated/black/deranged inputs: judge sensitivity, not quality labels."""
import argparse,hashlib,inspect,importlib.metadata,json,os,pathlib,signal,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.development_vqa_run import sha256,load_bound,load_questions,validate_protocol
from wcomr.development_vqa import score_answer
from wcomr.development_vqa_input import decode_video_input,prepare_question
from wcomr.vqa_controls import CONDITIONS,condition_order,summarize_controls
from verify_public_assets import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--gpu-uuid',required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();root=a.project.resolve();started=time.time()
    state={'pid':os.getpid(),'status':'INITIALIZING','started_unix':started,'gpu_uuid':a.gpu_uuid,'rows':[],'source_sha256':{}}
    def save():
        a.receipt.parent.mkdir(parents=True,exist_ok=True);tmp=a.receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(a.receipt)
    def terminate(*args):raise SystemExit('Input controls supervisor SIGTERM')
    signal.signal(signal.SIGTERM,terminate);save()
    try:
        if os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid or any(os.environ.get(k)!='1' for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE']):raise ValueError('Requires offline UUID supervisor')
        protocol=json.loads((root/'manifests/w1_vqa_controls_protocol.json').read_text());state['protocol']=protocol
        if protocol['status']!='FROZEN_AFTER_METHOD_PROXY_SCORES_BEFORE_INPUT_CONTROL_SCORES' or protocol['conditions']!=CONDITIONS or protocol['max_gpu_seconds']!=300 or protocol['expected_total_generated_answers']!=126:raise ValueError('Control protocol/cap differs')
        inputs=load_bound(root/protocol['input_protocol'],protocol['input_protocol_sha256']);validate_protocol(inputs)
        runtime=load_bound(root/protocol['runtime_protocol'],protocol['runtime_protocol_sha256'])
        baseline=load_bound(root/protocol['baseline_receipt'],protocol['baseline_sha256'])
        if baseline['status']!='W1_VQA_ALL_ORIGINAL8_QUESTIONS_ATTEMPTED' or baseline['protocol']!=inputs or [r['name'] for r in baseline['rows']]!=protocol['samples'] or inputs['samples']!=protocol['samples']:raise ValueError('Original baseline coverage differs')
        questions=load_questions(root,inputs)
        sources=load_bound(root/protocol['reference_receipt'],protocol['reference_sha256'])
        if [r['name'] for r in sources['cases']]!=protocol['samples']:raise ValueError('Original WC source order differs')
        source={r['name']:r['off'] for r in sources['cases']}
        if protocol['mismatch_source']!={n:protocol['samples'][(i+1)%8] for i,n in enumerate(protocol['samples'])}:raise ValueError('Fixed derangement mapping differs')
        for name,item in source.items():
            if item['outcome']!='ACCEPTED' or sha256(item['video_path'])!=item['video_sha256']:raise ValueError('Reference source video differs')
        for path in ['scripts/run_w1_vqa_controls.py','scripts/supervise_f1.py','scripts/verify_public_assets.py','src/wcomr/vqa_controls.py','src/wcomr/development_vqa.py','src/wcomr/development_vqa_input.py','src/wcomr/development_vqa_run.py','manifests/w1_vqa_controls_protocol.json',protocol['input_protocol'],protocol['runtime_protocol'],inputs['asset_integrity_manifest']]:state['source_sha256'][path]=sha256(root/path)
        asset=json.loads((root/inputs['asset_integrity_manifest']).read_text())[inputs['judge_repo']]
        if asset['revision']!=inputs['judge_revision']:raise ValueError('Judge revision differs')
        snapshot=root/'hfhub'/('models--'+inputs['judge_repo'].replace('/','--'))/'snapshots'/asset['revision']
        state['model_integrity']=[verify(snapshot,e) for e in asset['files']];save()
        if len(state['model_integrity'])!=10 or any(e['status']!='PASS' for e in state['model_integrity']):raise ValueError('Incomplete model assets')
        import torch
        from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
        from qwen_vl_utils import process_vision_info
        processor=AutoProcessor.from_pretrained(str(snapshot),local_files_only=True)
        installed={str(Path(inspect.getfile(obj))).split('/site-packages/',1)[1]:sha256(inspect.getfile(obj)) for obj in [Qwen3VLForConditionalGeneration,type(processor),process_vision_info]}
        versions={key:importlib.metadata.version(key) for key in runtime['versions']}
        if installed!=runtime['source_sha256'] or versions!=runtime['versions'] or torch.__version__!=runtime['torch'] or installed!=baseline['setup']['runtime_source_sha256']:raise ValueError('Baseline runtime/source differs')
        torch.set_num_threads(2);torch.manual_seed(0);torch.cuda.manual_seed_all(0);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        state['status']='LOADING_MODEL';save();start=time.time()
        model,loading=Qwen3VLForConditionalGeneration.from_pretrained(str(snapshot),local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'},output_loading_info=True)
        if any(loading.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']):raise ValueError('Model load mismatch')
        model.eval()
        if model.dtype!=torch.bfloat16 or model.config._attn_implementation!='sdpa' or protocol['generation']!=inputs['generation']:raise ValueError('Generation/precision/attention differs')
        state['setup']={'torch':torch.__version__,**versions,'runtime_source_sha256':installed,'model_eval':not model.training,'model_dtype':str(model.dtype),'attention':'sdpa','load_seconds':time.time()-start,'loading_info':loading,'generation':inputs['generation']}
        decoded={name:decode_video_input(processor,arm['video_path']) for name,arm in source.items()}
        state['status']='SCORING_INPUT_CONTROLS';save()
        for name in protocol['samples']:
            row={'name':name,'status':'SCORING','condition_order':condition_order(name),'conditions':{}};state['rows'].append(row);save()
            for condition in row['condition_order']:
                source_name=protocol['mismatch_source'][name] if condition=='cyclic_mismatch' else name
                original,metadata=decoded[source_name];video=torch.zeros_like(original) if condition=='blank' else original
                if not torch.isfinite(video).all():raise ValueError('Nonfinite control input')
                observed={'status':'SCORING','source_name':source_name,'input':{'source_video_sha256':source[source_name]['video_sha256'],'sampled_tensor_sha256':hashlib.sha256(video.numpy().tobytes()).hexdigest(),'video_shape':list(video.shape),'metadata':{k:[int(x) for x in v] if k=='frames_indices' else v for k,v in metadata.items()},'blank':condition=='blank','blank_all_zero_verified':bool(torch.count_nonzero(video)==0) if condition=='blank' else None},'answers':[],'generation_records':[]}
                row['current_condition']=condition;row['conditions'][condition]=observed;save()
                for question in questions[name]:
                    batch=prepare_question(processor,question,video,metadata)
                    if not torch.isfinite(batch['pixel_values_videos']).all():raise ValueError('Nonfinite processed input')
                    record={'uid':question['uid'],'input_ids_sha256':hashlib.sha256(batch['input_ids'].numpy().tobytes()).hexdigest(),'input_tokens':batch['input_ids'].shape[-1],'video_grid_thw':batch['video_grid_thw'].tolist()}
                    start=time.time();batch=batch.to('cuda:0')
                    with torch.inference_mode():generated=model.generate(**batch,do_sample=False,max_new_tokens=1024)
                    if generated.ndim!=2 or generated.shape[0]!=1:raise ValueError('Unexpected generation batch')
                    tokens=generated[0,batch['input_ids'].shape[-1]:].detach().cpu().tolist();raw=processor.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    parsed=score_answer(question,raw);observed['answers'].append({k:parsed[k] for k in ['uid','raw','parsed_answer','parse_status']})
                    record.update(generated_token_ids=tokens,generated_tokens=len(tokens),reached_token_cap=len(tokens)>=1024,seconds=time.time()-start);observed['generation_records'].append(record);del batch,generated;save()
                observed['status']='ALL_ORIGINAL_QUESTIONS_COMPLETE';save()
            row['status']='ALL_CONDITIONS_COMPLETE';row.pop('current_condition',None);save()
        state['summary']=summarize_controls(state['rows'],protocol,baseline,questions);state['status']='W1_VQA_CONTROLS_ALL_ORIGINAL8_COMPLETE'
        state['peak_memory']={'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()}
    except BaseException as e:state.update(status='TECH_BLOCKED',error_type=type(e).__name__,error=str(e));raise
    finally:state['ended_unix']=time.time();state['wall_seconds']=time.time()-started;save()


if __name__=='__main__':main()
