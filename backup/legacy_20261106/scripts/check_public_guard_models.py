"""Offline CPU load/forward checks for public safety-model dependencies.

This is component compatibility evidence, not validation of the complete
Cosmos safety pipeline or of a safety classifier's accuracy.
"""
import argparse
import json
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['qwen', 'siglip'], required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', HF_HUB_CACHE=str(args.cache))
    import torch
    import transformers
    torch.set_num_threads(4)
    torch.manual_seed(0)
    state = dict(model=args.model, pid=os.getpid(), started_unix=time.time(),
                 device='cpu', gpu_workload_started=False,
                 torch_version=torch.__version__, transformers_version=transformers.__version__,
                 scope='PUBLIC_COMPONENT_ONLY_NOT_FULL_SAFETY_PIPELINE')
    try:
        if args.model == 'qwen':
            repo = 'Qwen/Qwen3Guard-Gen-0.6B'
            tokenizer = transformers.AutoTokenizer.from_pretrained(repo, local_files_only=True)
            model = transformers.AutoModelForCausalLM.from_pretrained(repo, local_files_only=True)
            model = model.to(dtype=torch.bfloat16).eval()
            prompt = 'A red ball rolls across a wooden table.'
            text = tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}], tokenize=False)
            inputs = tokenizer([text], return_tensors='pt')
            with torch.inference_mode():
                result = model.generate(**inputs, max_new_tokens=128, do_sample=False)
            content = tokenizer.decode(result[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            state.update(prompt=prompt, output=content)
            if 'Safety: Safe' not in content:
                raise RuntimeError('Benign component probe did not produce the expected parseable label')
        else:
            from PIL import Image
            repo = 'google/siglip-so400m-patch14-384'
            model = transformers.SiglipModel.from_pretrained(repo, local_files_only=True).eval()
            processor = transformers.SiglipProcessor.from_pretrained(repo, local_files_only=True)
            inputs = processor(images=Image.new('RGB', (384, 384), (127, 127, 127)), return_tensors='pt')
            with torch.inference_mode():
                features = model.get_image_features(**inputs)
            if not torch.isfinite(features).all() or not (features.norm() > 0):
                raise RuntimeError('Nonfinite or zero image features')
            state.update(feature_shape=list(features.shape), feature_norm=float(features.norm()))
        state['status'] = 'CPU_LOAD_FORWARD_PASS'
    except Exception as exc:
        state.update(status='FAILED', error=repr(exc))
        raise
    finally:
        state['elapsed_seconds'] = time.time() - state['started_unix']
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(state, indent=2) + '\n')
        print(json.dumps(state))


if __name__ == '__main__':
    main()
