"""Bind the two observed Linux controls to current A32 orchestration sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--revision',type=int,default=11)
    args=parser.parse_args()
    assert not args.output.exists()
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    captures={host:json.loads((ROOT/'reports'/('cara_fast_orchestration_'+host+'_CPU_capture_r'+str(args.revision)+'_20261028.json')).read_text())
              for host in ('four_card','two_card')}
    first=captures['four_card']['CPU_proof']['payload_sha256']
    shared=['gpu_budget_pool_v2','wc73_execution_r1','wc73_exclusive_r1',
            'policy_price_mode_guard_r1','policy_asset_price_review_r1','history104_storage_r2',
            'wc_time_collection_r1','wc_time_diagnostics_r1','runtime_config','full_sampling',
            'h0_mode','paper_latency_r1','clean_speed20_r1']
    critical={name:expected for name,expected in first.items()
              if name.startswith(('src/wcomr/cara_fast_','scripts/','tests/test_cara_fast_'))
              or name.startswith('plans/cara_next_stage_20261028/mainline/')
              or name in ['src/wcomr/'+n+'.py' for n in shared]}
    assert all(sha(ROOT/name)==expected for name,expected in critical.items())
    receipts={}
    for host,capture in captures.items():
        state,proof,config=(capture[k] for k in ('container_state','CPU_proof','host_config'))
        assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0
        assert not state['Running'] and not state['OOMKilled']
        assert capture['payload_intact'] and capture['runtime_intact']
        assert config==dict(NanoCpus=10**9,Memory=4*1024**3,DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        assert proof['status']=='FAST_A32_ORCHESTRATION_CPU_CONTROL_COMPLETE_NOT_GPU'
        assert proof['host']==host and proof['tests_run']==6 and proof['tests_skipped']==0
        assert proof['external_GPU_observations_simulated'] and proof['real_OS_FD_child_and_process_groups']
        assert proof['new_GPU_submissions']==0 and proof['central_ledger_written'] is False
        assert proof['real_mode_changes']==0 and proof['actual_model_constructor_executed'] is False
        assert proof['registration_sha256']==capture['registration_sha256']
        assert all(proof['payload_sha256'].get(name)==expected for name,expected in critical.items())
        name='reports/cara_fast_orchestration_'+host+'_CPU_capture_r'+str(args.revision)+'_20261028.json'
        receipts[host]=dict(path=name,sha256=sha(ROOT/name),
            launch=capture['launch'],container_state=state,runtime_source_sha256=proof['runtime_source_sha256'])
    assert receipts['four_card']['runtime_source_sha256']==receipts['two_card']['runtime_source_sha256']
    value=dict(passed=True,status='ACCEPTED_A32_DUAL_HOST_ORCHESTRATION_CPU_CONTROLS_ONLY',
        critical_source_sha256=critical,receipts=receipts,
        sampler_scorer_acceptance_ref='reports/cara_fast_scoped_CPU_acceptance_r2_20261028.json',
        supplementary_authority_tests=dict(path='tests/test_cara_fast_authority_r2.py',
            sha256=sha(ROOT/'tests/test_cara_fast_authority_r2.py'),execution='Local Python3.9, two tests passed; no GPU'),
        scope='Real Linux supervisor/child PID, inherited flock FD, normal exit/child failure/90C stop, durable bill and no replay; exact original Docker arguments built only. GPU observations are simulated.',
        actual_GPU_model_constructor_accepted=False,actual_hardware_mode_accepted=False,
        original_Ada_R1_R2_exit_root_cause='UNPROVEN_NOT_REPRODUCED',
        GPU_authorized=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as handle:
        json.dump(value,handle,indent=2)
        handle.write('\n')
    print(json.dumps(dict(status=value['status'],passed=True,critical_files=len(critical),GPU_submissions=0)))


if __name__=='__main__':
    main()
