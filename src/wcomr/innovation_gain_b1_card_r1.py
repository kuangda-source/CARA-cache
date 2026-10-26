"""Bounded B1 phase of the single seven-GPUh innovation exploration.

The selected host writes a private phase ledger. The authoritative four-card
ledger reserves/settles its envelope; neither host's prior job is overwritten.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import time

from .gpu_budget_pool_v2 import BudgetPool
from .policy_generator_r1.dev128_finance import financial_hold, HostBudgetPool

RUN='cara-ig-b1-r1-20261027'
ROUND='cara-innovation-gain-r1-20261027'
ENVELOPE=RUN+'-central-envelope'
CONFIG='IG-config.json'
CPU_PROOF='IG-CPU.json'
COUNTS=dict(parent_paths=4,prompts=2,states=12,original_readout_positions=72,
            additional_guided_replays=108,additional_head_pairs=216)


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def validate(project,stage):
    project,stage=Path(project),Path(stage)
    reg=read(stage/'registration.json');c=read(stage/CONFIG)
    if reg['namespace']!='CARA_IG_B1_EXECUTION_R1' or reg['stage']!=str(stage):raise ValueError('Wrong B1 stage')
    for n,h in reg['payload_sha256'].items():
        p=stage/n
        if p.is_symlink() or not p.resolve().is_relative_to(stage.resolve()) or sha(p)!=h:
            raise ValueError('B1 payload changed: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned runtime changed: '+n)
    if (c['run_id']!=RUN or c['scope_counts']!=COUNTS or c['billed_limit_GPUh']!=1.5
            or c['round_cap_GPUh']!=7 or c['cumulative_cap_GPUh']!=226
            or c['compute_capability']!=({'two_card':[8,6],'four_card':[8,9]}[c['host']])):
        raise ValueError('B1 phase/round/host contract mismatch')
    q=read(stage/'pg-whole-quote.json')
    if q['scope_counts']!=COUNTS or not 0<q['forecast_GPUh']==c['forecast_complete_GPUh']<=1.5:
        raise ValueError('Complete B1 quote required')
    cpu=read(stage/CPU_PROOF)
    if cpu['status']!='IG_SOURCE_BOUND_CPU_PASS_NOT_REAL_MODEL_RESULT' or not cpu.get('B1_batch_controls'):
        raise ValueError('New B1 production-entry CPU control missing')
    for n,h in cpu['source_sha256'].items():
        if reg['payload_sha256'].get(n)!=h:raise ValueError('Accepted CPU source differs: '+n)
    return c,reg


class PhaseBudgetPool(HostBudgetPool):
    def __init__(self,project,stage):
        super().__init__(project)
        self.stage=Path(stage);self.path=self.stage/'IG-private-phase-ledger.json'
        self.lock_path=self.stage/'IG-private-phase-ledger.lock'

    def reserve(self,job,gpu):
        c,_=validate(self.project,self.stage)
        auth=read(self.stage/'pg-GPU-authorization.json');envelope=read(self.stage/'central-envelope.json')
        if (job['job_id']!=RUN or job['run_id']!=RUN or job['scope_counts']!=COUNTS
                or job['billed_limit_GPUh']!=1.5 or auth['launch_id']!=job['launch_id']
                or envelope['job']['launch_id']!=job['launch_id'] or envelope['job']['gpu_uuid']!=gpu['uuid']):
            raise ValueError('Exact central B1 envelope and scope required')
        family,cap={'four_card':('RTX 6000 Ada','8.9'),'two_card':('RTX A6000','8.6')}[c['host']]
        if (family not in gpu['name'] or gpu['compute_cap']!=cap or gpu['pids']
                or not 0<=gpu['memory_used_mib']<=1024 or gpu['uuid']!=job['gpu_uuid']):
            raise ValueError('Wrong/busy selected physical GPU')
        with self.transaction() as value:
            if value is None or RUN in value['jobs'] or value['cap_gpu_hours']!=226:
                raise ValueError('Private phase original unavailable/already used')
            if job['billed_limit_GPUh']>self.accounting(value)['available_gpu_hours']:
                raise ValueError('Phase cannot overbook original snapshot')
            value['jobs'][RUN]=dict(copy.deepcopy(job),kind='IG_PRIVATE_PHASE_RECEIPT',
                status='RESERVED_OR_RUNNING',reserved_unix=time.time(),round_id=ROUND)
            self.commit(value,dict(type='IG_PRIVATE_PHASE_RESERVE_ALREADY_CENTRALLY_HELD',job_id=RUN))
            return copy.deepcopy(value)
