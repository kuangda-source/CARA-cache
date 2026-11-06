#!/usr/bin/env python3
"""Bind actual five-model CPU proof to every original160/960 quality position."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def encode(value,*,newline=True):return (json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+('\n' if newline else '')).encode()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('model-capture','model-acceptance','output-root','output'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=(ROOT/a.output_root).resolve();dest=(ROOT/a.output).resolve()
    assert out.is_relative_to(ROOT) and dest.is_relative_to(ROOT) and not out.exists() and not dest.exists()
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
    from accept_wc_N10_models_cpu_r1 import accept as accept_models
    from wcomr.automatic_quality_inputs_r1 import prepare,original_source_protocol
    from wcomr.automatic_quality_r1 import fingerprint,vbench_metadata
    from wcomr.automatic_quality_models_r1 import SELF_REF,ROLES
    raw=read(a.model_capture);saved=read(a.model_acceptance);rebuilt=accept_models(raw)
    assert rebuilt['CPU_accepted'] and rebuilt['accepted_models']==5
    assert all(saved.get(k)==v for k,v in rebuilt.items())
    assert saved['capture_sha256']==sha(a.model_capture)
    reg=raw['registration'];regbytes=encode(reg,newline=False)
    assert hashlib.sha256(regbytes).hexdigest()==saved['registration_sha256']
    assert all(raw['payload_verified'].values()) and reg['roles']==list(ROLES)
    for n in ('scripts/accept_wc_N10_models_cpu_r1.py','scripts/evaluate_wc_N10_models_cpu_bundle_r1.py',
              'scripts/evaluate_wc_N10_metric_model_cpu_r1.py',SELF_REF):
        assert sha(ROOT/n)==reg['payload_sha256'][n],n
    resource=raw['files']['model-resources.json'];resourcebytes=encode(resource['data'])
    assert hashlib.sha256(resourcebytes).hexdigest()==resource['sha256']
    declaration=read(ROOT/'manifests/wc_paper_N10_R2_accepted160_expected_scorer_declaration_20261017.json')
    assert declaration['constructor_source_sha256']==reg['payload_sha256'][SELF_REF]
    identity=copy.deepcopy(declaration)
    identity.update(identity_role='ACTUAL_FULL_FIVE_MODEL_CPU_BOUND_SCORER_NOT_EXECUTION_AUTHORITY',
        real_model_CPU_proof_ref=str((out/'model-CPU-acceptance.json').relative_to(ROOT)),
        real_model_CPU_proof_sha256=sha(a.model_acceptance),
        model_CPU_registration_sha256=saved['registration_sha256'],
        model_CPU_source_revision=saved['source_revision'],model_constructor_CPU_accepted=True,
        production_eligible=False,rebuild_final_scorer_identity_after_actual_model_CPU=False,
        whole960_production_CPU_and_cost_required=True)
    source=ROOT/'reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz'
    accepted=ROOT/'reports/wc_paper_N07_refusal_repair180_R2_terminal_canonical_independent_acceptance_20261017.json'
    protocolpath=ROOT/'manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'
    original=read(source);protocol=read(protocolpath)
    proof=original_source_protocol(ROOT,original['launch']['source_revision'],protocolpath.read_bytes())
    result=prepare(original,read(accepted),protocol,identity,capture_sha256=sha(source),
        protocol_sha256=sha(protocolpath),source_proof=proof)
    old=read(ROOT/'reports/wc_paper_N10_R2_accepted160_full960_input_preparation_20261017.json.gz')
    spec=importlib.util.spec_from_file_location('unchanged_old960_independent',ROOT/'scripts/check_wc_N10_R2_actual_inputs_independent_r1.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    oldproof=checker.verify(original,old,protocol)
    b=result['input_bundle'];oldb=old['input_bundle']
    for k in oldb:
        if k not in ('evaluator_identity','scorer_fingerprint','fingerprint','rows'):assert b[k]==oldb[k],k
    assert len(b['rows'])==len(oldb['rows'])==960
    for row,previous in zip(b['rows'],oldb['rows']):
        assert {k:v for k,v in row.items() if k!='scorer_fingerprint'}=={k:v for k,v in previous.items() if k!='scorer_fingerprint'}
        assert row['scorer_fingerprint']==b['scorer_fingerprint']
    assert b['scorer_fingerprint']==fingerprint(b['evaluator_identity'])
    assert b['fingerprint']==fingerprint({k:v for k,v in b.items() if k!='fingerprint'})
    assert result['input_status_counts']==old['input_status_counts']
    # No file is written until the entire original cohort and CPU proof pass.
    out.mkdir(parents=True)
    records=[]
    for name,data in [('model-CPU-registration.json',regbytes),('model-resources.json',resourcebytes),
                      ('model-CPU-acceptance.json',a.model_acceptance.read_bytes()),('evaluator-identity.json',encode(identity))]:
        path=out/name;path.write_bytes(data);records.append(dict(ref=str(path.relative_to(ROOT)),sha256=sha(path),bytes=len(data)))
    metadata=[]
    for dimension in b['dimensions']:
        value=[r for r in b['rows'] if r['dimension']==dimension] if dimension=='MUSIQ_LONGER512' else vbench_metadata(b,dimension)
        path=out/(dimension+'.json');path.write_bytes(encode(value))
        metadata.append(dict(dimension=dimension,ref=str(path.relative_to(ROOT)),sha256=sha(path),role='PROJECT_FULL93_RAW_FRAME_SCORER_INPUTS' if dimension=='MUSIQ_LONGER512' else 'OFFICIAL_VBENCH_PROMPT_METADATA'))
        assert read(path)==value
    result.update(metadata_files=metadata,source_capture_ref=str(source.relative_to(ROOT)),
        source_acceptance_ref=str(accepted.relative_to(ROOT)),source_acceptance_sha256=sha(accepted),
        actual_metric_model_CPU_accepted=True,actual_model_CPU_acceptance_ref=str(a.model_acceptance),
        actual_model_CPU_acceptance_sha256=sha(a.model_acceptance),model_imported=False,
        source_metric_worker_or_GPU_started=False,scorer_resource_or_execution_authorization_granted=False,
        CPU_binding_files=records,original960_independent_content_proof=oldproof,
        only_input_bundle_identity_change='ACTUAL_FIVE_MODEL_CPU_SCORER_BINDING',
        expected_declaration_and_old960_preserved=True,producer_source_sha256=sha(Path(__file__)))
    blob=encode(result);dest.write_bytes(gzip.compress(blob) if dest.suffix=='.gz' else blob)
    assert 'torch' not in sys.modules
    print(json.dumps(dict(status='N10_ACTUAL_FIVE_MODEL_CPU_SCORER_FULL960_BOUND_NOT_PRODUCTION_OR_QUALITY',
        generation_positions=160,metric_positions=960,input_status_counts=result['input_status_counts'],
        actual_metric_model_CPU_accepted=True,new_quality_scores=0,GPU_submissions=0,SSH_queries=0,output=str(dest))))


if __name__=='__main__':main()
