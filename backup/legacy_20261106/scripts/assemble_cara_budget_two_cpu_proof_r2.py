"""Extend the accepted full CPU proof by the exact prelaunch repair delta."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.immutable_stage_payload_r1 import git_archive,overlay_bytes
from wcomr.cara_budget_central_r1 import STAGES
from wcomr.cara_budget_runner_binding_r1 import SPEC


def main():
    old_ref='reports/cara_budget_two_card_whole_CPU_composed_r1_20261031.json'
    delta_ref='reports/cara_budget_prelaunch_fix_CPU_accepted_r1_20261031.json'
    old=json.loads((ROOT/old_ref).read_text());delta=json.loads((ROOT/delta_ref).read_text())
    assert (ROOT/old_ref).read_bytes()==subprocess.check_output(['git','show','9478933263a6f8530cc2efee2824e481d04f5e96:'+old_ref],cwd=ROOT)
    for name,expected in old['evidence_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)/'rebuilt.json'
        subprocess.run([sys.executable,str(ROOT/'scripts/accept_cara_budget_prelaunch_fix_cpu_r1.py'),
            '--capture',delta['capture_ref'],'--launch',delta['launch_ref'],'--output',str(out)],cwd=ROOT,check=True,capture_output=True)
        rebuilt=json.loads(out.read_text())
    assert all(delta[k]==v for k,v in rebuilt.items() if k!='observed_unix')
    cap=json.loads((ROOT/delta['capture_ref']).read_text())['result'];reg=cap['registration']
    payload=reg['payload_sha256'];revision=reg['parent_git_revision']
    assert revision==delta['source_revision']=='8a4eb813e5122cc450d980be45d4c3816ad9b4ae'
    assert payload=={**old['payload_sha256'],**delta['overlay_sha256']}
    assert reg['runtime_source_sha256']==old['runtime_source_sha256']
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected for name,expected in payload.items())
    assert json.loads((ROOT/SPEC).read_text())['scope_sha256']==old['scope_sha256']
    plan=dict(status='CALIBRATION_SOURCE_PLAN_NO_GPU_AUTHORITY',overlay_sha256=payload,
        base_registration_sha256=cap['registration_sha256'],base_source_revision=revision,
        base_revision_field='parent_git_revision',GPU_submissions=0,execution_authorized=False)
    archive=git_archive(ROOT,plan,revision);assert len(overlay_bytes(archive,plan))==len(payload)
    package=ROOT/'.sync/cara-budget-two-card-production-package-r2-20261031';assert not package.exists();package.mkdir(mode=0o700)
    for name,value in [('source-plan.json',plan),('base-registration.json',reg)]:
        (package/name).write_text(json.dumps(value,indent=2)+'\n')
    (package/'source.tar.gz').write_bytes(archive)
    proof=copy.deepcopy(old);evidence={**old['evidence_sha256'],old_ref:hashlib.sha256((ROOT/old_ref).read_bytes()).hexdigest(),delta_ref:hashlib.sha256((ROOT/delta_ref).read_bytes()).hexdigest()}
    proof.update(status='COMPOSED_TWO_CARD_WHOLE_CPU_R2_ACCEPTED_NOT_GPU_DISPATCHED',observed_unix=time.time(),source_revision=revision,payload_sha256=payload,evidence_sha256=evidence,prelaunch_repair_delta_controls=81,registered_project_alias_CPU_accepted=True,original_full_numeric_replayed=False,package_ref=str(package.relative_to(ROOT)),package_plan_sha256=hashlib.sha256((package/'source-plan.json').read_bytes()).hexdigest(),package_archive_sha256=hashlib.sha256(archive).hexdigest(),assembler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    proof['host_receipts']['two_card'].update(payload_sha256=payload,evidence_sha256=evidence)
    output=ROOT/'reports/cara_budget_two_card_whole_CPU_composed_r2_20261031.json';assert not output.exists();output.write_text(json.dumps(proof,indent=2)+'\n')
    quote=json.loads((ROOT/'reports/cara_budget_two_card_whole_quote_r1_20261031.json').read_text());quote.update(source_revision=revision,observed_unix=time.time(),prelaunch_engineering_repair_does_not_change_numeric_cost_scope=True)
    output=ROOT/'reports/cara_budget_two_card_whole_quote_r2_20261031.json';assert not output.exists();output.write_text(json.dumps(quote,indent=2)+'\n')
    auth_ref='plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14GPUH_USER_AUTHORIZATION_20261031.json'
    authority=json.loads((ROOT/auth_ref).read_text());authority.update(status='APPROVED_SINGLE_CARD_EXECUTION_BINDING_R2_AFTER_PRELAUNCH_CPU_REPAIR',source_revision=revision,stage='/data20t/gaokuangda/worldcache_workspace/.sync/'+STAGES['two_card'],original_user_authorization_ref=auth_ref,original_user_authorization_sha256=hashlib.sha256((ROOT/auth_ref).read_bytes()).hexdigest(),prelaunch_repair_CPU_ref=delta_ref,original_scope_budget_launch_id_preserved=True,previous_prelaunch_authority_must_be_retired=True)
    output=ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14GPUH_EXECUTION_BINDING_R2_20261031.json';assert not output.exists();output.write_text(json.dumps(authority,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=proof['status'],source_revision=revision,payload_files=len(payload),launch_id=authority['launch_id'],stage=authority['stage'])))


if __name__=='__main__':main()
