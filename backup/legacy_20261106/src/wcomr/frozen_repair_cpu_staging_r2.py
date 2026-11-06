"""Reversible CPU-only staging/capture bindings of original N07 tools.

The installer still checks an immutable base, committed overlay and a fresh
stage. These tools cannot submit a GPU task or change the shared runtime.
"""
import ast
import hashlib
from pathlib import Path

ENTRIES = {
    'deploy': ('scripts/deploy_wc_paper_N07_production_cpu_r1.py',
        'a41a83442b547b899995f94795e41e86aef4b7a787f06ba804e4ace37e142823'),
    'capture': ('scripts/capture_wc_paper_N07_production_cpu_r1.py',
        'f2b73dbdd59c83a324cb5f965531ae0af4c776a3e97595d7488b3d5e2a733040'),
    'accept': ('scripts/accept_wc_paper_N07_production_cpu_r1.py',
        'f68a241e3111daad62600ad5f93ce2bae2571221c966a574c286f8648fb1bd7f'),
}
WRAPPERS = {
    'deploy': 'scripts/deploy_wc_paper_N07_repair_production_cpu_r2.py',
    'capture': 'scripts/capture_wc_paper_N07_repair_production_cpu_r2.py',
    'accept': 'scripts/accept_wc_paper_N07_repair_production_cpu_r2.py',
}
EXTRA_ENTRIES = tuple(WRAPPERS.values()) + (
    'scripts/run_wc_paper_N07_refusal_repair180_r2.py',
    'scripts/supervise_wc_paper_N07_refusal_repair180_r2.py',
    'scripts/watch_wc_paper_N07_refusal_repair180_r2.py',
    'scripts/postprocess_wc_paper_N07_refusal_repair180_r2.py',
    'scripts/run_wc_paper_N07_repair_production_cpu_bundle_r2.py')
EXTRA_FILES = (
    'src/wcomr/frozen_repair180_r2.py', 'src/wcomr/frozen_repair_cpu_acceptance_r2.py',
    'src/wcomr/frozen_guardrail_boundary_r2.py', 'tests/test_frozen_guardrail_boundary_r2.py',
    'tests/test_frozen_repair180_r2.py', 'tests/test_frozen_repair_cpu_acceptance_r2.py',
    'tests/test_frozen_repair_cpu_staging_r2.py',
    'tests/check_frozen_guardrail_boundary_sampling_cpu_r2.py',
    'scripts/check_wc_N07_refusal_boundary_full520_local_cpu_r2.py')


def derive(stage, kind):
    stage=Path(stage);name,expected=ENTRIES[kind];raw=(stage/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('Original CPU staging tool changed: '+name)
    source=raw.decode()
    if kind=='deploy':
        edits=[(
            'from wcomr.frozen_shared_production_r1 import CONFIG, sha, validate_contract, verify_sampling_sources',
            'from wcomr.frozen_shared_production_r1 import sha, verify_sampling_sources\n'
            '    from wcomr.frozen_repair180_r2 import CONFIG, validate_contract, validate_repair_proof\n'
            '    from wcomr.frozen_repair_entry_r2 import validate_all_entries',1),
            ('    numeric = verify_sampling_sources(ROOT, refs[\'shared_CPU_raw\'], refs[\'shared_CPU_acceptance\'])',
             '    numeric = verify_sampling_sources(ROOT, refs[\'shared_CPU_raw\'], refs[\'shared_CPU_acceptance\'])\n'
             '    validate_repair_proof(ROOT, config)\n    validate_all_entries(ROOT)',1),
            ('run_wc_paper_N07_production_cpu_bundle_r1.py','run_wc_paper_N07_repair_production_cpu_bundle_r2.py',3),
            ('expected_CPU_commands=6','expected_CPU_commands=9',1),
            ('N07_SHARED180_ACTUAL_PRODUCTION_CPU_SINGLE_DISPATCH','N07_REPAIR180_ACTUAL_PRODUCTION_CPU_SINGLE_DISPATCH',1)]
    elif kind=='capture':
        # The remote observer uses system python3, not the model environment.
        # Keep it stdlib-only: the production module also imports Torch owners.
        edits=[('from wcomr.frozen_shared_production_r1 import CONFIG',
                "CONFIG = 'configs/wc_paper_N07_refusal_repair180_r2_20261016.json'",1),
            ('N07_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE','N07_REPAIR_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',1)]
    else:
        edits=[('from wcomr.frozen_shared_cpu_acceptance_r1 import accept','from wcomr.frozen_repair_cpu_acceptance_r2 import accept',1)]
    changed=source
    for before,after,count in edits:
        if changed.count(before)!=count:raise ValueError('CPU tool replacement count differs: '+before)
        changed=changed.replace(before,after)
    restored=changed
    for before,after,count in reversed(edits):
        if restored.count(after)!=count:raise ValueError('CPU tool inverse is ambiguous')
        restored=restored.replace(after,before)
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('An undeclared CPU staging operation changed')
    compile(changed,name+'#repair-cpu-staging-r2','exec')
    return changed,dict(original_entry=name,original_sha256=expected,
        replacement_count=sum(e[2] for e in edits),inverse_bytes_and_AST_equal=True,
        only_declared_repair_contract_paths_and_command_count_changed=True,
        original_stage_written=False,GPU_submissions=0)


def namespace(stage, kind):
    stage=Path(stage).resolve();source,proof=derive(stage,kind)
    values={'__name__':'independent_repair_CPU_'+kind,'__file__':str(stage/WRAPPERS[kind]),'__package__':None}
    exec(compile(source,str(stage/ENTRIES[kind][0])+'#repair-cpu-staging-r2','exec'),values)
    if kind=='deploy':
        # Explicit dynamic entry paths also belong to the immutable packet.
        values['ENTRIES']=list(dict.fromkeys(values['ENTRIES']+list(EXTRA_ENTRIES)+[p for p,_ in ENTRIES.values()]))
        values['TESTS']=list(dict.fromkeys(values['TESTS']+list(EXTRA_FILES)))
    return values,proof


def execute_entry(entry, kind):
    entry=Path(entry).resolve();stage=entry.parents[1]
    if entry!=stage/WRAPPERS[kind]:raise ValueError('Unexpected independent CPU staging entry')
    values,_=namespace(stage,kind);values['main']()
