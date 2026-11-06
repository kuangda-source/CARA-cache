"""Execute the new dynamic CPU scope with the accepted import-only adapter."""
import ast
import hashlib
from pathlib import Path


BODY="    try:\n        value=module.run(args.runtime,own_loader,args.stage/'CPU-artifacts')\n        good=[v for v in value['checks'] if v['status']=='PASS']\n        bad=[v for v in value['checks'] if v['status']=='EXPECTED_FAILURE']\n        assert len(good)==len(bad)==4 and {v['flow'] for v in good}=={False,True}\n        assert all(v['actual_tensor_audit']['actual_guided_reloaded']==1152\n            and v['actual_tensor_audit']['actual_latents_reloaded']==32\n            and v['actual_tensor_audit']['full_GEMM_partial_trajectory_references']==4\n            and v['actual_tensor_audit']['original_RA_trajectory_references']==4\n            and v['actual_tensor_audit']['A_OFF_trajectory_references']==4\n            and len(v['actual_tensor_audit']['files'])==32 and len(v['mutation_refusals'])==8\n            and v['actual_artifact_truncation_refused'] and v['actual_P_pairs']>0\n            and v['P_source_C_pairs']>0 and v['consecutive_P_pairs']>0\n            and v['actual_A_extra_heads']>0 and v['original_RA_policy_comparisons']==144 for v in good)\n        assert all(v['complete_scope_retained'] and v['initial_full_state_restored']\n            and v['installed_MLP_methods_restored'] for v in bad)\n        assert {(c['working_epoch_strategy'],c['flow']) for c in good}=={(s,f) for s in reg['CPU_scope']['working_epoch_strategies'] for f in (False,True)}\n        assert all(len(c['working_epoch_mutation_refusals'])==3 for c in good)\n        assert value['P_birth_floor_and_actual_D_history_preserved'] and value['explicit_P_source_transfer_queries']>0\n        assert value['creation_phase_early_P_pairs']>0 and value['creation_phase_late_P_pairs']>0\n        assert not torch.cuda.is_initialized()\n        value.update(status='WORKING_EPOCH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL',\n            CPU_wall_seconds=time.perf_counter()-started,planned_scope=reg['CPU_scope'],\n            payload_sha256=reg['payload_sha256'],actual_import_only_adapter=adapter,\n            complete_successful_paths=128,complete_executed_paths_including_final_writer_failure=256,\n            actual_complete_solver_updates=9216,actual_normal_net_calls=18432,\n            actual_guided_reloaded=4608,actual_latents_reloaded=128,actual_all_tensors_reloaded=4736,\n            actual_truncation_refusals=4,mutation_refusals=32,working_epoch_mutation_refusals=12,last_parent_writer_failure_controls=4,\n            successful_additional_and_physical_checkpoint_roundtrips=1024,\n            actual_UniPC_source_executed=True,explicit_synthetic_policy_parameters=True,\n            real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim=False,\n            CUDA_initialized=False,GPU_submissions=0,CPU_driver_derivation_proof=DRIVER_PROOF)\n        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\\n')\n        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))\n    except BaseException as e:\n        args.output.with_suffix('.failure.json').write_text(json.dumps({\n            'status':'COMPLETE_SCOPE_FAILED_NOT_SUBSET','error':str(e),'error_type':type(e).__name__,\n            'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\\n')\n        raise\n"


def main():
    source=(Path(__file__).resolve().parents[1]/'scripts/check_wc_a_p0_sampling_cpu_r2.py').read_text()
    start=source.index('    try:\n        value=module.run(')
    end=source.index("\n\nif __name__=='__main__':",start)
    old=source[start:end];changed=source[:start]+BODY.rstrip()+source[end:]
    before,after='tests/check_partial_mlp_guided_sampling_cpu_r1.py','tests/check_source_aware_working_epoch_sampling_cpu_r1.py'
    assert changed.count(before)==1;changed=changed.replace(before,after)
    inverse=changed.replace(after,before).replace(BODY.rstrip(),old)
    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))
    proof={'inverse_AST_equal':True,'explicit_driver_sites':2,
           'original_driver_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
           'original_import_only_adapter_and_owned_loader_preserved':True}
    namespace={'__name__':'source_aware_CPU_driver','__file__':__file__,'DRIVER_PROOF':proof}
    exec(compile(changed,__file__+'#dynamic-CPU-driver','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
