"""Compose original CPU evidence and immutable source; no remote action or authority."""
import argparse
import ast
import subprocess
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from accept_cara_endpoint7_final_components_r1 import accept, encoded, sha
from wcomr.cara_budget_host_policy_r1 import POLICY, POLICY_SHA256
from wcomr.cara_s_endpoint_runner_binding_r1 import REQUIRED, CARD, BINDING, PROFILE
from wcomr.cara_s_endpoint_gpu_dispatch_r1 import REQUIRED as DISPATCH_REQUIRED
from wcomr.cara_s_endpoint_reuse_admission_r1 import expected_sources
from wcomr.cara_s_endpoint_artifacts_r1 import PROPOSAL, ORIGINAL_SCORES
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.immutable_stage_payload_r1 import git_archive, overlay_bytes, local_python_closure

FINAL='reports/cara_endpoint7_final_CPU_accepted_r2_20261101.json'
CENTRAL='reports/cara_endpoint7_central_CPU_accepted_r1_20261101.json'
NUMERIC='reports/cara_endpoint7_CPU_accepted_r1_20261101.json'
INTERFACES='reports/cara_endpoint7_interfaces_CPU_accepted_r1_20261101.json'
STORAGE='reports/cara_endpoint7_storage_accepted_r1_20261101.json'
IO='reports/cara_budget_private_RGB_CPU_accepted_r1_20261031.json'
ASSETS='reports/cara_endpoint7_original_arguments_assets_r1_20261101.json'
OLD=['reports/cara_s_endpoint_'+name+'_CPU_accepted_'+rev+'_20261031.json' for name,rev in (
    ('collection','r2'),('runner','r1'),('artifact','r1'),('score','r1'),('capture','r2'),
    ('dispatch','r1'),('guardian','r2'),('pipeline','r1'),('gpu_dispatch','r1'),('reuse','r1'))]


def read(name):return json.loads((ROOT/name).read_text())


def original(ref):
    accepted=read(ref); cap=read(accepted['capture_ref'])['result']
    assert sha(ROOT/accepted['capture_ref'])==accepted['capture_sha256']
    assert sha(ROOT/accepted['launch_ref'])==accepted['launch_sha256']
    assert cap['registration_sha256']==encoded(cap['registration'])==accepted['registration_sha256']
    assert cap['CPU_proof_sha256']==encoded(cap['CPU_proof'])==accepted['CPU_proof_sha256']
    state=cap['container_state']
    assert state['Status']=='exited' and state['ExitCode']==0 and not state['Running'] and not state['OOMKilled'] and state['Pid']==0
    assert cap['payload_intact'] and cap['runtime_intact']
    assert cap['CPU_proof']['payload_sha256']==cap['registration']['payload_sha256']
    return accepted,cap


def compose():
    records={ref:original(ref) for ref in OLD+[NUMERIC,INTERFACES,FINAL,CENTRAL]}
    assert read(FINAL)==accept('final') and read(CENTRAL)==accept('central')
    final,cap=records[CENTRAL]; reg=cap['registration']; payload=reg['payload_sha256']; revision=final['source_revision']
    assert all(sha(ROOT/n)==h for n,h in payload.items())
    required=set(REQUIRED)|set(DISPATCH_REQUIRED)|{PROPOSAL,ORIGINAL_SCORES,
        'src/wcomr/cara_endpoint7_analysis_r1.py','src/wcomr/cara_endpoint7_figures_r1.py',
        'src/wcomr/cara_endpoint7_central_r1.py','scripts/analyze_cara_endpoint7_complete_r1.py',
        'src/wcomr/cara_s_endpoint_score_dispatch_r1.py','src/wcomr/cara_s_endpoint_score_capture_r1.py'}
    assert required<=set(payload) and payload[POLICY]==POLICY_SHA256
    closure=local_python_closure(ROOT,[n for n in payload if n.endswith('.py')])
    assert all(payload.get(n)==h for n,h in closure.items())
    # Original route, selected policy and metric modules remain unchanged. Only the
    # documented container/storage and analysis/central additions use later checks.
    numeric, ncap=records[NUMERIC]; interfaces,icap=records[INTERFACES]
    name='src/wcomr/cara_endpoint7_plan_r1.py'
    assert payload[name]==ncap['registration']['payload_sha256'][name]
    execution='src/wcomr/cara_s_uniform_endpoint_execution_r1.py'
    old_raw=subprocess.check_output(['git','show',numeric['source_revision']+':'+execution],cwd=ROOT)
    assert hashlib.sha256(old_raw).hexdigest()==ncap['registration']['payload_sha256'][execution]
    before={n.name:n for n in ast.parse(old_raw).body if isinstance(n,ast.FunctionDef)}
    after={n.name:n for n in ast.parse((ROOT/execution).read_bytes()).body if isinstance(n,ast.FunctionDef)}
    for name in ('make_requests','check_collection','inspect_original'):
        assert ast.dump(before[name])==ast.dump(after[name])
    # request_card and the execute preamble add only the accepted46 production
    # binding. The collection/sample/save body after its count gate is identical.
    body=lambda fn:fn.body[next(i for i,n in enumerate(fn.body) if isinstance(n,ast.ClassDef)):]
    assert [ast.dump(n) for n in body(before['execute'])]==[ast.dump(n) for n in body(after['execute'])]
    affected_after_interfaces={'scripts/cara_s_endpoint_container_r1.py','src/wcomr/cara_s_endpoint_runner_binding_r1.py',
        'configs/cara_endpoint_container_profile.json','tests/test_cara_s_endpoint_runner_binding_r1.py',
        'tests/test_cara_s_endpoint_gpu_dispatch_r1.py'}
    differences={n for n,h in icap['registration']['payload_sha256'].items() if payload.get(n)!=h}
    assert differences<=affected_after_interfaces
    assert all(payload[n]==records[FINAL][1]['registration']['payload_sha256'][n] for n in differences)
    card,bound,proposal=[read(n) for n in (CARD,BINDING,PROPOSAL)]
    assert card==request_card(proposal,bound,load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'))
    assert len(card['physical_matrix'])==46 and len(card['formal_matrix'])==28 and bound['counts']['unique_new_scoring_pairs']==16
    selected=read('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    assert card['physical_matrix']==selected['physical_matrix']
    assert all(card['roles'][s['role']]==selected['roles'][s['role']] for s in card['physical_matrix'])
    assert proposal['selected_manifest_scope_sha256']==numeric['scope_sha256'] and numeric['actual_frozen_policy_routes_accepted']
    assert interfaces['actual_complete_synthetic_pairs']==16 and interfaces['original_rows_reused_unchanged']==12
    assert len(expected_sources(proposal,read(ORIGINAL_SCORES)))==16
    storage=read(STORAGE); io=read(IO)
    assert sha(ROOT/storage['capture_ref'])==storage['capture_sha256'] and sha(ROOT/io['capture_ref'])==io['capture_sha256']
    assert storage['storage_contract']['image_bytes']==64*2**30 and storage['helper_sha256']==payload['src/wcomr/history104_storage_r2.py']
    assert storage['independent_storage_observation']['journal_pristine'] and not storage['independent_storage_observation']['output_children']
    refs=OLD+[NUMERIC,INTERFACES,FINAL,CENTRAL,STORAGE,IO,ASSETS]
    evidence={ref:sha(ROOT/ref) for ref in refs}
    proof=dict(status='ENDPOINT7_COMPOSED_WHOLE_CPU_ACCEPTED_NOT_GPU_AUTHORIZED',observed_unix=time.time(),
        passed=True,whole_card_CPU_accepted=True,selected_policy_affected_CPU_accepted=True,host='two_card',source_revision=revision,
        scope_sha256=card['scope_sha256'],endpoint_binding_sha256=bound['binding_sha256'],
        original_budget_freeze_sha256=bound['original_freeze_sha256'],payload_sha256=payload,
        runtime_source_sha256=reg['runtime_source_sha256'],execution_host_policy_sha256=POLICY_SHA256,
        required_hosts=['two_card'],required_host_whole_card_CPU_accepted=True,
        host_receipts={'two_card':dict(whole_card_CPU_accepted=True,scope_sha256=card['scope_sha256'],payload_sha256=payload,evidence_sha256=evidence)},
        evidence_sha256=evidence,physical_paths=46,logical_positions=28,new_scoring_pairs=16,reused_score_rows=12,
        RGB_identity_controls=13,clean_timing_paths=38,original_numeric46_rerun=False,old_experiment_videos_rescored=0,
        final_dispatch_analysis_controls=16,temporary_central_ledger_controls=13,
        changed_after_interfaces=sorted(differences),actual_new_private64_storage_accepted=True,
        unchanged_full93_private_IO_component_reused=True,new_volume_full93_IO_remeasured=False,
        acceptance_mode='ORIGINAL_COMPLETE_ROUTES_AND_COMPONENTS_PLUS_EXACT_AFFECTED_DELTA',
        real_Docker_GPU_lifecycle_exercised=False,GPU_model_execution_exercised=False,
        GPU_dispatch_ready=False,execution_authorized=False,GPU_submissions=0,ledger_written=False,four_card_contacted=False,
        fresh_dispatch_boundaries=['Single seven GPUh and card-specific original central ledger authority',
            'Current exact GPU/runtime/assets, sole-runner exclusivity and original intents',
            'Fresh private storage identity, original source videos and empty output',
            'Single authoritative cap226 ledger with old16.5 obligations retained'])
    plan=dict(status='ENDPOINT7_SOURCE_PLAN_NO_GPU_AUTHORITY',overlay_sha256=payload,
        base_registration_sha256=cap['registration_sha256'],base_source_revision=revision,
        base_revision_field='parent_git_revision',GPU_submissions=0,execution_authorized=False)
    archive=git_archive(ROOT,plan,revision)
    assert set(overlay_bytes(archive,plan))==set(payload)
    return proof,plan,reg,archive


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--package',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and not a.package.exists()
    proof,plan,reg,archive=compose();a.package.mkdir(mode=0o700)
    for name,value in [('source-plan.json',plan),('base-registration.json',reg)]:
        (a.package/name).write_text(json.dumps(value,indent=2)+'\n')
    (a.package/'source.tar.gz').write_bytes(archive)
    proof.update(package_ref=str(a.package),package_plan_sha256=encoded(plan),package_archive_sha256=hashlib.sha256(archive).hexdigest(),assembler_sha256=sha(__file__))
    with a.output.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=proof['status'],source_revision=proof['source_revision'],payload_files=len(proof['payload_sha256']))))

if __name__=='__main__':main()
