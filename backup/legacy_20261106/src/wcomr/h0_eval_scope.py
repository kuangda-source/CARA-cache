"""Independent H0 r2 startup repair; retain every r1 scientific scope gate."""
import hashlib
import importlib.util
from pathlib import Path


def validate_h0_eval_scope(c):
    fixed = {
        'card': 'WC-H0-EVAL-COMPLEMENT-R2-20261003-A',
        'max_gpu_wall_seconds': 1200,
        'sample_name': 'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191',
        'eligible_call_range': [25, 40], 'dense_fallback_layers': [6, 23, 27],
        'stop_after_solver_steps': 20, 'state_steps': [13, 20],
        'phases': ['baseline_prefix', 'observed_prefix'],
        'policy': {'sim': .1, 'cdf': .98}, 'warmups': 1, 'repeats': 3,
        'pv_skipping': False, 'deployment_sparse': False, 'planned_cfg_denominator': 2,
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
    }
    if any(c.get(k) != v for k, v in fixed.items()):
        raise ValueError('Frozen H0 eval-r2 card altered')
    return {0, 1}


def cost_gate(c):
    e = c['cost_admission']
    if e['planning_envelope_seconds'] + e['shutdown_settlement_margin_seconds'] > c['max_gpu_wall_seconds']:
        raise ValueError('Cost admission failed')


def validate_mode_sources(runtime, contract, config):
    """Run before GPU/Torch imports; do not import package execution code."""
    for rel, digest in contract['source_sha256'].items():
        if rel.startswith('python-package/'):
            package, rest = rel.removeprefix('python-package/').split('/', 1)
            spec = importlib.util.find_spec(package)
            if spec is None or spec.origin is None:
                raise ValueError('Mode contract package missing: ' + package)
            path = Path(spec.origin).parent/rest
        else:
            path = Path(runtime)/rel
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Mode contract source changed: ' + rel)
    if contract['shared_policy'] != 'EXPLICIT_EVAL_BEFORE_BOTH_ARMS_KEEP_STRICT_SHADOW_EVAL_GUARD':
        raise ValueError('Shared mode adaptation changed')
    if config['payload_sha256']['manifests/wc_h0_eval_mode_contract_20261003.json'] is None:
        raise ValueError('Mode contract payload pin missing')
