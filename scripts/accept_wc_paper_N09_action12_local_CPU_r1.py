#!/usr/bin/env python3
"""Reload all original registered parent and point tensors from the full32 CPU run."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stage','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];stage=args.stage.resolve()
    if args.output.exists():raise FileExistsError('Preserve independent CPU acceptance')
    sys.path.insert(0,str(root/'src'))
    value=json.loads(gzip.decompress((stage/'CPU-result.json.gz').read_bytes()))
    registration=json.loads((stage/'registration.json').read_text());exit=json.loads((stage/'CPU-exit.json').read_text())
    if (exit['exit_code']!=0 or exit['result_sha256']!=sha(stage/'CPU-result.json.gz')
            or value['source_sha256']!=registration['source_sha256'] or exit['source_sha256']!=registration['source_sha256']
            or any(sha(root/n)!=h for n,h in registration['source_sha256'].items())
            or value['runtime_source_sha256']!=registration['runtime_source_sha256']
            or value['status']!='N09_ACTION12_ADAPTER_FULL32_CPU_PASS_NOT_PRODUCTION'
            or value['actual_complete_CPU_paths']!=32 or value['registered_adapter_CPU_paths']!=24
            or value['additional_Toy_selection_reference_paths']!=8 or value['actual_pairs']!=2176
            or value['CUDA_initialized'] or value['actual_Cosmos_production_CPU']
            or value['final_source_verification']['passed'] is not True
            or {r['flow'] for r in value['checks']}!={False,True}):
        raise ValueError('Original source-bound full32 CPU run, original exit and complete denominator required')
    runtime=Path(registration['runtime_root'])
    if ({str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*.py')}
            !=registration['runtime_source_sha256']):
        raise ValueError('Complete original runtime identity changed')
    import torch
    from wcomr.action_price16_audit_r1 import audit_scene
    from wcomr.mid_coverage import tree_digest
    from wcomr.frozen_shared_post_r1 import stable_history
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    files=[];tensor_count=0
    def load(asset):
        nonlocal tensor_count
        path=Path(asset['path']).resolve();path.relative_to(stage/'artifacts')
        if sha(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes']:
            raise ValueError('Original actual file SHA/bytes differ')
        payload=torch.load(path,map_location='cpu',weights_only=True)
        if 'tensor_sha256' in asset and tree_digest(payload)!=asset['tensor_sha256']:
            raise ValueError('Original point tensor tree differs')
        def finite(v):
            nonlocal tensor_count
            if isinstance(v,torch.Tensor):
                tensor_count+=1
                if not bool(torch.isfinite(v).all()):raise ValueError('Nonfinite original tensor')
            elif isinstance(v,dict):
                for item in v.values():finite(item)
            elif isinstance(v,list):
                for item in v:finite(item)
            else:raise ValueError('Only original tensor structures expected')
        finite(payload);files.append(dict(path=str(path),bytes=asset['bytes'],sha256=asset['sha256']))
        return payload
    flow_results=[]
    for flow in value['checks']:
        runner=flow['runner'];rows=runner['runs'];matrix=runner['matrix']
        if (flow['actual_complete_CPU_paths']!=16 or flow['registered_adapter_paths']!=12
                or runner['status']!='N09_ACTION12_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT'
                or len(rows)!=12 or [r['id'] for r in rows]!=[r['id'] for r in matrix]
                or sum(r['actual_pair_computations'] for r in rows)!=944):
            raise ValueError('All12 original actual adapter requests required per flow')
        indexed={}
        for row in rows:
            if (row['status']!='COMPLETE' or not row['full36_reference_parity']
                    or not row['Toy_video_reference_parity'] or row['guided_outputs']!=36
                    or row['request_memory_lifecycle']['components_alive_after']!=0):
                raise ValueError('All full36 path parity and owner release controls required')
            final=load(row['final_artifact']);guided=load(row['guided_artifact'])
            if (set(final)!={'final_latent'} or set(guided)!={'guided'} or len(guided['guided'])!=36
                    or tree_digest(final['final_latent'])!=row['final_latent_sha256']
                    or tree_digest(guided['guided'])!=row['guided_tree_sha256']):
                raise ValueError('Actual original final and all36 guided tensor identities required')
            for tensor in [final['final_latent'],*guided['guided']]:
                if tensor.dtype!=torch.float32 or tuple(tensor.shape)!=(1,2048,2,8,8):
                    raise ValueError('Original declared Tiny geometry and FP32 dtype required')
            indexed[(row['scene'],row['mode'])]=row
        scenes=[]
        for scene in sorted({r['scene'] for r in rows}):
            base,audit,lean=(indexed[(scene,m)] for m in ('BASELINE','AUDIT','LEAN'))
            for other in (audit,lean):
                for name in ('final_latent_sha256','guided_tree_sha256','actions','A_history'):
                    if other[name]!=base[name]:raise ValueError('All36 original mode controls differ: '+name)
                if stable_history(other['source_history'])!=stable_history(base['source_history']):
                    raise ValueError('Normal source histories changed across diagnostic modes')
            scenes.append(audit_scene(dict(AUDIT=audit['diagnostic_points'],LEAN=lean['diagnostic_points']),
                load,expected_shape=(1,2048,2,8,8)))
        flow_results.append(dict(flow=flow['flow'],registered_parent_controls=12,scenes=scenes,
            all36_guided_actions_A_and_source_histories_equal=True,all_request_owners_released=True))
    if len(files)!=112 or len({r['path'] for r in files})!=112 or tensor_count!=1528:
        raise ValueError('All48 original parent files plus64 point files/1528 tensors required')
    if torch.cuda.is_initialized():raise ValueError('Independent acceptance is CPU only')
    result=dict(status='N09_ACTION12_FULL32_RAW1528_CPU_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION',
        original_stage=str(stage),result_sha256=sha(stage/'CPU-result.json.gz'),registration_sha256=sha(stage/'registration.json'),
        exit_sha256=sha(stage/'CPU-exit.json'),actual_complete_CPU_paths=32,registered_adapter_CPU_paths=24,
        additional_Toy_selection_reference_paths=8,actual_pairs=2176,raw_files=112,raw_tensors=1528,
        flows=flow_results,artifact_identity_receipts=files,actual_Cosmos_production_CPU=False,
        actual_GPU_prices_or_quality_results=False,GPU_submissions=0,SSH_queries=0,ledger_written=False)
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps({k:result[k] for k in ('status','actual_complete_CPU_paths','raw_files','raw_tensors')}))


if __name__=='__main__':main()
