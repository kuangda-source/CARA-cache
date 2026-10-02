"""No-Torch scope and budget gates for the new middle-coverage card."""
import json


def request_wc_gate(net, requested_steps, probe_depth):
    """Call after the official request reset, not constructor initialization."""
    if net.worldcache_num_steps != 2*requested_steps or net.probe_depth != probe_depth:
        raise ValueError('Actual request WC horizon/probe differs')


def scope_gate(budget, seconds):
    if seconds != 1200 or budget['cap_gpu_hours'] != 12 or any(k.endswith('_inflight') for k in budget):
        raise ValueError('New card requires cumulative12h ledger,1200s cap and no inflight')
    if not budget.get('budget_authorization_ref') or (12-budget['used_gpu_hours'])*3600 < seconds+15:
        raise ValueError('Missing authorization or insufficient balance and settlement margin')


def validate_scope(c):
    if (c['max_gpu_wall_seconds'] != 1200 or c['capture_calls'] != [25,26,35,36]
            or c['capture_layers'] != list(range(2,28)) or c['stop_after_solver_steps'] != 18
            or c['state_steps'] != [13,18] or c['phases'] != ['baseline_prefix','observed_prefix']
            or c['policy'] != {'sim':.1,'cdf':.98} or c['warmups'] != 1 or c['repeats'] != 3
            or c['pv_skipping'] is not False or c['deployment_sparse'] is not False):
        raise ValueError('Frozen middle coverage/no-deployment scope changed')
    return {(call,layer) for call in c['capture_calls'] for layer in c['capture_layers']}


def compare_prefix(left,right):
    keys=['output_hashes','trace','block_counts','state_fingerprints','sampling']
    checks={k:left[k]==right[k] for k in keys}
    if not all(checks.values()):raise ValueError('Observed prefix altered baseline: '+json.dumps(checks))
    return checks
