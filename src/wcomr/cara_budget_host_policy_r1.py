"""Exact user-directed host restriction; no GPU or ledger authorization."""
from pathlib import Path

from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import require

SOURCE = 'src/wcomr/cara_budget_host_policy_r1.py'
POLICY = 'plans/cara_next_stage_20261028/mainline/r2/TWO_CARD_ONLY_HARDWARE_MAINTENANCE_20261031.json'
POLICY_SHA256 = '9083b1594ae89e9f79057cd04353328c0db8c255276a76bef44956af393eb199'
HOSTS = ('two_card',)


def bound_policy(stage, registration, authority):
    require(authority['host'] in HOSTS
            and registration['payload_sha256'].get(POLICY) == POLICY_SHA256
            and sha(Path(stage)/POLICY) == POLICY_SHA256
            and authority.get('execution_host_policy_sha256') == POLICY_SHA256,
            'Current user-directed two-card policy must be source and authority bound')
    return HOSTS
