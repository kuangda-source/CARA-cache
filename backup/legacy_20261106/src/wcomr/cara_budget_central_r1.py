"""One central reservation/settlement, with recoverable original transactions."""
import copy
import hashlib
import json
from pathlib import Path
import time

from .cara_budget_lifecycle_r1 import IDENTITY, JOB_IDENTITY, financial_terminal, audit_settlement
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_b36_dispatch_r2 import create
from .gpu_budget_pool_v2 import atomic_json, finite,sha
from .policy_price_terminal_r1 import require
from .wc73_execution_r1 import Pool, admit_host, hold
from .cara_budget_host_policy_r1 import HOSTS, POLICY_SHA256

RUN='cara-budget-calibration-14gpuh-r2-20261031'
STAGES={'four_card':'cara-budget-calibration-GPU-ada-r2-20261031',
        'two_card':'cara-budget-calibration-GPU-a6000-r3-20261031'}
SOURCE='src/wcomr/cara_budget_central_r1.py'


def original_absence(observations,project,*,hosts=tuple(STAGES)):
    require(bool(hosts) and set(observations)==set(hosts) and set(hosts)<=set(STAGES),
            'All required original handles must be observed')
    for host,row in observations.items():
        require(row['host']==host and row['stage']==str(Path(project)/'.sync'/STAGES[host])
                and row['run_id']==RUN and row['observation_complete'] is True
                and finite(row['observed_unix']) and 0<=time.time()-row['observed_unix']<=60
                and row['dispatch_records']==[] and row['container'] is None,
                'Original dispatch exists or is unknown on a registered host; recover it')


def ledger_valid(value):
    require(value is not None and value['cap_gpu_hours']==226
            and all(value[k]==v for k,v in Pool.accounting(value).items()),'Original central cap/totals required')
    old=[j for j in value['jobs'].values() if hold(j) and j['status']=='RESERVED_OR_RUNNING']
    require(sorted(j['billed_limit_GPUh'] for j in old)==[4.5,12.], 'Retain the two original financial liabilities')


def reserve(project,admission,observations):
    """Call only on four_card with the selected host's complete fresh admission."""
    project=Path(project);pool=Pool(project)
    receipt=project/'reports'/(RUN+'.central-reservation.json')
    auth=admission['authorization'];job={k:auth[k] for k in IDENTITY}
    require(auth['run_id']==RUN and auth['CPU_fixture_only'] is False
            and auth['execution_authorized'] is True and auth['direct_user_authorization'] is True
            and bool(auth['user_quote']) and auth['authorizes_replay'] is False
            and auth['billed_limit_GPUh']==14 and auth['host'] in HOSTS
            and auth.get('execution_host_policy_sha256')==POLICY_SHA256
            and auth['stage']==str(project/'.sync'/STAGES[auth['host']]),'One complete approved 14 GPUh card required')
    job.update(job_id=RUN,registration_sha256=admission['registration_sha256'],
        authorization_sha256=admission['authorization_sha256'],physical_paths=112,candidate_queries=51,
        forecast_GPUh=admission['forecast_GPUh'])
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
                require(current['jobs'].get(RUN)==original,'Reservation transaction unresolved; preserve original records')
            return saved
        require(RUN not in current['jobs'],'Original central job exists without receipt; recover it')
        require(not current.get('budget_overrun_recorded'), 'Unresolved actual overrun forbids a new reservation')
        original_absence(observations,project)
        require(admission['status']=='CALIBRATION_COMPLETE_FRESH_ADMISSION_NO_GPU'
                and admission['central_operator_sha256']==sha(__file__)
                and admission.get('required_host_whole_card_CPU_accepted') is True
                and admission.get('required_hosts')==list(HOSTS)
                and admission.get('execution_host_policy_sha256')==POLICY_SHA256
                and admission['physical_paths']==112 and admission['candidate_queries']==51
                and finite(admission['observed_unix']) and 0<=time.time()-admission['observed_unix']<=60
                and finite(job['forecast_GPUh']) and 0<job['forecast_GPUh']<=14,
                'Fresh full CPU/source/quote/asset/storage admission required')
        gpu=admission['resources']['gpu']
        name,capability={'four_card':('RTX 6000 Ada','8.9'),'two_card':('RTX A6000','8.6')}[auth['host']]
        require(gpu['uuid']==auth['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==capability
                and gpu['utilization_percent']==0 and gpu['pids']==[] and 0<=gpu['memory_used_mib']<=1024
                and 0<=gpu['temperature_C']<90 and 0<=time.time()-gpu['unix']<=60,
                'Fresh selected physical GPU required')
        admit_host(current,auth['host'])
        require(current['available_gpu_hours']>=14,'Complete whole-card funds required')
        before=copy.deepcopy(current);after=copy.deepcopy(current);now=time.time()
        job.update(status='RESERVED_OR_RUNNING',kind='V2',reserved_unix=now,central_ledger_host='four_card')
        after['jobs'][RUN]=job;after.update(Pool.accounting(after))
        after['events'].append(dict(sequence=len(after['events'])+1,unix=now,
            type='CALIBRATION_COMPLETE14_RESERVE',job_id=RUN))
        value=dict(central_ledger_host='four_card',new_reservation=True,job=job,
            central_before=before,central_after=after,observed_unix=now)
        # Record the exact proposed transaction before its sole atomic ledger write.
        create(receipt,value);atomic_json(pool.path,after)
        return value


def settle(project,capture,expected_launch_sha256,*,cpu_validation=False):
    launch,billing=financial_terminal(capture,expected_launch_sha256,cpu_validation=cpu_validation)
    require(launch['run_id']==RUN and launch['billed_limit_GPUh']==14,'Original whole calibration only')
    require(capture['payload_actual_sha256'].get(SOURCE)==sha(__file__), 'Original settlement operator source required')
    project=Path(project);pool=Pool(project)
    receipt=project/'reports'/(RUN+'.central-settlement.json')
    bill_sha=capture['files']['billing']['sha256']
    with pool.transaction() as current:
        ledger_valid(current);job=current['jobs'][RUN]
        require(all(job[k]==launch[k] for k in JOB_IDENTITY),'Original central job/source differs')
        if receipt.exists():
            saved=read_record(receipt)
            audit_settlement(capture,expected_launch_sha256,saved,cpu_validation=cpu_validation)
            if current==saved['central_before']:
                atomic_json(pool.path,saved['central_after'])
            else:
                require(job==saved['central_after']['jobs'][RUN],'Original settlement transaction unresolved')
            return saved
        before=copy.deepcopy(current);after=copy.deepcopy(current)
        if job['status']=='SETTLED':
            require(job['actual_GPUh']==billing['actual_GPUh'] and job['billing_sha256']==bill_sha,
                    'Original settled cost differs; never charge again')
        else:
            require(job['status']=='RESERVED_OR_RUNNING','Unknown original central state')
            now=time.time();after['jobs'][RUN].update(status='SETTLED',actual_GPUh=billing['actual_GPUh'],
                billing_sha256=bill_sha,settled_unix=now)
            if billing['actual_GPUh']>14:after['budget_overrun_recorded']=True
            after.update(Pool.accounting(after))
            after['events'].append(dict(sequence=len(after['events'])+1,unix=now,
                type='SETTLE_ACTUAL_ADDITIVELY',job_id=RUN))
        value=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=bill_sha,
            central_before=before,central_after=after)
        audit_settlement(capture,expected_launch_sha256,value,cpu_validation=cpu_validation)
        create(receipt,value)
        if before!=after:atomic_json(pool.path,after)
        return value
