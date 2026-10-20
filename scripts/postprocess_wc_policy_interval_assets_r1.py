#!/usr/bin/env python3
"""Read all original tensors and applicable93-frame controls after GPU release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def RGB(path):
    import cv2
    cap=cv2.VideoCapture(str(path));frames=[]
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            frames.append(hashlib.sha256(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB).tobytes()).hexdigest())
    finally:cap.release()
    if len(frames)!=93:raise ValueError('All93 original decoded RGB frames required')
    return frames


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    from wcomr.policy_interval_assets_r1 import RUN,CONFIG,read,sha,full_rows
    from wcomr.policy_interval_assets_audit_r1 import audit_cells,load_artifact,make_generator_bundle
    from wcomr.gpu_budget_pool_v2 import atomic_json
    c=read(a.stage/CONFIG);out=a.project/'outputs'/RUN;runner=read(out/'runner.json')
    rows=full_rows(runner['runs']);checked=[];errors=[];raw_by_id={};pixel_by_id={};formal_cells=0
    for row in rows:
        value={k:row[k] for k in ('id','scene','section','mode','observer','round','status')}
        try:
            if row['status'] in ('COMPLETE','VIDEO_REJECTED'):
                if not row['solver_steps']==row['guided_pairs']==36:raise ValueError('Incomplete original36-step path')
                if row['request_memory_lifecycle']['owners_alive_after']:raise ValueError('Original request owner was retained')
                guide=load_artifact(row['guided_artifact'],out)['guided']
                final=load_artifact(row['final_latent_artifact'],out)['final_latent']
                if len(guide)!=36 or any(v.shape!=final.shape or v.dtype!=torch.float32 or not torch.isfinite(v).all() for v in guide+[final]):
                    raise ValueError('All original finite guided outputs and final required')
                raw_by_id[row['id']]=(guide,final)
                if row['mode']=='COLLECT':
                    value['interval_raw_audit']=audit_cells(row['interval_cells'],out,list(final.shape))
                    if row['section']=='FORMAL':formal_cells+=len(row['interval_cells'])
                if row['status']=='COMPLETE':pixel_by_id[row['id']]=RGB(row['video_path'])
                value['original_raw_accepted']=True
            elif row['status']=='TEXT_REJECTED':
                if row['solver_steps'] or row['guided_pairs'] or row.get('interval_cells'):
                    raise ValueError('Rejected request acquired a fake trajectory')
                value['original_raw_accepted']=True
            else:raise ValueError('Technical failure or unarrived position retained')
        except Exception as e:
            value.update(original_raw_accepted=False,error_type=type(e).__name__,error=str(e));errors.append(value['id'])
        checked.append(value)
    parity=[];reference_ok=True;missing=[]
    groups=[['warm_1_CONTROL','warm_2_COLLECT']]+[['formal_'+str(i)+'_'+m for m in ('NATIVE','CONTROL','COLLECT')] for i in range(4)]
    for group in groups:
        if not all(k in raw_by_id for k in group):missing.append(group);continue
        guide,final=raw_by_id[group[0]]
        exact=all(all(torch.equal(x,y) for x,y in zip(guide,raw_by_id[k][0])) and torch.equal(final,raw_by_id[k][1]) for k in group[1:])
        rgb=None
        if all(k in pixel_by_id for k in group):rgb=all(pixel_by_id[k]==pixel_by_id[group[0]] for k in group[1:])
        if not exact or rgb is False:reference_ok=False
        parity.append(dict(ids=group,all36_and_final_equal=exact,applicable_all93_RGB_equal=rgb))
    bundle=make_generator_bundle([r for r in rows if r['section']=='FORMAL'],runner['config_sha256'])
    if not reference_ok or errors or missing:bundle['generator_input_ready']=False
    atomic_json(out/'generator-input-bundle.json',bundle)
    result=dict(status='POLICY_ASSETS_ALL_ORIGINALS_CPU_AUDIT_COMPLETE',runner_sha256=sha(out/'runner.json'),
        config_sha256=sha(a.stage/CONFIG),registered_paths=14,rows=checked,
        original_artifacts_accepted=not errors,reference_parity_accepted=reference_ok,
        reference_parity=parity,missing_reference_groups=missing,formal_source_time_cells=formal_cells,
        generator_input_ready=bundle['generator_input_ready'],generator_input_bundle_sha256=sha(out/'generator-input-bundle.json'),
        missing_or_rejected_paths=[dict(id=r['id'],status=r['status']) for r in rows if r['status']!='COMPLETE'],
        error_rows=errors,CUDA_initialized=False,GPU_submissions=0,ledger_written=False,clean_speed_or_new_policy_quality_result=False)
    atomic_json(out/'post-results.json',result)
    if errors or not reference_ok:raise ValueError('Original raw/reference gate failed; all failures retained')
    print(json.dumps({k:result[k] for k in ('registered_paths','formal_source_time_cells','generator_input_ready')}))


if __name__=='__main__':main()
