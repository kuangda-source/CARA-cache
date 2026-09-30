"""One offline Qwen3-VL2B development proxy over original CAL8 questions/videos.

No generation, safety bypass, prompt retries, or independent-quality claim.
Must be run through the existing budgeted supervisor, after CPU asset audit.
"""
import argparse, hashlib, importlib.metadata, inspect, json, os, signal, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.development_vqa_run import sha256, load_bound, validate_protocol, load_questions, evaluate_cases
from wcomr.development_vqa_input import decode_video_input, prepare_question
from wcomr.replay_results import summarize as replay_summary
from verify_public_assets import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True)
    p.add_argument('--gpu-uuid',required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();project=a.project.resolve();started=time.time()
    state={'pid':os.getpid(),'status':'INITIALIZING','gpu_uuid':a.gpu_uuid,'rows':[],
           'started_unix':started,'source_sha256':{}}
    def save():
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        tmp=a.receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(a.receipt)
    def terminate(*args):raise SystemExit('VQA supervisor SIGTERM')
    signal.signal(signal.SIGTERM,terminate);save()
    try:
        if os.environ.get('CUDA_VISIBLE_DEVICES') != a.gpu_uuid or any(
            os.environ.get(k) != '1' for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE']):
            raise ValueError('Requires UUID-bound offline supervisor environment')
        protocol=json.loads((project/'manifests/w1_development_vqa_protocol.json').read_text())
        validate_protocol(protocol);state['protocol']=protocol
        for path in ['scripts/run_w1_vqa.py','scripts/supervise_f1.py','scripts/verify_public_assets.py',
                     'src/wcomr/development_vqa.py','src/wcomr/development_vqa_input.py',
                     'src/wcomr/development_vqa_run.py','src/wcomr/replay_results.py',
                     'manifests/w1_development_vqa_protocol.json','manifests/w1_vqa_runtime_protocol.json',protocol['asset_integrity_manifest']]:
            state['source_sha256'][path]=sha256(project/path)
        reference=load_bound(project/protocol['reference_receipt'],protocol['reference_sha256'])
        candidate=load_bound(project/protocol['candidate_receipt'],protocol['candidate_sha256'])
        validated=replay_summary(candidate,reference=reference)
        if [r['name'] for r in validated['samples']] != protocol['samples'] or [
            r['name'] for r in reference['cases']] != protocol['samples']:
            raise ValueError('Original8 membership/order differs')
        questions=load_questions(project,protocol)
        cases=[{'name':old['name'],'reference':old['off'],'candidate':new['scalar_off']}
               for old,new in zip(reference['cases'],candidate['cases'])]
        if sum(len(questions[c['name']]) for c in cases if c['candidate']['outcome']=='ACCEPTED') != protocol['planned_candidate_questions_for_accepted']:
            raise ValueError('Accepted candidate question coverage differs')
        state['video_integrity']=[]
        for case in cases:
            for arm in ['reference','candidate']:
                item=case[arm]
                if item['outcome']=='ACCEPTED':
                    if sha256(item['video_path']) != item['video_sha256']:
                        raise ValueError('Video hash differs')
                    state['video_integrity'].append({'name':case['name'],'arm':arm,
                        'sha256':item['video_sha256'],'bytes':Path(item['video_path']).stat().st_size})
                elif item.get('video_path') is not None or item.get('video_sha256') is not None:
                    raise ValueError('Rejected candidate unexpectedly contains a saved video')
        asset=json.loads((project/protocol['asset_integrity_manifest']).read_text())[protocol['judge_repo']]
        if asset['revision'] != protocol['judge_revision']:raise ValueError('Judge revision differs')
        snapshot=project/'hfhub'/('models--'+protocol['judge_repo'].replace('/','--'))/'snapshots'/asset['revision']
        state['model_integrity']=[verify(snapshot,entry) for entry in asset['files']];save()
        if len(state['model_integrity']) != 10 or any(x['status']!='PASS' for x in state['model_integrity']):
            raise ValueError('Incomplete/corrupt model assets')
        import torch, transformers
        from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
        from qwen_vl_utils import process_vision_info
        versions={k:importlib.metadata.version(k) for k in ['transformers','qwen-vl-utils','decord']}
        runtime_lock=json.loads((project/'manifests/w1_vqa_runtime_protocol.json').read_text())
        if runtime_lock['input_protocol_sha256'] != state['source_sha256']['manifests/w1_development_vqa_protocol.json'] or versions != runtime_lock['versions'] or torch.__version__ != runtime_lock['torch']:
            raise ValueError('CPU-validated input runtime versions differ')
        processor=AutoProcessor.from_pretrained(str(snapshot),local_files_only=True)
        runtime_sources={str(Path(inspect.getfile(obj))).split('/site-packages/',1)[1]:sha256(inspect.getfile(obj))
                         for obj in [Qwen3VLForConditionalGeneration,type(processor),process_vision_info]}
        if runtime_sources != runtime_lock['source_sha256']:
            raise ValueError('CPU-validated installed model/processor/vision source differs')
        torch.set_num_threads(2);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
        torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        load_start=time.time();state['status']='LOADING_MODEL';save()
        model=Qwen3VLForConditionalGeneration.from_pretrained(str(snapshot),local_files_only=True,
            dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'},output_loading_info=True)
        model,loading=model
        if any(loading.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']):
            raise ValueError('Model loading key mismatch: '+str(loading))
        model.eval()
        state['setup']={'torch':torch.__version__,**versions,'device':torch.cuda.get_device_name(0),
            'model_class':type(model).__name__,'model_eval':not model.training,'model_dtype':str(model.dtype),
            'attention':model.config._attn_implementation,'load_seconds':time.time()-load_start,
            'loading_info':loading,'generation':protocol['generation'],
            'runtime_source_sha256':runtime_sources}
        if model.dtype!=torch.bfloat16 or model.config._attn_implementation!='sdpa':
            raise ValueError('Model precision/attention differs')
        state['status']='SCORING';save()
        def evaluate_video(arm, original_questions):
            video,metadata=decode_video_input(processor,arm['video_path'])
            if not torch.isfinite(video).all():raise ValueError('Nonfinite decoded video')
            provenance={'video_sha256':arm['video_sha256'],'video_shape':list(video.shape),
                        'metadata':{k:[int(x) for x in v] if k=='frames_indices' else v for k,v in metadata.items()},
                        'sampled_tensor_sha256':hashlib.sha256(video.numpy().tobytes()).hexdigest()}
            def outputs():
                for question in original_questions:
                    batch=prepare_question(processor,question,video,metadata)
                    if not torch.isfinite(batch['pixel_values_videos']).all():raise ValueError('Nonfinite processed video')
                    record={'uid':question['uid'],'input_ids_sha256':hashlib.sha256(batch['input_ids'].numpy().tobytes()).hexdigest(),
                            'input_tokens':batch['input_ids'].shape[-1],
                            'video_grid_thw':batch['video_grid_thw'].tolist()}
                    start=time.time();batch=batch.to('cuda:0')
                    with torch.inference_mode():
                        generated=model.generate(**batch,do_sample=False,max_new_tokens=1024)
                    if generated.ndim!=2 or generated.shape[0]!=1:raise ValueError('Unexpected output batch')
                    tokens=generated[0,batch['input_ids'].shape[-1]:].detach().cpu().tolist()
                    raw=processor.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    record.update(generated_token_ids=tokens,generated_tokens=len(tokens),
                                  reached_token_cap=len(tokens)>=1024,seconds=time.time()-start)
                    del batch,generated
                    yield raw,record
            return outputs(),provenance
        state['summary']=evaluate_cases(cases,questions,evaluate_video,state['rows'],save)
        state['status']='W1_VQA_ALL_ORIGINAL8_QUESTIONS_ATTEMPTED'
        state['peak_memory']={'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()}
    except BaseException as e:
        state.update(status='TECH_BLOCKED',error_type=type(e).__name__,error=str(e));raise
    finally:
        state['ended_unix']=time.time();state['wall_seconds']=time.time()-started;save()


if __name__=='__main__':main()
