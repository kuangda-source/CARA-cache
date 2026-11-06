#!/usr/bin/env python3
"""Publish-bound, single-dispatch Mac controller; all model bytes stay external."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def main():
    repo=Path.cwd()
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert source==subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],text=True).strip()
    recipe_ref=Path('manifests/wc_four_card_models_hybrid_r3_20261021.json')
    recipe=json.loads(recipe_ref.read_text())
    assert os.path.ismount('/Volumes/data')
    job=Path(recipe['job']);out=Path(recipe['launch_ref'])
    assert not job.exists() and not out.exists(),'Existing job or launch: restore original, never replay'
    L=json.loads(Path(recipe['parent_launch_ref']).read_text());old=Path(L['job'])
    parent_result=json.loads((old/'result.json').read_text())
    assert parent_result['status']=='AUTHORIZED_MODEL_RELAY_FAILURE_RETAINED'
    failure=json.loads(Path(recipe['parent_failure_capture_ref']).read_text())
    nonacceptance=json.loads(Path(recipe['parent_nonacceptance_ref']).read_text())
    assert nonacceptance['complete96_accepted'] is False and all(nonacceptance['checks'].values())
    assert nonacceptance['capture_sha256']==sha(recipe['parent_failure_capture_ref'])
    assert failure['manifest_sha256']==L['manifest_sha256'] and failure['original_process_live'] is False
    assert subprocess.run(['ps','-p',str(L['identity']['pid']),'-o','pid='],capture_output=True).returncode!=0
    assert sha(old/'worker.py')==L['worker_sha256'] and sha(old/'manifest.json')==L['manifest_sha256']
    old_m=json.loads((old/'manifest.json').read_text())
    paths={'worker.py':'scripts/relay_wc_four_card_models_hybrid_r3.py','server-worker.py':'scripts/prepare_wc_four_card_modelscope_hybrid_r3.py','resume_r2.py':'scripts/relay_wc_four_card_frozen_models_resume_r2.py','legacy_relay.py':'scripts/relay_wc_four_card_frozen_models_r1.py'}
    for path in list(paths.values())+[str(recipe_ref)]:
        assert subprocess.check_output(['git','show',source+':'+path])==Path(path).read_bytes(),'Actual payload differs from published GitHub source'
    ids=lambda a:[a['repo_id'],a['path'],a['digest']]
    complete=[ids(a) for a in parent_result['verified_files']]
    missing=[ids(a) for a in old_m['assets'] if ids(a) not in complete]
    assert len(complete)==86 and len(missing)==10
    seed_path=old/(old_m['assets'][86]['digest']+'.partial')
    assert not seed_path.is_symlink() and seed_path.stat().st_size==1132462080
    seed=dict(parent_path=str(seed_path),bytes=seed_path.stat().st_size,sha256=sha(seed_path),digest=old_m['assets'][86]['digest'])
    m=dict(recipe,assets=old_m['assets'],source_revision=source,parent_launch=L,
           worker_sha256=sha(paths['worker.py']),server_worker_sha256=sha(paths['server-worker.py']),
           legacy_helper_sha256=sha(paths['legacy_relay.py']),original_R2_worker_sha256=sha(paths['resume_r2.py']),
           allowed_missing_asset_identities=missing,parent_verified_asset_identities=complete,
           seeded_partial=seed,recipe_sha256=sha(recipe_ref))
    m['parent_failure_capture_sha256']=sha(recipe['parent_failure_capture_ref'])
    m['parent_nonacceptance_sha256']=sha(recipe['parent_nonacceptance_ref'])
    assert m['modelscope_assets']==[a for a in m['assets'] if a['repo_id']=='nvidia/Cosmos-Reason1-7B' and a['path'].startswith('model-000')]
    job.mkdir(mode=0o700)
    assert job.stat().st_dev==Path('/Volumes/data').stat().st_dev
    for dst,src in paths.items():shutil.copyfile(src,job/dst)
    (job/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    with (job/'controller-intent.json').open('x') as f:json.dump(dict(source_revision=source,manifest_sha256=sha(job/'manifest.json')),f)
    args=[sys.executable,str(job/'worker.py'),'--manifest',str(job/'manifest.json'),'--token-file',str(Path.home()/'.cache/codex-worldcache-hf-20261021/token'),'--hosts',str(repo/'configs/hosts.local.json'),'--control-record',str(repo/'.sync/four-card-bootstrap-transfer-20261020/owned-model-proxy-r4.json')]
    began=time.time()
    with (job/'console.private.log').open('xb') as log:
        os.chmod(log.name,0o600)
        child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=repo,start_new_session=True)
    ps=subprocess.run(['ps','-ww','-p',str(child.pid),'-o','lstart=,command='],capture_output=True,text=True)
    launch=dict(status='FIXED96_HYBRID_RESOURCE_R3_CONTROLLER_SINGLE_DISPATCHED',started_unix=began,identity=dict(pid=child.pid,ps_start_and_command=ps.stdout.strip()),job=str(job),server_job=m['server_job'],source_revision=source,worker_sha256=m['worker_sha256'],server_worker_sha256=m['server_worker_sha256'],legacy_helper_sha256=m['legacy_helper_sha256'],original_R2_worker_sha256=m['original_R2_worker_sha256'],manifest_sha256=sha(job/'manifest.json'),expected_files=96,expected_bytes=21358871258,allowed_missing_asset_identities=missing,seeded_partial=seed,parent_launch_ref=recipe['parent_launch_ref'],parent_failure_capture_ref=recipe['parent_failure_capture_ref'],parent_nonacceptance_ref=recipe['parent_nonacceptance_ref'],half_check_not_before_unix=began+recipe['planning_seconds']/2,final_check_not_before_unix=began+recipe['planning_seconds'],maximum_wall_seconds=m['maximum_wall_seconds'],resource_planning_seconds=m['planning_seconds'],server_maximum_wall_seconds=m['server_maximum_wall_seconds'],original_failed_jobs_and_partials_retained=True,credentials_restricted_to_Mac=True,token_exported_to_server=False,external_mount='/Volumes/data',local_model_bytes_on_internal_disk=0,GPU_submissions=0,ledger_written=False,CUDA_initialized=False,model_weights_loaded=0,GPU_dispatch_ready=False)
    with out.open('x') as f:json.dump(launch,f,indent=2);f.write('\n')
    print(json.dumps({k:launch[k] for k in ['status','started_unix','identity','source_revision','half_check_not_before_unix','final_check_not_before_unix','GPU_submissions']}))


if __name__=='__main__':main()
