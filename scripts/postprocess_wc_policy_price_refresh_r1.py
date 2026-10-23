#!/usr/bin/env python3
"""Independently read full new paths against accepted Native and immutable labels."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    from wcomr.policy_price_refresh_production_r1 import RUN,ORIGINAL_RUN,read,sha,full_rows,validate
    from wcomr.policy_interval_assets_audit_r1 import load_artifact
    from wcomr.policy_price_refresh_audit_r1 import audit_price_cells,make_repriced_bundle
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from postprocess_wc_policy_interval_assets_r1 import RGB
    c,reg,*_=validate(a.project,a.stage);out=a.project/'outputs'/RUN;old=a.project/'outputs'/ORIGINAL_RUN
    runner=read(out/'runner.json');rows=full_rows(runner['runs']);original=read(old/'runner.json')['runs']
    monitor=read(out/'exclusive-monitor-final.json');errors=[];checked=[];references={}
    for row in original:
        if row['mode']=='NATIVE':
            references[row['scene']]=(load_artifact(row['guided_artifact'],old)['guided'],
                load_artifact(row['final_latent_artifact'],old)['final_latent'],RGB(row['video_path']))
    old_cells={r['scene']:r['interval_cells'] for r in original if r['mode']=='COLLECT' and r['section']=='FORMAL'}
    for row in rows:
        result={k:row[k] for k in ('id','scene','section','mode','status')}
        try:
            if row['status']!='COMPLETE':raise ValueError('Original refusal/failure retained; no replacement')
            if row['guided_pairs']!=36 or row['solver_steps']!=36 or row['actions']!=['DD']*36:
                raise ValueError('Complete all-D parent required')
            if row['request_memory_lifecycle']['owners_alive_after']:raise ValueError('Retained request owner')
            guide=load_artifact(row['guided_artifact'],out)['guided']
            final=load_artifact(row['final_latent_artifact'],out)['final_latent']
            native,latent,rgb=references[row['scene']]
            if len(guide)!=36 or any(not torch.equal(x,y) for x,y in zip(guide,native)) or not torch.equal(final,latent):
                raise ValueError('All36/final differs from original accepted Native')
            if RGB(row['video_path'])!=rgb:raise ValueError('All93 RGB differs from original Native')
            if row['mode']=='PRICE':
                result['price_audit']=audit_price_cells(row['price_cells'],old_cells[row['scene']])
                if list((out/row['id']/'price-raw').glob('*.pt')):raise ValueError('New interval tensors unexpectedly written')
            result.update(accepted=True,all36_and_final_equal=True,all93_RGB_equal=True)
        except Exception as e:
            result.update(accepted=False,error_type=type(e).__name__,error=str(e));errors.append(row['id'])
        checked.append(result)
    if not monitor['accepted'] or sha(out/'exclusive-monitor.jsonl')!=monitor['monitor_sha256']:
        errors.append('exclusive_monitor')
    result=dict(status='PRICE_COMPLETE_ORIGINALS_AUDIT',runner_sha256=sha(out/'runner.json'),
        registered_paths=10,rows=checked,error_rows=errors,raw_parity_accepted=not errors,
        scope_counts=c['scope_counts'],clean_action_prices_accepted=False,CUDA_initialized=False,GPU_submissions=0)
    try:
        if errors:raise ValueError('New original parity or complete exclusivity failed')
        profile=sha(a.stage/'registration.json')
        bundle=make_repriced_bundle(rows,original,read(old/'generator-input-bundle.json'),
            original_bundle_sha256=sha(old/'generator-input-bundle.json'),prices_sha256=sha(out/'runner.json'),
            profile_identity=profile,exclusive_accepted=monitor['accepted'],parity_accepted=True)
        atomic_json(out/'generator-input-bundle.json',bundle)
        result.update(clean_action_prices_accepted=True,generator_input_bundle_sha256=sha(out/'generator-input-bundle.json'))
    finally:atomic_json(out/'post-results.json',result)
    print(json.dumps({k:result[k] for k in ('registered_paths','clean_action_prices_accepted')}))

if __name__=='__main__':main()
