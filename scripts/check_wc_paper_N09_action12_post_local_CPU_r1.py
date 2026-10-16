#!/usr/bin/env python3
"""Run the new post auditor over every existing local32 registered artifact.

Original sampling tensors are real CPU files. Toy video bytes stand in for
decoded RGB, and historical endpoints are Toy controls, never GPU evidence.
"""
import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','accepted','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if args.output.exists():raise FileExistsError('Preserve the independent original CPU post result')
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(root/'src'))
    accepted=json.loads(args.accepted.read_text());value=json.loads(gzip.decompress(args.capture.read_bytes()))
    if (accepted['status']!='N09_ACTION12_FULL32_RAW1528_CPU_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION'
            or accepted['result_sha256']!=sha(args.capture) or accepted['raw_files']!=112
            or accepted['raw_tensors']!=1528 or value['actual_complete_CPU_paths']!=32
            or {r['flow'] for r in value['checks']}!={False,True}):
        raise ValueError('Original independently accepted full32 CPU sampling files required')
    sources={n:sha(root/n) for n in ('src/wcomr/action_price12_post_r1.py',
        'scripts/postprocess_wc_paper_N09_action12_r1.py','tests/test_action_price12_post_r1.py',
        'scripts/check_wc_paper_N09_action12_post_local_CPU_r1.py')}
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbidden(*a,**kw):raise RuntimeError('Local post denies CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.action_price12_post_r1 import COUNTS,COMPLETE_STATUS,audit_rows,original_raw,summarize
    from wcomr.frozen_shared_post_r1 import artifact_path
    artifacts=Path(accepted['original_stage']).resolve()/'artifacts'
    files=[];flows=[];started=time.perf_counter()
    def loader(asset):
        path=artifact_path(artifacts,asset);data=torch.load(path,weights_only=True,map_location='cpu')
        files.append(dict(path=str(path),sha256=asset['sha256'],bytes=asset['bytes']));return data
    for flow in value['checks']:
        rows=copy.deepcopy(flow['runner']['runs']);plan=flow['runner']['matrix']
        bases=[r for r in rows if r['mode']=='BASELINE'];names=[r['scene'] for r in bases]
        states=[p['point'] for r in rows if r['mode']=='AUDIT' for p in r['diagnostic_points']]
        scope=dict(requests=[dict(name=n) for n in names],states=states,
            complete_parent_matrix=plan,scope_counts=COUNTS)
        bindings={}
        for index,row in enumerate(bases):
            base=Path(row['final_artifact']['path']).resolve().parents[2]
            reference=base/'reference'/str(index)/Path(row['video_path']).name
            if not reference.is_file() or reference.read_bytes()!=Path(row['video_path']).read_bytes():
                raise ValueError('The additional original Toy reference video bytes differ')
            bindings[row['scene']]=dict(final_artifact=row['final_artifact'],
                final_latent_sha256=row['final_latent_sha256'],actions=row['actions'],
                video_artifact=dict(path=str(reference),sha256=sha(reference),bytes=reference.stat().st_size),
                decoded_video=dict(frames=93,RGB_sha256=sha(reference)))
        def toy_video(row):
            path=Path(row['video_path']).resolve();path.relative_to(artifacts);digest=sha(path)
            return dict(decoded_video=dict(frames=93,RGB_sha256=digest,Toy_RGB_stub=True),
                video_artifact=dict(path=str(path),sha256=digest,bytes=path.stat().st_size,
                    decoded_rgb_sha256=[digest]*93,Toy_RGB_stub=True))
        def toy_old_video(binding):
            path=Path(binding['video_artifact']['path']).resolve();path.relative_to(artifacts)
            if sha(path)!=binding['video_artifact']['sha256']:raise ValueError('Original Toy reference changed')
            return dict(decoded_video=binding['decoded_video'])
        result=audit_rows(rows,scope,dict(bindings=bindings),loader,toy_video,
            lambda b:original_raw(b,expected_shape=(1,2048,2,8,8)),toy_old_video,
            expected_shape=(1,2048,2,8,8))
        result.update(summarize(result,scope,observed_paths=len(rows),child_exit_code=0))
        if (result['status']!=COMPLETE_STATUS or result['verified_formal_intervals']!=384
                or result['verified_parent_tensors']+result['verified_price_point_tensors']!=764):
            raise ValueError('The complete original12 local parent/point post audit failed')
        flows.append(dict(flow=flow['flow'],result=result,video_inspector='TOY_BYTES_NOT_REAL_RGB',
            independent_real_historical_endpoint_verified=False))
    if len(files)!=112 or len({r['path'] for r in files})!=112 or torch.cuda.is_initialized():
        raise ValueError('Every original112 parent/point file must be reread once, on CPU only')
    if any(sha(root/n)!=digest for n,digest in sources.items()):raise ValueError('New post sources changed during validation')
    result=dict(status='N09_ACTION12_POST_ALL24_REGISTERED_CPU_PATHS_RAW1528_PASS_NOT_GPU_PRICES',
        original_capture_ref=str(args.capture),original_capture_sha256=sha(args.capture),
        original_acceptance_ref=str(args.accepted),original_acceptance_sha256=sha(args.accepted),
        source_sha256=sources,flows=flows,raw_files=112,raw_tensors=1528,
        formal_intervals=768,total_trial_intervals=1024,artifact_identity_receipts=files,
        CPU_wall_seconds=time.perf_counter()-started,new_sampler_paths_run=0,
        actual_RGB_decoding=False,actual_Cosmos_production_CPU=False,actual_GPU_action_prices=False,
        actual_GPU_video_or_speed_result=False,GPU_submissions=0,SSH_queries=0,ledger_written=False)
    raw=gzip.compress(json.dumps(result,allow_nan=False).encode())
    with args.output.open('xb') as handle:handle.write(raw)
    print(json.dumps({k:result[k] for k in ('status','raw_files','raw_tensors','formal_intervals','CPU_wall_seconds')}))


if __name__=='__main__':main()
