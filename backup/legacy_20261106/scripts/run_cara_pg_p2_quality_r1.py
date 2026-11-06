#!/usr/bin/env python3
"""Explicit P2 quality entry: validate originals, preserve full journal, no dispatch.

CPU probes use a separately declared synthetic plan. Real CUDA use must run
inside the final approved card; this CLI deliberately allows CPU only until
the final stage admission/whole quote is bound after P1.
"""
import argparse,gzip,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_wc_N10_models_cpu_r1 import accept as accept_models
from wcomr.policy_generator_r1.p2_quality_entry import evaluator_identity,build_plan,original_factory,execute,audit
from wcomr.policy_generator_r1.continuation_preparation import require
from wcomr.policy_generator_r1.production_evidence import sha


def verified_models(capture_path,acceptance_path,registration_path,resources_path):
    raw=capture_path.read_bytes();saved=json.loads(acceptance_path.read_text())
    require(saved['capture_sha256']==hashlib.sha256(raw).hexdigest(),'Model acceptance/capture SHA mismatch')
    capture=json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    actual=accept_models(capture)
    require(actual['CPU_accepted'] is True and all(saved.get(k)==v for k,v in actual.items()),'Independent model acceptance mismatch')
    registration=json.loads(registration_path.read_text());resources=json.loads(resources_path.read_text())['resources']
    require(registration==capture['registration'] and sha(registration_path)==actual['registration_sha256'],'Original registered model source required')
    require(resources==capture['files']['model-resources.json']['data']['resources'],'Original CPU checkpoint paths changed')
    return registration,actual,resources


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('model-capture','model-acceptance','model-registration','model-resources','manifest','generation-state','members','output-root','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--declared-synthetic-CPU-probe',action='store_true');a=p.parse_args()
    require(a.declared_synthetic_CPU_probe,'Production scoring requires final P1-bound whole-card admission; CPU probe must be explicit')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','GPU-hidden process required')
    require(not a.output.exists(),'Do not replace original scoring output');a.output.mkdir()
    reg,accepted,resources=verified_models(a.model_capture,a.model_acceptance,a.model_registration,a.model_resources)
    manifest=json.loads(a.manifest.read_text());require(manifest.get('CPU_FIXTURE_ONLY') is True,'Only declared synthetic CPU data at this entry')
    identity=evaluator_identity(reg,accepted,resources,sha(a.model_registration))
    plan=build_plan(manifest,json.loads(a.generation_state.read_text()),json.loads(a.members.read_text()),identity,a.output_root)
    (a.output/'quality-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    import torch
    torch.set_num_threads(1)
    factory=original_factory(stage=reg['stage'],resources=resources,acceptance=accepted,registration=reg,identity=identity,torch=torch,device='cpu')
    state=execute(plan,factory,a.output/'quality-journal.jsonl');checked=audit(plan,state)
    require(not torch.cuda.is_initialized(),'CPU entry created a CUDA context')
    (a.output/'quality-CPU-result.json').write_text(json.dumps(dict(status='P2_REAL_QUALITY_MODELS_SYNTHETIC_CPU_ENTRY_PASS',audit=checked,
        state=state,model_weights_really_loaded=True,scientific_quality_result=False,GPU_submissions=0,final_budget_determined=False),indent=2)+'\n')
if __name__=='__main__':main()
