"""Accept original exited CPU selector coverage independently of the worker."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from cara_s_initialization_selector_cpu_r1 import STAGE, CONTRACT, OVERLAY, BASE_CAPTURE, BASE_ACCEPTED, LIMITS
from wcomr.cara_s_initialization_audit_r1 import audit
from wcomr.cara_fast_spec_r1 import digest, profile_from, policy_from_mask


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded_sha(value):
    return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured, launched):
    require(captured['exit_code'] == launched['exit_code'] == 0, 'Original capture and launch required')
    c, launch = captured['result'], launched['result']
    reg, proof, state = c['registration'], c['CPU_proof'], c['container_state']
    require(c['launch'] == launch and launch['host'] == 'two_card'
            and Path(launch['stage']).name == STAGE and launch['container'] == STAGE+'-cpu',
            'Only the original selector CPU container is admissible')
    require(state['Status'] == 'exited' and not state['Running'] and state['Pid'] == 0
            and state['ExitCode'] == 0 and not state['OOMKilled'] and proof is not None,
            'Original CPU must exit zero with complete proof')
    require(c['registration_sha256'] == encoded_sha(reg) == launch['registration_sha256']
            == proof['registration_sha256'] and c['CPU_proof_sha256'] == encoded_sha(proof),
            'Original source/proof byte binding differs')
    base = json.loads((ROOT/BASE_CAPTURE).read_text())['result']
    accepted = json.loads((ROOT/BASE_ACCEPTED).read_text())
    require(accepted['capture_sha256'] == file_sha(ROOT/BASE_CAPTURE)
            and accepted['total_controls_passed'] == 113, 'Original accepted CPU source base required')
    revision = launched['source_revision']
    overlay = {p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest()
               for p in OVERLAY}
    require(reg['payload_sha256'] == {**base['registration']['payload_sha256'],**overlay}
            and reg['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
            and reg['base_registration_sha256'] == base['registration_sha256']
            and reg['parent_git_revision'] == proof['source_revision'] == captured['source_revision'] == revision
            and c['payload_intact'] and c['runtime_intact'], 'Original full source and runtime differ')
    require(c['host_config'] == reg['expected_host_config'] == LIMITS
            and proof['actual_CPU_affinity'] == [26], '1CPU/CPU26/4GiB/no swap/no GPU boundary differs')
    contract = json.loads((ROOT/CONTRACT).read_text())
    require(file_sha(ROOT/CONTRACT) == proof['contract_sha256'] == overlay[CONTRACT], 'Original CPU contract differs')
    require(file_sha(ROOT/'src/wcomr/cara_s_initialization_audit_r1.py') == overlay['src/wcomr/cara_s_initialization_audit_r1.py'],
            'Local diagnostic validator source differs from original')
    require(proof['production_source_sha256'] == contract['production_source_sha256']
            and all(reg['payload_sha256'][p] == file_sha(ROOT/p) == h for p,h in proof['production_source_sha256'].items()),
            'Original production selector and grammar source required')
    risk = {j:{int(k):v for k,v in rows.items()} for j,rows in contract['risk'].items()}
    diagnostic = audit(contract['profile'],contract['baselines'],risk,contract['original_choices'],contract['original_candidate_count'])
    require(digest(diagnostic) == proof['diagnostic_digest'] == contract['expected_audit_digest'], 'Fixed diagnostic changed')
    profile = profile_from(contract['profile'])
    policies = {}
    for origin in diagnostic['origins'].values():
        for dense in [origin['initial_dense']] + [r['dense'] for r in origin['candidates']]:
            policy = policy_from_mask(profile,dense)
            policies[policy['fingerprint']] = policy
    # Compute coverage independently from the selector worker's running anchors.
    expected = set()
    for policy in policies.values():
        dense = [i for i,a in enumerate(policy['actions'],1) if a == 'D']
        for step, action in enumerate(policy['actions'],1):
            if action == 'C':
                past = [d for d in dense if d < step]
                expected.add((step,*past[-2:]))
    require(proof['status'] == 'S_TWO_INITIALIZATIONS_PRODUCTION_SELECTOR_CPU_COMPLETE_NOT_ENDPOINT'
            and proof['host'] == 'two_card' and proof['checked_distinct_policies'] == len(policies)
            and proof['checked_policy_fingerprints'] == sorted(policies)
            and proof['checked_selector_pairs'] == 36*len(policies)
            and proof['checked_C_branch_histories'] == 34*len(policies)
            and proof['supported_C_histories'] == [list(h) for h in sorted(expected)],
            'Incomplete full candidate policies or selector/history denominator')
    require(proof['additional_histories_verified'] == diagnostic['additional_selector_histories']
            == contract['expected_additional_histories'] and len(proof['additional_histories_verified']) == 138,
            'All 138 newly required history slots must be checked')
    require(proof['anchor_mutations_refused'] == [dict(branch=b,reason=r) for b in (0,1) for r in ('missing','future')]
            and proof['forced_dense_verified'] is True, 'Both-branch anchor refusals and forced-D control required')
    require(launch['started_unix'] <= proof['started_unix'] <= proof['ended_unix']
            and proof['ended_unix']-proof['started_unix'] <= 180 and proof['controlled_CPU_anchor_objects'] is True
            and not any(proof[k] for k in ('CUDA_initialized','actual_model_forward_calls','original_S_freeze_changed',
                'free_running_or_endpoint_acceptance','GPU_submissions','ledger_written')),
            'CPU scope, time or no-GPU boundary differs')
    return dict(status='TWO_CARD_S_INITIALIZATION_SELECTOR_HISTORY_CPU_ACCEPTED_NOT_ENDPOINT',
        observed_unix=time.time(),source_revision=revision,launch=launch,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        checked_distinct_policies=len(policies),checked_selector_pairs=proof['checked_selector_pairs'],
        checked_C_branch_histories=proof['checked_C_branch_histories'],supported_history_count=len(expected),
        additional_histories_verified=138,anchor_mutations_refused=proof['anchor_mutations_refused'],
        forced_dense_verified=True,CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        new_selector_history_CPU_accepted=True,controlled_CPU_anchor_objects=True,
        free_running_or_endpoint_acceptance=False,original_S_freeze_changed=False,
        new_method_recipe_frozen=False,model_calls=0,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','launch','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),'Preserve the original accepted receipt')
    report=accept(json.loads(args.capture.read_text()),json.loads(args.launch.read_text()))
    report.update(capture_ref=str(args.capture),capture_sha256=file_sha(args.capture),
                  launch_ref=str(args.launch),launch_sha256=file_sha(args.launch),acceptor_sha256=file_sha(__file__))
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:report[k] for k in ('status','checked_distinct_policies','checked_selector_pairs','additional_histories_verified')}))


if __name__ == '__main__':
    main()
