"""A32-only execution boundary and central envelope. No authority is created here."""
import copy
import json
import time
from pathlib import Path

from .cara_fast_binding_r2 import load_card
from .cara_fast_spec_r1 import digest
from .gpu_budget_pool_v2 import sha
from .wc73_execution_r1 import Pool as CentralPool, admit_host

RUN = 'cara-fast-cal-a32-r2-20261028'
SPEC = 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'
QUOTE = 'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json'
PROFILE = 'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json'
RA = 'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json'
HARD_GPUH = 5


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Pool(CentralPool):
    """One four-card central ledger, with the existing liability accounting."""
    def reserve(self, job, gpu):
        require(job['job_id']==job['run_id']==RUN and job['phase']=='A', 'Only registered A32')
        require(job['billed_limit_GPUh']==HARD_GPUH and 0<job['forecast_GPUh']<=HARD_GPUH,
                'A32 whole cost must fit 5 GPUh')
        name, capability = {'four_card':('RTX 6000 Ada','8.9'),
                            'two_card':('RTX A6000','8.6')}[job['host']]
        require(gpu['uuid']==job['gpu_uuid'] and name in gpu['name']
                and gpu['compute_cap']==capability and not gpu['pids']
                and gpu['utilization_percent']==0 and 0<=gpu['memory_used_mib']<=1024
                and 0<=time.time()-gpu['unix']<=60, 'Fresh idle selected physical GPU required')
        with self.transaction() as value:
            require(value is not None and not value.get('budget_overrun_recorded'), 'Valid central ledger required')
            require(RUN not in value['jobs'], 'Recover original A32 intent; never replay on either host')
            admit_host(value,job['host'])
            require(self.accounting(value)['available_gpu_hours']>=HARD_GPUH,
                    'Complete A32 requires its whole5GPUh in the central ledger')
            value['jobs'][RUN] = dict(copy.deepcopy(job),status='RESERVED_OR_RUNNING',kind='V2',
                                      reserved_unix=time.time(),central_ledger_host='four_card')
            self.commit(value,dict(type='FAST_A32_RESERVE_ONLY_NO_B_AUTHORITY',job_id=RUN))
            return copy.deepcopy(value)


def validate(project, stage):
    """Read and validate the staged external authorization/source boundary once."""
    project, stage = Path(project), Path(stage)
    registration = read(stage/'registration.json')
    require(all(sha(stage/name)==expected for name,expected in registration['payload_sha256'].items()),
            'Staged source differs')
    require(all(sha(project/'runtime'/name)==expected
                for name,expected in registration['runtime_source_sha256'].items()), 'Pinned runtime differs')
    card = load_card(stage,SPEC)
    profile, quote = read(stage/PROFILE), read(stage/QUOTE)
    authority = read(stage/'pg-GPU-authorization.json')
    require(authority.get('direct_user_authorization') is True and bool(authority.get('user_quote')),
            'Direct human authorization for the new A32 card is required')
    require(authority['run_id']==RUN and authority['phase']=='A' and authority['physical_paths']==32
            and authority['whole_GPUh']==HARD_GPUH and authority['authorizes_phase_B'] is False,
            'Exact A32-only authority; no B or replay')
    require(authority['host'] in profile['hosts'] and authority['scope_sha256']==card['scope_sha256'],
            'Authorized host/scope differs')
    require(authority['source_revision']==registration['source_revision']
            and authority['registration_sha256']==sha(stage/'registration.json'), 'Authorization source differs')
    proof = read(stage/'execution-CPU-proof.json')
    require(proof.get('passed') is True
            and authority['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json'), 'Affected orchestration CPU acceptance required')
    require(all(registration['payload_sha256'].get(name)==expected
                for name,expected in proof['critical_source_sha256'].items()), 'Untested execution source')
    require(profile['scope_sha256']==quote['scope_sha256']==card['scope_sha256'], 'Profile/quote scope differs')
    require(quote['host_quotes'][authority['host']]['phases']['A']['proposed_hard_GPUh']==HARD_GPUH,
            'Complete host quote differs')
    envelope = read(stage/'central-reservation.json')
    job = envelope['job']
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True,
            'Original central envelope required; the two-card replica grants no funds')
    for key,expected in dict(job_id=RUN,run_id=RUN,phase='A',host=authority['host'],
        gpu_uuid=authority['gpu_uuid'],launch_id=authority['launch_id'],
        registration_sha256=authority['registration_sha256'],billed_limit_GPUh=HARD_GPUH,
        authorization_sha256=sha(stage/'pg-GPU-authorization.json')).items():
        require(job.get(key)==expected, 'Central envelope differs: '+key)
    require(envelope['job']['status']=='RESERVED_OR_RUNNING', 'Original central envelope is not held')
    binding = read(stage/'launch-binding.json')
    require(binding['authorization_sha256']==sha(stage/'pg-GPU-authorization.json')
            and binding['central_reservation_sha256']==sha(stage/'central-reservation.json'),
            'Launch source/envelope binding differs')
    return card, registration, authority


def check_complete_A(card, collection):
    expected = [slot for slot in card['physical_matrix'] if slot['phase']=='A']
    require(collection['phase']=='A' and collection['scope_sha256']==card['scope_sha256']
            and collection['status']=='TERMINAL', 'Original A32 is incomplete')
    require(len(collection['rows'])==32 and [r['slot'] for r in collection['rows']]==expected
            and all(r['status']=='COMPLETE' for r in collection['rows']), 'Complete ordered A32 denominator required')
    gate = collection.get('diagnostic_gate',{})
    require(gate.get('passed') is True and gate.get('actual_roles')==['NATIVE35','ALLD','WC_T006'],
            'Actual three-arm GPU numerical gate required')
    for row in collection['rows']:
        slot, result = row['slot'], row['result']
        require(result.get('CPU_fixture') is False and result['slot_id']==slot['id']
                and result['scope_sha256']==card['scope_sha256'], 'CPU or wrong-slot data cannot accept GPU A32')
        if slot['eligible_clean_time']:
            require(not result['audit_enabled'] and 0<result['T_DD']<=result['T_request']
                    and all(result[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints')),
                    'Clean Native/calibration clock is contaminated')
    return digest(collection)
