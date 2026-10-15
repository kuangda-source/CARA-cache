#!/usr/bin/env python3
"""Inventory every original text-only request, without selecting final inputs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.frozen_shared_inputs_r1 import SOURCE_ROOT, inspect_source, safe_name


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.time()
    record_ref = 'reports/dataset_source_group_audit_20260930.json'
    protocol_ref = 'manifests/wc_paper_N07_common_input_protocol_r1_20261016.json'
    records_file, protocol_file = ROOT / record_ref, ROOT / protocol_ref
    protocol = json.loads(protocol_file.read_text())
    assert sha(records_file) == protocol['frozen_sources'][record_ref]
    dataset = json.loads(records_file.read_text())
    records = dataset['records']
    assert len(records) == len({r['name'] for r in records}) == 1044
    base = (ROOT / SOURCE_ROOT).resolve()
    rows, negative_prompts, schemas = [], Counter(), Counter()
    for record in records:
        row = dict(name=record['name'], category=record['category'], status='NOT_READ')
        try:
            path = (base / (safe_name(record['name']) + '.json')).resolve()
            assert path.is_relative_to(base)
            raw = path.read_bytes()
            value, proof = inspect_source(record, raw)
            row.update(status='SOURCE_BYTES_AND_ORIGINAL_REQUEST_PASS', **proof)
            negative_prompts[proof['negative_prompt_sha256']] += 1
            schemas[tuple(proof['original_fields'])] += 1
        except (ValueError, OSError, AssertionError, KeyError, TypeError) as error:
            row.update(status='SOURCE_GAP_RETAINED', error_type=type(error).__name__, error=str(error))
        rows.append(row)
    assert len(rows) == 1044 and {r['name'] for r in rows} == {r['name'] for r in records}
    assert 'torch' not in sys.modules
    gaps = [r for r in rows if r['status'] != 'SOURCE_BYTES_AND_ORIGINAL_REQUEST_PASS']
    result = dict(status='WHOLE_ORIGINAL1044_INPUT_METADATA_AUDITED_NOT_FINAL_SELECTION',
        observed_unix=time.time(), source_catalog_ref=record_ref, source_catalog_sha256=sha(records_file),
        input_protocol_ref=protocol_ref, input_protocol_sha256=sha(protocol_file),
        full_registered_input_denominator=1044, inspected_rows=len(rows), passed_original_request_bytes=1044 - len(gaps),
        gaps_retained=gaps, rows=rows, category_counts=dict(Counter(r['category'] for r in rows)),
        negative_prompt_hash_counts=dict(negative_prompts),
        passing_schema_counts=[dict(fields=list(k), count=v) for k, v in schemas.items()],
        original_prompt_text_not_published_by_inventory=True,
        no_performance_quality_or_rejection_screening=True, actual_final_inputs_selected=False,
        actual_final_methods_selected=False, actual_InferenceArguments_CPU_accepted=False,
        sampler_or_model_or_guardrails_run=False, Torch_imported=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False,
        CPU_wall_seconds=time.time() - started,
        implementation_sha256={str(p.relative_to(ROOT)): sha(p) for p in (
            ROOT/'src/wcomr/frozen_shared_inputs_r1.py', Path(__file__).resolve())})
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in (
        'rows', 'implementation_sha256', 'negative_prompt_hash_counts', 'passing_schema_counts', 'gaps_retained')}))


if __name__ == '__main__':
    main()
