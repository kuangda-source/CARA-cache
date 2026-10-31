"""Independently accept the original tiny paired numerical CPU matrix."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'scripts')]
from cara_s_initialization_numeric_cpu_r3 import STAGE,CONTRACT,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.cara_fast_spec_r1 import profile_from,policy_from_mask


def require(condition,message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded_sha(value):
    return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured,launched):
    require(captured['exit_code']==launched['exit_code']==0,'Original launch and capture required')
    c,l=captured['result'],launched['result']
    reg,proof,state=c['registration'],c['CPU_proof'],c['container_state']
    require(c['launch']==l and l['host']=='two_card' and Path(l['stage']).name==STAGE
        and l['container']==STAGE+'-cpu','Original numerical CPU identity differs')
    require(state['Status']=='exited' and not state['Running'] and state['Pid']==0
        and state['ExitCode']==0 and not state['OOMKilled'] and proof is not None,'Exited zero complete proof required')
    require(c['registration_sha256']==encoded_sha(reg)==l['registration_sha256']==proof['registration_sha256']
        and c['CPU_proof_sha256']==encoded_sha(proof),'Original bytes differ')
    base=json.loads((ROOT/BASE_CAPTURE).read_text())['result']
    base_accepted=json.loads((ROOT/BASE_ACCEPTED).read_text())
    require(base_accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE)
        and base_accepted['total_controls_passed']==113,'Accepted source base differs')
    revision=launched['source_revision']
    overlay={p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    require(reg['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}
        ==proof['payload_sha256'] and reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']
        ==proof['runtime_source_sha256'] and reg['base_registration_sha256']==base['registration_sha256']
        and reg['parent_git_revision']==proof['source_revision']==captured['source_revision']==revision
        and c['payload_intact'] and c['runtime_intact'],'Original source/runtime differs')
    require(c['host_config']==reg['expected_host_config']==LIMITS and proof['actual_CPU_affinity']==[26],
        'CPU resource boundary differs')
    contract=json.loads((ROOT/CONTRACT).read_text())
    require(sha(ROOT/CONTRACT)==proof['contract_sha256']==overlay[CONTRACT]
        and sha(ROOT/contract['selector_acceptance_ref'])==contract['selector_acceptance_sha256']
        and sha(ROOT/contract['selector_contract_ref'])==contract['selector_contract_sha256'],
        'Fixed initialization evidence differs')
    require(proof['status']=='UNIFORM_INITIALIZATION_TINY_PAIRED_NUMERIC_CPU_COMPLETE_NOT_ENDPOINT'
        and proof['host']=='two_card' and proof['production_paths']==36 and proof['old_fixed_paths']==12
        and proof['ordinary_pairs']==1728 and proof['CFG_calls']==3456 and proof['failure_controls']==18,
        'Complete numerical denominator differs')
    rows=proof['numeric']['checks']
    require(len(rows)==2 and {r['flow'] for r in rows}=={False,True},'Both flow modes required')
    profile=profile_from(contract['profile'])
    expected={(m,r):policy_from_mask(profile,d)['fingerprint'] for m in contract['FIT'] for r,d in contract['roles'].items()}
    failure_names={r+':'+f for r in contract['roles'] for f in ('refusal','decode','writer')}
    for row in rows:
        require(row['effective_settings']=={**contract['base_execution_settings'],'worldcache_flow_enabled':row['flow']}
            and row['verified_settings_installs']==33,'Matched actual execution settings required')
        require(row['status']=='PASS' and row['production_paths']==18 and row['old_fixed_paths']==6
            and row['registered_CPU_positions']==27 and len(row['comparisons'])==6
            and {(x['member'],x['role']):x['policy_fingerprint'] for x in row['comparisons']}==expected,
            'Exact FIT/policy matrix required')
        require(all(all(x[k] is True for k in ('all36_guided_old_new_equal','final_latent_RGB_RNG_old_new_equal',
            'ON_OFF_AUDIT_exact','strict_true_D_history')) for x in row['comparisons']),
            'All-step trajectory and output parity required')
        require(len(row['failures'])==9 and set(row['failures'])==failure_names,'All failure controls required')
        require(row['Cosmos_weights_loaded'] is False and row['real_video_quality_or_speed_result'] is False,
            'Tiny CPU scope differs')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
        and proof['ended_unix']-proof['started_unix']<=1200 and proof['actual_compile_threads']==1
        and proof['compile_pools']==[] and proof['work_seconds']==1200 and proof['exit_seconds']==60
        and all(proof[k] is False for k in ('CUDA_initialized','Cosmos_model_weights_loaded',
            'original_S_freeze_changed','free_running_or_endpoint_acceptance','whole_GPU_card_accepted','ledger_written'))
        and proof['GPU_submissions']==0,'Time or tiny CPU boundary differs')
    return dict(status='UNIFORM_INITIALIZATION_TINY_PAIRED_NUMERIC_CPU_ACCEPTED_NOT_ENDPOINT',
        observed_unix=time.time(),source_revision=revision,launch=l,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        production_paths=36,old_fixed_paths=12,ordinary_pairs=1728,CFG_calls=3456,failure_controls=18,
        checked_roles=list(contract['roles']),checked_members=contract['FIT'],checked_flows=[False,True],
        all36_old_new_guided_and_final_output_exact=True,ON_OFF_AUDIT_exact=True,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],CPU_process_seconds=proof['CPU_process_seconds'],
        original_S_freeze_changed=False,real_weights_or_endpoint_accepted=False,
        whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','launch','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),'Preserve original acceptance')
    report=accept(json.loads(args.capture.read_text()),json.loads(args.launch.read_text()))
    report.update(capture_ref=str(args.capture),capture_sha256=sha(args.capture),
                  launch_ref=str(args.launch),launch_sha256=sha(args.launch),acceptor_sha256=sha(__file__))
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:report[k] for k in ('status','production_paths','old_fixed_paths','CPU_wall_seconds')}))


if __name__=='__main__':
    main()
