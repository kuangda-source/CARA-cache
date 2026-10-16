#!/usr/bin/env python3
"""Prepare all final quality input/metadata positions from saved N07 receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'acceptance', 'protocol', 'evaluator-identity', 'metadata-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.metadata_root.exists()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.automatic_quality_inputs_r1 import PROTOCOL_ROLE, original_source_protocol, prepare
    from wcomr.automatic_quality_r1 import vbench_metadata
    value = json.loads(gzip.decompress(args.capture.read_bytes()))
    accepted = json.loads(args.acceptance.read_text()); protocol_raw = args.protocol.read_bytes(); protocol = json.loads(protocol_raw)
    proof = None
    if PROTOCOL_ROLE not in value['config']['references']:
        proof = original_source_protocol(Path(__file__).resolve().parents[1], value['launch']['source_revision'], protocol_raw)
    result = prepare(value, accepted, protocol, json.loads(args.evaluator_identity.read_text()),
                     capture_sha256=sha(args.capture), protocol_sha256=sha(args.protocol), source_proof=proof)
    args.metadata_root.mkdir(parents=True)
    metadata = []
    for dimension in result['input_bundle']['dimensions']:
        if dimension == 'MUSIQ_LONGER512':
            data = [r for r in result['input_bundle']['rows'] if r['dimension'] == dimension]
        else: data = vbench_metadata(result['input_bundle'], dimension)
        path = args.metadata_root / (dimension + '.json')
        with path.open('x') as handle: json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        metadata.append(dict(dimension=dimension, ref=str(path), sha256=sha(path),
            role='PROJECT_FULL93_RAW_FRAME_SCORER_INPUTS' if dimension == 'MUSIQ_LONGER512' else 'OFFICIAL_VBENCH_PROMPT_METADATA'))
    result.update(metadata_files=metadata, source_capture_ref=str(args.capture),
        source_acceptance_ref=str(args.acceptance), source_acceptance_sha256=sha(args.acceptance),
        model_imported=False, source_metric_worker_or_GPU_started=False)
    raw = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False).encode()
    with args.output.open('xb') as handle: handle.write(gzip.compress(raw) if args.output.suffix == '.gz' else raw)
    print(json.dumps(dict(status=result['status'], output=str(args.output),
        generation_positions=result['input_bundle']['registered_generation_positions'],
        metric_positions=result['input_bundle']['registered_metric_positions'],
        input_status_counts=result['input_status_counts'], metadata_files=len(metadata),
        quality_results_generated=0, GPU_submissions=0, SSH_queries=0), ensure_ascii=False))


if __name__ == '__main__': main()
