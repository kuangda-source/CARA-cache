"""Compose accepted CPU deltas for the distinct successor; no remote access."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CAPTURE='reports/cara_v1_P1_successor_identity_Linux_CPU_capture_r2_20261102.json'
LAUNCH='reports/cara_v1_P1_successor_identity_Linux_CPU_launch_r2_20261102.json'
ACCEPTED='reports/cara_v1_P1_successor_identity_Linux_CPU_accepted_r2_20261102.json'
WHOLE='reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json'
BASE='reports/cara_v1_P1_whole_CPU_memory50_accepted_r2_20261102.json'
REPAIR='reports/cara_v1_P1_publication_RPC_Linux_CPU_accepted_r2_20261102.json'


def read(name):return json.loads((ROOT/name).read_bytes())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def create(name,value):
    with (ROOT/name).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    cap,launch=read(CAPTURE),read(LAUNCH)
    assert cap['exit_code']==launch['exit_code']==0
    c=cap['result'];reg=c['registration'];proof=c['CPU_proof']
    assert c['launch']==launch['result'] and c['payload_intact'] and c['runtime_intact']
    assert c['original_host_observation']['original_live'] is False
    assert c['host_terminal']['error'] is None and c['host_terminal']['identity']==c['launch']['identity']
    raw=base64.b64decode(c['CPU_proof_base64'],validate=True)
    assert hashlib.sha256(raw).hexdigest()==c['CPU_proof_sha256'] and json.loads(raw)==proof
    assert proof['tests_run']==56 and proof['status']=='P1_SUCCESSOR_IDENTITY_FULL_READERS_CPU_PASS'
    assert proof['parent_identity']==c['launch']['identity'] and proof['payload_sha256']==reg['payload_sha256']
    assert proof['registration_sha256']==c['registration_sha256']==c['launch']['registration_sha256']
    assert proof['original_metric_pairs_recomputed']==0 and proof['GPU_authorized'] is False
    assert all(sha(n)==h for n,h in reg['payload_sha256'].items())
    base=read(BASE);repair=read(REPAIR);repair_raw=read('reports/cara_v1_P1_publication_RPC_Linux_CPU_original_proof_r2_20261102.json')
    assert repair['tests_run']==33 and repair['original_host_ended'] is True
    repaired=('src/wcomr/cara_source_lifecycle_fit_broker_r1.py','scripts/cara_source_lifecycle_p1_control_r1.py')
    assert all(reg['payload_sha256'][n]==repair_raw['payload_sha256'][n] for n in repaired)
    changed={n for n,h in base['payload_sha256'].items() if reg['payload_sha256'].get(n)!=h}
    assert changed==set(repaired)|{
        'src/wcomr/cara_source_lifecycle_p1_identity_r1.py',
        'src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py',
        'tests/test_cara_source_lifecycle_p1_profile_quote_r1.py',
        'tests/check_cara_source_lifecycle_p1_score_fixture_r1.py'}
    assert reg['runtime_source_sha256']==base['runtime_source_sha256']
    name=repaired[0]
    old_tree=ast.parse(subprocess.check_output(['git','show','6bf82dd262c082a6786588d39d9ea23da74cc907:'+name],cwd=ROOT,text=True))
    new_tree=ast.parse((ROOT/name).read_text());unchanged={}
    old_nodes={n.name:n for n in old_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    for node in new_tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name!='Client':
            assert ast.dump(node)==ast.dump(old_nodes[node.name]),node.name
            unchanged[node.name]=hashlib.sha256(ast.dump(node).encode()).hexdigest()
    accepted=dict(status='ORIGINAL_SUCCESSOR_IDENTITY_LINUX_CPU56_ACCEPTED',source_revision=reg['parent_git_revision'],
        stage=c['launch']['stage'],registration_sha256=c['registration_sha256'],capture_ref=CAPTURE,capture_sha256=sha(CAPTURE),
        launch_ref=LAUNCH,launch_sha256=sha(LAUNCH),original_host_ended=True,original_identity=c['launch']['identity'],
        tests_run=56,original_proof_sha256=c['CPU_proof_sha256'],real_metric_pairs_computed=0,
        GPU_authorized=False,GPU_submissions=0,ledger_written=False)
    create(ACCEPTED,accepted)
    with (ROOT/'reports/cara_v1_P1_successor_identity_Linux_CPU_original_proof_r2_20261102.json').open('xb') as stream:stream.write(raw)
    flags=('complete_algorithm_reused_source_bound','actual_host_FIT_broker_reused_source_bound',
        'guardian_FIT_cleanup_reused_source_bound','production_total_entry_CPU_accepted',
        'released_full146_reader_and_new32_scores_CPU_accepted')
    assert all(base[k] is True for k in flags)
    whole=dict(schema='CARA_V1_P1_WHOLE_CPU_COMPOSED_R1',
        status='SUCCESSOR_WHOLE_CPU_COMPOSED_WITH_REPAIR33_AND_IDENTITY56',host='two_card',
        source_revision=reg['parent_git_revision'],scope_sha256=base['scope_sha256'],
        whole_card_CPU_accepted=True,execution_authorized=False,payload_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'],supplemental_runtime_sha256=base['supplemental_runtime_sha256'],
        execution_host_policy_sha256=base['execution_host_policy_sha256'],source_CPU_stage=c['launch']['stage'],
        source_registration_sha256=c['registration_sha256'],original_base_proof_ref=BASE,original_base_proof_sha256=sha(BASE),
        repair33_ref=REPAIR,repair33_sha256=sha(REPAIR),successor_identity56_ref=ACCEPTED,
        successor_identity56_sha256=sha(ACCEPTED),unchanged_non_Client_broker_AST_sha256=unchanged,
        changed_original_payload_paths=sorted(changed),all_other_original_payload_bytes_unchanged=True,
        scientific_design_scope_changed=False,numerical_model_or_metrics_changed=False,
        failed_GPU_artifacts_or_partial_scores_reused=False,original_experiments_replayed=False,
        local_plot_control_ref='reports/cara_v1_P1_successor_identity_packaged_local_CPU_r2_20261102.json',
        local_plot_control_sha256=sha('reports/cara_v1_P1_successor_identity_packaged_local_CPU_r2_20261102.json'),
        GPU_submissions=0,ledger_written=False,**{k:True for k in flags})
    create(WHOLE,whole)
    print(json.dumps(dict(status=whole['status'],source_revision=whole['source_revision'],
        source_files=len(whole['payload_sha256']),GPU_authorized=False)))


if __name__=='__main__':main()
