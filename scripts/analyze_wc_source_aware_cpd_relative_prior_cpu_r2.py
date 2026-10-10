"""Read-only R2 repairs original proof-field schema; same complete ratio scope."""
import ast
from pathlib import Path


def main():
    original=Path('scripts/analyze_wc_source_aware_cpd_relative_prior_cpu_r1.py').read_text()
    changes=[("wc_source_aware_cpd_cpu_r1_preregistration_20261010.json",
              "wc_source_aware_cpd_cpu_r2_preregistration_20261010.json"),
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
    assert ast.dump(ast.parse(recovered))==ast.dump(ast.parse(original)) and recovered==original
    namespace={'__name__':'readonly_relative_prior_r2'}
    exec(compile(changed,'relative_prior_r2_proof_schema','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
