"""Read-only real UniPC schedule replay. No model, CUDA, weights or ledger writes."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

UNIPC='cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py'
UNIPC_SHA='f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3'
RF='cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py'
RF_SHA='c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'
REG='.sync/wc-p-acr-local12-production-cpu-r2-20261015/registration.json'
CPU_SOURCE='715cae725423bfef8a5a243a0729b80d9c68f5cb'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(project):
    project=Path(project).resolve();regpath=project/REG;reg=json.loads(regpath.read_text())
    if reg['source_revision']!=CPU_SOURCE:raise ValueError('Pinned accepted production CPU source changed')
    for name,digest in ((UNIPC,UNIPC_SHA),(RF,RF_SHA)):
        if reg['runtime_source_sha256'].get(name)!=digest or sha(project/'runtime'/name)!=digest:
            raise ValueError('Actual schedule runtime identity changed: '+name)
    source=(project/'runtime'/RF).read_text();calls=[]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node,ast.Call):
            func=ast.unparse(node.func)
            if 'UniPC' in func or func.endswith('.set_timesteps'):
                calls.append({'line':node.lineno,'call':ast.get_source_segment(source,node)})
    expected='FlowUniPCMultistepScheduler(\n            num_train_timesteps=1000, shift=1, use_dynamic_shifting=False\n        )'
    if not any(r['call']==expected for r in calls):raise ValueError('Actual model scheduler constructor changed')
    if not any('use_kerras_sigma=self.config.use_kerras_sigma_at_inference' in r['call'] for r in calls):
        raise ValueError('Actual Karras schedule callsite changed')
    budget_before=sha(project/'reports/budget.json');os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    if torch.cuda.is_initialized():raise ValueError('Readonly scheduler entered with CUDA initialized')
    def forbidden(*args,**kwargs):raise RuntimeError('No CUDA, weights or download in schedule replay')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    spec=importlib.util.spec_from_file_location('actual_pinned_UniPC_schedule_replay',project/'runtime'/UNIPC)
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    scheduler=native.FlowUniPCMultistepScheduler(num_train_timesteps=1000,shift=1,use_dynamic_shifting=False)
    scheduler.set_timesteps(35,device='cpu',shift=1,use_kerras_sigma=True)
    if (scheduler.sigmas.device.type!='cpu' or scheduler.timesteps.device.type!='cpu'
            or scheduler.sigmas.numel()!=37 or scheduler.timesteps.numel()!=36
            or scheduler.sigmas[-1].item()!=0 or torch.cuda.is_initialized()):
        raise ValueError('Actual requested35/36update CPU schedule shape changed')
    result={'status':'ACTUAL_PINNED_UNIPC_KARRAS_CONTINUOUS_CLOCK_CPU_REPLAY',
        'provenance':'NATIVE_SCHEDULER_REPLAY_NOT_ORIGINAL_PER_RUN_SIGMA_CAPTURE',
        'runtime_binding_source_revision':reg['source_revision'],'runtime_registration_sha256':sha(regpath),
        'runtime_sources':{UNIPC:UNIPC_SHA,RF:RF_SHA},'actual_callsites':calls,
        'constructor_kwargs':{'num_train_timesteps':1000,'shift':1,'use_dynamic_shifting':False},
        'set_timesteps_kwargs':{'num_inference_steps':35,'device':'cpu','shift':1,'use_kerras_sigma':True},
        'timesteps':scheduler.timesteps.tolist(),'sigmas':scheduler.sigmas.tolist(),
        'sigma_dtype':str(scheduler.sigmas.dtype),'timestep_dtype':str(scheduler.timesteps.dtype),
        'num_updates':scheduler.num_inference_steps,'Torch_version':torch.__version__,
        'integer_timestep_div1000_not_used_as_sigma':True,'GPU_submissions':0,'weights_loaded':0,
        'model_forwards':0,'CUDA_initialized':False,'ledger_written':False,
        'budget_before_sha256':budget_before,'budget_after_sha256':sha(project/'reports/budget.json'),
        'observed_unix':time.time()}
    if result['budget_after_sha256']!=budget_before:raise ValueError('CPU replay budget changed')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);a=p.parse_args()
    result=audit(a.project)
    result['audit_script_sha256']=globals().get('REMOTE_SCRIPT_SHA256')
    print(json.dumps(result,allow_nan=False))
