"""Human-advanced observation of an already completed, immutable BANK24 run.

Only the two observation-time predicates change. The deployed collector,
original launch, production payload and complete scientific audit stay intact.
"""
import inspect
import time
import types
import uuid
from pathlib import Path

import four_card_bank24_gpu_port_r1 as port
import wc_four_card_bank24_execution_r2 as controller
from four_card_bank24_execution_tools_r1 import read, sha, require
from wc_four_card_resource_cpu_r4 import write

AUTHORITY = 'reports/wc_four_card_BANK24_retry2_immediate_acceptance_authority_20261022.json'


def authority(launch):
    value = read(Path(AUTHORITY))
    require(value['status'] == 'DIRECT_HUMAN_ADVANCE_TERMINAL_OBSERVATION_ONLY'
            and value['user_quote'] == '现在就开始验收，然后一边继续推进实验，一边分析结果', 'Direct timing instruction required')
    ref = Path(value['launch_ref'])
    require(sha(ref) == value['launch_sha256'] and read(ref)['dispatch'] == launch
            and value['launch_id'] == launch['launch_id'], 'Advance applies only to the unchanged original launch')
    review_ref = Path(value['technical_review_ref'])
    require(sha(review_ref) == value['technical_review_sha256'], 'Original exit evidence changed')
    review = read(review_ref)
    require(review['launch_id'] == launch['launch_id'] and all(review['checks'].values())
            and review['complete_reported_paths'] == 24, 'Complete original exit evidence required')
    return value


def timing_allowed(capture, launch):
    if capture['observed_unix'] >= launch['next_check_not_before_unix']:
        return True
    value = authority(launch)
    require(capture.get('advanced_terminal_authority') == value
            and capture['observed_unix'] >= value['recorded_unix']
            and capture['launch'] == launch and capture['mode'] == 'terminal'
            and not any(capture['original_live_handles'].values()), 'Actual completed observation after human instruction required')
    return True


def capture(a):
    require(a.mode == 'terminal' and not a.output.exists(), 'New terminal receipt only')
    raw = read(a.launch_ref); launch = raw.get('dispatch', raw)
    value = authority(launch)
    require(time.time() >= value['recorded_unix'], 'Do not backdate observation')
    code = 'L=' + repr(launch) + '\nOBS=' + repr('capture-' + uuid.uuid4().hex) + '\n' + r'''
import json,sys
from pathlib import Path
stage=Path(L['stage']);sys.path.insert(0,str(stage))
from four_card_bank24_execution_tools_r1 import collect_once
value=collect_once(Path(L['project']),stage,L,'terminal',stage/OBS)
print(json.dumps(value,allow_nan=False))
'''
    result = controller.ssh(code, timeout=180)
    result['advanced_terminal_authority'] = value
    write(a.output, result)
    return dict(output=str(a.output), status=result.get('status'), mode='terminal')


def replace_once(source, before, after):
    require(source.count(before) == 1, 'Reviewed observation-time predicate changed')
    return source.replace(before, after)


def accept_capture(capture, launch, inputs):
    timing_allowed(capture, launch)
    # Clone the exact existing functions with only their scheduling predicates
    # replaced; every finance/raw/frame/control check executes unchanged.
    body = replace_once(inspect.getsource(port.accept_capture),
        "capture['observed_unix']>=launch['next_check_not_before_unix']",
        'timing_allowed(capture,launch)')
    original_generate = port.generate
    def generate(*args):
        generated, binding = original_generate(*args)
        name = 'bank24-fourcard-accept-terminal-function.py'
        generated[name] = replace_once(generated[name],
            "v['observed_unix'] >= launch['next_check_not_before_unix']",
            'timing_allowed(v,launch)')
        # The original function executes in the original lifecycle namespace.
        generated[name] = 'from wc_four_card_bank24_advance_terminal_r1 import timing_allowed\n' + generated[name]
        return generated, binding
    namespace = dict(port.__dict__, generate=generate, timing_allowed=timing_allowed)
    exec(compile(body, '<human-advanced-terminal-time-only>', 'exec'), namespace)
    return namespace['accept_capture'](capture, launch, inputs)


def accept_gpu(a):
    function = types.FunctionType(controller.accept_gpu.__code__,
        dict(controller.__dict__, accept_capture=accept_capture))
    return function(a)
