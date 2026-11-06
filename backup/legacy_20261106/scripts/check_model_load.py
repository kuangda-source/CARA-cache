"""F0 core-model construction only: never generate video or change guardrails."""
import argparse
import inspect
import json
import os
import sys
from pathlib import Path
import time
import traceback

p = argparse.ArgumentParser()
p.add_argument('--project', type=Path, required=True)
p.add_argument('--gpu-uuid', required=True)
p.add_argument('--receipt', type=Path, required=True)
a = p.parse_args()
sys.path.insert(0, str(a.project.resolve() / 'src'))
os.environ['CUDA_VISIBLE_DEVICES'] = a.gpu_uuid
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
state = {'stage': 'F0_CORE_MODEL_LOAD_ONLY', 'pid': os.getpid(), 'status': 'IMPORTING',
         'started_unix': time.time(), 'video_generation_started': False, 'state_load_calls': []}

def save():
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.receipt.with_suffix('.tmp'); tmp.write_text(json.dumps(state, indent=2)+'\n'); tmp.replace(a.receipt)

save()
try:
    import torch
    from cosmos_oss.init import init_environment
    from cosmos_predict2.config import SetupArguments
    from cosmos_predict2._src.predict2.inference.video2world import Video2WorldInference
    init_environment()
    params = json.loads((a.project / 'configs/f1_setup.json').read_text())
    setup = SetupArguments(**params, output_dir=str(a.receipt.parent/'unused-model-load'))
    from wcomr.runtime_config import install_core_inference_registration
    state['registration_adapter'] = install_core_inference_registration(setup.model, setup.experiment)
    checkpoint = Path(str(setup.checkpoint_path))
    state.update(status='LOADING', checkpoint=str(checkpoint), checkpoint_bytes=checkpoint.stat().st_size)
    save()
    original = torch.nn.Module.load_state_dict

    def observed(module, weights, *args, **kwargs):
        result = original(module, weights, *args, **kwargs)
        state['state_load_calls'].append({'class': type(module).__qualname__, 'input_key_count': len(weights),
            'missing_keys': list(getattr(result, 'missing_keys', [])),
            'unexpected_keys': list(getattr(result, 'unexpected_keys', []))})
        save()
        return result

    torch.nn.Module.load_state_dict = observed
    try:
        init_params = {key: value for key, value in params.items()
                       if key in inspect.signature(Video2WorldInference).parameters}
        init_params.update(experiment_name=setup.experiment, ckpt_path=str(setup.checkpoint_path),
                           config_file=setup.config_file, s3_credential_path='', worldcache_enabled=False)
        pipe = Video2WorldInference(**init_params)
        torch.cuda.synchronize()
        state.update(status='CORE_CONSTRUCTOR_PASS_REQUIRES_STATE_REVIEW',
                     network_class=type(pipe.model.net).__qualname__,
                     network_parameters=sum(x.numel() for x in pipe.model.net.parameters()),
                     blocks=len(pipe.model.net.blocks),
                     parameter_devices=sorted({str(x.device) for x in pipe.model.net.parameters()}),
                     parameter_dtypes=sorted({str(x.dtype) for x in pipe.model.net.parameters()}),
                     peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                     safety_pipeline_load_validated=False)
    finally:
        torch.nn.Module.load_state_dict = original
except BaseException as exc:
    state.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
    traceback.print_exc()
    raise
finally:
    state['ended_unix'] = time.time(); state['elapsed_seconds'] = state['ended_unix']-state['started_unix']; save()
