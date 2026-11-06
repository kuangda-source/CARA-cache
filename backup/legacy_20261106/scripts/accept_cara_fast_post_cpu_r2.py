"""Accept only the bounded dual-host postprocessing metadata controls."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--revision',type=int,default=13)
    parser.add_argument('--orchestration-acceptance',default='reports/cara_fast_orchestration_CPU_acceptance_r3_20261028.json')
    args=parser.parse_args()
    assert not args.output.exists()
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    required=['src/wcomr/cara_fast_terminal_r2.py','src/wcomr/cara_fast_capture_r2.py','src/wcomr/cara_fast_post_r2.py',
              'scripts/postprocess_cara_fast_r2.py','scripts/capture_cara_fast_terminal_r2.py',
              'scripts/check_cara_fast_post_cpu_r2.py','tests/test_cara_fast_post_r2.py',
              'scripts/score_cara_fast_fidelity_r1.py','src/wcomr/cara_fast_fidelity_r1.py',
              'src/wcomr/cara_fast_scoring_manifest_r2.py']
    expected={name:sha(ROOT/name) for name in required}
    receipts={}
    for host in ('four_card','two_card'):
        path=ROOT/'reports'/('cara_fast_post_'+host+'_CPU_capture_r'+str(args.revision)+'_20261028.json')
        capture=json.loads(path.read_text())
        state,config,proof=(capture[key] for key in ('container_state','host_config','CPU_proof'))
        assert state['Status']=='exited' and state['ExitCode']==0 and not state['Running']
        assert state['Pid']==0 and not state['OOMKilled']
        assert config==dict(NanoCpus=10**9,Memory=4*1024**3,DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        assert capture['payload_intact'] and capture['runtime_intact']
        assert proof['status']=='FAST_A32_POST_METADATA_CHAIN_CPU_COMPLETE_NOT_GPU'
        assert proof['host']==host and proof['tests_run']==11 and proof['tests_skipped']==0
        assert proof['GPU_submissions']==0 and proof['ledger_written'] is False
        assert proof['simulated_GPU_Docker_and_process_observations'] and proof['temporary_CPU_ledgers_only']
        assert proof['real_metric_execution'] is False and proof['real_model_execution'] is False
        assert all(proof['payload_sha256'][name]==value for name,value in expected.items())
        receipts[host]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),
                            launch=capture['launch'],container_state=state)
    unchanged=json.loads((ROOT/args.orchestration_acceptance).read_text())['critical_source_sha256']
    assert all(sha(ROOT/name)==value for name,value in unchanged.items())
    result=dict(status='ACCEPTED_DUAL_HOST_A32_POST_METADATA_CHAIN_CPU_ONLY',
        receipts=receipts,critical_source_sha256=expected,unchanged_GPU_core_source_count=len(unchanged),
        tests_per_host=11,resource_bound_per_container=dict(cpus=1,memory_GiB=4,work_seconds=30,exit_seconds=10),
        scope='Original handle/monitor/artifact/actual-argument identity; exact central failed/successful bill; all12 pair metadata, CPU command and immutable freeze. GPU/Docker/process observations are simulated.',
        existing_synthetic93_receipt_used_only_as_metadata_template=True,real_metrics_recomputed=False,
        actual_A32_terminal_accepted=False,actual_A32_scoring_accepted=False,GPU_authorized=False,
        GPU_submissions=0,new_GPUh=0,new_reserved_GPUh=0,cap_changed=False)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'],tests_per_host=11,unchanged_GPU_core_sources=len(unchanged))))


if __name__=='__main__':
    main()
