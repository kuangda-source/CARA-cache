"""Requested50 Native/all-D bridge; sparse36 policy support is not extended."""
import ast
import inspect
import types


def native50_ast(source):
    tree = ast.parse(source)
    guards, messages = 0, 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0], ast.NotIn)
                and isinstance(node.comparators[0], ast.Call)
                and ast.dump(node.comparators[0])==ast.dump(ast.parse('range(18, 36)', mode='eval').body)):
            node.comparators[0] = ast.Tuple(elts=[ast.Constant(50)], ctx=ast.Load())
            guards += 1
        if isinstance(node, ast.Constant) and node.value == 'Registered Native 18..35 step grid required':
            node.value = 'Registered Native50 grid required'
            messages += 1
    if (guards, messages) != (1, 1):
        raise ValueError('Pinned Native range guard changed')
    return ast.fix_missing_locations(tree)


def full50_ast(source):
    tree = ast.parse(source)
    constants = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is int]
    if [sum(n.value==v for n in constants) for v in (35, 36)] != [1, 5]:
        raise ValueError('Pinned complete-request bounds changed')
    class Bounds(ast.NodeTransformer):
        def visit_Constant(self, node):
            if type(node.value) is int and node.value in (35, 36):
                return ast.copy_location(ast.Constant(50 if node.value==35 else 51), node)
            messages = {'Exact complete method/35-step guarded request required':
                'Exact complete method/50-step guarded request required',
                'Complete guarded full36 output missing':'Complete guarded requested50/51-update output missing'}
            if isinstance(node.value, str) and node.value in messages:
                return ast.copy_location(ast.Constant(messages[node.value]), node)
            return node
    return ast.fix_missing_locations(Bounds().visit(tree))


def request_class():
    # Imports occur only after the caller establishes its runtime and CPU/GPU context.
    from . import clean_speed20_r1 as clean
    from .cara_fast_requests_r2 import Requests
    from .policy_generator_r1 import p2_native_sampling
    from .source_aware_phase_sampling import bind_globals

    native_namespace = dict(vars(p2_native_sampling))
    exec(compile(native50_ast(inspect.getsource(p2_native_sampling.execute)),
                 __file__+'#Native50-range', 'exec'), native_namespace)
    dense_namespace = dict(vars(clean))
    exec(compile(full50_ast(inspect.getsource(clean.execute)),
                 __file__+'#full51-request', 'exec'), dense_namespace)

    class Native50Requests(Requests):
        def __init__(self, **kwargs):
            card = kwargs['card']
            schedules = card['schedules']
            if (len(schedules)!=1 or schedules[0]['requested_steps']!=50
                    or schedules[0]['actual_updates']!=51
                    or len(schedules[0]['timesteps'])!=51 or len(schedules[0]['sigmas'])!=52
                    or any(card['roles'][s['role']]['requested_steps']!=50
                        or card['roles'][s['role']]['kind'] not in ('native','allD')
                        for s in card['physical_matrix'])):
                raise ValueError('Only the registered Native50/all-D51 component is supported')
            super().__init__(**kwargs)

    Native50Requests.__call__ = bind_globals(Requests.__call__, dict(
        clean=types.SimpleNamespace(execute=dense_namespace['execute']),
        p2_native_sampling=types.SimpleNamespace(execute=native_namespace['execute'])))
    proof = dict(original_request_bytecode_identical=Native50Requests.__call__.__code__ is Requests.__call__.__code__,
        Native_range_and_message_only=True, full_request_bounds_35_to_50_36_to_51=True,
        original_module_globals_unchanged=p2_native_sampling.execute is not native_namespace['execute']
            and clean.execute is not dense_namespace['execute'], sparse_policy_support_extended=False)
    return Native50Requests, proof
