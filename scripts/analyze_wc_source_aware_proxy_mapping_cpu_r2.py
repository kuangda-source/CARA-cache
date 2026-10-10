"""Read-only receipt-schema repair; the complete numerical protocol is unchanged."""
import ast
from pathlib import Path


def main():
    path=Path('scripts/analyze_wc_source_aware_proxy_mapping_cpu_r1.py')
    original=path.read_text()
    changes=[('wc_source_aware_proxy_mapping_cpu_r1_preregistration_20261010.json',
              'wc_source_aware_proxy_mapping_cpu_r2_preregistration_20261010.json'),
        ("assert proof['independent_source_complete_results_and_actual_artifact_hashes_verified']",
         "assert proof['independent_checks']['success'] and proof['independent_checks']['complete_8_parent_8_origin_6_mode_reconstruction'] and proof['independent_checks']['all_real_Linear_rows_source_and_full_group_repetitions_verified']")]
    changed=original
    for before,after in changes:
        assert changed.count(before)==1
        changed=changed.replace(before,after)
    recovered=changed
    for before,after in reversed(changes):
        assert recovered.count(after)==1
        recovered=recovered.replace(after,before)
    assert recovered==original and ast.dump(ast.parse(recovered))==ast.dump(ast.parse(original))
    namespace={'__name__':'readonly_proxy_mapping_r2','__file__':str(path.resolve())}
    exec(compile(changed,'proxy_mapping_r2_receipt_schema','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
