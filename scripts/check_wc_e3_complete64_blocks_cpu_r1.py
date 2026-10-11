"""Accepted CPU import adapter, with only the affected block fixture replaced."""
import ast
import hashlib
from pathlib import Path


BODY=r'''    try:
        value=module.run(args.runtime,own_loader,args.stage/'CPU-artifacts')
        good=[c for c in value['checks'] if c['status']=='PASS']
        bad=[c for c in value['checks'] if c['status']=='EXPECTED_FAILURE']
        assert len(good)==24 and len(bad)==4
        assert (value['successful_complete_CPU_paths'],value['writer_failure_attempted_CPU_paths'])==(64,12)
        assert (value['actual_complete_CPU_solver_updates'],value['actual_normal_CPU_CFG_calls'])==(2736,5472)
        assert (value['actual_all_tensors_reloaded'],value['actual_direct_guided36_and_final_comparisons'])==(2368,1184)
        assert (value['actual_CPU_storage_roundtrips'],value['path_semantic_mutation_refusals'],value['actual_truncation_refusals'])==(160,144,24)
        assert value['actual_original_and_CPU_persistence_pairing_passed']
        assert value['registered_GPU_scientific_scope']['complete_scientific_positions']==64
        assert not torch.cuda.is_initialized()
        value.update(status='E3_COMPLETE64_BLOCK_AFFECTED_CPU_PASS_NOT_REAL_GPU_OR_PRODUCTION_ADMISSION',
            CPU_wall_seconds=time.perf_counter()-started,payload_sha256=reg['payload_sha256'],
            actual_import_only_adapter=adapter,actual_UniPC_source_executed=True,
            explicit_synthetic_policy_and_Toy_weights=True,real_Cosmos_or_video_or_quality_or_clean_latency_claim=False,
            CUDA_initialized=False,GPU_submissions=0,CPU_driver_derivation_proof=DRIVER_PROOF)
        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status':'E3_BLOCK_AFFECTED_CPU_FAILED_NOT_SUBSET_SUCCESS','error':str(error),'error_type':type(error).__name__,
            'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\n')
        raise
'''


def main():
    original=(Path(__file__).resolve().parents[1]/'scripts/check_wc_a_p0_sampling_cpu_r2.py').read_text()
    start=original.index('    try:\n        value=module.run(')
    end=original.index("\n\nif __name__=='__main__':",start)
    old=original[start:end];changed=original[:start]+BODY.rstrip()+original[end:]
    before='tests/check_partial_mlp_guided_sampling_cpu_r1.py';after='tests/check_e3_complete64_block_sampling_cpu_r1.py'
    assert changed.count(before)==1;changed=changed.replace(before,after)
    inverse=changed.replace(after,before).replace(BODY.rstrip(),old)
    assert inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
    proof={'inverse_bytes_and_AST_equal':True,'explicit_driver_sites':2,
        'original_source_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'accepted_actual_import_only_adapter_and_owned_artifact_loader_preserved':True}
    namespace={'__name__':'E3_affected_block_CPU_driver','__file__':__file__,'DRIVER_PROOF':proof}
    exec(compile(changed,__file__+'#affected-block-CPU','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
