"""Complete saved-state Q1 orchestration, including every extra head call.

Formal scope stays 12 states x eight C roles. Two C warmups, one preview C,
and twelve stored-D-hidden head pairs are additional work. This module owns
neither device admission nor authorization, and never samples a new parent.
"""
import gc

import torch

from .innovation_gain_observer_r1 import restore_readout_inputs
from .partial_mlp_deployment_state import plain, tensor_bytes
from .scout_readout_v22 import validate_state
from .sq_q1_readout_r1 import (PROMPTS, STEPS, source_from_anchors,
    evaluate_saved_state)
from .sq_readout_subgraph_r1 import original_controls, dense_hidden_outputs, compare_outputs

STATE_KEYS = tuple((prompt, step) for prompt in PROMPTS for step in STEPS)
COUNTS = dict(states=12, formal_C_pairs=96, formal_head_calls=192,
              warm_C_pairs=2, preview_original_C_pairs=1, stored_dense_hidden_head_pairs=12,
              complete_readout_pairs=111, complete_head_calls=222,
              codec_C_pairs=72, new_deep_pairs=0, new_parent_paths=0, new_videos=0)


@torch.no_grad()
def collect_saved_q1(kernel, records, load, schema, *, device, max_copy_bytes, save_health, synchronize=None):
    """Run all fixed roles, or retain a failed original control without selection.

    The loader must verify immutable B1 artifact/source identities. Health
    receipts contain counts only; scores and LOPO are returned at terminal.
    CPU fixture execution is supported for production-entry tests.
    """
    keys = [(row['prompt'], row['step']) for row in records]
    if len(keys) != len(set(keys)) or set(keys) != set(STATE_KEYS):
        raise ValueError('Exactly the complete registered twelve-state cohort required')
    if type(max_copy_bytes) is not int or max_copy_bytes <= 0:
        raise ValueError('Explicit private-input resource cap required')
    by_key = dict(zip(keys, records))
    states = []
    phase = ['warm']
    calls = {name:dict(started=0, completed=0) for name in ('warm','controls','formal')}
    def head_started(module, args): calls[phase[0]]['started'] += 1
    def head_completed(module, args, output): calls[phase[0]]['completed'] += 1
    before = kernel.net.final_layer.register_forward_pre_hook(head_started)
    after = kernel.net.final_layer.register_forward_hook(head_completed)
    sync = synchronize or (lambda: None)
    def health(status):
        save_health(dict(status=status, completed_states=len(states), expected_states=12,
            formal_C_pairs_completed=calls['formal']['completed']//2,
            head_calls={k:dict(v) for k,v in calls.items()}, scientific_selection=False))
    def terminal(status, failure=None):
        health(status)
        return dict(status=status, scope_counts=COUNTS, completed_states=len(states), states=states,
            head_calls={k:dict(v) for k,v in calls.items()}, failure=failure,
            complete_Q1_cohort=False, selections=None, partial_state_selection=False,
            new_deep_pairs=0, new_parent_paths=0, new_videos=0,
            deployment_memory_measured=False)
    health('Q1_LOADING_ORIGINAL_SAVED_STATE')
    try:
        for index, (prompt, step) in enumerate(STATE_KEYS):
            payload = load(by_key[(prompt,step)])
            if (tuple(payload['context'])[0],payload['step']) != (prompt,step):
                raise ValueError('Loaded state does not match its immutable manifest row')
            if not all(payload[k] for k in ('P0_actual_dense','P1_dense_head_RF_equal','P2_C_actual_parent_equal')):
                raise ValueError('Original same-state controls missing before any warm/head call')
            cpu_inputs = restore_readout_inputs(payload, schema, 'cpu')
            validate_state(cpu_inputs['context'],step,cpu_inputs['xi'],cpu_inputs['anchors'])
            logical = tensor_bytes(plain((cpu_inputs['anchors'],cpu_inputs['current'],
                cpu_inputs['pair_inputs'][:3],[vars(c) for c in cpu_inputs['pair_inputs'][3]])))
            if logical > max_copy_bytes:
                raise ValueError('Private-input cap exceeded before device transfer')
            inputs = restore_readout_inputs(payload, schema, device)
            if index == 0:
                phase[0] = 'warm'; health('Q1_TWO_ORIGINAL_C_WARMUPS')
                for _ in range(2):
                    output = kernel.run('C', source=source_from_anchors(inputs['anchors']),
                        current=inputs['current'], pair_inputs=inputs['pair_inputs'])[0]
                    sync()
                    if not all(torch.isfinite(v).all() for v in output):
                        raise ValueError('Nonfinite original C warmup')
                    del output
                phase[0] = 'controls'; health('Q1_ORIGINAL_C_AND_DENSE_HEAD_PREVIEW')
                controls = original_controls(kernel, inputs, payload)
                sync()
                if not controls['original_controls_exact']:
                    return terminal('Q1_ORIGINAL_PARITY_NOT_ACCEPTED_NO_CODEC_SELECTION',
                        dict(prompt=prompt,step=step,kind='ORIGINAL_C_AND_DENSE_HEAD',controls=controls))
            else:
                phase[0] = 'controls'; health('Q1_STORED_DENSE_HIDDEN_HEAD_CONTROL')
                outputs = dense_hidden_outputs(kernel, inputs, payload['teacher_hidden'])
                sync()
                check = compare_outputs(outputs,payload['teacher'])
                del outputs
                if not check['exact']:
                    return terminal('Q1_ORIGINAL_PARITY_NOT_ACCEPTED_NO_CODEC_SELECTION',
                        dict(prompt=prompt,step=step,kind='STORED_DENSE_HIDDEN_HEAD',control=check))
            del inputs, cpu_inputs
            phase[0] = 'formal'; health('Q1_EIGHT_FORMAL_C_ROLES')
            try:
                value = evaluate_saved_state(kernel,payload,schema,device=device,
                    max_copy_bytes=max_copy_bytes,synchronize=sync)
            except ValueError as error:
                if str(error) != 'Original C replay mismatch; do not score codecs or change tolerance':
                    raise
                return terminal('Q1_ORIGINAL_PARITY_NOT_ACCEPTED_NO_CODEC_SELECTION',
                    dict(prompt=prompt,step=step,kind='FORMAL_ORIGINAL_C',reason=str(error)))
            states.append(value)
            del payload
            gc.collect()
        if {k:v['completed'] for k,v in calls.items()} != dict(warm=4,controls=26,formal=192):
            raise ValueError('Actual complete head-call denominator differs from the frozen whole card')
        if any(v['started'] != v['completed'] for v in calls.values()):
            raise ValueError('An incomplete head call cannot enter Q1 acceptance')
        result = terminal('Q1_COMPLETE_ACTUAL_OUTPUTS_PENDING_INDEPENDENT_ACCEPTANCE')
        # Only a post-release, independently accepted terminal may run LOPO or
        # choose bit directions. The GPU-held collection returns raw records.
        result.update(complete_Q1_cohort=True, selections=None)
        return result
    except BaseException:
        health('Q1_TECHNICAL_FAILURE_NO_SELECTION')
        raise
    finally:
        before.remove(); after.remove()
