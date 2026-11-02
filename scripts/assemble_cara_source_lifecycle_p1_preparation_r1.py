"""Compose source-bound accepted P1 CPU evidence; never run an old experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]

from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID,SCOPE_SHA256
from wcomr import cara_source_lifecycle_p1_runner_binding_r1 as binding
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr import cara_source_lifecycle_p1_result_bundle_r1 as bundle


def assemble():
    read=lambda n:json.loads((ROOT/n).read_bytes())
    sha=lambda n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    accepted_ref='reports/cara_v1_P1_final_CPU_accepted_r1_20261102.json'
    final=read(accepted_ref)
    assert final['status']=='ORIGINAL_P1_FINAL_EXPORT_PROFILE_PARENT_LINUX_CPU13_ACCEPTED_SYNTHETIC_ONLY'
    assert final['original_host_ended'] and final['tests_run']==13
    assert sha(final['capture_ref'])==final['capture_sha256']
    cap=read(final['capture_ref'])['result'];reg=cap['registration']
    assert cap['original_host_observation']['original_live'] is False and cap['host_terminal']['error'] is None
    assert cap['payload_intact'] and cap['runtime_intact']
    assert sha(final['original_proof_ref'])==final['original_proof_sha256']==cap['CPU_proof_sha256']
    payload,runtime=reg['payload_sha256'],reg['runtime_source_sha256']
    assert all(sha(n)==h for n,h in payload.items())
    assert set(binding.REQUIRED)|set(dispatch.REQUIRED)|set(bundle.SOURCES)<=set(payload)
    local_ref='reports/cara_v1_P1_final_packaged_local_CPU_r1_20261102.json';local=read(local_ref)
    assert local['status']=='EXACT_REGISTERED_P1_FINAL_PAYLOAD_ISOLATED_LOCAL14_PASS'
    assert local['tests_run']==14 and local['payload_sha256']==payload and not local['checkout_on_import_path']
    audit_ref='reports/cara_v1_P1_selected_core_source_reuse_audit_r1_20261102.json';audit=read(audit_ref)
    assert audit['selected_source_bindings']==35 and audit['all_selected_source_bindings_unchanged']
    evidence={accepted_ref:sha(accepted_ref),local_ref:sha(local_ref),audit_ref:sha(audit_ref)}
    reused={}
    for role,row in audit['groups'].items():
        old=read(row['accepted_ref'])
        assert sha(row['accepted_ref'])==row['accepted_sha256']
        assert sha(old['capture_ref'])==old['capture_sha256']
        assert sha(row['original_proof_ref'])==row['original_proof_sha256']
        original=read(row['original_proof_ref'])
        assert original['runtime_source_sha256']==runtime
        for name,identity in row['files'].items():
            assert identity['unchanged'] and identity['original']==original['payload_sha256'][name]==payload[name]==sha(name)
        evidence[row['accepted_ref']]=row['accepted_sha256']
        reused[role]=dict(source_revision=row['source_revision'],accepted_ref=row['accepted_ref'],
            source_sha256={n:v['original'] for n,v in row['files'].items()})
    entry_ref='reports/cara_v1_P1_entry_delta_CPU_accepted_r2_20261102.json';entry=read(entry_ref)
    assert entry['tests_run']==23 and entry['original_host_ended']
    assert sha(entry['capture_ref'])==entry['capture_sha256'] and sha(entry['original_proof_ref'])==entry['original_proof_sha256']
    old=read(entry['original_proof_ref'])
    entry_names=(*binding.REQUIRED,*dispatch.REQUIRED,*bundle.report.SOURCES,
        'scripts/cara_source_lifecycle_p1_container_r1.py','scripts/cara_source_lifecycle_p1_supervisor_worker_r1.py',
        'scripts/cara_source_lifecycle_p1_control_r1.py')
    for name in entry_names:
        if name!=binding.PROFILE:assert old['payload_sha256'][name]==payload[name]==sha(name)
    evidence[entry_ref]=sha(entry_ref)
    rendering_ref='reports/cara_v1_P1_actual_Linux_bundle_local_figures_CPU_r1_20261102.json';rendered=read(rendering_ref)
    assert rendered['status']=='P1_COMPLETE_ORIGINAL_BUNDLE_FIGURES_EXPORTED' and rendered['CPU_fixture_only']
    assert rendered['original_bundle_sha256']==final['portable_result_bundle_sha256']==sha(final['portable_result_bundle_ref'])
    assert rendered['binding']['source_sha256']=={n:payload[n] for n in bundle.SOURCES}
    directory=Path(rendered['directory']);assert all(hashlib.sha256((directory/n).read_bytes()).hexdigest()==h for n,h in rendered['files_sha256'].items())
    evidence[rendering_ref]=sha(rendering_ref)
    storage_ref='reports/cara_v1_P1_storage_accepted_r1_20261102.json';storage=read(storage_ref)
    assert storage['original_process_exited'] and storage['journal_pristine'] and storage['output_empty']
    assert sha(storage['capture_ref'])==storage['capture_sha256']
    assert storage['storage_contract']['run_id']==RUN_ID and storage['storage_contract']['image_bytes']==64*2**30
    evidence[storage_ref]=sha(storage_ref)
    profile=read(binding.PROFILE);binding.validate_profile(profile,SCOPE_SHA256)
    quote_ref='plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json';quote=read(quote_ref)
    assert profile['hard_GPUh']==quote['hard_GPUh']==19. and quote['profile_sha256']==sha(binding.PROFILE)
    assert quote['whole_quote_accepted'] and not quote['P1_GPU_authorized'] and not quote['snapshot_is_measured_V1_cost']
    evidence[quote_ref]=sha(quote_ref)
    supplemental=read(binding.RUNTIME_ENTRY)['files']
    release=read('reports/cara_v1_P1_release_Linux_CPU_original_proof_r3_20261102.json')
    assert release['supplemental_runtime_sha256']==supplemental
    return dict(schema='CARA_V1_P1_WHOLE_CPU_COMPOSED_R1',status='P1_SOURCE_BOUND_WHOLE_CPU_PREPARATION_ACCEPTED_NOT_GPU_ADMISSION',
        run_id=RUN_ID,source_revision=final['source_revision'],scope_sha256=SCOPE_SHA256,host='two_card',
        whole_card_CPU_accepted=True,payload_sha256=payload,runtime_source_sha256=runtime,
        supplemental_runtime_sha256=supplemental,execution_host_policy_sha256=POLICY_SHA256,
        required_hosts=['two_card'],required_host_whole_card_CPU_accepted=True,
        source_registration_sha256=final['registration_sha256'],source_CPU_stage=final['CPU_stage'],
        complete_algorithm_reused_source_bound=True,actual_host_FIT_broker_reused_source_bound=True,
        guardian_FIT_cleanup_reused_source_bound=True,production_total_entry_CPU_accepted=True,
        released_full146_reader_and_new32_scores_CPU_accepted=True,
        original_post_score_Docker_two_new_pairs_accepted=True,complete_report_once_freeze_Linux23_accepted=True,
        final_profile_quote_source_parent_Linux13_accepted=True,original_Linux_bundle_to_local_figures_accepted=True,
        original_private64_storage_accepted=True,evidence_sha256=evidence,reused_selected_core_sources=reused,
        component_counts=dict(algorithm33=33,guardian34=34,outer_post31=31,entry23=23,final13=13,local_package14=14),
        semantic_positions=146,physical_generation_upper=142,physical_model_pairs_upper=5176,
        internal_FIT_queries_upper=42,internal_FIT_metric_pairs_upper=84,postrelease_new_metric_pairs_upper=32,
        proposed_hard_GPUh=19.,forecast_GPUh=quote['forecast_GPUh'],
        real_GPU_container_exercised=False,real_Cosmos_video_or_V1_labels_accepted=False,scientific_accepted=False,
        execution_authorized=False,GPU_dispatch_ready=False,requires_fresh_production_admission=True,
        old_component_experiments_replayed=False,original_metric_pairs_recomputed=0,
        real_four_card_accessed=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists();proof=assemble()
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:proof[k] for k in ('status','whole_card_CPU_accepted','forecast_GPUh','proposed_hard_GPUh','execution_authorized')}))
