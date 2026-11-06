#!/usr/bin/env python3
"""Read-only CPU audit of all12 original action-price parent positions."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('project','stage'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();args.project=args.project.resolve();args.stage=args.stage.resolve()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.action_price12_production_r1 import CONFIG,RUN,validate
    from wcomr.action_price12_post_r1 import (
        GPU_TERMINAL_STATUS,COMPLETE_STATUS,audit_rows,original_raw,original_video,summarize)
    from wcomr.frozen_shared_post_r1 import artifact_path,inspect_video
    from wcomr.frozen_shared_production_r1 import sha,write
    from wcomr.gpu_budget_pool_v2 import same_live_process
    config,registration,old,_,_,baseline,bound,_=validate(args.project,args.stage)
    if not all(sha(args.stage/name)==digest for name,digest in registration['payload_sha256'].items()):
        raise ValueError('Original action12 payload differs from its immutable registration')
    root=(args.project/'outputs'/RUN).resolve()
    supervisor=json.loads((root/'supervisor.json').read_text())
    if (supervisor['status']!=GPU_TERMINAL_STATUS or supervisor['run_id']!=RUN
            or supervisor['source_revision']!=registration['source_revision']
            or supervisor['config_sha256']!=sha(args.stage/CONFIG)
            or supervisor['scope_counts']!=bound['scope_counts']
            or supervisor['bound_action_fingerprint']!=bound['fingerprint']
            or same_live_process(dict(pid=supervisor['pid'],start_ticks=supervisor['start_ticks']))
            or (supervisor.get('child_identity') and same_live_process(supervisor['child_identity']))):
        raise ValueError('Collect only the original terminated action12 supervisor and worker')
    runner_path=root/'runner.json'
    runner=json.loads(runner_path.read_text()) if runner_path.exists() else dict(runs=[])
    if runner_path.exists() and (sha(runner_path)!=supervisor['runner_sha256']
            or runner['source_revision']!=registration['source_revision']
            or runner['config_sha256']!=sha(args.stage/CONFIG)
            or runner['scope_counts']!=bound['scope_counts']
            or runner['bound_action_fingerprint']!=bound['fingerprint']
            or runner['matrix']!=bound['complete_parent_matrix']):
        raise ValueError('The original complete action12 runner or parent matrix differs')
    import torch
    torch.set_num_threads(2)
    if torch.cuda.is_initialized():raise RuntimeError('Start the original-file audit without CUDA')
    def forbidden(*a,**kw):raise RuntimeError('Action12 CPU audit denies CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    destination=args.stage/'N09-action12-CPU-final-results.json'
    if destination.exists():raise FileExistsError('Preserve the original action12 CPU audit receipt')
    started=time.time();loaded=[]
    value=dict(status='N09_ACTION12_CPU_AUDIT_RUNNING',source_revision=registration['source_revision'],
        config_sha256=sha(args.stage/CONFIG),bound_action_fingerprint=bound['fingerprint'],
        scope_counts=bound['scope_counts'],GPU_supervisor=supervisor,audit_failures=[],
        original_model_load_calls=runner.get('model_load_calls'),
        original_model_loads_completed=runner.get('model_loads_completed'),
        original_load_seconds=runner.get('load_seconds'),
        resource_boundary_observations=runner.get('resource_observations',[]),
        GPU_submissions=0,ledger_written=False,CUDA_initialized=False)
    def save():
        value['CPU_wall_seconds']=time.time()-started;write(destination,value)
    def progress(partial):value.update(partial);save()
    def loader(asset):
        path=artifact_path(root,asset)
        payload=torch.load(path,weights_only=True,map_location='cpu')
        loaded.append(dict(path=str(path),bytes=asset['bytes'],sha256=asset['sha256']))
        return payload
    save()
    try:
        value.update(audit_rows(runner['runs'],bound,baseline,loader,
            lambda row:inspect_video(root,row),
            lambda binding:original_raw(binding,expected_shape=old['expected_real_shape']),
            original_video,expected_shape=old['expected_real_shape'],save=progress))
        value['referenced_tensor_file_reads']=loaded
        value['artifact_inventory']=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
            for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.pt','.mp4')]
        declared=set()
        for row in value['rows']:
            for key in ('final_artifact','guided_artifact'):
                if row.get(key):declared.add(str(Path(row[key]['path']).resolve()))
            for point in row.get('diagnostic_points',[]):
                if point.get('artifact'):declared.add(str(Path(point['artifact']['path']).resolve()))
        actual={a['path'] for a in value['artifact_inventory'] if Path(a['path']).suffix=='.pt'}
        value['unreferenced_original_tensor_files']=sorted(actual-declared)
        if actual-declared and len(runner['runs'])==12 and all(r['status']=='COMPLETE' for r in value['rows']):
            value['audit_failures'].append(dict(kind='UNEXPECTED_ORIGINAL_TENSOR_FILES',
                id=RUN,error_type='ValueError',error='Complete paths contain unreferenced original tensor files'))
        value.update(summarize(value,bound,observed_paths=len(runner['runs']),
            child_exit_code=supervisor['child_exit_code']))
        if value['all_requested_measurements_valid']:
            if len(loaded)!=56 or len({a['path'] for a in loaded})!=56:
                raise ValueError('All24 parent and32 point original tensor files must be read exactly once')
        if torch.cuda.is_initialized():raise RuntimeError('Original-file CPU audit unexpectedly initialized CUDA')
        save()
        if value['audit_failures']:
            raise RuntimeError('Original audit failures retained; no complete action12 acceptance')
    except BaseException as error:
        value.update(CPU_terminal_error_type=type(error).__name__,CPU_terminal_error=str(error))
        value['all_requested_measurements_valid']=False
        if value['status'] in ('N09_ACTION12_CPU_AUDIT_RUNNING',COMPLETE_STATUS):
            value['status_before_CPU_terminal_error']=value['status']
            value['status']='N09_ACTION12_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        save();raise


if __name__=='__main__':main()
