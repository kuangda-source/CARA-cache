"""Refine the logical copy guard from pinned native fields, without tensors."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    ref='reports/cara_sq_s_native_window_readonly_r1_20261029.json'
    old='reports/cara_sq_s_resource_analytical_floor_r2_20261029.json'
    observed=json.loads((ROOT/ref).read_text());prior=json.loads((ROOT/old).read_text())
    if (len(observed['rows'])!=27 or any(r['native_window_lengths']!=[3,3]
            or not r['captured_before_pair'] for r in observed['rows'])):
        raise ValueError('Original pinned before-pair native window inventory differs')
    # These are logical references, including aliases. The deployed tensor_bytes
    # counts each appearance; this must not be reported as physical allocation.
    feature=127401984
    fields=dict(residual_window=6,probe_residual_window=6,residual_cache=2,
                probe_residual_cache=2,previous_internal_states=2,previous_input=2)
    native=sum(fields.values())*feature
    calibrators=8*feature
    inputs=prior['per_raw_tensor_components_bytes']['pair_inputs_including_conditions']
    guard=8*(native+calibrators+inputs)
    paths=[ref,old,'src/wcomr/sq_s_collection_r1.py','src/wcomr/mid_coverage.py',
        'src/wcomr/partial_mlp_deployment_state.py',
        'cache/runtime/cosmos_predict2/_src/predict2/inference/worldcache_utils.py']
    value=dict(status='S_PINNED_NATIVE_FIELD_LOGICAL_COPY_FLOOR_NOT_PHYSICAL_PEAK_OR_FULL_QUOTE',
        evidence_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths},
        basis='Pinned production CPU before-pair window inventory plus accepted real B1 BF16 feature/condition geometry',
        assumption='Same full2B model, resolution and BF16 native feature geometry as the accepted B1 assets',
        observed_native_slots_per_branch=3,native_feature_reference_count_by_field=fields,
        native_known_feature_tensor_reference_bytes=native,
        calibrator_two_true_D_anchor_reference_bytes=calibrators,
        paired_input_tensor_reference_bytes=inputs,copy_guard_multiplier=8,
        logical_copy_guard_bytes_lower_bound=guard,logical_copy_guard_GiB_lower_bound=guard/2**30,
        prior_logical_copy_guard_GiB_lower_bound=prior['logical_copy_guard_GiB_lower_bound'],
        reference_aliases_not_deduplicated=True,physical_GPU_or_RAM_peak_measured=False,
        excluded=['previous_output, affine/log embeddings and projected cross-attention fields',
                  'Scheduler tensor state, module buffers, other owner fields and metadata',
                  'Model weights, transient activations, allocator/cache overhead and actual transfers'],
        native_source_modified=False,tensor_allocation_bytes=0,
        consequence='The complete S logical copy cap must exceed this floor plus excluded fields; it is not a GPU allocation estimate',
        S_real_labels=0,GPU_submissions=0,ledger_writes=0)
    out=ROOT/'reports/cara_sq_s_resource_native_copy_floor_r3_20261029.json'
    with out.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value[k] for k in ('status','logical_copy_guard_GiB_lower_bound')}))


if __name__=='__main__':main()
