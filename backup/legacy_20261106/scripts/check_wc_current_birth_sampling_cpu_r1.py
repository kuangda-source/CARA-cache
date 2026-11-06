"""Preserve the whole working-epoch driver and add current-P objective checks."""
import ast
from pathlib import Path


def main():
    path = Path('scripts/check_wc_working_epoch_sampling_cpu_r1.py')
    original = path.read_text()
    changes = [
        ('tests/check_source_aware_working_epoch_sampling_cpu_r1.py',
         'tests/check_source_aware_current_birth_sampling_cpu_r1.py'),
        ('WORKING_EPOCH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL',
         'CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'),
        ("    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))\n",
         "    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))\n"
         "    checks = '        assert value[\"additional_current_birth_mutation_refusals\"] == 12 and all(len(c[\"current_birth_mutation_refusals\"]) == 3 for c in good)\\n'\n"
         "    site = \"        assert value['creation_phase_early_P_pairs']>0 and value['creation_phase_late_P_pairs']>0\\n\"\n"
         "    assert changed.count(site)==1\n"
         "    changed=changed.replace(site, checks+site)\n")]
    changed = original
    for before, after in changes:
        if changed.count(before) != 1: raise ValueError('Pinned full256 CPU driver changed')
        changed = changed.replace(before, after)
    inverse = changed
    for before, after in reversed(changes): inverse = inverse.replace(after, before)
    if inverse != original or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(original)):
        raise ValueError('Full256 CPU driver changed outside current objective checks')
    namespace = {'__name__': 'current_birth_complete_CPU_driver', '__file__': str(path.resolve())}
    exec(compile(changed, __file__+'#current-birth-full256-driver', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__': main()
