"""Accept only the original complete V1 source/DP/point CPU terminal."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from accept_cara_read_write_transition_linux_cpu_r1 import original_capture
from cara_source_lifecycle_linux_cpu_r1 import OVERLAY,STAGE


def accept(launch,capture):
    cap,revision,overlay=original_capture(launch,capture,stage=STAGE,overlay_names=OVERLAY,expected_tests=15)
    proof=cap['CPU_proof'];metrics=proof['metrics']
    assert proof['status']=='SOURCE_LIFECYCLE_V1_ACTUAL_LINUX_CPU_PASS_NOT_VIDEO_METHOD'
    assert proof['real_source_labels_fitted'] is proof['real_generated_plan_efficacy'] is False
    assert proof['point_tiny_paths']==24 and len(proof['points'])==2
    for target,point in zip((8,20),proof['points']):
        assert point['status']=='PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE'
        assert [row['flow'] for row in point['checks']]==[False,True]
        for row in point['checks']:
            assert row['target_update']==target and row['complete_paths']==6 and row['four_corner_paths']==4
            assert row['original_inputs_and_prewrite_state_exact'] and row['all_solver_memory_with_read']
            assert row['entire_cache_and_sources_with_write'] and row['caller_restored']
            assert row['corner00_C_and_corner11_D'+str(target)+'_latent_and_mock_RGB_exact']
    dp=metrics['test_cara_source_lifecycle_planner_r1']
    assert dp['brute_force']['top3_exact'] and set(dp['synthetic_full36'])=={'19','22'}
    assert dp['source_recomputation']['full_affected_intervals_recomputed']
    assert dp['UniPC_current_input_scale']['max_gradient_error']<=1e-5
    design=metrics['test_cara_source_lifecycle_design_r1']
    assert design['old_coverage']['C_only_exact_age_gap_contrasts']==0
    assert design['prospective_C_coverage']['shadow_D_labels_max']==64
    assert design['prospective_C_coverage']['exact_stage_age_previous_gap_contrasts']
    assert design['no_future_consumer']['full_remaining_endpoint_latent_bitwise_equal']
    provenance=metrics['test_cara_read_write_provenance_r1']
    assert provenance['reset_lifecycle']['output_sources_after_epilogue']==[None,35]
    error=provenance['bound_augmented_adjoint']['max_absolute_error']
    assert math.isfinite(error) and error<=2e-8
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return dict(status='ORIGINAL_SOURCE_LIFECYCLE_V1_LINUX_CPU_ACCEPTED_NOT_REAL_VIDEO',
        source_revision=revision,launch_ref=str(launch),launch_sha256=sha(launch),capture_ref=str(capture),
        capture_sha256=sha(capture),launch=cap['launch'],container_state=cap['container_state'],
        registration_sha256=cap['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],
        affected_source_sha256=overlay,tests_run=15,point_tiny_paths=24,metrics=metrics,
        wall_seconds=proof['ended_unix']-proof['started_unix'],actual_Linux_WC_RF_imports=True,
        true_model_point20_or_video=False,real_V1_planner_efficacy=False,
        GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('launch','capture','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    value=accept(args.launch,args.capture)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=value['status'],wall_seconds=value['wall_seconds'])))


if __name__=='__main__':main()
