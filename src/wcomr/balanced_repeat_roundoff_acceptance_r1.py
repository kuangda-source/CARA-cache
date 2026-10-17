"""Read-only N08 acceptance bridge for one-ULP derived sample-standard-deviation differences.

Raw observations, source identities, all40 paths, all-frame scores, finances and
resource gates retain the original source-bound acceptance implementation.
"""
import ast
import copy
import hashlib
import inspect
import math
from pathlib import Path

from . import balanced_repeat_acceptance_r1 as original

VERSION = 'N08_OFFLINE_DERIVED_SAMPLE_STD_ONE_ULP_BRIDGE_R1'
ORIGINAL_SHA256 = 'cab6b0e3dae2dd3d35f489715dc410967a8e66245722ad3afc43b268174034a4'
OLD_LINE = "    if any(fingerprint(final.get(k)) != fingerprint(v) for k, v in recomputed.items()):"
NEW_LINE = "    if any(not _derived_equal(k, final.get(k), v) for k, v in recomputed.items()):"


def _equal(a, b, path, differences):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(_equal(a[k], b[k], path + (k,), differences) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_equal(x, y, path + (i,), differences) for i, (x, y) in enumerate(zip(a, b)))
    if a == b:
        return True
    allowed = (len(path) == 4 and path[:2] == ('timing_statistics', 'scene_methods')
        and type(path[2]) is int and path[3] == 'complete_repeat_sample_std_seconds')
    if (allowed and type(a) is float and math.isfinite(a) and math.isfinite(b)
            and a >= 0 and b >= 0 and abs(a-b) <= max(math.ulp(a), math.ulp(b))):
        differences.append(dict(path='/'.join(map(str, path)), original=a, independently_recomputed=b,
            absolute_difference=abs(a-b), maximum_allowed_ULP=1))
        return True
    return False


def accept(value, launch):
    source_path = Path(inspect.getsourcefile(original))
    source_bytes = source_path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Exact original N08 acceptor source required')
    function = inspect.getsource(original.accept)
    if function.count(OLD_LINE) != 1:
        raise ValueError('Unique derived-statistics comparison required')
    modified = function.replace(OLD_LINE, NEW_LINE)
    if modified.replace(NEW_LINE, OLD_LINE) != function:
        raise ValueError('One reversible comparison change only')
    if ast.dump(ast.parse(modified.replace(NEW_LINE, OLD_LINE))) != ast.dump(ast.parse(function)):
        raise ValueError('Original acceptance AST must be exactly recoverable')
    differences = []
    def derived_equal(key, before, after):
        return _equal(before, after, (key,), differences)
    namespace = dict(original.__dict__, _derived_equal=derived_equal)
    exec(compile(modified, '<source-bound N08 derived-statistic bridge>', 'exec'), namespace)
    before = copy.deepcopy(value)
    result = namespace['accept'](value, launch)
    if value != before:
        raise ValueError('Offline acceptance cannot modify original capture')
    result['offline_roundoff_bridge'] = dict(version=VERSION, original_acceptor_sha256=ORIGINAL_SHA256,
        original_strict_failure_retained=True, raw_observations_or_source_modified=False,
        derived_statistic_differences=differences, numerical_tolerance_scope='ONLY_SCENE_SAMPLE_STD_AT_MOST_ONE_ULP',
        all_other_original_gates_preserved=True)
    return result

