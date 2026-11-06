"""Accept complete original bounded endpoint CPU collections after container exit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from cara_s_endpoint_collection_cpu_r2 import STAGE, CONTRACT, OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_sha(value): return hashlib.sha256((json.dumps(value, indent=2) + '\n').encode()).hexdigest()


def accept(captured, launched):
    require(captured['exit_code'] == launched['exit_code'] == 0, 'Original launch and capture required')
    c, l = captured['result'], launched['result']
    reg, proof, state = c['registration'], c['CPU_proof'], c['container_state']
    require(c['launch'] == l and l['host'] == 'two_card' and Path(l['stage']).name == STAGE
            and l['container'] == STAGE + '-cpu', 'Original endpoint CPU identity differs')
    require(state['Status'] == 'exited' and not state['Running'] and state['Pid'] == 0
            and state['ExitCode'] == 0 and not state['OOMKilled'] and proof is not None,
            'Exited zero complete proof required')
    require(c['registration_sha256'] == encoded_sha(reg) == l['registration_sha256'] == proof['registration_sha256']
            and c['CPU_proof_sha256'] == encoded_sha(proof), 'Original bytes differ')
    base = json.loads((ROOT / BASE_CAPTURE).read_text())['result']
    accepted = json.loads((ROOT / BASE_ACCEPTED).read_text())
    require(accepted['capture_sha256'] == sha(ROOT / BASE_CAPTURE) and accepted['total_controls_passed'] == 113,
            'Accepted source base differs')
    revision = launched['source_revision']
    overlay = {p: hashlib.sha256(subprocess.check_output(['git', 'show', revision + ':' + p], cwd=ROOT)).hexdigest()
               for p in OVERLAY}
    require(reg['payload_sha256'] == {**base['registration']['payload_sha256'], **overlay} == proof['payload_sha256']
            and reg['runtime_source_sha256'] == base['registration']['runtime_source_sha256'] == proof['runtime_source_sha256']
            and reg['base_registration_sha256'] == base['registration_sha256']
            and reg['parent_git_revision'] == proof['source_revision'] == captured['source_revision'] == revision
            and c['payload_intact'] and c['runtime_intact'], 'Original source/runtime differs')
    require(c['host_config'] == reg['expected_host_config'] == LIMITS
            and proof['actual_CPU_affinity'] == [26], 'CPU resource boundary differs')
    contract = json.loads((ROOT / CONTRACT).read_text())
    require(sha(ROOT / CONTRACT) == proof['contract_sha256'] == overlay[CONTRACT]
            and all(sha(ROOT / p) == h == overlay[p] for p, h in contract['evidence_sha256'].items()),
            'Fixed proposal/evidence differs')
    require(proof['status'] == 'ENDPOINT_COMPLETE_COLLECTION_TINY_CPU_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE'
            and proof['host'] == 'two_card' and proof['production_paths'] == 114
            and proof['independent_reference_paths'] == 16 and proof['failure_controls'] == 6,
            'Complete endpoint denominator differs')
    rows = proof['numeric']['checks']
    require(len(rows) == 2 and {r['flow'] for r in rows} == {False, True}, 'Both flow modes required')
    proposal = json.loads((ROOT / 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json').read_text())
    base_card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    for row in rows:
        require(row['status'] == 'PASS' and row['complete_production_paths'] == 57
                and row['independent_reference_calls'] == 8 and row['verified_policy_settings_installs'] == 51
                and row['effective_settings'] == {**contract['base_execution_settings'], 'worldcache_flow_enabled': row['flow']}
                and row['Cosmos_weights_loaded'] is False and row['actual_budget_policy_bound'] is False,
                'Complete matched production CPU routes required')
        cases = row['cases']
        require(len(cases) == 2 and {c['aliased_budget'] for c in cases} == {False, True}, 'Full32 and alias25 required')
        for case in cases:
            alias = case['aliased_budget']
            policy = proposal['new_policies']['SU19_CFG_C'] if alias else base_card['roles']['UNIFORM19_C']['policy']
            bound = map_physical_slots(proposal, policy)
            bound.update(CPU_fixture_only=True, status='CPU_FIXTURE_BINDING_ONLY',
                proposal_scope_sha256=proposal['scope_sha256'],
                original_freeze_sha256=digest({'DECLARED_CPU_SYNTHETIC_POLICY': policy}),
                actual_original_budget_freeze_read=False)
            bound['binding_sha256'] = digest(bound)
            card = request_card(proposal, bound, base_card)
            card['roles']['ALLD']['settings']['worldcache_flow_enabled'] = row['flow']
            expected_scope = digest({k: v for k, v in card.items() if k != 'scope_sha256'})
            require(case['status'] == 'PASS' and case['flow'] == row['flow']
                    and case['scope_sha256'] == expected_scope
                    and case['paths'] == (25 if alias else 32) and case['logical_quality_positions'] == 24
                    and case['clean_samples'] == (20 if alias else 26)
                    and case['synthetic_identity_checks'] == 9 and case['exact_repeats'] == (4 if alias else 6)
                    and case['failures'] == ([] if alias else ['refusal', 'decode', 'writer']),
                    'Complete matrix, reference or failure controls differ')
            require(all(case[k] is True for k in ('recovery_without_callback', 'existing_output_rejected',
                        'changed_artifact_rejected', 'original_methods_restored', 'CPU_fixture_GPU_refused'))
                    and case['original_budget_outputs_read'] is False
                    and case['actual_historical_RGB_acceptance'] is False,
                    'Recovery, no-replay or synthetic-scope boundary differs')
    require(l['started_unix'] <= proof['started_unix'] <= proof['ended_unix']
            and proof['ended_unix'] - proof['started_unix'] <= 1200
            and proof['actual_compile_threads'] == 1 and proof['compile_pools'] == []
            and proof['work_seconds'] == 1200 and proof['exit_seconds'] == 60
            and all(proof[k] is False for k in ('CUDA_initialized', 'Cosmos_model_weights_loaded',
                'actual_original_budget_outputs_read', 'actual_budget_policy_bound',
                'actual_historical_RGB_accepted', 'whole_GPU_card_accepted', 'ledger_written'))
            and proof['GPU_submissions'] == 0, 'Time or CPU boundary differs')
    return dict(status='ENDPOINT_COMPLETE_COLLECTION_CPU_ACCEPTED_NOT_SCIENTIFIC_ACCEPTANCE',
        observed_unix=time.time(), source_revision=revision, launch=l, container_state=state,
        host_config=LIMITS, registration_sha256=c['registration_sha256'], CPU_proof_sha256=c['CPU_proof_sha256'],
        production_paths=114, independent_reference_paths=16, failure_controls=6,
        full32_and_alias25_both_flows=True, synthetic_identity_checks=36, exact_repeat_checks=20,
        original_output_recovery_without_execution=True, whole_GPU_card_accepted=False,
        actual_budget_policy_bound=False, actual_historical_RGB_accepted=False,
        CPU_wall_seconds=proof['ended_unix'] - proof['started_unix'],
        CPU_process_seconds=proof['CPU_process_seconds'], GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ('capture', 'launch', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve original acceptance')
    result = accept(json.loads(args.capture.read_text()), json.loads(args.launch.read_text()))
    result.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture),
                  launch_ref=str(args.launch), launch_sha256=sha(args.launch), acceptor_sha256=sha(__file__))
    with args.output.open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'production_paths', 'CPU_wall_seconds')}))


if __name__ == '__main__': main()
