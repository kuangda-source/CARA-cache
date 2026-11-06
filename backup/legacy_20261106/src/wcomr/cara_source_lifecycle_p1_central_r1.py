"""P1 central transactions: one original reservation/bill and explicit24GPUh cap steps."""
import copy
import hashlib
import json
import math
import re
from pathlib import Path
import time

from .cara_s_endpoint_lifecycle_r1 import IDENTITY, JOB_IDENTITY, financial_terminal, audit_settlement
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_b36_dispatch_r2 import create
from .gpu_budget_pool_v2 import atomic_json, finite,sha
from .policy_price_terminal_r1 import require,record as read_record_from_capture
from .wc73_execution_r1 import Pool, admit_host, hold
from .cara_budget_host_policy_r1 import HOSTS, POLICY_SHA256
from .cara_source_lifecycle_p1_identity_r1 import RUN_ID as RUN,STAGE_NAME,GPU,KIND,SCOPE_SHA256

STAGES={'two_card':STAGE_NAME}
SOURCE='src/wcomr/cara_source_lifecycle_p1_central_r1.py'


def validate_authority(auth,project):
    require(auth['run_id']==RUN and auth['CPU_fixture_only'] is False
        and auth['execution_authorized'] is True and auth['authorization_basis']=='DIRECT_USER_SINGLE_CARD'
        and bool(auth['user_quote']) and auth['authorizes_replay'] is False
        and finite(auth['billed_limit_GPUh']) and auth['billed_limit_GPUh']>4
        and auth['host']=='two_card' and auth['gpu_uuid']==GPU and auth['card_kind']==KIND
        and auth.get('central_transaction_authorized') is True and bool(auth.get('central_user_quote'))
        and auth.get('central_exception_run_id')==RUN
        and auth['scope_sha256']==SCOPE_SHA256
        and re.fullmatch('[0-9a-f]{40}',auth['source_revision']) is not None
        and re.fullmatch('[0-9a-f]{32}',auth['launch_id']) is not None
        and auth.get('execution_host_policy_sha256')==POLICY_SHA256
        and auth['stage']==str(Path(project)/'.sync'/STAGE_NAME)
        and auth['semantic_positions']==146 and auth['physical_generation_upper']==142,
        'Separate complete P1 GPU authority and exact original central transaction exception required')


def original_absence(observations,project,*,hosts=tuple(STAGES),run_id=RUN):
    require(run_id==RUN,'Only the complete original P1 run may reserve')
    stages = STAGES
    require(bool(hosts) and set(observations)==set(hosts) and set(hosts)<=set(STAGES),
            'All required original handles must be observed')
    for host,row in observations.items():
        require(row['host']==host and row['stage']==str(Path(project)/'.sync'/stages[host])
                and row['run_id']==run_id and row['observation_complete'] is True
                and finite(row['observed_unix']) and 0<=time.time()-row['observed_unix']<=60
                and row['dispatch_records']==[] and row['container'] is None,
                'Original dispatch exists or is unknown on a registered host; recover it')


def ledger_valid(value):
    require(value is not None and finite(value['cap_gpu_hours']) and value['cap_gpu_hours']>=226
            and math.isclose((value['cap_gpu_hours']-226)/24,round((value['cap_gpu_hours']-226)/24),abs_tol=1e-9)
            and all(finite(value[k]) and math.isclose(value[k],v,rel_tol=0,abs_tol=1e-9) for k,v in Pool.accounting(value).items()),
            'Original central totals and standing24GPUh cap series required')
    old=[j for j in value['jobs'].values() if hold(j) and j['status']=='RESERVED_OR_RUNNING']
    require(sorted(j['billed_limit_GPUh'] for j in old)==[4.5,12.], 'Retain the two original financial liabilities')


def reserve(project,admission,observations):
    """Call only on four_card with the selected host's complete fresh admission."""
    project=Path(project);pool=Pool(project)
    auth=admission['authorization'];job={k:auth[k] for k in IDENTITY}
    run_id=RUN
    receipt=project/'reports'/(run_id+'.central-reservation.json')
    validate_authority(auth,project)
    job.update(job_id=run_id,registration_sha256=admission['registration_sha256'],
        authorization_sha256=admission['authorization_sha256'],semantic_positions=146,physical_generation_upper=142,
        physical_model_pairs_upper=5176,postrelease_new_pairs_upper=32,forecast_GPUh=admission['forecast_GPUh'])
    require(hashlib.sha256(admission['authorization_raw_utf8'].encode()).hexdigest()==job['authorization_sha256']
            and json.loads(admission['authorization_raw_utf8'])==auth,'Original authority bytes required')
    with pool.transaction() as current:
        ledger_valid(current)
        # A persisted transaction is recovered before considering new admission.
        if receipt.exists():
            saved=read_record(receipt);original=saved['job']
            require(all(original[k]==job[k] for k in JOB_IDENTITY),'Original reservation differs; no other launch')
            if current==saved['central_before']:
                atomic_json(pool.path,saved['central_after'])
            else:
                require(current['jobs'].get(run_id)==original,'Reservation transaction unresolved; preserve original records')
            return saved
        require(run_id not in current['jobs'],'Original central job exists without receipt; recover it')
        require(not current.get('budget_overrun_recorded'), 'Unresolved actual overrun forbids a new reservation')
        original_absence(observations,project,run_id=run_id)
        require(admission['status']=='P1_COMPLETE_FRESH_ADMISSION_NO_GPU'
                and admission['central_operator_sha256']==sha(__file__)
                and admission.get('required_host_whole_card_CPU_accepted') is True
                and admission.get('required_hosts')==list(HOSTS)
                and admission.get('execution_host_policy_sha256')==POLICY_SHA256
                and admission['semantic_positions']==146 and admission['physical_generation_upper']==142 and admission['physical_model_pairs_upper']==5176 and admission['postrelease_new_pairs_upper']==32
                and finite(admission['observed_unix']) and 0<=time.time()-admission['observed_unix']<=60
                and finite(job['forecast_GPUh']) and 0<job['forecast_GPUh']<=auth['billed_limit_GPUh'],
                'Fresh full CPU/source/quote/asset/storage admission required')
        gpu=admission['resources']['gpu']
        name,capability={'four_card':('RTX 6000 Ada','8.9'),'two_card':('RTX A6000','8.6')}[auth['host']]
        require(gpu['uuid']==auth['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==capability
                and gpu['utilization_percent']==0 and gpu['pids']==[] and 0<=gpu['memory_used_mib']<=1024
                and 0<=gpu['temperature_C']<90 and 0<=time.time()-gpu['unix']<=60,
                'Fresh selected physical GPU required')
        admit_host(current,auth['host'])
        before=copy.deepcopy(current);base=copy.deepcopy(current);now=time.time()
        steps=max(0,math.ceil((auth['billed_limit_GPUh']-base['available_gpu_hours'])/24))
        require(not steps or auth.get('standing_cap_increment24_authorized') is True,
                'This original card needs the standing24GPUh cap adjustment in its central exception')
        for _ in range(steps):
            prior=base['cap_gpu_hours'];base['cap_gpu_hours']+=24
            base.update(Pool.accounting(base))
            base['events'].append(dict(sequence=len(base['events'])+1,unix=now,type='P1_STANDING_CAP_INCREMENT24',
                job_id=run_id,previous_cap_GPUh=prior,cap_GPUh=base['cap_gpu_hours'],increment_GPUh=24))
        require(base['available_gpu_hours']>=auth['billed_limit_GPUh'],'Complete whole-card funds required')
        after=copy.deepcopy(base)
        job.update(status='RESERVED_OR_RUNNING',kind='V2',reserved_unix=now,central_ledger_host='four_card')
        after['jobs'][run_id]=job;after.update(Pool.accounting(after))
        after['events'].append(dict(sequence=len(after['events'])+1,unix=now,
            type='P1_COMPLETE146_RESERVE',job_id=run_id))
        value=dict(central_ledger_host='four_card',new_reservation=True,job=job,
            central_before=before,reservation_base=base,central_after=after,cap_increments24=steps,observed_unix=now)
        # Record the exact proposed transaction before its sole atomic ledger write.
        create(receipt,value);atomic_json(pool.path,after)
        return value


def settle(project,capture,expected_launch_sha256,*,cpu_validation=False):
    launch,billing=financial_terminal(capture,expected_launch_sha256,cpu_validation=cpu_validation)
    run_id=RUN
    require(launch['run_id']==RUN and launch['billed_limit_GPUh']>4,'Original complete P1 allocation only')
    authority=read_record_from_capture(capture,'authorization')
    validate_authority(authority,Path(project))
    require(capture['payload_actual_sha256'].get(SOURCE)==sha(__file__), 'Original settlement operator source required')
    project=Path(project);pool=Pool(project)
    receipt=project/'reports'/(run_id+'.central-settlement.json')
    bill_sha=capture['files']['billing']['sha256']
    with pool.transaction() as current:
        ledger_valid(current);job=current['jobs'][run_id]
        require(all(job[k]==launch[k] for k in JOB_IDENTITY),'Original central job/source differs')
        if receipt.exists():
            saved=read_record(receipt)
            audit_settlement(capture,expected_launch_sha256,saved,cpu_validation=cpu_validation)
            if current==saved['central_before']:
                atomic_json(pool.path,saved['central_after'])
            else:
                require(job==saved['central_after']['jobs'][run_id],'Original settlement transaction unresolved')
            return saved
        before=copy.deepcopy(current);after=copy.deepcopy(current)
        if job['status']=='SETTLED':
            require(job['actual_GPUh']==billing['actual_GPUh'] and job['billing_sha256']==bill_sha,
                    'Original settled cost differs; never charge again')
        else:
            require(job['status']=='RESERVED_OR_RUNNING','Unknown original central state')
            now=time.time();after['jobs'][run_id].update(status='SETTLED',actual_GPUh=billing['actual_GPUh'],
                billing_sha256=bill_sha,settled_unix=now)
            if billing['actual_GPUh']>launch['billed_limit_GPUh']:after['budget_overrun_recorded']=True
            after.update(Pool.accounting(after))
            after['events'].append(dict(sequence=len(after['events'])+1,unix=now,
                type='SETTLE_ACTUAL_ADDITIVELY',job_id=run_id))
        value=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=bill_sha,
            central_before=before,central_after=after)
        audit_settlement(capture,expected_launch_sha256,value,cpu_validation=cpu_validation)
        create(receipt,value)
        if before!=after:atomic_json(pool.path,after)
        return value
