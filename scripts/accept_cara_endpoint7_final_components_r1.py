"""Accept the two original bounded CPU terminals offline; never repeat execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(kind):
    if kind=='final':
        from cara_endpoint7_final_cpu_r2 import STAGE, OVERLAY
        suffix='r2'; count=16; seconds=300
        status='ENDPOINT7_FINAL_AFFECTED_BINDING_ANALYSIS_CPU_PASS'
    else:
        from cara_endpoint7_central_cpu_r1 import STAGE, OVERLAY
        suffix='r1'; count=13; seconds=180
        status='ENDPOINT7_CENTRAL_TEMPORARY_LEDGER_CPU_PASS'
    prefix='reports/cara_endpoint7_'+kind+'_CPU_'
    launch=prefix+'launch_'+suffix+'_20261101.json'
    capture=prefix+'capture_'+suffix+'_20261101.json'
    l,c=[json.loads((ROOT/p).read_text()) for p in (launch,capture)]
    assert l['exit_code']==c['exit_code']==0
    start=l['result']; cap=c['result']; reg=cap['registration']; proof=cap['CPU_proof']; state=cap['container_state']
    assert cap['launch']==start and Path(start['stage']).name==STAGE and start['container']==STAGE+'-cpu'
    assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0 and not state['Running'] and not state['OOMKilled']
    assert cap['registration_sha256']==encoded(reg)==start['registration_sha256']==proof['registration_sha256']
    assert cap['CPU_proof_sha256']==encoded(proof)
    base=json.loads((ROOT/BASE_CAPTURE).read_text())['result']; base_ok=json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert base_ok['capture_sha256']==sha(ROOT/BASE_CAPTURE) and base_ok['total_controls_passed']==113
    revision=l['source_revision']; full=subprocess.check_output(['git','rev-parse',revision+'^{commit}'],cwd=ROOT,text=True).strip()
    overlay={p:hashlib.sha256(subprocess.check_output(['git','show',full+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    assert reg['payload_sha256']==proof['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}
    assert all(sha(ROOT/p)==h for p,h in overlay.items())
    assert reg['runtime_source_sha256']==proof['runtime_source_sha256']==base['registration']['runtime_source_sha256']
    assert reg['base_registration_sha256']==base['registration_sha256'] and reg['parent_git_revision']==proof['source_revision']==c['source_revision']==revision
    assert cap['payload_intact'] and cap['runtime_intact'] and cap['host_config']==reg['expected_host_config']==LIMITS
    assert proof['actual_CPU_affinity']==[26] and proof['tests_run']==count and proof['status']==status
    assert start['started_unix']<=proof['started_unix']<proof['ended_unix']<=proof['started_unix']+seconds
    assert not proof['GPU_submissions'] and not proof['ledger_written']
    if kind=='final':
        assert (proof['dispatch_storage_controls'],proof['analysis_controls'],proof['figure_controls'])==(8,5,3)
        assert all(not proof[k] for k in ('original_numeric46_rerun','metric_computation','actual_GPU_or_Docker_executed','actual_storage_provisioned','whole_card_CPU_accepted'))
        assert proof['synthetic_metadata_only'] and proof['fixture_export']
        assert {Path(p).suffix for p in proof['fixture_export']} >= {'.png','.pdf','.csv','.json'}
    else:
        assert proof['temporary_ledger_only'] and not proof['production_ledger_accessed'] and not proof['four_card_accessed']
    return dict(status=status+'_ACCEPTED',source_revision=full,launch=start,container_state=state,host_config=LIMITS,
        registration_sha256=cap['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],
        launch_ref=launch,launch_sha256=sha(ROOT/launch),capture_ref=capture,capture_sha256=sha(ROOT/capture),
        affected_source_sha256=overlay,tests_run=count,wall_seconds=proof['ended_unix']-proof['started_unix'],
        original_numeric46_rerun=False,old_experiment_videos_rescored=0,whole_card_CPU_accepted=False,
        fixture_export=proof.get('fixture_export'),temporary_ledger_only=kind=='central',production_ledger_accessed=False,
        four_card_accessed=False,GPU_submissions=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['final','central']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    result=accept(a.kind)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','tests_run','wall_seconds')}))

if __name__=='__main__':main()
