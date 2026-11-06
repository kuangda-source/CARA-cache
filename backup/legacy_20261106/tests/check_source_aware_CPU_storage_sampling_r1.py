"""Existing complete CPU sampler controls on the new storage-only owner."""
import ast
from pathlib import Path


def run(runtime,tensor_loader,artifact_root):
    path=Path(__file__).with_name('check_source_aware_current_birth_sampling_cpu_r2.py')
    source=path.read_text()
    before='source_aware_current_birth_sampling_r2 as working'
    after='source_aware_CPU_storage_sampling_r1 as working'
    if source.count(before)!=1:raise ValueError('Original current-birth CPU fixture binding changed')
    changed=source.replace(before,after)
    assert changed.replace(after,before)==source and ast.dump(ast.parse(changed.replace(after,before)))==ast.dump(ast.parse(source))
    namespace={'__name__':'CPU_storage_complete_fixture','__file__':str(path)}
    exec(compile(changed,__file__+'#storage-owner-only','exec'),namespace)
    value=namespace['run'](runtime,tensor_loader,artifact_root)
    changed_roundtrips=0
    for check in value['checks']:
        for request in check['receipt']['requests']:
            for row in request['paths']:
                if row['collect']=='SOURCE_RA':continue
                for roundtrip in row['P0_roundtrips']:
                    assert roundtrip['CPU_owned_storage_version']=='R1' and roundtrip['original_logical_cap_unchanged']
                    assert all(not g['GPU_measurement'] for g in roundtrip['serial_next_copy_guards'])
                    assert [g['stage'] for g in roundtrip['serial_next_copy_guards']]==['physical_restore','owned_restore']
                    assert roundtrip['owned_storage_inventory']['unique_GPU_storage_bytes']==0
                    changed_roundtrips+=1
    assert changed_roundtrips==896
    value['actual_CPU_backed_additional_roundtrips']=changed_roundtrips
    value['original_fixture_inverse_AST_equal']=True
    return value
