"""Accept the original E1 CPU container's saved proof; never execute its reader."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_endpoint7_cpu_r1 import STAGE,CONTRACT,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.cara_endpoint7_plan_r1 import NEW_ROLES
from wcomr.cara_fast_spec_r1 import digest

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return hashlib.sha256((json.dumps(v,indent=2)+'\n').encode()).hexdigest()
def accept(captured,launched):
    assert captured['exit_code']==launched['exit_code']==0
    c,l=captured['result'],launched['result'];reg,proof,state=c['registration'],c['CPU_proof'],c['container_state']
    assert c['launch']==l and l['host']=='two_card' and Path(l['stage']).name==STAGE and l['container']==STAGE+'-cpu'
    assert state['Status']=='exited' and state['ExitCode']==0 and not state['Running'] and state['Pid']==0 and not state['OOMKilled']
    assert c['registration_sha256']==encoded(reg)==l['registration_sha256']==proof['registration_sha256']
    assert c['CPU_proof_sha256']==encoded(proof)
    base=json.loads((ROOT/BASE_CAPTURE).read_text())['result'];accepted=json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed']==113
    revision=launched['source_revision']
    overlay={p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    assert reg['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}==proof['payload_sha256']
    assert reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']==proof['runtime_source_sha256']
    assert reg['base_registration_sha256']==base['registration_sha256'] and reg['parent_git_revision']==proof['source_revision']==captured['source_revision']==revision
    assert c['payload_intact'] and c['runtime_intact'] and c['host_config']==reg['expected_host_config']==LIMITS
    assert proof['actual_CPU_affinity']==[26] and proof['contract_sha256']==sha(ROOT/CONTRACT)==overlay[CONTRACT]
    contract=json.loads((ROOT/CONTRACT).read_text())
    assert all(sha(ROOT/p)==h==overlay[p] for p,h in contract['evidence_sha256'].items())
    assert proof['status']=='ENDPOINT7_COMPLETE46_TINY_CPU_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE' and proof['production_paths']==46 and proof['extra_timing_OFF_paths']==5
    rows=proof['numeric']['checks'];assert len(rows)==2 and rows[0]['status']=='SKIPPED_UNCHANGED_FLOW_OFF'
    row=rows[1];card=json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    assert row['status']=='PASS' and row['flow'] and row['original_source_scope_sha256']==card['scope_sha256']
    assert row['actual_frozen_policies']=={r:card['roles'][r]['policy']['fingerprint'] for r in NEW_ROLES}
    assert row['complete_production_paths']==46 and row['extra_timing_OFF_paths']==5 and row['repeat_identity_controls']==10
    assert all(row[k] for k in ['same_latent_RGB_RNG_ON_OFF','true_Native_allD_equal','recovery_without_callback','replay_refused','new_GPU_scope_refused'])
    assert row['failure_denominator']==46 and not row['actual_historical_RGB_accepted']
    assert l['started_unix']<=proof['started_unix']<=proof['ended_unix'] and proof['ended_unix']-proof['started_unix']<=1200
    assert proof['actual_compile_threads']==1 and proof['compile_pools']==[]
    assert not any(proof[k] for k in ['CUDA_initialized','Cosmos_model_weights_loaded','actual_historical_RGB_accepted','whole_GPU_card_accepted','ledger_written','GPU_submissions'])
    return dict(status='ENDPOINT7_ORIGINAL_COMPLETE46_PRODUCTION_ROUTE_CPU_ACCEPTED_ONLY',source_revision=revision,
        launch=l,container_state=state,host_config=LIMITS,registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        scope_sha256=card['scope_sha256'],physical_paths=46,extra_timing_OFF=5,repeat_controls=10,allD_control=1,
        actual_frozen_policy_routes_accepted=True,CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        Cosmos_weights_loaded=False,actual_historical_RGB_accepted=False,whole_GPU_lifecycle_accepted=False,
        production_dispatch_and_28_position_acceptance_binding_pending=True,GPU_submissions=0,ledger_written=False)
if __name__=='__main__':
    launch='reports/cara_endpoint7_CPU_launch_r1_20261101.json';capture='reports/cara_endpoint7_CPU_capture_r2_20261101.json'
    result=accept(json.loads((ROOT/capture).read_text()),json.loads((ROOT/launch).read_text()))
    result.update(launch_ref=launch,launch_sha256=sha(ROOT/launch),capture_ref=capture,capture_sha256=sha(ROOT/capture))
    path=ROOT/'reports/cara_endpoint7_CPU_accepted_r1_20261101.json'
    with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=result['status'],CPU_wall_seconds=result['CPU_wall_seconds'])))
