"""Source-exact Video2World condition construction and paired velocity call.

Only the two adjacent denoise assignments are replaced. The original CFG
arithmetic and full sampler stay unchanged. Binding this method is explicit;
old restoration helpers are not implicitly compatible with its new globals.
"""
import ast
import copy
import hashlib
from types import MappingProxyType

from .cfg_paired_probe_forward import _function, _compile, RF_PATH, RF_SHA
from .cfg_paired_probe_production import _origin, _bindings


def compile_velocity(runtime, rf_module, executor, choose):
    _origin(rf_module, runtime, RF_PATH, RF_SHA)
    original = _function(runtime, RF_PATH, RF_SHA, 'get_velocity_fn_from_batch')
    actual = rf_module.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch
    if actual.__globals__ is not vars(rf_module):
        raise ValueError('Original velocity globals differ')
    node = copy.deepcopy(original)
    nested = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == 'velocity_fn']
    if len(nested) != 1:
        raise ValueError('Pinned velocity closure differs')
    body = nested[0].body
    expected = [ast.parse(s).body[0] for s in (
        'cond_v = self.denoise(noise, noise_x, timestep, condition)',
        'uncond_v = self.denoise(noise, noise_x, timestep, uncondition)')]
    if [ast.dump(n, include_attributes=False) for n in body[:2]] != [ast.dump(n, include_attributes=False) for n in expected]:
        raise ValueError('Two adjacent original denoise assignments differ')
    replacement = ast.parse('cond_v, uncond_v = _paired_velocity(self, noise, noise_x, timestep, (condition, uncondition))').body[0]
    nested[0].body = [replacement] + body[2:]
    inverse = copy.deepcopy(node)
    target = next(n for n in inverse.body if isinstance(n, ast.FunctionDef) and n.name == 'velocity_fn')
    target.body = copy.deepcopy(expected) + target.body[1:]
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('Velocity body changed outside the two assignments')
    if not callable(choose):
        raise ValueError('Explicit selector required')
    def paired(model, noise, latent, timestep, conditions):
        if model is not executor.model or model.net is not executor.net:
            raise ValueError('Velocity executor model identity differs')
        return executor.pair(noise, latent, timestep, conditions, choose)
    function = _compile(node, dict(vars(rf_module), _paired_velocity=paired), RF_PATH+'#paired-velocity')
    bindings = _bindings(function, vars(rf_module), {'_paired_velocity': paired})
    proof = {'RF_source_sha256': RF_SHA, 'velocity_inverse_AST_equal': True,
        'original_velocity_AST_sha256': hashlib.sha256(ast.dump(original, include_attributes=False).encode()).hexdigest(),
        'production_velocity_globals': bindings, 'condition_construction_and_CFG_arithmetic_unchanged': True,
        'two_adjacent_denoise_assignments_replaced': True, 'real_model_or_policy_claim': False}
    return function, MappingProxyType(proof)
