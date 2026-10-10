"""Run the full128 driver with the phase fixture and explicit phase checks."""
import ast
import hashlib
from pathlib import Path


def main():
    p = Path(__file__).resolve().parents[1]/'scripts/check_wc_source_aware_sampling_cpu_r1.py'
    source = p.read_text()
    changes = [
        ('tests/check_source_aware_partial_sampling_cpu_r1.py',
         'tests/check_source_aware_phase_sampling_cpu_r1.py'),
        ('SOURCE_AWARE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL',
         'CREATION_PHASE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'),
        ("        good=[v for v in value['checks'] if v['status']=='PASS']",
         "        assert value['creation_phase_early_P_pairs']>0 and value['creation_phase_late_P_pairs']>0\n"
         "        assert value['P_birth_floor_and_only_D_reset_verified_in_all_success_histories']\n"
         "        good=[v for v in value['checks'] if v['status']=='PASS']"),
    ]
    changed = source
    for before,after in changes:
        assert changed.count(before) == 1
        changed = changed.replace(before,after)
    inverse = changed
    for before,after in reversed(changes):inverse = inverse.replace(after,before)
    assert inverse == source and ast.dump(ast.parse(inverse)) == ast.dump(ast.parse(source))
    namespace = {'__name__':'creation_phase_CPU_driver','__file__':__file__}
    exec(compile(changed,__file__+'#phase-fixture-and-checks','exec'),namespace)
    namespace['main']()


if __name__ == '__main__':main()
