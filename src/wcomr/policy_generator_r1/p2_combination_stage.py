"""P2 supervision preparation. Real admission remains closed until P1 binding.

CPU lifecycle patches validate in a separate fixture tree only. No inherited P1
quote or planning envelope grants a P2 GPU authorization.
"""
from .production_stage import read,sha
from .p2_production_contract import COUNTS
RUN='cara-pg-p2-whole-pending-p1-dedup'
CONFIG='pg-p2-config.json'
CPU_PROOF='PG-P2-combination-CPU.json'

def validate(project,stage):
    raise ValueError('P2 admission closed: accepted P1, physical policy dedup, final whole quote and final stage binding required')
