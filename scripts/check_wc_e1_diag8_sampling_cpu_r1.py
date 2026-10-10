"""Keep the accepted CPU import/owned-loader adapter; run all E1 controls."""
import ast
import hashlib
from pathlib import Path


BODY=r'''    try:
        value=module.run(args.runtime,own_loader,args.stage/'CPU-artifacts')
        good=[c for c in value['checks'] if c['status']=='PASS']
        bad=[c for c in value['checks'] if c['status']=='EXPECTED_FAILURE']
        assert len(good)==8 and len(bad)==4
        assert value['successful_complete_CPU_paths']==16 and value['writer_failure_attempted_CPU_paths']==12
        assert value['actual_complete_CPU_solver_updates']==1008 and value['actual_normal_CPU_CFG_calls']==2016
        assert value['actual_guided_reloaded']==576 and value['actual_final_latents_reloaded']==16
        assert value['scope_mutation_refusals']==72 and value['arm_contract_refusals']==12
        assert value['actual_truncation_refusals']==8 and value['metadata_observer_events']==336
        assert value['original_CPU_and_cold_prefix_numerical_parity']
        assert {(c['arm'],c['flow']) for c in good}=={(a,f) for a in reg['CPU_scope']['arms'] for f in (False,True)}
        assert not torch.cuda.is_initialized()
        value.update(status='E1_DIAG8_COMPLETE_SAMPLING_CPU_PASS_NOT_REAL_GPU_CAPACITY',
            CPU_wall_seconds=time.perf_counter()-started,payload_sha256=reg['payload_sha256'],
            planned_scope=reg['CPU_scope'],actual_import_only_adapter=adapter,
            actual_UniPC_source_executed=True,explicit_synthetic_policy_parameters=True,
            real_Cosmos_or_video_or_quality_or_clean_latency_claim=False,
            CUDA_initialized=False,GPU_submissions=0,CPU_driver_derivation_proof=DRIVER_PROOF)
        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status':'E1_DIAG8_COMPLETE_CPU_SCOPE_FAILED_NOT_SUBSET','error':str(error),'error_type':type(error).__name__,
            'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\n')
        raise
'''


def main():
    original=(Path(__file__).resolve().parents[1]/'scripts/check_wc_a_p0_sampling_cpu_r2.py').read_text()
    start=original.index('    try:\n        value=module.run(')
    end=original.index("\n\nif __name__=='__main__':",start)
    old=original[start:end];changed=original[:start]+BODY.rstrip()+original[end:]
    before='tests/check_partial_mlp_guided_sampling_cpu_r1.py';after='tests/check_e1_memory_diagnostic_sampling_cpu_r1.py'
    assert changed.count(before)==1;changed=changed.replace(before,after)
    inverse=changed.replace(after,before).replace(BODY.rstrip(),old)
    assert inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
    proof={'inverse_bytes_and_AST_equal':True,'explicit_driver_sites':2,
        'original_source_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'accepted_import_only_adapter_and_owned_artifact_loader_preserved':True}
    namespace={'__name__':'E1_diag8_CPU_driver','__file__':__file__,'DRIVER_PROOF':proof}
    exec(compile(changed,__file__+'#complete-diagnostic-CPU','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
