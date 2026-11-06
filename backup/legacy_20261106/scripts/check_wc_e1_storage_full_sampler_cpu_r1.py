"""Reuses the whole accepted sampler fixture; only storage-owner binding changes."""
import ast
from pathlib import Path


def main():
    path=Path(__file__).with_name('check_wc_current_birth_sampling_cpu_r3.py')
    original=path.read_text()
    changes=[('tests/check_source_aware_current_birth_sampling_cpu_r2.py','tests/check_source_aware_CPU_storage_sampling_r1.py'),
        ('CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL','CPU_STORAGE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL')]
    changed=original
    for before,after in changes:
        if changed.count(before)!=1:raise ValueError('Frozen complete CPU driver derivation changed')
        changed=changed.replace(before,after)
    inverse=changed
    for before,after in reversed(changes):inverse=inverse.replace(after,before)
    assert inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
    namespace={'__name__':'E1_CPU_storage_complete_driver','__file__':str(path)}
    exec(compile(changed,__file__+'#storage-binding-only','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
