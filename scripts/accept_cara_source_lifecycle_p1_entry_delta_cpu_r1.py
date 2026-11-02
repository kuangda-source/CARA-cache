"""Accept original ended Linux entry-delta CPU bytes and source-bound local plots."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]

from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED
from cara_source_lifecycle_p1_entry_delta_cpu_r1 import STAGE,OVERLAY
from check_cara_source_lifecycle_p1_entry_delta_cpu_r1 import TESTS


def accept(launch_path,capture_path):
    read=lambda p:json.loads(Path(p).read_bytes())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    launch,capture=read(launch_path),read(capture_path)
    assert launch['exit_code']==capture['exit_code']==0
    launched,cap=launch['result'],capture['result']
    assert cap['launch']==launched and Path(launched['stage']).name==STAGE
    assert launched['status']=='ORIGINAL_P1_ENTRY_DELTA_CPU_PROBE_LAUNCHED_NOT_GPU'
    assert cap['status']=='ORIGINAL_P1_ENTRY_DELTA_CPU_CAPTURE_ONLY'
    assert cap['original_host_observation']['original_live'] is False
    assert cap['payload_intact'] and cap['runtime_intact']
    reg,terminal=cap['registration'],cap['host_terminal'];revision=launch['source_revision']
    assert revision==capture['source_revision']==reg['parent_git_revision']==launched['source_revision']
    reg_sha=hashlib.sha256((json.dumps(reg,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    assert reg_sha==cap['registration_sha256']==launched['registration_sha256']
    base,accepted=read(ROOT/BASE_CAPTURE)['result'],read(ROOT/BASE_ACCEPTED)
    assert accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed']==113
    expected={**base['registration']['payload_sha256'],**{
        n:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in OVERLAY}}
    assert reg['payload_sha256']==expected and reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']
    assert reg['source_identity']=='EXACT_PAYLOAD_P1_ENTRY_DELTA_CPU_ONLY' and reg['CPU_fixture_only'] is True
    bounds=dict(affinity=[26,27],RLIMIT_AS=[4*2**30]*2,RLIMIT_CPU=[1200]*2,
        work_seconds=1200,Docker_container=False,GPU_visible=False)
    assert launched['parent_bounds']==bounds and launched['parent_Docker_container'] is False
    assert launched['CPU_fixture_only'] is True and launched['work_seconds']==1200 and launched['exit_seconds']==60
    assert terminal['identity']==launched['identity'] and terminal['error'] is None
    assert launched['started_unix']<terminal['ended_unix']<=launched['started_unix']+1200
    raw=base64.b64decode(cap['CPU_proof_base64'],validate=True)
    assert hashlib.sha256(raw).hexdigest()==cap['CPU_proof_sha256']
    proof=json.loads(raw);assert proof==cap['CPU_proof']
    assert proof['status']=='ACTUAL_P1_ENTRY_REPORT_RPC_LINUX_CPU_DELTA23_PASS'
    assert proof['source_revision']==revision and proof['registration_sha256']==reg_sha
    assert proof['payload_sha256']==expected and proof['runtime_source_sha256']==reg['runtime_source_sha256']
    assert proof['parent_bounds']==bounds and proof['parent_identity']==launched['identity']
    assert launched['started_unix']<=proof['started_unix']<proof['ended_unix']<=terminal['ended_unix']
    assert proof['tests_run']==23 and proof['test_modules']==list(TESTS)
    assert [proof[k] for k in ('report52_analysis_once_freeze_controls','source_bound_local_figures_and_CSV_controls_reused',
        'simulated_central_settlement_controls','simulated_RPC_controls','simulated_container_supervisor_entry_controls')]==[5,3,5,5,8]
    assert proof['original_liveness_refresh_keeps_analysis_and_freeze_bytes']
    assert proof['actual_PNG_PDF_CSV_rendered_in_this_Linux_job'] is False
    assert proof['original_metric_pairs_recomputed']==0
    assert all(proof[k] is False for k in ('old_component_experiments_replayed','actual_Cosmos_weights','real_V1_video',
        'actual_GPU_Docker_started','real_four_card_accessed','real_central_ledger_read',
        'whole_GPU_entry_accepted','P1_GPU_authorized','ledger_written'))
    assert proof['GPU_submissions']==launched['GPU_submissions']==cap['GPU_submissions']==0
    local=read(ROOT/proof['local_figures_CPU_ref'])
    assert sha(ROOT/proof['local_figures_CPU_ref'])==proof['local_figures_CPU_sha256']
    assert local['tests_run']==26 and local['status']=='EXACT_REGISTERED_P1_ENTRY_DELTA_PAYLOAD_ISOLATED_LOCAL26_PASS'
    assert all(local['payload_sha256'][n]==expected[n]==h for n,h in proof['local_figure_source_sha256'].items())
    result=dict(status='ORIGINAL_P1_REPORT_RPC_CONTAINER_ENTRY_LINUX_CPU_DELTA23_ACCEPTED_SYNTHETIC_ONLY',
        source_revision=revision,CPU_stage=STAGE,registration_sha256=reg_sha,
        launch_ref=str(launch_path),launch_sha256=sha(launch_path),capture_ref=str(capture_path),capture_sha256=sha(capture_path),
        original_proof_sha256=cap['CPU_proof_sha256'],original_host_identity=launched['identity'],original_host_ended=True,
        parent_bounds=bounds,started_unix=launched['started_unix'],ended_unix=terminal['ended_unix'],tests_run=23,
        local_figure_controls_reused=3,local_figures_CPU_ref=proof['local_figures_CPU_ref'],
        local_figures_CPU_sha256=proof['local_figures_CPU_sha256'],
        actual_PNG_PDF_CSV_rendered_in_this_Linux_job=False,
        original_metric_pairs_recomputed=0,old_component_experiments_replayed=False,
        container_and_supervisor_entry_simulated=True,central_and_RPC_metadata_simulated=True,
        real_V1_video=False,whole_GPU_entry_accepted=False,P1_GPU_authorized=False,
        real_four_card_accessed=False,real_central_ledger_read=False,GPU_submissions=0,ledger_written=False)
    return result,raw


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('launch','capture','output','proof-output'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and not args.proof_output.exists()
    result,raw=accept(args.launch,args.capture)
    with args.proof_output.open('xb') as stream:stream.write(raw)
    result.update(original_proof_ref=str(args.proof_output))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','tests_run','original_host_ended','P1_GPU_authorized')}))
