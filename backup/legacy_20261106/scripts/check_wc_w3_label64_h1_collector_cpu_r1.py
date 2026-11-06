"""Actual-import CPU harness for complete W3 CAD collection; no real weights."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest


def main():
    path=Path(__file__).with_name('check_wc_source_phase_absolute_h1_cpu_r1.py')
    original=path.read_text();changed=original
    replacements=[("'tests/check_source_phase_absolute_h1_sampling_cpu_r1.py'","'tests/check_w3_label64_h1_collector_cpu_r1.py'",1),
        ('SOURCE_PHASE_ABSOLUTE_H1_TWO_FLOW_ALL48_AUDIT48_LEAN_CPU_PASS_NOT_GPU',
         'W3_FULL_H1_72_CPU_PATHS288_ORIGINS864_CAD_TRIALS_NONCOMMITTING_CPU_PASS_NOT_GPU',1),
        ("value['actual_CPU_paths']==96","value['actual_CPU_paths']==72",1),
        ("c['complete_CPU_paths']==48","c['complete_CPU_paths']==36",1)]
    for old,new,count in replacements:
        if changed.count(old)!=count:raise ValueError('Original actual-import harness site changed: '+old)
        changed=changed.replace(old,new)
    inverse=changed
    for old,new,count in reversed(replacements):inverse=inverse.replace(new,old)
    if inverse!=original:raise ValueError('Harness changed outside fixture/status/counts')
    tree=ast.parse(changed);tree.body=[n for n in tree.body if not isinstance(n,ast.If) or ast.unparse(n.test)!="__name__ == '__main__'"]
    ns={'__name__':'W3_actual_import_full_CPU_harness','__file__':str(path)}
    exec(compile(ast.fix_missing_locations(tree),str(path)+'#W3-explicit-sites','exec'),ns);ns['main']()
    # The original CLI owns its output path; parse the same argv without
    # changing the actual-import or guarded execution body.
    import sys
    output=Path(sys.argv[sys.argv.index('--output')+1]);stage=Path(sys.argv[sys.argv.index('--stage')+1])
    result=json.loads(output.read_text())
    for module_name,filename,count,key in (
            ('W3_original_support_unit_CPU','test_w3_label64_original_support_r1.py',3,'original_support_guard_tests'),
            ('W3_native_cycle_unit_CPU','test_w3_label64_cycle_guard_r1.py',2,'exact_native_cycle_guard_tests')):
        spec=importlib.util.spec_from_file_location(module_name,stage/'tests'/filename)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        verdict=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        assert verdict.wasSuccessful() and verdict.testsRun==count
        result[key]=count
    result['W3_sampler_science_or_real_teacher_claim']=False
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
