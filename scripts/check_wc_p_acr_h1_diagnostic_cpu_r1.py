"""Derive the accepted actual-import CPU harness for new full H1 diagnostics.

All CUDA/download/weight-load prohibitions, exact actual module origins,
runtime/payload hashes and ordinary input adapters remain unchanged.
"""
from pathlib import Path


def main():
    path=Path(__file__).with_name('check_wc_source_phase_absolute_h1_cpu_r1.py')
    original=path.read_text()
    replacements=[
        ("'tests/check_source_phase_absolute_h1_sampling_cpu_r1.py'", "'tests/check_p_acr_h1_diagnostic_cpu_r1.py'",1),
        ('SOURCE_PHASE_ABSOLUTE_H1_TWO_FLOW_ALL48_AUDIT48_LEAN_CPU_PASS_NOT_GPU',
         'PA_FULL_H1_32_PATHS48_ORIGINS528_NONCOMMITTED_TRIALS_CPU_PASS_NOT_GPU',1),
        ("value['actual_CPU_paths']==96", "value['actual_CPU_paths']==32",1),
        ("c['complete_CPU_paths']==48", "c['complete_CPU_paths']==16",1),
    ]
    changed=original
    for old,new,count in replacements:
        if changed.count(old)!=count:raise ValueError('Pinned imported CPU harness site differs: '+old)
        changed=changed.replace(old,new)
    inverse=changed
    for old,new,count in reversed(replacements):
        if inverse.count(new)!=count:raise ValueError('CPU harness inverse is ambiguous')
        inverse=inverse.replace(new,old)
    if inverse!=original:raise ValueError('CPU harness changed beyond fixture/status/counts')
    # The legacy file uses a multiline __main__ block; avoid executing its
    # entry twice while preserving every statement of the main function.
    import ast
    tree=ast.parse(changed)
    tree.body=[n for n in tree.body if not isinstance(n,ast.If) or not ast.unparse(n.test)=="__name__ == '__main__'"]
    namespace={'__name__':'full_H1_PA_CPU_source_bound_harness','__file__':str(path)}
    exec(compile(ast.fix_missing_locations(tree),str(path)+'#PA-explicit-fixture-sites','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
