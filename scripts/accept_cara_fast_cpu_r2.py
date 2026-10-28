"""Accept only the observed sampler/scorer CPU boundary, never a GPU card."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_capture(name, host):
    path = ROOT/'reports'/name
    value = json.loads(path.read_text())
    state, config, proof = (value[k] for k in ('container_state','host_config','CPU_proof'))
    assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0
    assert not state['OOMKilled'] and not state['Running']
    assert config==dict(NanoCpus=10**9,Memory=4*1024**3,DeviceRequests=None,
                        NetworkMode='none',ReadonlyRootfs=True)
    assert value['payload_intact'] and value['runtime_intact']
    assert proof['host']==value['launch']['host']==host
    assert proof['GPU_submissions']==0 and proof['ledger_written'] is False
    assert proof['CUDA_initialized'] is False
    assert proof['registration_sha256']==value['registration_sha256']
    changed = [name for name,expected in value['registration']['payload_sha256'].items()
               if file_sha(ROOT/name)!=expected]
    # These unrelated S/Q files were part of the inherited broad payload. None
    # is imported by the mainline check; they have their own concurrent owner.
    unrelated = {'src/wcomr/sq_readout_subgraph_r1.py','tests/test_sq_readout_subgraph_r1.py'}
    assert set(changed)<=unrelated, ('Affected source changed',changed)
    return value, dict(path=str(path.relative_to(ROOT)),sha256=file_sha(path),
                       launch=value['launch'],container_state=state,
                       unrelated_payload_differences=changed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    receipts = []
    for host, binding_name, scoring_name in [
        ('four_card','cara_fast_binding_four_card_CPU_capture3_r6_20261028.json',
         'cara_fast_score_cli_four_card_CPU_capture_r8_20261028.json'),
        ('two_card','cara_fast_binding_two_card_CPU_capture_r8_20261028.json',
         'cara_fast_score_cli_two_card_CPU_capture_r7_20261028.json')]:
        binding, binding_ref = read_capture(binding_name,host)
        proof = binding['CPU_proof']
        assert proof['status']=='FAST_R2_CLEAN_AUDIT_ROUTING_CPU_COMPLETE_NOT_GPU'
        assert proof['actual_compile_threads']==1 and proof['compile_pools']==[]
        checks = proof['numeric']['checks']
        assert [r['flow'] for r in checks]==[False,True]
        for row in checks:
            assert row['registered_physical_positions']==68
            assert row['actual_successful_tiny_paths']==28
            assert (row['diagnostic_paths'],row['clean_paths'],row['clean_OFF_ON_pairs'])==(12,12,4)
            assert row['writer_failure_and_no_replay_roles']==['F19_A1','WC_T008','RA_T15','NATIVE24']
            assert all(row[k] is True for k in ('full_diagnostic_gate_equal',
                'clean_native_matches_audited_native','clean_research_counters_zero',
                'production_context_required','phaseB_freeze_required'))
            assert row['Cosmos_weights_loaded'] is False
        scoring, scoring_ref = read_capture(scoring_name,host)
        proof = scoring['CPU_proof']
        raw_path = ROOT/'reports'/('cara_fast_score_cli_'+host+'_raw_receipts_r2_20261028.json')
        raw = json.loads(raw_path.read_text())['files']
        assert raw['scoring-control-result.json']['sha256']==proof['result_sha256']
        assert raw['scoring-control-manifest.json']['sha256']==proof['manifest_sha256']
        result = raw['scoring-control-result.json']['data']
        manifest = raw['scoring-control-manifest.json']['data']
        assert result['manifest_sha256']==proof['manifest_sha256']
        assert result['worker_sha256']==file_sha(ROOT/'scripts/score_cara_fast_fidelity_r1.py')
        assert result['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
        assert result['CUDA_initialized'] is False and proof['scorer_subprocess_exit_code']==0
        assert manifest['CPU_SYNTHETIC_CONTROL_ONLY'] and manifest['GPU_ever_used'] is False
        assert result['registered_pairs']==['CPU_SYNTHETIC_MATCHED_PAIR'] and len(result['rows'])==1
        row = result['rows'][0]
        assert (row['frames'],row['temporal_frame_pairs'],row['PTS_equal'])==(93,92,True)
        assert row['Alex']==0 and row['PSNR_video_dB']=='+inf' and row['PSNR_is_infinite']
        assert abs(row['SSIM']-1)<1e-6
        assert row['reference_temporal_L1']==row['reference_gradient_L1']==0
        assert len(row['Alex_frames'])==len(row['SSIM_frames'])==93
        assert row['decoded_RGB_sha256'][0]==row['decoded_RGB_sha256'][1]
        assert row['candidate']['execution_request_sha256']!=row['reference']['execution_request_sha256']
        receipts.append(dict(host=host,binding=binding_ref,scoring=scoring_ref,
                             raw_scores=dict(path=str(raw_path.relative_to(ROOT)),sha256=file_sha(raw_path))))
    result = dict(status='ACCEPTED_SCOPED_DUAL_HOST_FAST_R2_CPU_ONLY',receipts=receipts,
        sampler_scope='68 registered positions; 28 successful tiny paths and 4 declared writer failures per flow, two flow modes, each host',
        scoring_scope='One synthetic 93-frame identity pair per host through actual original-weight scoring CLI',
        resource_bound_per_container=dict(cpus=1,memory_GiB=4,work_seconds=600,exit_seconds=60),
        maximum_aggregate_vCPUh=4*660/3600,
        original_Ada_R1_R2_exit142_retained=True,original_exit_root_cause='UNPROVEN_NOT_REPRODUCED',
        production_orchestration_CPU_accepted=False,whole_68_GPU_card_accepted=False,
        model_video_quality_or_speed_result=False,GPU_authorized=False,GPU_dispatch_ready=False,
        GPU_submissions=0,new_reserved_GPUh=0)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
        handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='receipts'}))


if __name__=='__main__':
    main()
