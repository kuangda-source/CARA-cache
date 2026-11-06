"""Per-path evidence from a terminal failed card; never whole-card acceptance.

Uses the frozen verifier's row-loop AST without executing sampler imports.
Card cardinality checks stay in their original verifier. This explicitly new
CPU scope retains all64 slots and does not synthesize missing prepare records.
"""
import ast
import copy
import hashlib
import math
from pathlib import Path

STRATEGIES = ('WORKING_P_AGE_KEEP_INTERVAL', 'WORKING_P_AGE_NONZERO_REBASE')
NAMES = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199',
         'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191')
METHODS = ('SOURCE_RA', 'DYNAMIC_NO_P', 'CPD', 'REF_CPD', 'A_CPD_OFF',
           'A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE', 'DENSE_CONTROL')
CHECK_SOURCES = ('source_aware_partial_sampling.py', 'source_aware_working_epoch_sampling_r1.py',
                 'source_aware_current_birth_sampling_r1.py', 'cfg_guided_w1_deployment.py',
                 'source_aware_current_birth_control_r1.py')


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def function(tree, name):
    values = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(values) != 1:
        raise ValueError('One original named verifier function required: '+name)
    return values[0]


def compile_function(node, namespace):
    module = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]))
    exec(compile(module, '<frozen-per-path-verifier>', 'exec'), namespace)
    return namespace[node.name]


def verifier(source_root, expected_sha256):
    root = Path(source_root)/'src/wcomr'
    texts = {}
    for name in CHECK_SOURCES:
        key = 'src/wcomr/'+name
        if sha_file(root/name) != expected_sha256[key]:
            raise ValueError('Frozen original verifier source changed: '+name)
        texts[name] = (root/name).read_text()
    alpha_tree = ast.parse(texts['cfg_guided_w1_deployment.py'])
    alpha = compile_function(function(alpha_tree, 'alpha_at'),
        {'METHODS': ('OFF', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE')})
    working = ast.parse(texts['source_aware_working_epoch_sampling_r1.py'])
    interval = compile_function(function(working, 'valid_P_interval'), {'STRATEGIES': STRATEGIES})
    rule_tree = ast.parse(texts['source_aware_current_birth_control_r1.py'])
    rule = next(ast.literal_eval(n.value) for n in rule_tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'CURRENT_BIRTH_RULE' for t in n.targets))
    base = function(ast.parse(texts['source_aware_partial_sampling.py']), 'verify_batch')
    request_loop = next(n for n in base.body if isinstance(n, ast.For))
    row_loop = next(n for n in request_loop.body if isinstance(n, ast.For))
    before = "p['accumulated_interval_proxy_after'] < p['decision']['state_before'][4]"
    original_loop = ast.unparse(row_loop)
    if original_loop.count(before) != 1:
        raise ValueError('Original interval verifier site differs')
    # Same single replacement as the frozen working-age module, no row checks removed.
    changed = original_loop.replace(before, "not valid_P_interval(p, d['working_epoch_strategy'])")
    changed_loop = ast.parse(changed).body[0]
    if ast.dump(ast.parse(changed.replace("not valid_P_interval(p, d['working_epoch_strategy'])", before))) != ast.dump(ast.parse(original_loop)):
        raise ValueError('Verifier changed outside the original working-interval adaptation')
    current = function(ast.parse(texts['source_aware_current_birth_sampling_r1.py']), 'verify_batch')
    working_function = function(working, 'verify_batch')
    node = ast.parse('def check(request, state):\n    pass').body[0]
    rows_assignment = next(n for n in request_loop.body if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == 'rows' for t in n.targets))
    node.body = [copy.deepcopy(rows_assignment), changed_loop]
    for fn in (working_function, current):
        # Exclude only calls to the full-card checker and its cardinality return.
        loop = next(n for n in fn.body if isinstance(n, ast.For))
        initializers = [n for n in fn.body[:fn.body.index(loop)]
                        if isinstance(n, ast.Assign) and not any(isinstance(t, ast.Name) and t.id == 'result' for t in n.targets)]
        node.body.extend(copy.deepcopy(initializers + [loop]))
    check = compile_function(node, {'METHODS': METHODS, 'STRATEGIES': STRATEGIES,
                                   'alpha_at': alpha, 'valid_P_interval': interval,
                                   'CURRENT_BIRTH_RULE': rule})

    def verify(row, strategy):
        if row.get('collect') not in METHODS or row.get('status') != 'COMPLETE_PARENT_PATH':
            raise ValueError('Only original completed method rows are path candidates')
        actions = row['actions']
        if len(actions) != 36 or any(a not in ('CC', 'PP', 'DD') for a in actions):
            raise ValueError('All36 original double-CFG actions required')
        if row['collect'] == 'DENSE_CONTROL' and actions != ['DD']*36:
            raise ValueError('Dense control did not execute all D')
        if [r['step'] for r in row['P0_roundtrips']] != [12, 30, 35, 36]:
            raise ValueError('Original four checkpoint boundaries required')
        if not math.isfinite(row['instrumented_parent_pipeline_wall_seconds']) or row['instrumented_parent_pipeline_wall_seconds'] < 0:
            raise ValueError('Finite nonnegative recorded cost required')
        d = row['collection_complete'].get('deployment')
        if d is not None and d['working_epoch_strategy'] != strategy:
            raise ValueError('Path source rule differs from registered slot')
        request = {'paths': [row]}
        check(request, {'requests': [request]})
        return True
    return verify, {'row_loop_original_AST_sha256': hashlib.sha256(ast.dump(row_loop).encode()).hexdigest(),
                    'original_per_row_checks_preserved': True, 'working_and_current_birth_history_loops_preserved': True,
                    'whole_card_cardinality_not_asserted': True,
                    'source_sha256': {n: expected_sha256[n] for n in expected_sha256 if n in ['src/wcomr/'+x for x in CHECK_SOURCES]}}


def slots(runner):
    if runner['planned_scope']['complete_paths'] != 64 or list(runner['batches']) != list(STRATEGIES):
        raise ValueError('Original full64 denominator and strategy order required')
    found = {}; requests = {}
    for strategy in STRATEGIES:
        for request in runner['batches'][strategy].get('requests', []):
            if request['sample_name'] not in NAMES or (strategy, request['sample_name']) in requests:
                raise ValueError('Unexpected or duplicate request in original partial receipt')
            requests[strategy, request['sample_name']] = request
            for index, row in enumerate(request['paths']):
                if index >= len(METHODS) or row['collect'] != METHODS[index]:
                    raise ValueError('Original method order differs in partial receipt')
                found[strategy, request['sample_name'], row['collect']] = (request, row, index)
    result = []
    for strategy in STRATEGIES:
        for name in NAMES:
            for method in METHODS:
                value = found.get((strategy, name, method))
                result.append({'strategy': strategy, 'sample_name': name, 'method': method,
                    'request_record': value[0] if value else None, 'row': value[1] if value else None,
                    'method_index': value[2] if value else None,
                    'written_complete': bool(value and value[1]['status'] == 'COMPLETE_PARENT_PATH')})
    return result


def compatibility(slot, reference):
    row = slot['row']; request = slot['request_record']; index = slot['method_index']
    prepared = request.get('prepared_input_calls', [])
    entry = prepared[index] if index < len(prepared) else None
    ref_entry = reference['prepared_input_calls'][0]
    checks = {'complete36_guided': len(row.get('guided_sha256', [])) == 36,
        'same_prepared_call_arguments': entry is not None and entry.get('request') == ref_entry['request'],
        'same_prepared_data': entry is not None and entry.get('prepared') == ref_entry['prepared'],
        'same_condition_fields_before': row.get('condition_fields_before') == reference['condition_fields_before'],
        'same_condition_fields_after': row.get('condition_fields_after') == reference['condition_fields_after'],
        'same_conditions_before': row.get('conditions_before') == reference['conditions_before'],
        'same_conditions_after': row.get('conditions_after') == reference['conditions_after'],
        'same_actual_solver_configuration': row.get('actual_raw_solver_configuration') == reference['actual_raw_solver_configuration'],
        'same_first_seven_dense_guided': row.get('guided_sha256', [])[:7] == reference['guided_sha256'][:7]}
    return {'compatible': all(checks.values()), 'checks': checks,
            'incompatible_fields': [k for k, value in checks.items() if not value],
            'prepared_evidence_available': entry is not None, 'missing_not_synthesized': entry is None}


def numerical_pairing(slot, reference, source_proof):
    strict = compatibility(slot, reference); row = slot['row']
    checks = dict(strict['checks'])
    masks = row.get('actual_condition_masks')
    zero_mask = (source_proof.get('zero_mask_gt_has_no_model_effect') is True
        and masks == reference.get('actual_condition_masks') and isinstance(masks, list) and len(masks) == 2
        and all(m.get('finite') is True and m.get('nonzero_elements') == 0
                and m.get('shape') == [1, 1, 24, 54, 96] for m in masks))
    changed_fields = []
    for suffix in ('before', 'after'):
        a = row.get('condition_fields_'+suffix); b = reference.get('condition_fields_'+suffix)
        fields_match = isinstance(a, list) and isinstance(b, list) and len(a) == len(b) == 2
        if fields_match:
            for left, right in zip(a, b):
                differences = [k for k in set(left)|set(right) if left.get(k) != right.get(k)]
                changed_fields += differences
                fields_match &= not differences or zero_mask and differences == ['gt_frames']
        checks['same_condition_fields_'+suffix] = bool(fields_match)
        # The full digest differs only if the verified component map differs at inactive gt_frames.
        checks['same_conditions_'+suffix] = bool(fields_match and (
            strict['checks']['same_conditions_'+suffix] or zero_mask))
    def solver(value):
        required = {'raw_values','raw_sha256','numerical_values','numerical_sha256','default_name_metadata'}
        if set(value) != required:
            return None
        raw = value['raw_values']; numerical = value['numerical_values']; names = value['default_name_metadata']
        if (not isinstance(raw, dict) or not isinstance(numerical, dict) or not isinstance(names, list)
                or any(type(x) is not str for x in names) or len(set(names)) != len(names)
                or names != raw.get('_use_default_values')
                or numerical != {k:v for k,v in raw.items() if k!='_use_default_values'}
                or primitive_digest(raw) != value['raw_sha256'] or primitive_digest(numerical) != value['numerical_sha256']):
            return None
        return {'numerical_values': numerical, 'numerical_sha256':value['numerical_sha256'],
                'default_name_set':sorted(names)}
    left_solver = solver(row['actual_raw_solver_configuration']); right_solver = solver(reference['actual_raw_solver_configuration'])
    checks['same_actual_solver_configuration'] = left_solver is not None and left_solver == right_solver
    return {'compatible': all(checks.values()), 'checks': checks,
        'incompatible_fields': [k for k, value in checks.items() if not value],
        'strict_original_verdict': strict, 'zero_mask_gt_normalization_applied': bool(changed_fields and zero_mask),
        'ignored_condition_fields': sorted(set(changed_fields)) if zero_mask else [],
        'solver_default_name_order_only_normalized': not strict['checks']['same_actual_solver_configuration'] and checks['same_actual_solver_configuration'],
        'prepared_evidence_available': strict['prepared_evidence_available'], 'missing_prepare_not_synthesized': not strict['prepared_evidence_available']}


def primitive_digest(value):
    """Original tree_digest bytes for serialized primitive solver values only."""
    h=hashlib.sha256()
    def walk(x):
        if isinstance(x, dict):
            for key in sorted(x):h.update(str(key).encode());walk(x[key])
        elif isinstance(x, (list, tuple)):
            h.update(type(x).__name__.encode())
            for v in x:walk(v)
        elif x is None or isinstance(x,(str,int,float,bool)):
            if isinstance(x,float) and not math.isfinite(x):raise ValueError('Nonfinite solver value')
            h.update(repr(x).encode())
        else:raise ValueError('Nonprimitive serialized solver configuration')
    walk(value);return h.hexdigest()


def zero_mask_proof(runtime, source_root, config):
    runtime, source_root = Path(runtime), Path(source_root)
    rf = 'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
    net = 'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py'
    dig = 'src/wcomr/mid_coverage.py'
    if any(sha_file(runtime/n) != config['runtime_source_sha256'][n] for n in (rf, net)) or sha_file(source_root/dig) != config['payload_sha256'][dig]:
        raise ValueError('Frozen masking/forward/tensor-finiteness source changed')
    nodes = ast.parse((runtime/rf).read_text())
    denoise = next(n for n in ast.walk(nodes) if isinstance(n, ast.FunctionDef) and n.name == 'denoise')
    source = ast.unparse(denoise)
    if (source.count('condition.gt_frames') != 2 or 'condition_state_in_B_C_T_H_W * condition_video_mask' not in source
            or 'gt_frames_velocity * condition_video_mask' not in source):
        raise ValueError('Original gt_frames masking dataflow differs')
    tree = ast.parse((runtime/net).read_text())
    forward = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'forward')
    names = [n for n in ast.walk(forward) if isinstance(n, ast.Name) and n.id == 'kwargs']
    if len(names) != 1 or not isinstance(names[0].ctx, ast.Del) or any(a.arg == 'gt_frames' for a in forward.args.args):
        raise ValueError('Original network no longer discards the unused gt_frames kwarg')
    digest = ast.unparse(function(ast.parse((source_root/dig).read_text()), 'tree_digest'))
    if 'torch.isfinite(x).all()' not in digest or "raise ValueError('Nonfinite state')" not in digest:
        raise ValueError('Original condition hash did not require finite tensor values')
    return {'zero_mask_gt_has_no_model_effect': True, 'finite_condition_tensors_required_by_original_digest': True,
        'runtime_source_sha256': {n: config['runtime_source_sha256'][n] for n in (rf, net)},
        'tensor_digest_source_sha256': config['payload_sha256'][dig],
        'nonzero_mask_or_active_condition_change_not_accepted': True}
