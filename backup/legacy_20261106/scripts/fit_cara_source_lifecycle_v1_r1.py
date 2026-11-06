"""Offline fixed V1 scalar fit and candidate generation; no model or GPU access."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from wcomr.cara_fast_spec_r1 import digest, profile_from
from wcomr.cara_source_lifecycle_design_r1 import calibration_design
from wcomr.cara_source_lifecycle_estimation_r1 import complete_samples, fit_validate_plan

BASE = ROOT/'plans/cara_next_stage_20261101/source_lifecycle'


def frozen_weights(record, schedule, contract, fixture):
    original = 'CARA_SOURCE_LIFECYCLE_FROZEN_UNIPC_SCALE_R1'
    synthetic = 'CARA_SOURCE_LIFECYCLE_SYNTHETIC_SCALE_CPU_R1'
    allowed = (original, synthetic) if fixture else (original,)
    if (record.get('schema') not in allowed or record.get('actual_updates') != 36
            or record.get('sigmas') != schedule['sigmas']
            or record.get('timesteps') != schedule['timesteps']):
        raise ValueError('Complete36 matching original-grid scale export required')
    coefficients, weights = record['coefficients'], record['weights']
    if (len(coefficients) != 36 or len(weights) != 36
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in coefficients+weights)
            or weights != [v*v for v in coefficients] or not any(v > 0 for v in weights)):
        raise ValueError('Complete squared finite current-velocity coefficients required')
    if record['schema'] == original and (record.get('original_UniPC_source_sha256') != contract['original_UniPC_source_sha256']
                        or record.get('current_corrector_and_predictor_included') is not True
                        or record.get('terminal_sensitivity') is not False):
        raise ValueError('Pinned original UniPC numerical scale, without terminal-sensitivity substitution')
    return weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', type=Path, required=True)
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--fixture-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve original offline report; choose a fresh output')
    read = lambda p: json.loads(Path(p).read_text())
    protocol_file = BASE/'V1_PROTOCOL_R1.json'
    contract_file = BASE/'V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json'
    design_file = BASE/'V1_CALIBRATION64_DESIGN_R1.json'
    manifest_file = ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'
    manifest, design, contract = read(manifest_file), read(design_file), read(contract_file)
    if (design != calibration_design(manifest['schedule'], profile_from(manifest['profile']), manifest['FIT'])
            or contract['protocol_sha256'] != hashlib.sha256(protocol_file.read_bytes()).hexdigest()
            or contract['design_scope_sha256'] != design['scope_sha256']):
        raise ValueError('Exact original design and component/protocol binding required')
    packet = read(args.labels)
    if (packet['input_kind'] == 'SYNTHETIC_CPU') != args.fixture_only:
        raise ValueError('Explicit fixture-only flag must match synthetic input kind')
    weights = frozen_weights(read(args.weights), manifest['schedule'], contract, args.fixture_only)
    samples = complete_samples(packet, design, manifest['schedule'])
    result = fit_validate_plan(samples, design, manifest, weights)
    inputs = dict(labels=args.labels, weights=args.weights, protocol=protocol_file,
                  component_contract=contract_file, design=design_file, manifest=manifest_file)
    result.update(CPU_fixture_only=args.fixture_only, input_kind=packet['input_kind'],
                  input_sha256={k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in inputs.items()},
                  input_refs={k: str(p) for k, p in inputs.items()},
                  source_collection_requires_separate_original_acceptance=True,
                  endpoint_selection_performed=False, labels_structure_only_validated=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], CPU_fixture_only=args.fixture_only,
                          samples=len(samples), families=3, budgets=[19, 22], top_k=3,
                          result_sha256=digest(result), GPU_submissions=0)))


if __name__ == '__main__':
    main()
