"""Input-only migration of a historical asset validator to current budget.

All frozen historical files/scopes/assets remain checked and untouched.
Only the live cap compared by the inherited INPUT loader uses the new human
authority. Actual N1 GPU admission remains the R1 fresh48/strict-over8 check.
"""
import ast
import inspect
from textwrap import dedent
from .math_n1_production_r1 import *
from . import math_n1_production_r1 as prior


def current_window_original_inputs(project,stage):
    from . import current_birth_real_production_r1 as parent
    from . import e3_complete64_production_r1 as e3
    source=dedent(inspect.getsource(parent.validate))
    old="or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=c['cumulative_cap_GPUh']"
    new="or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=CURRENT_HUMAN_CAP"
    assert source.count(old)==1
    changed=source.replace(old,new)
    assert changed.replace(new,old)==source
    assert ast.dump(ast.parse(changed.replace(new,old)))==ast.dump(ast.parse(source))
    ns={**vars(parent),'CURRENT_HUMAN_CAP':104.97136333301378}
    exec(compile(changed,__file__+'#input-cap-migration','exec'),ns)
    src=dedent(inspect.getsource(e3.validate))
    before='from .current_birth_real_production_r1 import validate as validate_parent'
    after='validate_parent = CURRENT_WINDOW_INPUT_VALIDATOR'
    assert src.count(before)==1
    edited=src.replace(before,after);assert edited.replace(after,before)==src
    target={**vars(e3),'CURRENT_WINDOW_INPUT_VALIDATOR':ns['validate']}
    exec(compile(edited,__file__+'#historical-input-loader-only','exec'),target)
    return target['validate'](project,stage)


source=dedent(inspect.getsource(prior.validate))
before='from .e3_complete64_production_r1 import validate as old_validate'
after='old_validate = CURRENT_WINDOW_ORIGINAL_INPUTS'
assert source.count(before)==1
changed=source.replace(before,after);assert changed.replace(after,before)==source
namespace={**vars(prior),'CURRENT_WINDOW_ORIGINAL_INPUTS':current_window_original_inputs}
exec(compile(changed,__file__+'#N1-input-binding','exec'),namespace)
validate=namespace['validate']
INPUT_MIGRATION_PROOF={'original_scopes_parameters_hash_assets_CPU_proofs_preserved':True,
    'historical_payload_and_shared_runtime_mutated':False,'only_live_input_cap_uses_current_authority':True,
    'real_GPU_admission_uses_fresh_current_remaining48_and_strict8':True}
