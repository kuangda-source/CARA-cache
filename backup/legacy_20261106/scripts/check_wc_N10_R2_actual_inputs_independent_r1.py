#!/usr/bin/env python3
"""Independently bind every real R2 input slot; no model, video read or server."""
import argparse,collections,gzip,hashlib,itertools,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE='reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz'
INPUTS='reports/wc_paper_N10_R2_accepted160_full960_input_preparation_20261017.json.gz'
PROTOCOL='manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'

def load(name):
    p=ROOT/name;b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def verify(raw,prepared,protocol):
    bound=raw['bound_inputs'];bundle=prepared['input_bundle'];formal=[q for q in raw['final']['rows'] if q['section']=='TIMED']
    assert prepared['source_N07_revision']==raw['launch']['source_revision']
    assert len(raw['final']['rows'])==180 and len(formal)==160
    assert len(bundle['cases'])==16 and bundle['methods']==bound['method_ids'] and len(bundle['methods'])==10
    assert bundle['dimensions']==protocol['dimensions'] and len(bundle['dimensions'])==6
    assert bundle['fingerprint']==fingerprint({k:v for k,v in bundle.items() if k!='fingerprint'})
    assert bundle['registered_generation_positions']==160 and bundle['registered_metric_positions']==960
    assert all(not c['static_eligible'] for c in bundle['cases']) and prepared['static_eligible_prompts']==0
    actual={(r['case_id'],r['method']):r for r in formal};cases={c['id']:c for c in bound['cases']}
    expected=set(itertools.product(cases,bound['method_ids'],protocol['dimensions']))
    keys=[(r['case_id'],r['method'],r['dimension']) for r in bundle['rows']]
    assert len(keys)==len(set(keys))==960 and set(keys)==expected
    by_dim=collections.defaultdict(collections.Counter);by_method=collections.defaultdict(collections.Counter)
    for row in bundle['rows']:
        case=cases[row['case_id']];source=actual[row['case_id'],row['method']]
        assert row['prompt']==case['prompt'] and row['seed']==case['seed']
        assert row['prompt_sha256']==case['prompt_sha256']==hashlib.sha256(row['prompt'].encode()).hexdigest()
        assert row['expected_sampling']==protocol['dimension_sampling'][row['dimension']]
        assert row['generation_record_fingerprint']==fingerprint(source)
        assert row['original_generation_status']==source['status']
        usable=source['status']=='COMPLETE' and source.get('endpoint_audit')=='PASS'
        want='NOT_APPLICABLE_STATIC_SCOPE' if row['dimension']=='temporal_flickering' else 'READY_TO_SCORE' if usable else 'VIDEO_UNAVAILABLE'
        assert row['input_status']==want
        if usable:
            a=source['video_artifact'];assert a['frames']==len(a['decoded_rgb_sha256'])==93 and a['fps']==16
            assert row['video_path']==a['path'] and row['video_sha256']==a['sha256']
        else:assert row['video_path'] is None and row['video_sha256'] is None
        by_dim[row['dimension']][want]+=1;by_method[row['method']][want]+=1
    identity=bundle['evaluator_identity']
    assert identity['vbench_commit']==protocol['source_commit']
    assert bundle['scorer_fingerprint']==fingerprint(identity)
    assert all(q['scorer_fingerprint']==bundle['scorer_fingerprint'] for q in bundle['rows'])
    assert identity['production_eligible'] is False and identity['real_model_CPU_proof_ref'] is None
    assert identity['rebuild_final_scorer_identity_after_actual_model_CPU'] is True
    assert prepared['actual_metric_model_CPU_accepted'] is False and prepared['real_quality_scores_generated']==0
    assert not prepared['source_metric_worker_or_GPU_started'] and not prepared['model_imported']
    assert all(not prepared[k] for k in ('GPU_submissions','SSH_queries','server_ledger_written'))
    for record in prepared['metadata_files']:
        path=ROOT/record['ref'];assert sha(path)==record['sha256'];values=json.loads(path.read_text())
        dimension=record['dimension']
        if dimension=='MUSIQ_LONGER512':
            assert values==[r for r in bundle['rows'] if r['dimension']==dimension]
        else:
            ready=[r for r in bundle['rows'] if r['dimension']==dimension and r['input_status']=='READY_TO_SCORE']
            assert sorted(p for q in values for p in q['video_list'])==sorted(q['video_path'] for q in ready)
            for q in values:
                assert q['dimension']==[dimension]
                assert {r['prompt'] for r in ready if r['video_path'] in q['video_list']}=={q['prompt_en']}
    return dict(original_generation_statuses=dict(collections.Counter(q['status'] for q in formal)),
        per_dimension={k:dict(v) for k,v in by_dim.items()},per_method={k:dict(v) for k,v in by_method.items()},
        formal_generation_denominator=160,metric_position_denominator=960,expected_ready_scores=sum(q['input_status']=='READY_TO_SCORE' for q in bundle['rows']),
        expected_missing_video_positions=sum(q['input_status']=='VIDEO_UNAVAILABLE' for q in bundle['rows']),static_not_applicable_positions=160,
        real_quality_scores_generated=0,original_video_references_not_LPIPS_paired_filter=True,production_eligible=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    raw,prepared,protocol=[load(n) for n in (SOURCE,INPUTS,PROTOCOL)]
    assert prepared['source_N07_capture_sha256']==sha(ROOT/SOURCE) and prepared['measurement_protocol_sha256']==sha(ROOT/PROTOCOL)
    assert prepared['source_N07_revision']==raw['launch']['source_revision']
    acceptance=load(prepared['source_acceptance_ref'])
    assert prepared['source_acceptance_sha256']==sha(ROOT/prepared['source_acceptance_ref'])
    assert acceptance['capture_sha256']==sha(ROOT/SOURCE)
    assert acceptance['terminal_receipt_audit_accepted'] and acceptance['scientific_available_cohorts_with_registered_missingness']
    result=verify(raw,prepared,protocol)
    result.update(status='N10_R2_ACTUAL_ALL160_ALL960_METADATA_INDEPENDENTLY_ACCEPTED_NOT_MODEL_OR_QUALITY',
        source_capture=SOURCE,source_capture_sha256=sha(ROOT/SOURCE),prepared_ref=INPUTS,prepared_sha256=sha(ROOT/INPUTS),
        protocol_ref=PROTOCOL,protocol_sha256=sha(ROOT/PROTOCOL),GPU_submissions=0,SSH_queries=0,ledger_written=False,model_imported=False)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('per_dimension','per_method')}))
if __name__=='__main__':main()
