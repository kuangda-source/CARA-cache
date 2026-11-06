#!/usr/bin/env python3
"""Independent raw-slot checks for the actual five-model-bound input cohort."""
import argparse
import collections
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def verify(prepared,original,protocol,CPU,CPU_raw):
    from accept_wc_N10_models_cpu_r1 import accept
    actual=accept(CPU_raw);assert actual['CPU_accepted'] and actual['accepted_models']==5
    assert all(CPU.get(k)==v for k,v in actual.items())
    b=prepared['input_bundle'];identity=b['evaluator_identity'];cases={c['id']:c for c in original['bound_inputs']['cases']}
    formal=[r for r in original['final']['rows'] if r['section']=='TIMED'];rows={(r['case_id'],r['method']):r for r in formal}
    assert len(formal)==len(rows)==160 and len(cases)==16
    assert b['cases']==[dict(c,static_eligible=False) for c in original['bound_inputs']['cases']]
    assert b['methods']==original['bound_inputs']['method_ids'] and b['dimensions']==protocol['dimensions']
    assert len(b['rows'])==960 and len({(r['case_id'],r['method'],r['dimension']) for r in b['rows']})==960
    assert {(r['case_id'],r['method'],r['dimension']) for r in b['rows']}==set(itertools.product(cases,b['methods'],b['dimensions']))
    for r in b['rows']:
        source=rows[r['case_id'],r['method']];case=cases[r['case_id']]
        assert r['prompt']==case['prompt'] and r['seed']==case['seed'] and r['prompt_id']==case['prompt_id']
        assert r['prompt_sha256']==case['prompt_sha256']==hashlib.sha256(r['prompt'].encode()).hexdigest()
        assert r['generation_record_fingerprint']==fingerprint(source) and r['original_generation_status']==source['status']
        usable=source['status']=='COMPLETE' and source.get('endpoint_audit')=='PASS'
        expected='NOT_APPLICABLE_STATIC_SCOPE' if r['dimension']=='temporal_flickering' else 'READY_TO_SCORE' if usable else 'VIDEO_UNAVAILABLE'
        assert r['input_status']==expected and r['expected_sampling']==protocol['dimension_sampling'][r['dimension']]
        assert r['scorer_fingerprint']==b['scorer_fingerprint']
        if usable:assert r['video_path']==source['video_artifact']['path'] and r['video_sha256']==source['video_artifact']['sha256']
        else:assert r['video_path'] is None and r['video_sha256'] is None
    assert b['scorer_fingerprint']==fingerprint(identity) and b['fingerprint']==fingerprint({k:v for k,v in b.items() if k!='fingerprint'})
    assert identity['vbench_commit']==protocol['source_commit'] and identity['production_eligible'] is False
    assert identity['model_constructor_CPU_accepted'] is True and identity['model_CPU_source_revision']==CPU['source_revision']
    assert identity['model_CPU_registration_sha256']==CPU['registration_sha256']
    assert identity['constructor_source_sha256']==CPU_raw['registration']['payload_sha256']['src/wcomr/automatic_quality_models_r1.py']
    resources=CPU_raw['files']['model-resources.json']['data']['resources']
    assert set(identity['expected_weights'])==set(resources)
    for role,resource in resources.items():
        expected=identity['expected_weights'][role]
        assert (expected['bytes'],expected['sha256'])==(resource['bytes'],resource['sha256'])
        assert expected['model_class']==CPU_raw['files']['CPU-model-'+role+'.json']['data']['actual']['model_class']
    assert sha(ROOT/identity['real_model_CPU_proof_ref'])==identity['real_model_CPU_proof_sha256']
    assert identity['real_model_CPU_proof_sha256']==sha(Path(prepared['actual_model_CPU_acceptance_ref']))
    counts=dict(collections.Counter(r['input_status'] for r in b['rows']))
    assert counts==prepared['input_status_counts']=={'READY_TO_SCORE':645,'VIDEO_UNAVAILABLE':155,'NOT_APPLICABLE_STATIC_SCOPE':160}
    assert prepared['actual_metric_model_CPU_accepted'] and not prepared['scorer_resource_or_execution_authorization_granted']
    assert prepared['real_quality_scores_generated']==0 and not prepared['model_imported'] and not prepared['source_metric_worker_or_GPU_started']
    assert not any(prepared[k] for k in ('SSH_queries','GPU_submissions','server_ledger_written'))
    for ref in prepared['CPU_binding_files']:assert sha(ROOT/ref['ref'])==ref['sha256']
    assert len(prepared['metadata_files'])==6
    for record in prepared['metadata_files']:
        path=ROOT/record['ref'];assert sha(path)==record['sha256'];values=read(path);dim=record['dimension']
        if dim=='MUSIQ_LONGER512':assert values==[r for r in b['rows'] if r['dimension']==dim]
        else:
            ready=[r for r in b['rows'] if r['dimension']==dim and r['input_status']=='READY_TO_SCORE']
            assert sorted(p for q in values for p in q['video_list'])==sorted(r['video_path'] for r in ready)
            for q in values:
                assert q['dimension']==[dim] and {r['prompt'] for r in ready if r['video_path'] in q['video_list']}=={q['prompt_en']}
    return counts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('prepared','model-capture','model-acceptance','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();sys.path.insert(0,str(ROOT/'scripts'))
    original=read(ROOT/'reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz')
    protocol=read(ROOT/'manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json')
    counts=verify(read(a.prepared),original,protocol,read(a.model_acceptance),read(a.model_capture))
    out=dict(status='N10_ACTUAL_MODEL_CPU_FULL960_INPUTS_INDEPENDENTLY_ACCEPTED_NOT_SCORING',
        prepared_ref=str(a.prepared),prepared_sha256=sha(a.prepared),model_acceptance_ref=str(a.model_acceptance),
        model_acceptance_sha256=sha(a.model_acceptance),input_status_counts=counts,all960_original_slots_verified=True,
        metadata_files_verified=6,actual_metric_model_CPU_accepted=True,production_CPU_accepted=False,
        new_quality_scores=0,GPU_submissions=0,SSH_queries=0,ledger_written=False,verifier_source_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))


if __name__=='__main__':main()
