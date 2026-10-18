#!/usr/bin/env python3
"""Bind one full scout entry config only after the guard-corrected CPU result."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--kind',choices=['CAL12','BANK24'],required=True)
    p.add_argument('--quote-output',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    os.environ['WC_SCOUT_KIND']=a.kind;sys.path.insert(0,str(ROOT/'src'))
    from wcomr import scout_production_entry_r1 as entry
    configpath=ROOT/entry.CONFIG
    assert not configpath.exists() and not a.quote_output.exists() and not a.output.exists()
    values={}
    def read(name):
        raw=(ROOT/name).read_bytes();return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    values={k:read(n) for k,n in entry.REFERENCES.items()}
    spec=importlib.util.spec_from_file_location('scout_R2_numeric_acceptor',ROOT/'scripts/capture_wc_scout_numeric248_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    accepted=module.accept(values['numeric_capture'])
    assert accepted['guard_refusal_controls']==10 and all(values['numeric_acceptance'].get(k)==v for k,v in accepted.items())
    assert values['exposure_R2']['project_output_scope_accepted'] is True
    quote=entry.quote(ROOT,values['window_config'],values['blueprint'])
    qb=(json.dumps(quote,indent=2,allow_nan=False)+'\n').encode()
    refs={k:dict(ref=n,sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for k,n in entry.REFERENCES.items()}
    refs['cost']=dict(ref=str(a.quote_output.resolve().relative_to(ROOT)),sha256=hashlib.sha256(qb).hexdigest())
    c=dict(card=values['blueprint']['id'],kind=a.kind,run_id=entry.RUN,namespace='SCOUT_'+a.kind,
        requests=values['blueprint']['requests'],methods=list(entry.METHODS),scope_counts=entry.COUNTS,
        plans={k:list(v) for k,v in entry.plans().items()},strategy=entry.STRATEGY,A_method='BETA1_ONE_PHASE',
        memory_policy='BOUNDARY_GC_ONLY_R2',cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
        autonomy_exclusive_upper_GPUh=12,timing_claim=entry.TIMING,warmup_repeats=2,
        training=False,online_teachers=False,P_enabled=False,F_B_enabled=False,endpoint_tuning=False,
        new_native_generation=a.kind=='BANK24',GPU_lifecycle_accepted=False,references=refs,
        forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'])
    entry.validate_contract(c)
    with a.quote_output.open('xb') as f:f.write(qb)
    cb=(json.dumps(c,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with configpath.open('xb') as f:f.write(cb)
    result=dict(status='SCOUT_REAL_NUMERIC_R2_BOUND_ENTRY_CONFIG_NOT_PRODUCTION_CPU_OR_GPU',kind=a.kind,
        config_ref=entry.CONFIG,config_sha256=hashlib.sha256(cb).hexdigest(),quote_ref=refs['cost']['ref'],
        quote_sha256=refs['cost']['sha256'],forecast_complete_GPUh=quote['forecast_complete_GPUh'],
        billed_limit_GPUh=quote['billed_limit_GPUh'],scope_counts=entry.COUNTS,GPU_submissions=0,
        GPU_lifecycle_accepted=False,new_quality_results=None)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
