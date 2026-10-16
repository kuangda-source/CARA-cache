#!/usr/bin/env python3
"""Validate one frozen metric model on synthetic CPU inputs, never paper videos.

The eventual bundle must execute all five roles. A resource or model failure
is retained; neither the resource download nor this probe is a quality result.
"""
import argparse
import gc
import hashlib
import inspect
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback
import urllib.request

ROLES = ('DINO','AMT_S','RAFT_THINGS','ViCLIP','MUSIQ_SPAQ')
WEIGHTS = {
    'DINO': (343242485,'bf34ad0f424b9029b593e8dc3ed553bf26e88bcba0d32bf3e62a6209cb64c85e'),
    'AMT_S': (12038359,'07e7e03405c213fe4405678db9b42d05671e48c56faf6a441b99bb0047d3cf77'),
    'RAFT_THINGS': (21108000,'fcfa4125d6418f4de95d84aec20a3c5f4e205101715a79f193243c186ac9a7e1'),
    'ViCLIP': (1710545812,'7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56'),
    'MUSIQ_SPAQ': (108610983,'358bb6af275e28ea56821d44fb55c6cb83645db11f394d3ad65b2d149965ab50'),
}
BPE_SHA='924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a'
MUSIQ_SOURCE_SHA='ddab924a5ff529e1668404fa058777a9d00890390166c2b12ef7fffdc0baebb3'


def sha(path):
    path=Path(path);before=path.stat();digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):digest.update(block)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('Resource changed while reading: '+str(path))
    return digest.hexdigest()


def preflight(stage,role):
    stage=Path(stage).resolve()
    registration=json.loads((stage/'registration.json').read_text())
    if (registration['purpose']!='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
            or registration['roles']!=list(ROLES) or role not in ROLES):
        raise ValueError('The complete original five-model CPU scope is required')
    for name,digest in registration['payload_sha256'].items():
        relative=Path(name);path=stage/relative
        if (relative.is_absolute() or '..' in relative.parts or path.is_symlink()
                or not path.resolve().is_relative_to(stage) or sha(path)!=digest):
            raise ValueError('Changed or escaped frozen metric source: '+name)
    manifest=json.loads((stage/'model-resources.json').read_text())
    if set(manifest['resources'])!=set(ROLES):
        raise ValueError('Do not drop a metric model because its resource is missing')
    for name,(size,digest) in WEIGHTS.items():
        resource=manifest['resources'][name];path=Path(resource['path'])
        if (not path.is_absolute() or not path.is_file() or path.name.endswith('.part')
                or resource['bytes']!=size or resource['sha256']!=digest or path.stat().st_size!=size):
            raise ValueError('Complete exact registered model resource required: '+name)
    current=Path(manifest['resources'][role]['path'])
    if sha(current)!=WEIGHTS[role][1]:raise ValueError('Model checkpoint SHA changed: '+role)
    bpe=stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz'
    if sha(bpe)!=BPE_SHA or bpe.stat().st_size!=1356917:
        raise ValueError('Verify the real tokenizer before importing the upstream package')
    return registration,manifest,current


def deny_external_access(events):
    """Process-local guards; do not change another job's environment."""
    def blocked(*args,**kwargs):
        events.append(dict(kind='NETWORK_OR_DOWNLOAD_BLOCKED'))
        raise RuntimeError('Metric CPU validation forbids network access or implicit downloads')
    socket.create_connection=blocked
    socket.socket.connect=blocked
    socket.socket.connect_ex=blocked
    urllib.request.urlopen=blocked
    original_run,original_popen=subprocess.run,subprocess.Popen
    def inspect_command(command):
        first=(command.split()[0] if isinstance(command,str) else str(command[0]))
        if Path(first).name in ('wget','curl','git','pip','pip3'):
            blocked()
    def run(command,*args,**kwargs):
        inspect_command(command);return original_run(command,*args,**kwargs)
    def popen(command,*args,**kwargs):
        inspect_command(command);return original_popen(command,*args,**kwargs)
    subprocess.run,subprocess.Popen=run,popen
    return blocked


def tensor_receipt(tensor,torch):
    if tensor.device.type!='cpu' or tensor.dtype!=torch.float32 or not bool(torch.isfinite(tensor).all()):
        raise ValueError('Actual finite FP32 CPU model output required')
    return dict(shape=list(tensor.shape),dtype=str(tensor.dtype),device=str(tensor.device),
        finite=True,requires_grad=tensor.requires_grad,
        sha256=hashlib.sha256(tensor.detach().contiguous().numpy().tobytes()).hexdigest())


def probe(role,stage,resource,torch):
    import numpy as np
    from vbench.utils import clip_transform,dino_transform
    generator=torch.Generator(device='cpu').manual_seed(0)
    images=torch.randint(0,256,(2,3,432,768),generator=generator,dtype=torch.uint8)
    extra={}
    if role=='DINO':
        torch.hub.set_dir(str(resource.parent.parent))
        model=torch.hub.load(repo_or_dir=str(stage/'external/dino'),model='dino_vitb16',
                             source='local',path=str(resource),read_frame=False)
        model=model.float().cpu().eval().requires_grad_(False)
        prepared=dino_transform(224)(images)
        outputs={'features':model(prepared)}
        if tuple(outputs['features'].shape)!=(2,768):raise ValueError('DINO interface shape differs')
        extra.update(actual_model_input_shape=list(prepared.shape),synthetic_source_frames=2)
    elif role=='AMT_S':
        from vbench.motion_smoothness import MotionSmoothness,InputPadder,img2tensor
        wrapper=MotionSmoothness(str(stage/'upstream/vbench/third_party/amt/cfgs/AMT-S.yaml'),
                                 str(resource),'cpu')
        model=wrapper.model.float().cpu().eval().requires_grad_(False)
        inputs=[img2tensor(image.permute(1,2,0).numpy()).cpu() for image in images]
        padder=InputPadder(inputs[0].shape,16);left,right=padder.pad(*inputs)
        prediction=model(left,right,wrapper.embt,scale_factor=1.,eval=True)['imgt_pred']
        prediction=padder.unpad(prediction)
        outputs={'interpolated_frame':prediction}
        if tuple(prediction.shape)!=(1,3,432,768):raise ValueError('AMT output geometry differs')
        extra.update(synthetic_frame_pairs=1,interpolation_iterations=wrapper.niters,
                     scale_factor=1.,actual_model_input_shape=list(left.shape))
    elif role=='RAFT_THINGS':
        from easydict import EasyDict
        from vbench.dynamic_degree import DynamicDegree,InputPadder
        args=EasyDict(model=str(resource),small=False,mixed_precision=False,alternate_corr=False)
        wrapper=DynamicDegree(args,'cpu');model=wrapper.model.float().cpu().eval().requires_grad_(False)
        padder=InputPadder((1,3,432,768));left,right=padder.pad(*[image.unsqueeze(0).float() for image in images])
        coarse,full=model(left,right,iters=20,test_mode=True)
        outputs={'coarse_flow':coarse,'full_flow':padder.unpad(full)}
        if tuple(outputs['full_flow'].shape)!=(1,2,432,768):raise ValueError('RAFT output geometry differs')
        extra.update(synthetic_frame_pairs=1,flow_iterations=20,mixed_precision=False,
                     actual_model_input_shape=list(left.shape))
    elif role=='ViCLIP':
        from vbench.overall_consistency import get_vid_features,get_text_features
        from vbench.third_party.ViCLIP.simple_tokenizer import SimpleTokenizer
        from vbench.third_party.ViCLIP.viclip import ViCLIP
        tokenizer=SimpleTokenizer(str(stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz'))
        model=ViCLIP(tokenizer=tokenizer,pretrain=str(resource)).float().cpu().eval().requires_grad_(False)
        frames=torch.randint(0,256,(8,3,432,768),generator=generator,dtype=torch.uint8)
        prepared=clip_transform(224)(frames).unsqueeze(0)
        outputs={'video_features':get_vid_features(model,prepared),
                 'text_features':get_text_features(model,'Synthetic CPU model validation only.',tokenizer)}
        if any(tuple(t.shape)!=(1,768) for t in outputs.values()):raise ValueError('ViCLIP embedding shape differs')
        extra.update(synthetic_source_frames=8,actual_model_input_shape=list(prepared.shape),
                     text_context_length=model.max_txt_l,real_tokenizer_vocab_size=len(tokenizer.encoder))
    else:
        if importlib.metadata.version('pyiqa')!='0.1.10':raise ValueError('Frozen PyIQA version changed')
        import pyiqa.archs.musiq_arch as architecture
        from wcomr.imaging_quality import prepare_frame
        if sha(inspect.getfile(architecture))!=MUSIQ_SOURCE_SHA:
            raise ValueError('Installed MUSIQ architecture differs from the frozen original protocol')
        model=architecture.MUSIQ(pretrained_model_path=str(resource)).float().cpu().eval().requires_grad_(False)
        prepared=prepare_frame(images[0].permute(1,2,0).numpy())
        outputs={'synthetic_scalar_output':model(prepared)}
        if outputs['synthetic_scalar_output'].numel()!=1:raise ValueError('MUSIQ interface is not scalar')
        extra.update(synthetic_source_frames=1,actual_model_input_shape=list(prepared.shape),
                     preprocessing='ORIGINAL_LONGER512_BILINEAR_NO_ANTIALIAS')
    if model.training or any(p.device.type!='cpu' or p.dtype!=torch.float32 for p in model.parameters()):
        raise ValueError('All actual model parameters must be FP32 CPU in eval mode')
    source=Path(inspect.getfile(type(model)))
    return dict(role=role,model_class=type(model).__module__+'.'+type(model).__qualname__,
        model_source=str(source),model_source_sha256=sha(source),parameter_count=sum(p.numel() for p in model.parameters()),
        outputs={key:tensor_receipt(value,torch) for key,value in outputs.items()},
        model_eval=True,all_parameters_CPU_FP32=True,**extra)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--role',choices=ROLES,required=True)
    args=parser.parse_args();stage=args.stage.resolve();result=stage/('CPU-model-'+args.role+'.json')
    assert not result.exists()
    sys.dont_write_bytecode=True
    started=time.time();events=[];torch=None;exit_code=1
    observation=dict(status='N10_METRIC_MODEL_CPU_RUNNING',role=args.role,
        synthetic_inputs_only=True,paper_quality_scores_generated=False,final_videos_read=False,
        GPU_submissions=0,server_ledger_written=False)
    try:
        registration,manifest,resource=preflight(stage,args.role)
        observation.update(source_revision=registration['source_revision'],
            registration_sha256=sha(stage/'registration.json'),resource_sha256=WEIGHTS[args.role][1],
            checkpoint_SHA_verified_before_import=True,
            resource_path=str(resource),complete_registered_model_roles=list(ROLES))
        if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Explicit CPU-only visibility required')
        os.environ.update(VBENCH_CACHE_DIR=str(stage/'cache'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                          PYTHONDONTWRITEBYTECODE='1')
        blocked=deny_external_access(events)
        sys.path[:0]=[str(stage/'upstream'),str(stage/'src')]
        import torch as torch_module
        torch=torch_module;torch.set_num_threads(2);torch.set_default_dtype(torch.float32)
        observation.update(interpreter=sys.executable,torch_version=str(torch.__version__))
        versions={}
        for distribution in ('torchvision','pyiqa','decord','easydict','omegaconf','einops','timm','ftfy','regex'):
            try:versions[distribution]=importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:versions[distribution]=None
        observation['dependency_versions']=versions
        def no_cuda(*args,**kwargs):
            events.append(dict(kind='CUDA_INITIALIZATION_BLOCKED'))
            raise RuntimeError('Metric model validation is CPU only')
        torch.cuda._lazy_init=no_cuda;torch.hub.download_url_to_file=blocked
        original_load=torch.load;loads=[];state_loads=[]
        original_state_load=torch.nn.Module.load_state_dict
        def checked_state_load(module,state,*positional,**kwargs):
            answer=original_state_load(module,state,*positional,**kwargs)
            state_loads.append(dict(model_class=type(module).__module__+'.'+type(module).__qualname__,
                state_keys=len(state),missing_keys=list(answer.missing_keys),unexpected_keys=list(answer.unexpected_keys)))
            return answer
        def checked_load(path,*positional,**kwargs):
            if not isinstance(path,(str,Path)) or Path(path).resolve()!=resource.resolve():
                raise ValueError('An undeclared checkpoint load was requested')
            if positional:positional=('cpu',)+positional[1:];kwargs.pop('map_location',None)
            else:kwargs['map_location']='cpu'
            loads.append(dict(path=str(path),map_location='cpu'))
            return original_load(path,*positional,**kwargs)
        torch.load=checked_load
        torch.nn.Module.load_state_dict=checked_state_load
        with torch.inference_mode():actual=probe(args.role,stage,resource,torch)
        if (not loads or not state_loads or any(r['missing_keys'] or r['unexpected_keys'] for r in state_loads)
                or torch.cuda.is_initialized() or events):
            raise ValueError('Missing real weight load or forbidden CUDA/network activity')
        imported=[]
        for name,module in list(sys.modules.items()):
            if name=='vbench' or name.startswith('vbench.'):
                filename=getattr(module,'__file__',None)
                if filename:
                    path=Path(filename).resolve()
                    if not path.is_relative_to(stage/'upstream'):
                        raise ValueError('Installed VBench code was mixed with the pinned package')
                    imported.append(dict(module=name,path=str(path),sha256=sha(path)))
        observation.update(status='N10_METRIC_MODEL_REAL_CPU_SYNTHETIC_INPUT_PASS_NOT_VIDEO_SCORE',
            actual=actual,real_checkpoint_loads=loads,actual_state_dict_loads=state_loads,
            imported_pinned_modules=imported,CUDA_initialized=False,forbidden_events=events,exit_code=0)
        exit_code=0
    except Exception as error:
        observation.update(status='N10_METRIC_MODEL_CPU_FAILURE_RETAINED',error_type=type(error).__name__,
            error=str(error),traceback=traceback.format_exc(),forbidden_events=events,exit_code=1,
            CUDA_initialized=torch.cuda.is_initialized() if torch is not None else False)
    finally:
        observation['wall_seconds']=time.time()-started
        with result.open('x') as handle:json.dump(observation,handle,indent=2,allow_nan=False)
        gc.collect()
    raise SystemExit(exit_code)


if __name__=='__main__':main()
