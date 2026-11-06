"""Bounded F0 compatibility check using the actual retained safety components."""
import argparse
import json
import os
from pathlib import Path
import time

p = argparse.ArgumentParser()
p.add_argument('--project', type=Path, required=True)
p.add_argument('--gpu-uuid', required=True)
p.add_argument('--receipt', type=Path, required=True)
a = p.parse_args()
os.environ.update(CUDA_VISIBLE_DEVICES=a.gpu_uuid, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
state = {'stage': 'F0_GUARDRAIL_PIPELINE', 'pid': os.getpid(), 'status': 'INITIALIZING',
         'started_unix': time.time(), 'video_generation_started': False}
def save():
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.receipt.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2)+'\n'); tmp.replace(a.receipt)
save()
try:
    import torch
    import numpy as np
    from PIL import Image
    from cosmos_oss.init import init_environment
    init_environment()
    torch.set_num_threads(4)
    from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common import presets
    text = presets.create_text_guardrail_runner(offload_model_to_cpu=True)
    video = presets.create_video_guardrail_runner(offload_model_to_cpu=True)
    state['components'] = [type(x).__name__ for x in text.safety_models + video.safety_models + video.postprocessors]
    save()
    prompt = 'A red ball rolls across a wooden table.'
    # Direct Qwen call propagates exceptions that its public wrapper otherwise catches.
    results = []
    for component in text.safety_models:
        check = getattr(component, 'extract_label_and_categories', component.is_safe)
        safe, message = check(prompt)
        if not safe:
            raise RuntimeError(f'Text compatibility probe failed: {type(component).__name__}: {message}')
        results.append({'component': type(component).__name__, 'safe': bool(safe)})
    state['text_results'] = results
    frames = np.full((1, 256, 256, 3), 127, dtype=np.uint8)
    classifier = video.safety_models[0]
    classifier._to_cuda_if_offload()
    # Direct inference prevents an internal catch-and-continue from hiding kernel errors.
    label = classifier._VideoContentSafetyFilter__infer(Image.fromarray(frames[0]))
    classifier._to_cpu_if_offload()
    state['synthetic_frame_label'] = int(label)
    state['synthetic_video_decision'] = video.run_safety_check(frames)[0]
    processed = video.postprocess(frames)
    if processed.shape != frames.shape or not np.isfinite(processed).all():
        raise RuntimeError('Face filter returned malformed output')
    torch.cuda.synchronize()
    state.update(status='PIPELINE_LOAD_FORWARD_PASS', output_shape=list(processed.shape),
                 limitation='Compatibility on benign synthetic inputs only; not classifier accuracy or F1 generation')
except Exception as exc:
    state.update(status='FAILED', error=repr(exc))
    raise
finally:
    state['elapsed_seconds'] = time.time() - state['started_unix']
    save()
    print(json.dumps(state))
