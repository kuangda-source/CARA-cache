"""GPU-hidden Q1 changed-path checks and actual condition/weight metadata.

No model construction, deep forward, new sample, video or GPU context. Full
checkpoints are mapped read-only for metadata/selected-head identity only.
"""
import argparse
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'tests')]
import torch
from wcomr.innovation_gain_observer_r1 import restore_readout_inputs
from wcomr.scout_readout_v22 import validate_state
from wcomr.sq_q1_readout_r1 import cosmos_condition_schema


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def run(args):
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('test_sq_q1_readout_r1'))
    if not result.wasSuccessful():
        raise RuntimeError(stream.getvalue())
    print('Q1_FIXTURE_AND_S_PROFILE_CHECKS_PASS',flush=True)
    project=ROOT.parent.parent
    runtime=project/'runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    probe=dict(status='Q1_AFFECTED_CPU_PATH_PASS_NOT_REAL_MODEL_REPLAY',profile=args.profile,
               fixture_checks=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                                   log=stream.getvalue(),formal_C_fixture_pairs=96,real_model=False),
               actual_condition_schema=None,actual_saved_conditions=[],actual_head_metadata=None,
               actual_model_C_replayed=False,CUDA_initialized=False,GPU_submissions=0,ledger_writes=0)
    try:
        x=torch.ones(1,1,2,2,dtype=torch.bfloat16)
        torch.nn.functional.grid_sample(x,torch.zeros(1,2,2,2,dtype=torch.bfloat16),align_corners=True)
        probe['BF16_CPU_grid_sample_supported']=True
    except RuntimeError as error:
        probe['BF16_CPU_grid_sample_supported']=False
        probe['BF16_CPU_grid_sample_error']=str(error)
    try:
        schema=cosmos_condition_schema()
        probe['actual_condition_schema']=[dict(module=cls.__module__,class_name=cls.__qualname__,
            enum_fields={k:typ.__module__+'.'+typ.__qualname__ for k,typ in enums.items()}) for cls,enums in schema]
    except (ImportError,RuntimeError,OSError) as error:
        # Preserve an actual dependency/context limitation; no stand-in schema.
        schema=None
        probe['condition_schema_import_error']=dict(type=type(error).__name__,message=str(error)[-1800:])
    if args.profile=='two_card' and schema is not None:
        if sha(args.assets/'manifest.json') != args.manifest_sha256:
            raise ValueError('Original B1 manifest drifted')
        manifest=json.loads((args.assets/'manifest.json').read_text())
        verified={}
        def load(ref):
            path=args.assets/ref['name']
            if path.resolve().parent != args.assets.resolve() or path.is_symlink() or path.stat().st_size != ref['bytes']:
                raise ValueError('Original B1 artifact path/size mismatch')
            if ref['name'] not in verified:
                if sha(path)!=ref['sha256']:raise ValueError('Original B1 SHA mismatch')
                verified[ref['name']]=ref
            return torch.load(path,map_location='cpu',weights_only=True,mmap=True)
        for row in manifest['states']:
            payload=load(row['artifact'])
            payload['anchors']=tuple(tuple(load(ref) for ref in pair) for pair in payload['anchors'])
            restored=restore_readout_inputs(payload,schema,'cpu')
            support=validate_state(restored['context'],restored['step'],restored['xi'],restored['anchors'])
            for original,condition in zip(payload['pair_inputs']['conditions'],restored['pair_inputs'][3]):
                if type(condition).__qualname__ != original['class_name'] or not condition.is_video:
                    raise ValueError('Real condition class/data type restoration mismatch')
                for key,value in original['fields'].items():
                    actual=getattr(condition,key)
                    if isinstance(value,torch.Tensor):
                        if actual is not value or actual.dtype!=value.dtype:
                            raise ValueError('CPU restoration changed a saved condition tensor')
                    elif str(actual)!=str(value):
                        raise ValueError('Restored scalar/enum differs: '+key)
            probe['actual_saved_conditions'].append(dict(prompt=row['prompt'],step=row['step'],
                true_anchor_steps=[a.step for a in restored['anchors'][0]],support=support,
                exact_types_and_tensor_bindings=True))
            del payload,restored;gc.collect()
            print(json.dumps(dict(phase='ACTUAL_CONDITION_RESTORE',completed=len(probe['actual_saved_conditions']),total=12)),flush=True)
        probe['verified_B1_files']=list(verified.values())
    # The selected-head identity is useful for Q1 source/resource binding. It
    # does not load the full model or turn CPU metadata into CUDA acceptance.
    checkpoint=project/'cache/huggingface/hub/models--nvidia--Cosmos-Predict2.5-2B/snapshots/15a82a2ec231bc318692aa0456a36537c806e7d4/base/post-trained/81edfebe-bd6a-4039-8c1d-737df1a790bf_ema_bf16.pt'
    if checkpoint.is_file():
        started=time.monotonic();weight_sha=sha(checkpoint)
        value=torch.load(checkpoint,map_location='cpu',weights_only=True,mmap=True)
        for name in ('state_dict','model'):
            if isinstance(value,dict) and name in value and isinstance(value[name],dict):value=value[name]
        if not isinstance(value,dict):raise ValueError('Unexpected registered checkpoint topology')
        head={name:t for name,t in value.items() if 'final_layer.' in name and isinstance(t,torch.Tensor)}
        if not head:raise ValueError('Registered 2B checkpoint has no final-layer tensors')
        probe['actual_head_metadata']=dict(checkpoint=str(checkpoint),checkpoint_sha256=weight_sha,
            checkpoint_bytes=checkpoint.stat().st_size,read_and_hash_wall_seconds=time.monotonic()-started,
            tensors={name:dict(shape=list(t.shape),dtype=str(t.dtype),bytes=t.numel()*t.element_size(),
                sha256=hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()) for name,t in head.items()},
            full_model_constructed=False,head_executed=False)
        del value,head;gc.collect()
    else:
        probe['weight_resource_gap']=str(checkpoint)
    if torch.cuda.is_initialized():raise RuntimeError('CPU preparation initialized CUDA')
    return probe


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--profile',choices=('two_card','four_card'),required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();assert not args.output.exists()
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise RuntimeError('CPU profile must hide GPU devices')
    def forbidden(*args,**kwargs):raise RuntimeError('GPU context or model download forbidden in CPU preparation')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2);os.nice(10)
    started=time.monotonic();cpu=time.process_time();result=run(args)
    result.update(wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
                  peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  torch_version=torch.__version__,observed_unix=time.time())
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'],flush=True)


if __name__=='__main__':main()
