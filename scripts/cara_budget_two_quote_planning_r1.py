"""Two-card planning quote with measured IO and explicit unmeasured allowances."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from wcomr import cara_budget_calibration_r1 as calibration
import test_cara_budget_calibration_r1 as fixtures


def main():
    output = Path(sys.argv[1])
    if output.exists():
        raise ValueError('Fresh planning receipt required')
    io_ref = 'reports/cara_budget_two_RGB_cost_CPU_accepted_r1_20261031.json'
    design_ref = 'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_14GPUH_DESIGN_R1.json'
    io = json.loads((ROOT/io_ref).read_text())
    design = json.loads((ROOT/design_ref).read_text())
    assert io['status'] == 'TWO_CARD_FULL93_RGB_CPU_IO_COMPONENT_ACCEPTED'
    assert io['geometry'] == [3,93,432,768] and design['candidate_queries'] == 51 and design['new_GPU_paths'] == 112
    # Count the real producer's calls on small synthetic RGB. This does not
    # measure disk performance or execute either original remote CPU container.
    fixture = fixtures.CalibrationTests()
    fixture.setUp()
    counts = Counter()
    def counted(name, function):
        def call(*args, **kwargs):
            counts[name] += 1
            return function(*args, **kwargs)
        return call
    try:
        with patch.object(calibration, 'save_endpoint', counted('save', calibration.save_endpoint)), \
             patch.object(calibration, 'read_endpoint', counted('read', calibration.read_endpoint)), \
             patch.object(calibration, 'full_rgb_mse', counted('MSE', calibration.full_rgb_mse)):
            produced = fixture.entry(True, calibration.PRODUCTION_CONFIG).run(allow_new=True)
            production_counts = dict(counts)
            counts.clear()
            recovered = fixture.entry(False, calibration.PRODUCTION_CONFIG).run(allow_new=False)
            recovery_counts = dict(counts)
        assert produced['complete'] and produced['new_physical_calls'] == 112
        assert recovered['complete'] and recovered['new_physical_calls'] == 0
        assert production_counts == dict(save=112, read=102, MSE=204)
        assert recovery_counts == dict(read=112, MSE=102)
    finally:
        fixture.doCleanups()
    measured = io['measurement']
    per_save = max(measured['native_save_fsync_and_hash_seconds'], measured['candidate_save_fsync_and_hash_seconds'])
    per_read = measured['read_hash_validate_two_arrays_seconds']/2
    per_mse = measured['full_MSE_validate_and_compute_seconds']
    components = dict(
        generation=design['planning_allowances']['all_paths_at_slowest_original_Native_request_seconds'],
        path_artifacts_and_objectives=6720,
        producer_final_full_readback=1800,
        admission_and_model_load=1800,
        stop_and_release=600)
    total = sum(components.values())
    assert total < 14*3600
    source_names = ['src/wcomr/cara_budget_calibration_r1.py',
                    'src/wcomr/cara_budget_rgb_objective_r1.py',
                    'tests/test_cara_budget_calibration_r1.py']
    report = dict(status='TWO_CARD_COMPLETE_COST_FORECAST_DRAFT_NOT_DISPATCH_ACCEPTED',
        observed_unix=time.time(), host='two_card', physical_paths=112, candidate_queries=51,
        components_seconds=components, forecast_GPUh=total/3600, hard_GPUh=14,
        hard_limit_margin_seconds=14*3600-total,
        synthetic_producer_operation_counts=production_counts,
        synthetic_postrelease_recovery_operation_counts=recovery_counts,
        measured_IO_extrapolation_seconds=dict(
            path_save_and_initial_objectives=112*per_save+102*per_mse,
            producer_candidate_RGB_readback_and_objectives=102*(per_read+per_mse),
            postrelease_CPU_recovery_not_GPU_billed=112*per_read+102*per_mse),
        assumptions=[
            'Generation uses the slowest historical A6000 Native full request for every path; this is a conservative proxy, not a proven bound.',
            '6720s covers path artifacts, initial objectives and unmeasured GPU-to-CPU transfer; two-card full-size IO is one cache-uncontrolled observation.',
            '1800s final producer readback includes102 candidate RGB checks/objectives plus generation-payload hashing and metadata/storage scans; cold-volume timing remains unmeasured.',
            'Admission/model loading1800s and stop/release600s are planning allowances, not current-host measurements.',
            'Postrelease acceptance and once-freeze are CPU work after the original GPU is released; do not add them to the allocation clock twice.'],
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_names},
        evidence_refs=[io_ref, design_ref, 'reports/cara_budget_calibration_cost_basis_r1_20261030.json'],
        unresolved=['Complete original R4 CPU acceptance', 'Actual dispatcher-child integration',
                    'Actual64GiB private storage and cold-readback admission',
                    'Two-card-only execution binding', 'Single authoritative central ledger availability',
                    'Separate actual GPU-card approval and fresh admission'],
        matched_actual_spend_with_S=False, whole_GPU_quote_accepted=False,
        GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k:report[k] for k in ('status','forecast_GPUh','hard_limit_margin_seconds')}))


if __name__ == '__main__':
    main()
