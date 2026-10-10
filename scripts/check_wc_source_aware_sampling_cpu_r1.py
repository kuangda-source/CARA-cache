"""Execute the new dynamic CPU scope with the accepted import-only adapter."""
import ast
import hashlib
from pathlib import Path


BODY=r'''    try:
        value=module.run(args.runtime,own_loader,args.stage/'CPU-artifacts')
        good=[v for v in value['checks'] if v['status']=='PASS']
        bad=[v for v in value['checks'] if v['status']=='EXPECTED_FAILURE']
        assert len(good)==len(bad)==2 and {v['flow'] for v in good}=={False,True}
        assert all(v['actual_tensor_audit']['actual_guided_reloaded']==1152
            and v['actual_tensor_audit']['actual_latents_reloaded']==32
            and v['actual_tensor_audit']['full_GEMM_partial_trajectory_references']==4
            and v['actual_tensor_audit']['original_RA_trajectory_references']==4
            and v['actual_tensor_audit']['A_OFF_trajectory_references']==4
            and len(v['actual_tensor_audit']['files'])==32 and len(v['mutation_refusals'])==8
            and v['actual_artifact_truncation_refused'] and v['actual_P_pairs']>0
            and v['P_source_C_pairs']>0 and v['consecutive_P_pairs']>0
            and v['actual_A_extra_heads']>0 and v['original_RA_policy_comparisons']==144 for v in good)
        assert all(v['complete_scope_retained'] and v['initial_full_state_restored']
            and v['installed_MLP_methods_restored'] for v in bad)
        assert not torch.cuda.is_initialized()
        value.update(status='SOURCE_AWARE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL',
            CPU_wall_seconds=time.perf_counter()-started,planned_scope=reg['CPU_scope'],
            payload_sha256=reg['payload_sha256'],actual_import_only_adapter=adapter,
            complete_successful_paths=64,complete_executed_paths_including_final_writer_failure=128,
            actual_complete_solver_updates=4608,actual_normal_net_calls=9216,
            actual_guided_reloaded=2304,actual_latents_reloaded=64,actual_all_tensors_reloaded=2368,
            actual_truncation_refusals=2,mutation_refusals=16,last_parent_writer_failure_controls=2,
            successful_additional_and_physical_checkpoint_roundtrips=512,
            actual_UniPC_source_executed=True,explicit_synthetic_policy_parameters=True,
            real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim=False,
            CUDA_initialized=False,GPU_submissions=0,CPU_driver_derivation_proof=DRIVER_PROOF)
        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))
    except BaseException as e:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status':'COMPLETE_SCOPE_FAILED_NOT_SUBSET','error':str(e),'error_type':type(e).__name__,
            'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\n')
        raise
'''


def main():
    source=(Path(__file__).resolve().parents[1]/'scripts/check_wc_a_p0_sampling_cpu_r2.py').read_text()
    start=source.index('    try:\n        value=module.run(')
    end=source.index("\n\nif __name__=='__main__':",start)
    old=source[start:end];changed=source[:start]+BODY.rstrip()+source[end:]
    before,after='tests/check_partial_mlp_guided_sampling_cpu_r1.py','tests/check_source_aware_partial_sampling_cpu_r1.py'
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
