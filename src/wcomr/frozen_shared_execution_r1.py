"""Reusable seed-aware execution of accepted points; no final method selection.

The ongoing N05 modules and stage stay immutable. Two reversible seed gates
and per-request cache identity are adapted here; numerical executors, guards,
Native update counts, thresholds, fixed masks and readouts remain unchanged.
"""
import ast
from functools import lru_cache
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent
import weakref

from . import clean_speed20_r1 as clean
from . import paper_baseline_grid_r1 as grid
from . import simple26d_r1 as simple
from . import simple26d_memory_r2 as memory

AVAILABLE_METHODS = grid.METHODS + simple.METHODS
SEEDS = (0, 17, 43)
SOURCE_HASHES = {
    'paper_baseline_grid_r1.py': '65e001e5b31cede8c21ac997b19f36d3c31b17a0899dc5002cfd849d03da298b',
    'simple26d_r1.py': '7cf7cb6b321a9541f01e560cdde070e42dfd267612661078fc1df681ce4cb8a7',
}


def point(method):
    if method in grid.METHODS:
        return grid.point(method)
    if method not in simple.METHODS:
        raise ValueError('Only the seventeen accepted finite method configurations are available')
    plan = simple.plans()[method]
    return dict(method=method, family='FIXED26', requested_steps=35,
                actual_updates=36, threshold=None, dense_quota=26,
                corrected_reuses=plan.count('A'), plain_reuses=plan.count('C'))


def cache_context(context, name, seed):
    if (type(seed) is not int or seed not in SEEDS or len(context) != 3
            or not isinstance(name, str) or not name
            or not context[0].endswith(':' + name)):
        raise ValueError('Explicit registered seed and original three-part context required')
    if seed == 0:
        return context
    return (context[0] + ':seed' + str(seed), context[1], 'frozen-input-seed' + str(seed))


@lru_cache(maxsize=2)
def compile_seed_gate(kind):
    module, old = (grid, 'sample.seed != 0') if kind == 'GRID' else (simple, 'sample.seed!=0')
    if kind not in ('GRID', 'SIMPLE'):
        raise ValueError('Only the two accepted execution wrappers are adapted')
    path = Path(module.__file__)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_HASHES[path.name]:
        raise ValueError('Original accepted wrapper source changed')
    source = dedent(inspect.getsource(module.execute))
    new = 'sample.seed not in _FROZEN_SEEDS'
    if source.count(old) != 1:
        raise ValueError('Seed adaptation must replace exactly one original gate')
    changed = source.replace(old, new)
    inverse = changed.replace(new, old)
    if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
        raise ValueError('An undeclared numerical operation changed')
    namespace = {**vars(module), '_FROZEN_SEEDS': SEEDS}
    exec(compile(changed, str(path) + '#frozen-registered-seeds-r1', 'exec'), namespace)
    return namespace['execute'], dict(source_sha256=SOURCE_HASHES[path.name],
        replacements=1, inverse_bytes_and_AST_equal=True, allowed_seeds=list(SEEDS),
        thresholds_readouts_or_sampler_changed=False)


def matrix(cases, methods):
    """The unselected 8-prompt/two-seed/ten-method template, all 180 slots."""
    if (len(cases) != 16 or len({c['id'] for c in cases}) != 16
            or len(methods) != 10 or len(set(methods)) != 10
            or 'NATIVE35' not in methods
            or any(type(c['seed']) is not int for c in cases)):
        raise ValueError('Complete sixteen-case ten-method shared template required')
    prompts = {c['prompt_id'] for c in cases}
    if len(prompts) != 8:
        raise ValueError('Eight original prompt groups required')
    for prompt in prompts:
        if sorted(c['seed'] for c in cases if c['prompt_id'] == prompt) != [17, 43]:
            raise ValueError('Keep both original seeds for every prompt')
    for method in methods:
        point(method)
    rows = []
    for repeat in (1, 2):
        for method in methods if repeat == 1 else methods[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}', case_id=cases[0]['id'],
                             method=method, section='WARMUP', round=repeat))
    for index, case in enumerate(cases):
        for method in methods if index % 2 == 0 else methods[::-1]:
            rows.append(dict(id=f'formal_{index}_{method}', case_id=case['id'],
                             method=method, section='TIMED', round=1))
    return rows


def execute(inference, sample, method, *, table_parameters, previous_parameters,
            settings, specs, **kwargs):
    selected = point(method)
    if (type(sample.seed) is not int or sample.seed not in SEEDS
            or sample.num_steps != selected['requested_steps']):
        raise ValueError('Frozen seed/step identity must match the selected point')
    original_install = clean.install
    installed_contexts = []
    components = []

    def install_with_seed(model, mapped_method, context, *args, **kw):
        actual = cache_context(context, sample.name, sample.seed)
        value = original_install(model, mapped_method, actual, *args, **kw)
        installed_contexts.append(list(actual))
        components.extend(weakref.ref(c) for c in value[1:] if c is not None)
        return value

    proof_kind = 'GRID' if method in grid.METHODS else 'SIMPLE'
    adapted, proof = compile_seed_gate(proof_kind)
    try:
        with clean.patched(clean, 'install', install_with_seed):
            common = dict(table_parameters=table_parameters, previous_parameters=previous_parameters,
                          settings=settings, specs=specs, **kwargs)
            if proof_kind == 'GRID':
                result = adapted(inference, sample, method, **common)
            else:
                with clean.patched(simple, 'execute', adapted):
                    result = memory.execute(inference, sample, method, **common)
    finally:
        cleanup = memory.collect_boundary()
    if any(reference() is not None for reference in components):
        raise ValueError('Frozen request retained a live algorithm component')
    if not installed_contexts:
        raise ValueError('No actual executor installation was observed')
    if sample.seed != 0 and any(c[2] != 'frozen-input-seed' + str(sample.seed) for c in installed_contexts):
        raise ValueError('The installed cache identity belongs to a different seed')
    if 'timing_claim' in result:
        result['legacy_executor_timing_label'] = result['timing_claim']
    result.update(method=method, frozen_execution_point=selected,
        frozen_input_identity=dict(name=sample.name, actual_sample_seed=sample.seed,
            requested_steps=sample.num_steps, installed_contexts=installed_contexts),
        registered_seed_gate_proof=proof,
        frozen_request_cleanup=dict(components_observed=len(components), components_alive_after=0,
                                    collection=cleanup),
        timing_claim='SHARED_SINGLE_REQUEST_TIMER_NOT_REPEATED_SPEED_CLAIM',
        final_test_inputs_or_methods_selected_by_this_executor=False)
    return result
