"""New assets scope over unchanged, accepted Cosmos request dependencies."""
import os
from pathlib import Path

from .policy_interval_assets_r1 import CONFIG, COUNTS, PROFILE, read, sha, validate_contract


def validate(project, stage):
    os.environ['WC_SCOUT_KIND']='CAL12'
    from .scout_production_entry_r1 import validate as validate_original
    original,reg,old,inputs,tables,prior=validate_original(project,stage)
    stage=Path(stage);config=read(stage/CONFIG);validate_contract(config)
    if config['requests']!=original['requests']:
        raise ValueError('Preserve complete original four-CAL Cosmos requests')
    for name,binding in config['references'].items():
        if sha(stage/binding['ref'])!=binding['sha256']:
            raise ValueError('New assets reference changed: '+name)
    quote=read(stage/config['references']['quote']['ref'])
    if any(config[k]!=quote[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh')):
        raise ValueError('Whole collection and price scope must match its quote')
    if quote['scope_counts']!=COUNTS or quote['action_unit_prices_measured']:
        raise ValueError('Planning inputs cannot be promoted to observed prices')
    if PROFILE['protected_dense']!=list(range(1,8))+[36]:
        raise ValueError('Pinned native-policy protected domain changed')
    return config,reg,old,inputs,tables,prior


def require_BANK24(capture, accepted):
    from .scout_gpu_lifecycle_r1 import accept_terminal
    value=accept_terminal(capture,capture['launch'])
    if (capture['config']['kind']!='BANK24' or not value.get('full_protocol_accepted')
        or any(accepted.get(k)!=v for k,v in value.items())):
        raise ValueError('Original complete BANK24 and its own independent acceptance required')
    return value
