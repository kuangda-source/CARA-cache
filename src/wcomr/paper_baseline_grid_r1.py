"""Finite main-paper baseline grid; accepted executors and native step domains.

The native timing body is derived reversibly from the accepted clean executor.
Only its requested-step gate and final-update capture/count are parameterized.
WC, RA and both frozen candidates continue to call their accepted executors.
This module does not submit GPU work or decide that a production card passed.
"""
import ast
import copy
import hashlib
import inspect
import types
import weakref
from pathlib import Path
from textwrap import dedent

import torch

from . import clean_speed20_r1 as clean
from .simple26d_memory_r2 import collect_boundary

METHODS = (
    'NATIVE35', 'NATIVE26', 'NATIVE18',
    'WC_HALF', 'WC_DEFAULT', 'WC_DOUBLE',
    'RA_HALF', 'RA_DEFAULT', 'RA_DOUBLE',
    'A_NO_P', 'TABLE_PHASE_H1',
)
SCALES = {'HALF': .5, 'DEFAULT': 1., 'DOUBLE': 2.}
NATIVE_UPDATES = {35: 36, 26: 27, 18: 19}
LEGACY_SHA256 = '49ebb32a6f9afce64f223c435b2fd87090229de9c40708f8852999c35628637c'
RA_THRESHOLD = 0.070744235098772


def point(method):
    if method not in METHODS:
        raise ValueError('Finite preregistered eleven-point core grid required')
    if method.startswith('NATIVE'):
        steps = int(method.removeprefix('NATIVE'))
        return dict(method=method, family='NATIVE', requested_steps=steps,
                    actual_updates=NATIVE_UPDATES[steps], threshold=None)
    family = method.split('_')[0]
    threshold = ((.06 if family == 'WC' else RA_THRESHOLD)
                 * SCALES[method.split('_')[1]]) if family in ('WC', 'RA') else None
    return dict(method=method, family=family, requested_steps=35,
                actual_updates=36, threshold=threshold)


def matrix(scenes):
    if len(scenes) != 4 or len(set(scenes)) != 4:
        raise ValueError('All original four CAL requests required')
    result = []
    for repeat in (1, 2):
        order = METHODS if repeat == 1 else METHODS[::-1]
        for method in order:
            result.append(dict(id=f'warm_{repeat}_{method}', scene=scenes[0],
                               method=method, section='WARMUP', round=repeat))
    for i, scene in enumerate(scenes):
        for method in METHODS if i % 2 == 0 else METHODS[::-1]:
            result.append(dict(id=f'timed_{i}_{method}', scene=scene,
                               method=method, section='TIMED', round=1))
    return result


def compile_native_execute():
    """Four explicit reversible replacements, preserving guarded execution."""
    file = Path(clean.__file__)
    if (hashlib.sha256(file.read_bytes()).hexdigest() != LEGACY_SHA256
            or Path(clean.execute.__code__.co_filename).resolve() != file.resolve()):
        raise ValueError('Accepted clean executor source identity changed')
    source = dedent(inspect.getsource(clean.execute))
    replacements = (
        ('audit=False,save_video=True,CPU_native=None):',
         'audit=False,save_video=True,CPU_native=None,expected_updates=36):'),
        ('if method not in METHODS or sample.num_steps!=35 or not inference.rank0:',
         "if method!='NATIVE' or sample.num_steps not in (18,26,35) or expected_updates!=_NATIVE_UPDATES.get(sample.num_steps) or not inference.rank0:"),
        ("if result['solver_steps']==36:",
         "if result['solver_steps']==expected_updates:"),
        ("(result['solver_steps'],result['guided_pairs'])!=(36,36)",
         "(result['solver_steps'],result['guided_pairs'])!=(expected_updates,expected_updates)"),
    )
    changed = source
    for old, new in replacements:
        if changed.count(old) != 1:
            raise ValueError('Native adaptation origin is not unique: ' + old)
        changed = changed.replace(old, new)
    inverse = changed
    for old, new in reversed(replacements):
        if inverse.count(new) != 1:
            raise ValueError('Native adaptation is not reversible')
        inverse = inverse.replace(new, old)
    if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
        raise ValueError('Native adaptation changed an undeclared operation')
    namespace = {**vars(clean), '_NATIVE_UPDATES': NATIVE_UPDATES}
    exec(compile(changed, str(file) + '#paper-baseline-native-counts-r1', 'exec'), namespace)
    proof = dict(legacy_file_SHA256=LEGACY_SHA256, reversible_replacements=len(replacements),
                 inverse_bytes_and_AST_equal=True,
                 upstream_model_forward_or_sampler_changed=False)
    return namespace['execute'], proof


def execute(inference, sample, method, *, table_parameters, previous_parameters,
            settings, specs, **kwargs):
    """Run exactly one grid point with independent request-boundary cleanup."""
    p = point(method)
    if sample.num_steps != p['requested_steps'] or sample.seed != 0:
        raise ValueError('Requested steps and original CAL seed must match the grid point')
    if (settings.get('worldcache_rel_l1_thresh') != .06
            or specs['SOURCE_RA']['threshold'] != RA_THRESHOLD
            or previous_parameters['original_RA_threshold'] != RA_THRESHOLD):
        raise ValueError('Grid must start from the accepted WC/RA default settings')
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary guardrails required')
    original_settings = copy.deepcopy(settings)
    original_spec = dict(specs['SOURCE_RA'])
    selected_settings = dict(settings)
    selected_specs = dict(specs)
    if p['family'] == 'WC':
        selected_settings['worldcache_rel_l1_thresh'] = p['threshold']
    elif p['family'] == 'RA':
        selected_specs['SOURCE_RA'] = {**specs['SOURCE_RA'], 'threshold': p['threshold']}
    before = collect_boundary()
    refs = []
    installed_thresholds = []
    install = clean.install

    def observe_install(*args, **kw):
        components = install(*args, **kw)
        for component in components[1:]:
            if component is not None:
                refs.append(weakref.ref(component))
        actual = dict(mapped_method=args[1],
            net_WC_threshold=args[0].net.worldcache_rel_l1_thresh,
            spec_RA_threshold=args[8]['SOURCE_RA']['threshold'],
            controller_RA_threshold=getattr(getattr(components[2], 'controller', None), 'threshold', None))
        if p['family'] == 'WC' and actual['net_WC_threshold'] != p['threshold']:
            raise ValueError('Actual WC installation does not match the grid threshold')
        if p['family'] == 'RA' and actual['controller_RA_threshold'] != p['threshold']:
            raise ValueError('Actual RA controller does not match the grid threshold')
        installed_thresholds.append(actual)
        return components

    common = dict(settings=selected_settings, specs=selected_specs, **kwargs)
    counts = {'first_block_CFG': 0, 'last_block_CFG': 0}
    hooks = []
    derived = None
    try:
        with clean.patched(clean, 'install', observe_install):
            if p['family'] == 'NATIVE':
                net = inference.pipe.model.net

                def counter(key):
                    def observe(_module, _args):
                        if (inference.pipe.worldcache_enabled
                                or net.worldcache_enabled):
                            raise ValueError('Native path enabled WorldCache')
                        counts[key] += 1
                    return observe

                hooks = [net.blocks[0].register_forward_pre_hook(counter('first_block_CFG')),
                         net.blocks[-1].register_forward_pre_hook(counter('last_block_CFG'))]
                derived, proof = compile_native_execute()
                result = derived(inference, sample, 'NATIVE',
                                 expected_updates=p['actual_updates'], **common)
                result['native_count_adaptation'] = proof
                result['native_block_CFG_counts'] = counts.copy()
                if result['status'] != 'TEXT_REJECTED':
                    if any(n != p['actual_updates'] * 2 for n in counts.values()):
                        raise ValueError('Native did not run both branches through all blocks')
            elif p['family'] == 'WC':
                result = clean.execute(inference, sample, 'WC', **common)
            else:
                from .source_phase_absolute_h1_batch_r1 import execute as accepted_execute
                old_method = 'RA' if p['family'] == 'RA' else method
                result, _ = accepted_execute(inference, sample, old_method,
                    table_parameters=table_parameters, previous_parameters=previous_parameters, **common)
    finally:
        for hook in hooks:
            hook.remove()
        # A derived function owns a globals dictionary; release it before GC.
        derived = None
        after = collect_boundary()
    if any(ref() is not None for ref in refs):
        raise ValueError('Completed grid executor/readout/owner remains reachable')
    if settings != original_settings or specs['SOURCE_RA'] != original_spec:
        raise ValueError('A grid point mutated shared WC/RA settings')
    result.update(grid_bridge_method=result['method'], method=method,
        baseline_grid_point=p, installed_thresholds=installed_thresholds,
        request_memory_lifecycle=dict(version='BOUNDARY_GC_ONLY_BASELINE_GRID_R1',
            before=before, after=after, observed_components=len(refs), components_alive_after=0,
            within_request_algorithm_or_guardrails_changed=False,
            cleanup_excluded_from_core_seconds=True))
    return result
