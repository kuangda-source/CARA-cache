#!/usr/bin/env python3
"""Bind actual full960/five-role evidence before pricing or production selection."""
import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
INPUT='reports/wc_paper_N10_actual_model_CPU_full960_inputs_20261018.json.gz'
CAPTURE='reports/wc_paper_N10_full_five_model_CPU_R2_collection_20261018_0230.json.gz'
MODEL_CPU_ACCEPTANCE_REF='reports/wc_paper_N10_full_five_model_CPU_R2_independent_acceptance_20261018.json'
ORIGINAL='reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz'
PROTOCOL='manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'


def read(ref):
    path=ROOT/ref;raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def binding(ref):
    raw=(ROOT/ref).read_bytes()
    return dict(ref=ref,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))


def original_comparisons(source, methods):
    """Execute the frozen pure function without importing the old GPU stack."""
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='comparisons']
    if len(nodes)!=1:raise ValueError('One original comparison function required')
    namespace={'__builtins__':{}}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'ORIGINAL_REGISTERED_COMPARISONS_ONLY','exec'),namespace)
    return namespace['comparisons'](methods)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(ROOT) and not target.exists()
    assert target.name!='N10-production-config.json','An unpriced source preparation is never a selected config'
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
    from wcomr.automatic_quality_preparation_r1 import build_unpriced
    from wcomr.immutable_stage_payload_r1 import local_python_closure
    from check_wc_N10_actual_scorer_inputs_r1 import verify
    inputs,raw,CPU,original,protocol=[read(n) for n in (INPUT,CAPTURE,MODEL_CPU_ACCEPTANCE_REF,ORIGINAL,PROTOCOL)]
    counts=verify(inputs,original,protocol,CPU,raw)
    assert CPU['capture_sha256']==binding(CAPTURE)['sha256']
    directory='manifests/wc_paper_N10_actual_model_CPU_full960_20261018/'
    refs=dict(accepted_inputs=INPUT,model_CPU_acceptance=directory+'model-CPU-acceptance.json',
              model_CPU_registration=directory+'model-CPU-registration.json',model_resources=directory+'model-resources.json')
    references={k:binding(v) for k,v in refs.items()}
    original_post='src/wcomr/frozen_shared_post_r1.py'
    assert original['registration']['payload_sha256'][original_post]==binding(original_post)['sha256']
    primary=[list(pair) for pair in original_comparisons((ROOT/original_post).read_text(),inputs['input_bundle']['methods'])]
    assert len(primary)==18 and len({tuple(p) for p in primary})==18
    secondary=['FRONT_DENSE_A','FRONT_DENSE_C'];assert secondary not in primary
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    result=build_unpriced(inputs,read(refs['model_CPU_acceptance']),read(refs['model_CPU_registration']),
        read(refs['model_resources']),primary+[secondary],source_revision=revision,references=references)
    assert result['original_input_status_counts']==counts
    entrypoints=['scripts/prepare_wc_N10_unpriced_production_scope_r1.py',
        'scripts/score_wc_paper_N10_full960_r1.py','scripts/supervise_wc_paper_N10_full960_r1.py',
        'scripts/check_wc_N10_actual_scorer_inputs_r1.py','scripts/accept_wc_N10_models_cpu_r1.py']
    closure=local_python_closure(ROOT,entrypoints)
    conflicts=[n for n,h in closure.items() if n in raw['registration']['payload_sha256']
               and h!=raw['registration']['payload_sha256'][n]]
    assert not conflicts,conflicts
    result.update(source_revision_before_preparation_commit=revision,
        complete_original960_independent_check_reexecuted=True,
        complete_actual_five_model_CPU_acceptance_reexecuted=True,
        original_primary_comparisons=primary,additional_fixed_front_readout_comparison=secondary,
        secondary_comparison_registered_before_N10_scoring=True,
        comparison_source=binding(original_post),source_evidence={name:binding(ref) for name,ref in
            [('actual_inputs',INPUT),('actual_model_capture',CAPTURE),('actual_model_acceptance',MODEL_CPU_ACCEPTANCE_REF),
             ('original_generation_capture',ORIGINAL),('measurement_protocol',PROTOCOL)]},
        preserved_actual_model_payload_files=len(raw['registration']['payload_sha256']),
        original_model_registration_sha256=CPU['registration_sha256'],
        original_model_payload_overwrites=conflicts,prepared_Python_source_sha256=closure,
        payload_installation_or_CPU_launch_performed=False,neural_framework_imported='torch' in sys.modules)
    assert not result['neural_framework_imported']
    with target.open('x') as h:json.dump(result,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(dict(status=result['status'],output=str(a.output),
        input_status_counts=counts,source_files=len(closure),original_model_payload_files=len(raw['registration']['payload_sha256']),
        comparisons=len(primary)+1,complete_quote_GPUh=None,production_CPU_accepted=False,new_quality_scores=0,GPU_submissions=0)))


if __name__=='__main__':main()
