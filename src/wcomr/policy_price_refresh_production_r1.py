"""Validate a separate immutable price stage and its accepted original bindings."""
import os
from pathlib import Path
from .policy_interval_assets_r1 import read, sha, PROFILE
from .policy_price_refresh_contract_r1 import COUNTS, matrix, VERSION

RUN = 'wc-policy-price-refresh-cal4-full1624-ada-r1'
CONFIG = 'price-refresh-config.json'
CPU_PROOF = 'price-production-CPU.json'
CPU_BUNDLE = 'price-CPU-bundle.json'
ORIGINAL_RUN = 'wc-policy-interval-assets-cal4-full1624-ada-r2'


def full_rows(rows):
    observed = {r['id']: r for r in rows}
    if len(observed) != len(rows) or set(observed)-{r['id'] for r in matrix()}:
        raise ValueError('Duplicate or unregistered price path')
    return [observed.get(p['id'], dict(**p, status='NOT_REACHED')) for p in matrix()]


def validate(project, stage):
    os.environ['WC_SCOUT_KIND']='CAL12'
    project, stage = Path(project), Path(stage)
    reg = read(stage/'registration.json')
    if reg['namespace'] != VERSION or reg['stage'] != str(stage):
        raise ValueError('Wrong price stage registration')
    for n, h in reg['payload_sha256'].items():
        p = stage/n
        if p.is_symlink() or not p.resolve().is_relative_to(stage.resolve()) or sha(p) != h:
            raise ValueError('Registered price payload changed: '+n)
    for n, h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n) != h: raise ValueError('Pinned runtime changed')
    from four_card_policy_assets_port_r1 import reconstruct
    base, parent, inputs, tables, prior = reconstruct(stage)
    c = read(stage/CONFIG); quote = read(stage/'price-whole-quote.json')
    if c['version'] != VERSION or c['scope_counts'] != COUNTS or c['matrix'] != matrix():
        raise ValueError('Full independent price scope changed')
    if c['requests'] != base['requests'] or c['profile'] != PROFILE or c['run_id'] != RUN:
        raise ValueError('Original CAL, profile or run identity changed')
    if quote['scope_counts'] != COUNTS or not 0 < quote['forecast_complete_GPUh'] <= quote['billed_limit_GPUh'] < 12:
        raise ValueError('Whole-card autonomous quote required')
    if any(c[k] != quote[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh')):
        raise ValueError('Whole quote differs')
    original = project/'outputs'/ORIGINAL_RUN
    for name, h in c['accepted_original_files'].items():
        if sha(original/name) != h: raise ValueError('Original accepted asset changed: '+name)
    return c, reg, parent, inputs, tables, prior
