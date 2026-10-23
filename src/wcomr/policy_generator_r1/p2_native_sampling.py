"""18..35-step guarded Native requests with full-block witnesses, no WC install."""
import ast
import copy
import inspect
import types
import torch
from .. import clean_speed20_r1 as clean
from ..w1_native_reference_sampling import official_native_forward
from .production_sampling import complete_request_seconds
from .continuation_preparation import TIME_BOUNDARY


def execute(inference, sample, *, schedule, **kw):
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary guardrails required')
    n = sample.num_steps
    if type(n) is not int or n not in range(18, 36) or schedule['requested_steps'] != n:
        raise ValueError('Registered Native 18..35 step grid required')
    updates = schedule['actual_updates']
    if updates != len(schedule['timesteps']) or updates < 1:
        raise ValueError('Actual scheduler grid required')
    net = inference.pipe.model.net
    def install(model, method, *args, **kwargs):
        if method != 'NATIVE' and kw.get('CPU_native') is None:raise ValueError('Pure Native only')
        if kw.get('CPU_native') is None:model.net.forward = official_native_forward(model.net)
        model.net.worldcache_enabled = False
        return model.get_velocity_fn_from_batch.__func__, None, None, None
    # Keep the complete guarded request/timing/cleanup body. Only its literal
    # full35/full36 bounds are parameterized; neither upstream sampler nor RF changes.
    tree = ast.parse(inspect.getsource(clean.execute))
    class Bounds(ast.NodeTransformer):
        def visit_Constant(self, node):
            if type(node.value) is int and node.value in (35, 36):
                return ast.copy_location(ast.Name(id='_requested' if node.value == 35 else '_updates', ctx=ast.Load()),node)
            return node
    tree = ast.fix_missing_locations(Bounds().visit(tree))
    ns = dict(vars(clean), install=install, _requested=n, _updates=updates)
    exec(compile(tree, __file__+'#complete-Native-request', 'exec'), ns)
    counts = [0, 0]
    def count(which):
        def hook(*args):counts[which] += 1
        return hook
    hooks = [net.blocks[0].register_forward_pre_hook(count(0)),net.blocks[-1].register_forward_pre_hook(count(1))]
    try:
        result = ns['execute'](inference,sample,'NATIVE',**kw)
    finally:
        for hook in hooks:hook.remove()
    result.update(requested_steps=n,actual_updates=result['solver_steps'],full_block_calls=counts,
        cache_installed=False,timing_boundary=TIME_BOUNDARY,
        full_request_seconds=complete_request_seconds(result) if result.get('core_seconds') else None)
    if result['solver_steps']:
        if result['scheduler_timesteps'] != schedule['timesteps'] or counts != [2*updates]*2:
            raise ValueError('Native actual schedule/full-block calls differ')
        scheduler=inference.pipe.model.sample_scheduler
        if scheduler.sigmas.cpu().tolist()!=schedule['sigmas']:
            raise ValueError('Native sigma schedule differs')
    return result
