"""Extend S's analytical floor with already accepted real condition geometry."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def tensor_bytes(value):
    if isinstance(value, dict):
        if {'shape', 'dtype', 'bytes'} <= set(value):
            return value['bytes']
        return sum(tensor_bytes(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(tensor_bytes(v) for v in value)
    return 0


def main():
    from wcomr.sq_q1_readout_r1 import source_from_anchors
    receipt = 'reports/cara_sq_two_card_cpu_terminal_20261028.json'
    schema = json.loads((ROOT/receipt).read_text())['result']['saved_state_schema']
    previous = 'reports/cara_sq_s_resource_analytical_floor_r1_20261029.json'
    old = json.loads((ROOT/previous).read_text())
    output = ROOT/'reports/cara_sq_s_resource_analytical_floor_r2_20261029.json'
    if output.exists():
        raise FileExistsError('Preserve original analytical receipt')
    feature = schema['current'][0]['original']
    if feature != dict(shape=[1, 24, 27, 48, 2048], dtype='torch.bfloat16', bytes=127401984):
        raise ValueError('Original real feature geometry differs')
    inputs = tensor_bytes(schema['pair_inputs'])
    conditions = tensor_bytes(schema['pair_inputs']['conditions'])
    embeddings = sum(tensor_bytes({k: row[k] for k in ('embedding', 'adaln')})
                     for row in schema['current'])
    components = dict(current=tensor_bytes(schema['current']),
        pair_inputs_including_conditions=inputs, teacher=tensor_bytes(schema['teacher']),
        reference_C=tensor_bytes(schema['teacher']),
        teacher_features=tensor_bytes(schema['teacher_hidden'])+embeddings)
    raw = sum(components.values())
    anchors = 24*2*feature['bytes']
    if raw != old['raw_state_known_tensor_bytes_lower_bound']+conditions+8:
        raise ValueError('Expanded raw schema does not reconcile with retained R1 floor')
    # Match the deployed helper's alias references: direct last p/r are also
    # present in the two native windows. tree_digest intentionally visits both.
    pair = [SimpleNamespace(probe=feature, residual=feature) for _ in range(2)]
    source_bytes = tensor_bytes(source_from_anchors([pair, pair]))
    before_and_two_restores = 3
    source_hash_bytes = 108*before_and_two_restores*source_bytes
    input_hash_bytes = 108*before_and_two_restores*inputs
    logical_copy_floor = 8*(16*feature['bytes']+inputs)
    refs = [receipt, previous, 'src/wcomr/sq_s_collection_r1.py', 'src/wcomr/sq_s_storage_r1.py',
            'src/wcomr/sq_q1_readout_r1.py', 'src/wcomr/mid_coverage.py',
            'src/wcomr/partial_mlp_deployment_state.py']
    result = dict(status='S_CONDITION_INCLUSIVE_ANALYTICAL_FLOOR_AND_HASH_VISITS_NOT_MEASURED_PEAK_OR_QUOTE',
        evidence_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in refs},
        basis='Accepted old B1 actual field geometry; prospective S assumes same model/resolution/condition shapes',
        tensor_allocation_bytes=0, per_raw_tensor_components_bytes=components,
        conditions_bytes_per_raw=conditions, raw_state_known_tensor_bytes_lower_bound=raw,
        raw8_plus_anchor24_known_tensor_bytes_lower_bound=8*raw+anchors,
        raw8_plus_anchor24_known_tensor_GiB_lower_bound=(8*raw+anchors)/2**30,
        logical_copy_guard_bytes_lower_bound=logical_copy_floor,
        logical_copy_guard_GiB_lower_bound=logical_copy_floor/2**30,
        physical_GPU_or_RAM_peak_measured=False,
        hash_visits=dict(successful_target_rows=108, calls_per_input_or_source=before_and_two_restores,
            source_feature_references_per_call=source_bytes//feature['bytes'],
            source_unique_feature_tensors_per_call=8,
            source_tensor_bytes_per_call=source_bytes, source_tensor_visits_bytes=source_hash_bytes,
            paired_input_tensor_visits_bytes=input_hash_bytes,
            combined_tensor_visits_bytes=source_hash_bytes+input_hash_bytes,
            combined_tensor_visits_GiB=(source_hash_bytes+input_hash_bytes)/2**30,
            actual_device_transfer_or_hash_time_measured=False,
            interpretation='Logical byte visits without alias dedup; GPU-resident entries also incur CPU transfers'),
        exclusions=['Serialization and non-tensor metadata; videos and complete OFF/ON witnesses',
                    'Remaining native WC fields, scheduler, buffers and owner state',
                    'Snapshot clones/restores, finite scans and all other state fingerprints',
                    'Model loading, parent/teacher/head execution and lifecycle/I-O time'],
        consequence='Q1/tiny caps cannot admit S; include hash/copy work in complete host-specific quote before GPU',
        actual_new_S_labels=0, GPU_submissions=0, ledger_writes=0)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'raw8_plus_anchor24_known_tensor_GiB_lower_bound',
                                           'logical_copy_guard_GiB_lower_bound')}))
    print(json.dumps(result['hash_visits']))


if __name__ == '__main__':
    main()
