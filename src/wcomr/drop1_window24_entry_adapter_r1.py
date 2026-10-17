"""Explicit reversible scope changes to immutable original production entries."""
import ast
import hashlib

RUNNER_SHA = '3a4aa59bc8559a82e43717bc7d04592a8a346e2812f209bd8f98243045a63b4c'
POST_SHA = 'c2b9feb6efd2a37584665488a70a8942f3bb0c99400febbf1a9c4fca9b727936'


def adapt(source, kind):
    expected = {'runner': RUNNER_SHA, 'post': POST_SHA}[kind]
    if hashlib.sha256(source.encode()).hexdigest() != expected:
        raise ValueError('Exact original whole18 source required before scope adaptation')
    imports = ('from wcomr.drop1_full18_r1 import',
               'from wcomr.drop1_window24_production_r1 import', 4 if kind == 'runner' else 5)
    replacements = [imports]
    if kind == 'runner':
        replacements += [
            ('production-CPU-result.json', 'window24-production-CPU-result.json', 2),
            ('drop1-sampling-CPU-result.json',
             'reports/wc_drop1_window88_actual_CPU_R1_collection_20261018_0220.json.gz', 1),
            ('sampling_CPU_sha256=', 'numerical_CPU_capture_sha256=', 1),
            ("'scientific_paths':11", "'formal_paths':15", 1),
            ("'billed_limit_GPUh':12.", "'billed_limit_GPUh':0.", 1),
            ("len(state['runs'])==18", "len(state['runs'])==24", 1),
            ('DROP1_INITIALIZING_SINGLE_RESIDENT_MODEL', 'WINDOW24_INITIALIZING_SINGLE_RESIDENT_MODEL', 1),
            ('DROP1_ALL18_FULL_PATHS_RUNNING', 'WINDOW24_ALL24_FULL_PATHS_RUNNING', 1),
            ('DROP1_ALL18_FULL12_SCIENCE_GPU_COMPLETE_CPU_AUDIT_PENDING',
             'WINDOW24_ALL24_FULL16_SCIENCE_GPU_COMPLETE_CPU_AUDIT_PENDING', 1),
            ('DROP1_TECHNICAL_STOP_FULL12_SCOPE_RETAINED', 'WINDOW24_TECHNICAL_STOP_FULL16_SCOPE_RETAINED', 1),
        ]
    else:
        start = source.index('        baseline_controls=[]\n')
        end = source.index('        guided_controls=[]\n', start)
        old = source[start:end]
        new = ("        from wcomr.drop1_window24_production_r1 import old_endpoint_controls,common_prefix_controls\n"
               "        baseline_controls=old_endpoint_controls(done,c,a.stage)\n"
               "        prefix_controls=common_prefix_controls(guided_by_id)\n")
        replacements += [
            (old, new, 1),
            ('DROP1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT', 'WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT', 1),
            ('DROP1_ALL18_RAW_AUDIT_RUNNING', 'WINDOW24_ALL24_RAW_AUDIT_RUNNING', 1),
            ('len(scored)==12', 'len(scored)==16', 1),
            ('len(done)==18', 'len(done)==24', 1),
            ('len(warm_controls)==3', 'len(warm_controls)==4', 1),
            ('len(baseline_controls)==4',
             "len(baseline_controls)==12 and len(prefix_controls)==2 and all(x['status'].startswith('PASS') for x in prefix_controls)", 1),
            ("len(runner['runs'])==18", "len(runner['runs'])==24", 1),
            ('len(memory_records)==18', 'len(memory_records)==24', 1),
            ('original_baseline_controls=baseline_controls,warm_guided_controls=guided_controls,',
             'original_baseline_controls=baseline_controls,warm_guided_controls=guided_controls,warm_common_prefix_controls=prefix_controls,', 1),
            ('DROP1_FULL12_SCIENCE_ALL18_AUDITED_93FRAME_SCORED', 'WINDOW24_FULL16_SCIENCE_ALL24_AUDITED_93FRAME_SCORED', 1),
            ('DROP1_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED',
             'WINDOW24_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED', 1),
            ('DROP1_CPU_AUDIT_TECH_FAILED_FULL12_RETAINED', 'WINDOW24_CPU_AUDIT_TECH_FAILED_FULL16_RETAINED', 1),
        ]
    changed = source
    for before, after, count in replacements:
        if changed.count(before) != count:
            raise ValueError('Scope substitution is not exact: ' + before[:120])
        changed = changed.replace(before, after)
    restored = changed
    for before, after, count in reversed(replacements):
        if restored.count(after) != count:
            raise ValueError('Cannot reverse the scope substitution exactly')
        restored = restored.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('Original physical execution and CPU/guardrail boundaries must be recoverable')
    ast.parse(changed)
    return changed
