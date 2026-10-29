"""Complete S work inventory and explicitly unmeasured engineering allowances.

The source-exact complete-state protocol is retained. Synthetic CPU rates are
not GPU prices. Outputs remain proposals until the full GPU lifecycle/entry,
actual asset admission, original card authority and central envelope exist.
"""
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'plans/cara_next_stage_20261028/sq'
REPORT=ROOT/'reports/cara_sq_s_other_A6000_complete_quote_proposal_r2_20261029.json'


def main():
    evidence={}
    def read(name):
        raw=(ROOT/name).read_bytes();evidence[name]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
    def source(name):
        raw=(ROOT/name).read_bytes();evidence[name]=hashlib.sha256(raw).hexdigest();return ast.parse(raw)
    source('scripts/prepare_cara_sq_s_other_A6000_quote_r2.py')
    source('scripts/prepare_cara_sq_s_whole_quote_r1.py')
    source('src/wcomr/sq_s_model_entry_r1.py')
    source('src/wcomr/sq_s_runner_r1.py')
    identity=read('plans/cara_next_stage_20261028/sq/S_EXECUTION_IDENTITY_R1.json')
    setup=read('configs/f1_setup.json')
    if setup!=identity['model_setup'] or identity['setup_overrides']!={'keep_going':True,'worldcache_enabled':True}:
        raise ValueError('Original S/A32 inference setup identity differs')
    assets_ref='plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'
    assets=read(assets_ref)
    if len(assets['files'])!=20 or not any(r['digest']==identity['primary_checkpoint_sha256']
            and r['digest_kind']=='sha256' for r in assets['files']):
        raise ValueError('Compatible full model/auxiliary asset cohort missing')
    asset_contract=dict(schema='SQ_S_MODEL_AND_AUXILIARY_ASSET_MEMBERSHIP_R1',
        copied_source_ref=assets_ref,copied_source_sha256=evidence[assets_ref],
        same_frozen_setup_verified=True,S_execution_identity_sha256=identity['identity_sha256'],
        files=assets['files'],snapshot_links=assets['snapshot_links'],
        total_file_bytes=sum(r['bytes'] for r in assets['files']),primary_checkpoint_sha256=identity['primary_checkpoint_sha256'],
        fresh_full_digest_and_links_required_before_new_S_admission=True,
        actual_new_S_host_asset_acceptance=False,GPU_authority=False,GPU_submissions=0,ledger_writes=0)
    if read('plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json')!=asset_contract:
        raise ValueError('Original model/auxiliary asset membership changed')
    geometry=read('reports/cara_sq_s_complete_resource_geometry_r1_20261029.json')
    guard=read('reports/cara_sq_s_resource_guard_dual_cpu_accepted_r1_20261029.json')
    if guard['target_checks_per_host']!=216 or not guard['original_numerical_and_physical_sources_unchanged']:
        raise ValueError('Complete unchanged affected resource entry required')
    collection=source('src/wcomr/sq_s_collection_r1.py')
    observe=next(n for n in ast.walk(collection) if isinstance(n,ast.FunctionDef) and n.name=='observe')
    calls=[n for n in ast.walk(observe) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
    if sum(n.func.id=='restore_and_verify' for n in calls)!=2:
        raise ValueError('Two full original restoration/verifications per selected target required')
    if any(sum(n.func.id==name for n in calls)!=1 for name in ('CompleteStateRoundtrip','PolicyOwnerRoundtrip')):
        raise ValueError('One original post-state and owner snapshot per target required')
    for name in ('src/wcomr/sq_s_owner_roundtrip_r1.py','src/wcomr/full_sampling.py',
                 'src/wcomr/mid_prefix_audit.py','src/wcomr/mid_coverage.py',
                 'src/wcomr/sq_s_sources_r1.py','src/wcomr/sq_s_storage_r1.py',
                 'src/wcomr/sq_s_batch_r1.py','src/wcomr/policy_generator_r1/production_sampling.py'):
        source(name)
    real_contract=read('plans/cara_next_stage_20261028/sq/S_RESOURCE_GUARD_REAL_CONTRACT_R1.json')
    old=read('reports/cara_sq_s_resource_analytical_floor_r2_20261029.json')
    original_feature_bytes=127401984;latent=7962624
    visits=dict(selected_targets=108,extra_Dense_teacher_pairs=56,extra_C_shadow_pairs=52,
        physical_snapshots=108+56,physical_restores=2*108+56,
        post_physical_fingerprints=3*108,owner_snapshots_and_restores=3*108,
        owner_fingerprints=7*108,paired_input_fingerprints=3*108,past_source_fingerprints=3*108,
        raw_anchor_content_hashes=8*4,unique_tensor_files_hashed_after_write=8+24,
        approximate_protected_tensor_hash_calls=324*44+756*8+324*15+324*12,
        extra_shadow_hidden_head_replays=0)
    results={}
    from wcomr.policy_generator_r1.interval_grammar import Profile
    from wcomr.sq_s_batch_r1 import make_scope
    from wcomr.sq_s_physical_r1 import make_physical_scope
    profile=read('plans/cara_next_stage_20261028/sq/S_SUPPORT_RECONCILIATION_R2.json')['profile']
    for key in ('protected_dense','alpha_candidates'):profile[key]=tuple(profile[key])
    upper=make_scope(Profile(**profile))
    for host in ('two_card','four_card'):
        physical_ref=('plans/cara_next_stage_20261028/sq/S_PHYSICAL_TWO_CARD_OTHER_GPU_R2.json'
            if host=='two_card' else 'plans/cara_next_stage_20261028/sq/S_PHYSICAL_FOUR_CARD_R1.json')
        physical=read(physical_ref)
        if physical!=make_physical_scope(upper,host,identity['identity_sha256']):
            raise ValueError('R2 quotes require the exact all-new ten-role physical scope')
        counts=physical['counts'];new=counts['new_paths']
        if (counts['moment_rows'],counts['extra_Dense_teacher_pairs'],counts['extra_C_shadow_pairs'],
                counts['raw_states'],counts['unique_anchors'])!=(108,56,52,8,24):
            raise ValueError('Complete source-specific S physical counts changed')
        accepted=read(f'reports/cara_sq_s_host_cost_{host}_cpu_accepted_r1_20261029.json')
        raw=read(accepted['capture_ref'])
        if not accepted['passed'] or evidence[accepted['capture_ref']]!=accepted['capture_sha256']:
            raise ValueError('Original accepted CPU timing bytes changed')
        rates=accepted['conservative_observed_CPU_rates_bytes_per_second']
        digest_rate=rates['source_exact_tree_digest_including_finite_scan']
        clone_rate=min(rates['source_exact_data_record_CPU_clone'],rates['original_deepcopy_CPU_tensor'])
        serialization_rate=rates['original_torch_save_CPU_to_BytesIO_no_disk']
        cases={}
        for label,multiple in (('original_BF16_features',1),('conservative_FP32_features',2)):
            groups=geometry['projections'][label]['max_by_group_logical_bytes']
            feature=original_feature_bytes*multiple
            physical_state=groups['native']+groups['solver']+groups['buffers']+latent+32768
            owner_state=groups['calibrators']
            paired=groups['paired_inputs']+groups['conditions'];past=12*feature
            protected_hash=324*physical_state+756*owner_state+324*paired+324*past
            # Each raw artifact contains six large current/teacher features.
            # Its four inline anchors contain eight more before deduplication.
            raw_state=old['raw_state_known_tensor_bytes_lower_bound']+(multiple-1)*6*original_feature_bytes
            anchor=2*feature
            raw_CPU_conversion=8*(raw_state+4*anchor)
            tensor_payload=8*raw_state+24*anchor
            raw_content_hash=32*anchor
            guided=(36+1)*new*latent
            rgb=new*93*432*768*3
            CPU_hash=protected_hash+raw_content_hash+tensor_payload+guided+2*rgb+100*2**20
            GPU_to_CPU=protected_hash+raw_CPU_conversion+guided+4*rgb
            # Conservative reference-byte copies, including alias references.
            GPU_copy_and_compare=(164+272)*physical_state+324*owner_state+108*paired
            GPU_copy_and_compare+=(108*4+56*4+8*2)*feature+16*108*feature+8*56*feature
            GPU_copy_and_compare+=16*(counts['parent_Dense_pairs']+counts['parent_C_pairs'])*feature
            terms=dict(model_and_matrix_entry_control_allowance=15.,
                host_mode_admission_and_restoration_allowance=100.,
                container_startup_and_teardown_allowance=60.,allocation_release_allowance=180.,
                pinned_context_and_native_import_allowance=180. if host=='two_card' else 600.,
                full_model_and_auxiliary_loading_allowance=900.,fresh_source_asset_and_OFF_identity_allowance=300.,
                all_physical_C_or_D_pair_compute_allowance=counts['total_pairs']*12.,
                per_new_request_conditioning_guardrail_decode_allowance=new*60.,
                complete_protected_and_artifact_CPU_hash_work=CPU_hash/digest_rate,
                full_registered_GPU_to_CPU_transfer_allowance=GPU_to_CPU/2**30,
                per_hash_contiguous_materialization_allowance=protected_hash/(10*2**30),
                GPU_state_copy_and_equality_allowance=GPU_copy_and_compare/(10*2**30),
                raw_CPU_copy_conversion=raw_CPU_conversion/clone_rate,
                raw_tensor_serialization_CPU=tensor_payload/serialization_rate,
                private_SSD_tensor_write_reread_and_video_allowance=(2*tensor_payload+rgb)/(128*2**20),
                per_target_FP64_control_and_metadata_allowance=108*2.,
                per_tensor_hash_synchronization_allowance=visits['approximate_protected_tensor_hash_calls']*.005,
                independent_saved_video_decode_and_witness_allowance=new*30.)
            subtotal=math.fsum(terms.values());forecast=math.ceil(subtotal*1.25)/3600
            cases[label]=dict(work_bytes=dict(physical_state_reference_bytes=physical_state,
                owner_state_reference_bytes=owner_state,paired_input_reference_bytes=paired,
                past_source_reference_bytes=past,protected_fingerprint_byte_visits=protected_hash,
                raw_CPU_conversion_byte_visits=raw_CPU_conversion,tensor_serialized_payload_bytes=tensor_payload,
                CPU_hash_byte_visits_including_artifacts=CPU_hash,GPU_to_CPU_logical_byte_visits=GPU_to_CPU,
                GPU_copy_and_equality_logical_byte_visits=GPU_copy_and_compare),
                terms_GPU_held_wall_seconds=terms,subtotal_GPU_held_seconds=subtotal,
                failure_allowance_fraction=.25,forecast_complete_GPUh=forecast)
        # The Original resource schema permits FP32 cache tensors. Keep that complete
        # scenario visible in the planning envelope instead of pricing BF16 only.
        proposed_hard=math.ceil(cases['conservative_FP32_features']['forecast_complete_GPUh']*1.10)
        result=dict(schema='SQ_S_COMPLETE_ENGINEERING_ALLOWANCE_QUOTE_R2_FULL_OTHER_A6000',host=host,
            status='PROPOSAL_PENDING_COMPLETE_GPU_ENTRY_AND_FRESH_NATIVE_ADMISSION',physical_counts=counts,
            physical_scope_ref=physical_ref,physical_scope_sha256=physical['physical_scope_sha256'],upper_scope_sha256=physical['upper_scope_sha256'],
            S_execution_identity_sha256=identity['identity_sha256'],model_loads=1,timing_repeats=0,
            model_asset_contract_ref='plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json',
            model_asset_contract_sha256=hashlib.sha256((PLAN/'S_MODEL_ASSETS_R1.json').read_bytes()).hexdigest(),
            source_exact_successful_protocol_visit_counts=visits,cases=cases,
            primary_planning_case='conservative_FP32_features',
            forecast_complete_GPUh=cases['conservative_FP32_features']['forecast_complete_GPUh'],
            proposed_hard_limit_GPUh=proposed_hard,proposed_hard_limit_frozen=False,
            measurements=dict(host_CPUs=2,synthetic_feature_bytes=127401984,CPU_rates=rates,
                native_GPU_forward_or_transfer_price_measured=False,real_SSD_IO_price_measured=False),
            unmeasured_allowances=dict(per_C_or_D_pair_seconds=12.,GPU_to_CPU_bytes_per_second=2**30,
                GPU_copy_compare_bytes_per_second=10*2**30,private_SSD_bytes_per_second=128*2**20,
                cold_model_aux_import_and_request_costs='Explicit allowances, not observed native prices'),
            resources_proposed=dict(GPU_devices=1,host_CPUs=2,host_RAM_GiB=40,CUDA_allocator_fraction=.9,
                output_SSD_GiB=32,streaming_tensor_artifact_cap_GiB=28,artifact_file_GiB=2,journal_MiB=48,
                resource_contract_sha256=real_contract['contract_sha256'],physical_peak_measured=False),
            CPU_before_GPU=dict(CPUs_max=2,RAM_GiB_max=8,wall_seconds_max=7200,
                scope='Fresh original model/auxiliary/reused-OFF source assets and runtime; no model forward'),
            CPU_after_allocation_release=dict(CPUs_max=2,RAM_GiB_max=8,wall_seconds_max=3600,
                scope='Original artifact hashes/cohort and complete fixed risk-rule calculation; no GPU or partial selection'),
            source_evidence_sha256=dict(evidence),no_cross_hardware_timing_pooling=True,
            calibration_costs_are_separate_from_deployed_video_latency=True,
            complete_S_GPU_entry_CPU_accepted=False,whole_native_GPU_quote_accepted=False,
            GPU_authority=False,GPU_submissions=0,budget_reserved_GPUh=0,ledger_writes=0)
        results[host]=result
        filename='S_WHOLE_QUOTE_TWO_CARD_OTHER_GPU_R2.json' if host=='two_card' else 'S_WHOLE_QUOTE_FOUR_CARD_R2.json'
        result.update(prior_quotes_preserved=True,new_OFF_on_other_A6000=host=='two_card',
            model_entry_CPU_status='Local15_controls_only; native parser and full lifecycle still pending')
        with (PLAN/filename).open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    report=dict(status='S_ORIGINAL_COMPLETE_PROTOCOL_WORK_AND_ENGINEERING_ALLOWANCES_NOT_EXECUTION_AUTHORITY',
        asset_contract_ref='plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json',
        host_quotes={h:dict(ref='plans/cara_next_stage_20261028/sq/'+('S_WHOLE_QUOTE_TWO_CARD_OTHER_GPU_R2.json' if h=='two_card' else 'S_WHOLE_QUOTE_FOUR_CARD_R2.json'),
            expected_original_BF16_GPUh=q['cases']['original_BF16_features']['forecast_complete_GPUh'],
            permitted_FP32_scenario_GPUh=q['forecast_complete_GPUh'],proposed_hard_limit_GPUh=q['proposed_hard_limit_GPUh'])
            for h,q in results.items()},
        whole_S_quote_frozen=False,complete_S_GPU_entry_accepted=False,actual_S_labels=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with REPORT.open('x') as f:
        json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(report['host_quotes']))


if __name__=='__main__':main()
