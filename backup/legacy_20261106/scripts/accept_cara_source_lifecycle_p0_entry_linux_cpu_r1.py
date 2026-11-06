"""Offline acceptance of the original distinct point20 entry Linux CPU terminal."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from cara_source_lifecycle_p0_entry_linux_cpu_r1 import OVERLAY, STAGE
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS


def accept(launch_path, capture_path):
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    encoded = lambda value: hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()
    launch, capture = [json.loads(Path(p).read_text()) for p in (launch_path,capture_path)]
    assert capture['exit_code'] == 0
    cap = capture['result'];reg = cap['registration'];proof = cap['CPU_proof'];state = cap['container_state']
    recovered_unknown_launch = launch['exit_code'] != 0
    if recovered_unknown_launch:
        assert launch['result'] is None and launch['unknown_requires_original_capture'] is True
        assert launch['stage_name'] == Path(cap['launch']['stage']).name
        assert launch['host'] == cap['launch']['host'] == 'two_card'
    else:
        assert cap['launch'] == launch['result']
    assert cap['host_config'] == reg['expected_host_config'] == LIMITS
    assert state['Status'] == 'exited' and state['ExitCode'] == 0 and state['Pid'] == 0 and not state['OOMKilled']
    assert reg['host'] == 'two_card' and reg['parent_git_revision'] == launch['source_revision'] == capture['source_revision']
    assert cap['registration_sha256'] == encoded(reg) == proof['registration_sha256'] == cap['launch']['registration_sha256']
    assert cap['CPU_proof_sha256'] == encoded(proof) and cap['payload_intact'] and cap['runtime_intact']
    base_bytes = (ROOT/BASE_CAPTURE).read_bytes();base = json.loads(base_bytes)['result']
    base_accept = json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert base_accept['capture_sha256'] == hashlib.sha256(base_bytes).hexdigest() and base_accept['total_controls_passed'] == 113
    revision = subprocess.check_output(['git','rev-parse',launch['source_revision']],cwd=ROOT,text=True).strip()
    overlay = {p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    assert reg['payload_sha256'] == proof['payload_sha256'] == {**base['registration']['payload_sha256'],**overlay}
    assert reg['runtime_source_sha256'] == proof['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert proof['status'] == 'SOURCE_LIFECYCLE_P0_POINT20_FULL_ENTRY_LINUX_CPU_PASS_NOT_GPU'
    assert proof['tests_run'] == 77 and proof['complete_loaded_tiny_requests'] == 28
    assert proof['actual_WC_RF_module_globals'] and proof['actual_Cosmos_arguments']
    assert proof['actual_CPU_affinity'] == [26]
    assert proof['target_update'] == 20
    assert Path(cap['launch']['stage']).name == STAGE
    assert all(proof[k] is False for k in ('generative_model_weights_loaded','actual_GPU_resources_or_storage_provisioned',
        'actual_central_ledger_accessed','original_experiments_replayed','CUDA_initialized','whole_GPU_card_accepted','ledger_written'))
    assert proof['GPU_submissions'] == 0
    assert cap['launch']['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= proof['started_unix']+600
    assert len(proof['loaded']['checks']) == 2 and sum(r['complete_paths'] for r in proof['loaded']['checks']) == 28
    assert all(r['physical_model_pairs']==512 and r['target_update']==20 and r['actual_Cosmos_arguments']
        and r['precision_mode_storage_parameter_refusals'] and r['replay_refused'] for r in proof['loaded']['checks'])
    metric=proof['scorer']
    assert metric['complete_pairs']==8 and metric['frames_per_pair']==93 and metric['latent_RGB_controls']==4
    assert metric['target_update']==20 and metric['cross_point_Native_controls']==2
    assert metric['actual_metric_weights'] and metric['artifact14_read'] and metric['no_replay']
    assert metric['failure_denominator']==8 and metric['failure_completed_pairs']==1
    for result,code in ((metric['execution'],0),(metric['failure_execution'],1)):
        assert result['kind']=='ACTUAL_CPU_FIXTURE_CHILD' and result['original_process_ended'] and result['GPU_hidden']
        assert result['original_observation']['original_live'] is False
        assert result['exit_code']==0 if code==0 else result['exit_code']!=0
    return dict(status='ORIGINAL_P0_POINT20_ENTRY_LOADED_AND_REAL8_SCORER_LINUX_CPU_ACCEPTED',
        source_revision=revision, recorded_revision=reg['parent_git_revision'],
        launch_ref=str(launch_path),launch_sha256=sha(launch_path),capture_ref=str(capture_path),capture_sha256=sha(capture_path),
        launch=cap['launch'],launch_transport_was_unknown=recovered_unknown_launch,
        original_launch_recovered_without_resubmission=True,
        container_state=state,registration_sha256=cap['registration_sha256'],
        CPU_proof_sha256=cap['CPU_proof_sha256'],affected_source_sha256=overlay,
        actual_Linux_imports=True,actual_Cosmos_argument_class=True,tests_run=77,complete_loaded_tiny_requests=28,
        real_synthetic_video_frames=93,real_synthetic_metric_pairs=8,synthetic_latent_RGB_controls=4,
        failure_fixture_completed_pairs=1,original_metric_pairs_rerun=0,wall_seconds=proof['ended_unix']-proof['started_unix'],
        GPU_runner_source_and_scorer_affected_paths_accepted=True,
        actual_Cosmos_weights=False,real_model_VJP=False,actual_GPU_admission=False,
        actual_GPU_storage_provisioned=False,actual_central_ledger_accessed=False,
        whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    p = argparse.ArgumentParser()
    for name in ('launch','capture','output'):p.add_argument('--'+name,type=Path,required=True)
    args = p.parse_args();assert not args.output.exists()
    value = accept(args.launch,args.capture)
    with args.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=value['status'],wall_seconds=value['wall_seconds'])))


if __name__ == '__main__':main()
