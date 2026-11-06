"""Compose the tested prelaunch resource-only delta, without GPU or ledger I/O."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'reports/cara_v1_P1_whole_CPU_accepted_r1_20261102.json'
CPU = 'reports/cara_v1_P1_memory50_Linux_CPU_r1_20261102.json'
PROPOSAL = 'reports/cara_v1_P1_memory50_candidate_r1_20261102.json'
PROOF = 'reports/cara_v1_P1_whole_CPU_memory50_accepted_r2_20261102.json'
AUTH = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json'
PLAN = 'reports/cara_v1_P1_source_memory50_plan_r2_20261102.json'
QUOTE = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json'


def load(name):
    return json.loads((ROOT/name).read_bytes())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()


def create(name, value):
    with (ROOT/name).open('xb') as stream:
        stream.write(encoded(value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    assert args.source_revision == subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    old, proposal, receipt = load(BASE), load(PROPOSAL), load(CPU)
    cpu = receipt['result']; proof = cpu['proof']
    assert receipt['exit_code'] == cpu['terminal']['exit_code'] == 0
    assert cpu['terminal']['observation']['original_live'] is False
    assert proof['status'] == 'CPU_DELTA_ACCEPTED' and proof['tests_run'] == 9
    assert proof['errors'] == proof['failures'] == proof['real_metrics_computed'] == 0
    assert hashlib.sha256(encoded(proof)).hexdigest() == cpu['proof_sha256']
    changed = {n for n,h in old['payload_sha256'].items() if sha(n) != h}
    assert changed == set(proposal['changed_files']) and len(changed) == 4
    for name in changed:
        assert sha(name) == proposal['changed_files'][name]['proposed'] == proof['source_sha256'][name]
        committed = subprocess.check_output(['git','show',args.source_revision+':'+name],cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest() == sha(name)
    for name in ('src/wcomr/cara_source_lifecycle_fit_broker_r1.py',
                 'src/wcomr/cara_source_lifecycle_p1_service_r1.py'):
        assert sha(name) == old['payload_sha256'][name] == proof['source_sha256'][name]
    source = 'src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py'
    reverted = (ROOT/source).read_text().replace('minimum_MemAvailable_GiB=50)', 'minimum_MemAvailable_GiB=52)')
    assert hashlib.sha256(reverted.encode()).hexdigest() == old['payload_sha256'][source]
    new = copy.deepcopy(old)
    new.update(status='WHOLE_CPU_COMPOSED_WITH_TESTED_PRELAUNCH_MEMORY50_DELTA',
        source_revision=args.source_revision,
        payload_sha256={n:sha(n) for n in old['payload_sha256']},
        source_registration_sha256=hashlib.sha256(encoded(cpu['source'])).hexdigest(),
        source_CPU_stage=cpu['stage'],base_whole_CPU_ref=BASE,base_whole_CPU_sha256=sha(BASE),
        resource_delta_CPU_ref=CPU,resource_delta_CPU_sha256=sha(CPU),
        resource_delta_source_sha256={n:sha(n) for n in changed},
        resource_delta_initial_memory_GiB=dict(before=52,after=50),
        resource_delta_keeps_GPU40_CPU8_and_query12=True,
        original_scientific_compute_sources_changed=False,
        numerical_model_or_metric_replayed=False)
    new['evidence_sha256'][QUOTE] = sha(QUOTE)
    new['evidence_sha256'][CPU] = sha(CPU)
    new['reused_selected_core_sources']['released146_score52_core']['resource_only_binding_derivation'] = dict(
        path=source,before_sha256=old['payload_sha256'][source],after_sha256=sha(source),
        CPU_delta_ref=CPU,change='Only initial MemAvailable52 to50; all other binding checks unchanged')
    create(PROOF,new)
    initial = load('plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_AUTHORIZATION_R1.json')
    authority = copy.deepcopy(initial)
    authority.update(source_revision=args.source_revision,minimum_MemAvailable_GiB=50,
        CPU_proof_sha256=sha(PROOF),quote_sha256=sha(QUOTE),
        original_single_card_authorization_ref='plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_AUTHORIZATION_R1.json',
        prelaunch_resource_amendment=dict(recorded_at=datetime.now(timezone.utc).isoformat(),
            user_request='内存门限一定要这么严格吗，看下现有状态能不能推进',
            basis='USER_REQUESTED_PRELAUNCH_ENGINEERING_REVIEW_WITHIN_APPROVED_SINGLE19GPUH',
            old_initial_GiB=52,new_initial_GiB=50,GPU_container_GiB=40,CPU_container_GiB=8,
            per_query_fresh_GiB=12,CPU_delta_ref=CPU,scientific_scope_changed=False,
            extra_GPU_card_authorized=False,original_hard19_unchanged=True))
    create(AUTH,authority)
    prepared=load('reports/cara_v1_P1_source_preparation_r1_20261102.json')['result']
    registration=copy.deepcopy(prepared['registration'])
    registration.update(source_revision=args.source_revision,payload_sha256=new['payload_sha256'],
        prelaunch_memory50_derivation=dict(base_GPU_registration_sha256=prepared['registration_sha256'],
            CPU_delta_registration_sha256=new['source_registration_sha256'],CPU_delta_ref=CPU))
    old_sidecars=prepared['sidecar_sha256']
    replacements={n:dict(old_sha256=old['payload_sha256'][n],new_raw_utf8=(ROOT/n).read_text()) for n in changed}
    for name,value,old_sha in (
            ('registration.json',registration,prepared['registration_sha256']),
            ('execution-CPU-proof.json',new,old_sidecars['execution-CPU-proof.json']),
            ('whole-quote.json',load(QUOTE),old_sidecars['whole-quote.json']),
            ('GPU-authorization.json',authority,sha('plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_AUTHORIZATION_R1.json'))):
        replacements[name]=dict(old_sha256=old_sha,new_raw_utf8=encoded(value).decode())
    create(PLAN,dict(schema='CARA_P1_UNSTARTED_MEMORY50_SOURCE_AMENDMENT_R2',
        stage=authority['stage'],run_id=authority['run_id'],launch_id=authority['launch_id'],
        source_revision=args.source_revision,base_registration_sha256=prepared['registration_sha256'],
        new_registration_sha256=hashlib.sha256(encoded(registration)).hexdigest(),
        replacements=replacements,authority_ref=AUTH,CPU_proof_ref=PROOF,
        unstarted_and_unreserved_required=True,GPU_submissions=0,ledger_written=False))
    print(json.dumps(dict(proof_ref=PROOF,authority_ref=AUTH,plan_ref=PLAN,
        source_revision=args.source_revision,initial_MemAvailable_GiB=50,GPU_submissions=0)))


if __name__ == '__main__':
    main()
