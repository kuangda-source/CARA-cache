"""Compose the successor's complete evidence and review; grant no execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.immutable_stage_payload_r1 import git_archive,overlay_bytes
from wcomr.cara_budget_central_r1 import RUN,STAGES
from wcomr.cara_budget_runner_binding_r1 import SPEC


def main():
    read=lambda name:json.loads((ROOT/name).read_text())
    sha=lambda name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    def write(name,value):
        with (ROOT/name).open('x') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    old_ref='reports/cara_budget_two_card_whole_CPU_composed_r2_20261031.json'
    delta_ref='reports/cara_budget_successor_CPU_accepted_r2_20261031.json'
    closeout_ref='reports/cara_budget_single14_failed_settled_closeout_r1_20261031.json'
    storage_ref='reports/cara_budget_successor_storage_accepted_r1_20261031.json'
    old=read(old_ref);delta=read(delta_ref);closeout=read(closeout_ref);storage=read(storage_ref)
    assert closeout['evidence_sha256'][old_ref]==sha(old_ref)
    assert closeout['lifecycle_acceptance']['cost_settled'] and closeout['lifecycle_acceptance']['GPU_released']
    for name,expected in old['evidence_sha256'].items():assert sha(name)==expected,name
    with tempfile.TemporaryDirectory() as temporary:
        output=Path(temporary)/'rebuilt.json'
        subprocess.run([sys.executable,str(ROOT/'scripts/accept_cara_budget_successor_cpu_r2.py'),
            '--capture',delta['capture_ref'],'--launch',delta['launch_ref'],'--output',str(output)],cwd=ROOT,check=True,capture_output=True)
        rebuilt=json.loads(output.read_text())
    assert all(delta[k]==value for k,value in rebuilt.items() if k!='observed_unix')
    capture=read(delta['capture_ref'])['result'];reg=capture['registration'];payload=reg['payload_sha256']
    revision=reg['parent_git_revision']
    assert revision==delta['source_revision']
    assert payload=={**old['payload_sha256'],**delta['overlay_sha256']}
    assert reg['runtime_source_sha256']==old['runtime_source_sha256']
    assert all(sha(name)==expected for name,expected in payload.items())
    assert read(SPEC)['scope_sha256']==old['scope_sha256']
    for name in ('src/wcomr/cara_budget_calibration_r1.py','src/wcomr/cara_budget_search_r1.py',
                 'src/wcomr/cara_budget_rgb_objective_r1.py','src/wcomr/cara_fast_requests_r2.py'):
        assert payload[name]==old['payload_sha256'][name]
    assert storage['storage_contract']['run_id']==RUN and storage['original_storage_paths_not_reused']
    plan=dict(status='CALIBRATION_SUCCESSOR_SOURCE_PLAN_NO_GPU_AUTHORITY',overlay_sha256=payload,
        base_registration_sha256=capture['registration_sha256'],base_source_revision=revision,
        base_revision_field='parent_git_revision',GPU_submissions=0,execution_authorized=False)
    archive=git_archive(ROOT,plan,revision);assert len(overlay_bytes(archive,plan))==len(payload)
    package=ROOT/'.sync/cara-budget-successor-production-package-r1-20261031'
    assert not package.exists();package.mkdir(mode=0o700)
    for name,value in [('source-plan.json',plan),('base-registration.json',reg)]:
        (package/name).write_text(json.dumps(value,indent=2)+'\n')
    (package/'source.tar.gz').write_bytes(archive)
    refs=[old_ref,delta_ref,closeout_ref,storage_ref]
    evidence={**old['evidence_sha256'],**{name:sha(name) for name in refs}}
    proof=copy.deepcopy(old)
    proof.update(status='SUCCESSOR_WHOLE_CPU_COMPOSED_ACCEPTED_NO_GPU_AUTHORITY',observed_unix=time.time(),
        source_revision=revision,payload_sha256=payload,evidence_sha256=evidence,
        successor_control_chain_tests_passed=113,real_exec_handoff_accepted=True,
        previous_original_failed_settled_ref=closeout_ref,previous_GPU_authorization_reused=False,
        successor_storage_ref=storage_ref,successor_new_volume_full93_IO_remeasured=False,
        original_full_numeric_replayed=False,package_ref=str(package.relative_to(ROOT)),
        package_plan_sha256=hashlib.sha256((package/'source-plan.json').read_bytes()).hexdigest(),
        package_archive_sha256=hashlib.sha256(archive).hexdigest(),assembler_sha256=sha('scripts/assemble_cara_budget_successor_review_r1.py'))
    proof['host_receipts']['two_card'].update(payload_sha256=payload,evidence_sha256=evidence)
    proof_ref='reports/cara_budget_successor_whole_CPU_composed_r1_20261031.json';write(proof_ref,proof)
    quote=read('reports/cara_budget_two_card_whole_quote_r2_20261031.json')
    quote.update(source_revision=revision,observed_unix=time.time(),run_id=RUN,
        previous_actual_failure_GPUh=closeout['actual_GPUh'],previous_failure_is_separate_sunk_cost=True,
        new_card_has_full_scope_no_partial_resume=True,successor_storage_ref=storage_ref,
        original_full93_IO_component_reused=True,new_volume_full93_IO_remeasured=False)
    quote_ref='reports/cara_budget_successor_whole_quote_r1_20261031.json';write(quote_ref,quote)
    review=dict(status='SUCCESSOR_SINGLE14_COMPLETE_REVIEW_AWAITING_NEW_EXPLICIT_APPROVAL',
        run_id=RUN,launch_id=uuid.uuid4().hex,host='two_card',gpu_uuid=closeout['gpu_uuid'],
        stage='/data20t/gaokuangda/worldcache_workspace/.sync/'+STAGES['two_card'],source_revision=revision,
        scope_sha256=proof['scope_sha256'],purpose='Complete SA30 plus one HC20 sweep, 19D on two original FIT inputs; freeze one full-search strong baseline',
        physical_paths=112,candidate_queries=51,forecast_GPUh=quote['host_quotes']['two_card']['forecast_GPUh'],hard_GPUh=14,
        predecessor_launch_id=closeout['launch_id'],predecessor_run_id=closeout['run_id'],
        predecessor_cost_GPUh=closeout['actual_GPUh'],predecessor_settled=True,original_replay_allowed=False,
        new_card_approval_required=True,new_central_transaction_approval_required=True,
        proposed_central_operations='Only this successor reservation and final actual settlement in the original four-card ledger',
        four_card_GPU_experiments_allowed=False,ledger_migration_allowed=False,central_cap_GPUh=226,old_unknown_liability_GPUh=16.5,
        last_observed_available_GPUh=closeout['central_available_GPUh'],historical_balance_is_not_fresh_admission=True,
        whole_CPU_ref=proof_ref,whole_CPU_sha256=sha(proof_ref),whole_quote_ref=quote_ref,whole_quote_sha256=sha(quote_ref),
        storage_ref=storage_ref,storage_sha256=sha(storage_ref),source_package_ref=str(package.relative_to(ROOT)),
        planned_checks=dict(halfway_hours_after_actual_start=6.5,final_hours_after_actual_start=13.25,hard_limit_hours=14),
        remaining_dispatch_gates=['New explicit approval including this card central transactions','Published immutable source binding','Fresh original handles, assets, runtime, GPU exclusivity, memory, storage and central funds','Actual-start-bound halfway and final checks after unique launch'],
        execution_authorized=False,GPU_dispatch_ready=False,new_GPU_submissions=0,new_central_reservations=0)
    write('plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14GPUH_REVIEW_R1_20261031.json',review)
    print(json.dumps(dict(status=review['status'],run_id=RUN,launch_id=review['launch_id'],source_revision=revision,source_files=len(payload),forecast_GPUh=review['forecast_GPUh'])))


if __name__=='__main__':main()
