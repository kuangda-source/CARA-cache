#!/usr/bin/env python3
"""Reuse the exact original CPU import guards for the registered complete88."""
import ast
import hashlib
import importlib.util
import inspect
from pathlib import Path
from textwrap import dedent

TEMPLATE_SHA256 = 'cdd6c1099227a195070f533136deab568b45b5097c3e5c17ef1368b99c70ec39'
REPLACEMENTS = (
    ('from wcomr.drop1_full18_r1 import CONFIG,METHODS,matrix,validate_contract,CPU_STATUS',
     'from wcomr.drop1_correction_window24_r1 import METHODS,matrix,validate_static_manifest,CPU_STATUS', 1),
    ("config=json.loads((args.stage/CONFIG).read_text());validate_contract(config)",
     "config=json.loads((args.stage/'manifests/wc_drop1_correction_window_full24_static_scope_20261018.json').read_text());validate_static_manifest(config,json.loads((args.stage/'configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json').read_text()))", 1),
    ("assert len(matrix([r['name'] for r in config['requests']]))==18",
     "assert len(matrix([r['name'] for r in config['requests']]))==24", 1),
    ('tests/check_drop1_full18_sampling_cpu_r1.py', 'tests/check_drop1_correction_window88_sampling_cpu_r1.py', 1),
    ('CPU-drop1-artifacts', 'CPU-drop1-window24-artifacts', 2),
    ("value['actual_CPU_paths']==56", "value['actual_CPU_paths']==88", 1),
    ("c['complete_CPU_paths']==28 and c['all36_clean_outputs_actions_video_equal']",
     "c['complete_CPU_paths']==44 and c['all36_audit_guided_controls'] and c['common_A1_A3_first21_guided_equal']", 1),
    ("args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\\n')",
     "value['unchanged_CPU_import_guard_template_sha256']=_TEMPLATE_SHA256\n        value['scope_replacements_reversibly_checked']=True\n        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\\n')", 1),
)


def adapted_main_source(template_source):
    if hashlib.sha256(template_source.encode()).hexdigest() != TEMPLATE_SHA256:
        raise ValueError('Exact original full56 CPU import-guard template required')
    tree = ast.parse(template_source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    original = dedent(ast.get_source_segment(template_source, node))
    changed = original
    for before, after, count in REPLACEMENTS:
        if changed.count(before) != count:
            raise ValueError('Registered CPU scope replacement is not unique: ' + before)
        changed = changed.replace(before, after)
    restored = changed
    for before, after, count in reversed(REPLACEMENTS):
        if restored.count(after) != count:
            raise ValueError('CPU import guards cannot be recovered exactly')
        restored = restored.replace(after, before)
    if restored != original or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(original)):
        raise ValueError('Only the declared complete88 scope changes are permitted')
    ast.parse(changed)
    return changed


def main():
    path = Path(__file__).with_name('check_wc_drop1_full18_cpu_r1.py')
    source = path.read_text()
    changed = adapted_main_source(source)
    spec = importlib.util.spec_from_file_location('original_bound_CPU_guard_template', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    namespace = dict(vars(module), _TEMPLATE_SHA256=TEMPLATE_SHA256)
    exec(compile(changed, str(Path(__file__)) + '#original-guards-complete88-scope', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
