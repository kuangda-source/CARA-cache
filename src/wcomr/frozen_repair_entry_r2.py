"""Exact, reversible metadata import/path bindings of original N07 entries.

No original script is edited. The original request loop, leases, actual-wall
settlement, guardrails, sampling and post-processing bodies are preserved.
"""
import ast
import hashlib
from pathlib import Path

PRODUCTION_IMPORT = 'from wcomr.frozen_shared_production_r1 import '
REPAIR_IMPORT = 'from wcomr.frozen_repair180_r2 import '
ENTRIES = {
    'worker': ('scripts/run_wc_paper_N07_frozen_shared180_r1.py',
        'b852f4d11cec26992d7ab5428a10c85e4f2c490414fdbbc762e9e52e3ff27274'),
    'post': ('scripts/postprocess_wc_paper_N07_frozen_shared180_r1.py',
        '9a7632d4abea48371e152f6e0437ce782dc9337a23e78c4a2e1ebcf871198d15'),
    'supervisor': ('scripts/supervise_wc_paper_N07_frozen_shared180_r1.py',
        '26e57e5e3ad206706d5893d612669feb802a0bb431d2ed1075d93f468a2b8973'),
    'watcher': ('scripts/watch_wc_paper_N07_post_cpu_r1.py',
        '7a64d15608ecc756f14ed74f9cfb8da394b23574afbda24141798f04d016d600'),
}
WORKER = 'scripts/run_wc_paper_N07_refusal_repair180_r2.py'
POST = 'scripts/postprocess_wc_paper_N07_refusal_repair180_r2.py'
SUPERVISOR = 'scripts/supervise_wc_paper_N07_refusal_repair180_r2.py'
WATCHER = 'scripts/watch_wc_paper_N07_refusal_repair180_r2.py'
WRAPPERS = dict(worker=WORKER, post=POST, supervisor=SUPERVISOR, watcher=WATCHER)


def derive(stage, kind):
    stage = Path(stage); name, expected = ENTRIES[kind]
    raw = (stage / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('The original N07 entry changed: ' + name)
    source = raw.decode(); changed = source; edits = [(PRODUCTION_IMPORT, REPAIR_IMPORT, 1)]
    if kind == 'worker':
        edits.append(('from wcomr.frozen_shared_execution_r1 import execute, point',
            'from wcomr.frozen_guardrail_boundary_r2 import execute\n    from wcomr.frozen_shared_execution_r1 import point', 1))
        edits.append(("if point(method)['family'] != 'NATIVE': continue",
                      "if point(method)['family'] not in ('NATIVE', 'FIXED26'): continue", 1))
    elif kind == 'supervisor':
        edits.extend([('from wcomr.frozen_shared_cpu_acceptance_r1 import validate_bundle',
                       'from wcomr.frozen_repair_cpu_acceptance_r2 import validate_bundle', 1),
                      (ENTRIES['worker'][0], WORKER, 2)])
    elif kind == 'watcher':
        edits.append((ENTRIES['post'][0], POST, 1))
    for before, after, count in edits:
        if changed.count(before) != count or after in changed:
            raise ValueError('Exact declared entry metadata replacement required: ' + before)
        changed = changed.replace(before, after)
    restored = changed
    for before, after, count in reversed(edits):
        if restored.count(after) != count: raise ValueError('Ambiguous metadata inverse')
        restored = restored.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('An undeclared operation changed')
    compile(changed, name + '#refusal-repair-metadata-r2', 'exec')
    return changed, dict(original_entry=name, original_sha256=expected,
        replacement_count=sum(e[2] for e in edits), inverse_bytes_and_AST_equal=True,
        only_declared_metadata_imports_paths_and_CPU_guard_coverage_changed=True,
        original_stage_or_script_written=False)


def validate_all_entries(stage):
    return {kind: derive(stage, kind)[1] for kind in ENTRIES}


def execute_entry(entry, kind):
    entry = Path(entry).resolve(); stage = entry.parents[1]
    if entry != stage / WRAPPERS[kind]: raise ValueError('Unexpected independent repair entry path')
    source, _ = derive(stage, kind)
    namespace = {'__name__': 'independent_N07_refusal_repair_' + kind,
                 '__file__': str(entry), '__package__': None}
    exec(compile(source, str(stage / ENTRIES[kind][0]) + '#refusal-repair-metadata-r2', 'exec'), namespace)
    namespace['main']()
