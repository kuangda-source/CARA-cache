"""Q1 authority, terminal classification and one central budget envelope.

Host-side code is deliberately independent of torch/CUDA imports. A numeric
original-control failure is a terminal diagnostic; it grants no codec choice
or retry. All failed executions still require exact settlement.
"""
import copy
import json
from pathlib import Path
import time

from .gpu_budget_pool_v2 import sha, finite
from .sq_q1_spec_r1 import (RUN,SCOPE,PROFILE,QUOTES,COUNTS,STATE_KEYS,LIMITS,
                            CHECKPOINT_SHA,MANIFEST_SHA,EXECUTION_CRITICAL,RUNTIME_REQUIRED)
from .wc73_execution_r1 import Pool as CentralPool, admit_host


def read(path):return json.loads(Path(path).read_text())


def require(condition,message):
    if not condition:raise ValueError(message)


class Pool(CentralPool):
    def reserve(self,job,gpu):
        host=job['host'];limit=LIMITS[host]
        require(job['job_id']==job['run_id']==RUN and job['scope_counts']==COUNTS,
                'Only the complete registered Q1 scope')
        require(job['billed_limit_GPUh']==limit and 0<job['forecast_GPUh']<=limit,
                'Exact host Q1 whole quote required')
        name,cap={'two_card':('RTX A6000','8.6'),'four_card':('RTX 6000 Ada','8.9')}[host]
        require(gpu['uuid']==job['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==cap
                and not gpu['pids'] and gpu['utilization_percent']==0
                and 0<=gpu['memory_used_mib']<=1024 and 0<=time.time()-gpu['unix']<=60,
                'Fresh idle physical Q1 GPU required')
        with self.transaction() as value:
            require(value is not None and value['cap_gpu_hours']==226
                    and not value.get('budget_overrun_recorded'),'Valid original central ledger required')
            require(RUN not in value['jobs'],'Recover original Q1 envelope; never replay on either host')
            admit_host(value,host)
            require(self.accounting(value)['available_gpu_hours']>=limit,'Whole Q1 limit exceeds available funds')
            value['jobs'][RUN]=dict(copy.deepcopy(job),kind='V2',status='RESERVED_OR_RUNNING',
                reserved_unix=time.time(),central_ledger_host='four_card')
            self.commit(value,dict(type='SQ_Q1_ONCE_ONLY_CENTRAL_RESERVATION',job_id=RUN))
            return copy.deepcopy(value)


def validate(project,stage):
    project,stage=Path(project),Path(stage)
    registration=read(stage/'registration.json')
    require(registration['namespace']=='SQ_Q1_EXECUTION_R1' and stage.parent==project/'.sync',
            'Independent registered Q1 stage required')
    require(all(sha(stage/name)==expected for name,expected in registration['payload_sha256'].items()),
            'Staged Q1 source differs')
    require(set(EXECUTION_CRITICAL)<=set(registration['payload_sha256'])
            and set(RUNTIME_REQUIRED)<=set(registration['runtime_source_sha256']),
            'Q1 execution or original runtime source binding is incomplete')
    require(all(sha(project/'runtime'/name)==expected for name,expected in registration['runtime_source_sha256'].items()),
            'Pinned runtime differs')
    scope=read(stage/SCOPE);scope_sha=sha(stage/SCOPE)
    require(scope['scope_counts']==COUNTS,'Complete 111-pair Q1 denominator differs')
    authority=read(stage/'pg-GPU-authorization.json')
    host=authority['host'];quote=read(stage/QUOTES[host]);profile=read(stage/PROFILE)
    storage=read(stage/'history104-storage.json')
    require(authority['storage_contract_sha256']==sha(stage/'history104-storage.json')
            and storage['run_id']==RUN and storage['output_mount']==str(project/'outputs'/RUN)
            and storage['image_path']==profile['hosts'][host]['image_path']
            and storage['journal_path']==profile['hosts'][host]['journal_path']
            and storage['image_bytes']==profile['output_image_GiB']*2**30,
            'Original Q1 private storage identity differs')
    require(authority.get('direct_user_authorization') is True and bool(authority.get('user_quote')),
            'Direct human authorization for this new Q1 card is required')
    require(authority['run_id']==RUN and authority['scope_sha256']==scope_sha
            and authority['scope_counts']==COUNTS and authority['whole_GPUh']==LIMITS[host]
            and authority['authorizes_retry'] is False and authority['authorizes_S_collection'] is False,
            'Exact Q1-only authority; no retry or S collection')
    require(host in profile['hosts'] and quote['host']==host and quote['scope_counts']==COUNTS
            and quote['input_source_sha256'][SCOPE]==scope_sha
            and quote['proposed_hard_limit_GPUh']==LIMITS[host]
            and authority['quote_sha256']==sha(stage/QUOTES[host]),'Authorized host/whole quote differs')
    require(authority['source_revision']==registration['source_revision']
            and authority['registration_sha256']==sha(stage/'registration.json'),'Authorization source differs')
    proof=read(stage/'execution-CPU-proof.json')
    require(proof.get('passed') is True and proof.get('GPU_submissions')==0
            and authority['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json'),
            'Affected GPU-entry/lifecycle CPU acceptance required')
    require(set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256']) and all(
        registration['payload_sha256'].get(name)==expected
        for name,expected in proof['critical_source_sha256'].items()),'Untested Q1 execution source')
    envelope=read(stage/'central-reservation.json');job=envelope['job']
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
            and job['status']=='RESERVED_OR_RUNNING','Original central reservation is not held')
    for key,expected in dict(job_id=RUN,run_id=RUN,host=host,gpu_uuid=authority['gpu_uuid'],
        launch_id=authority['launch_id'],scope_counts=COUNTS,billed_limit_GPUh=LIMITS[host],
        scope_sha256=scope_sha,source_revision=registration['source_revision'],
        registration_sha256=authority['registration_sha256'],
        authorization_sha256=sha(stage/'pg-GPU-authorization.json')).items():
        require(job.get(key)==expected,'Original central envelope differs: '+key)
    require(job['forecast_GPUh']==quote['forecast_complete_GPUh'],'Central envelope whole forecast differs')
    binding=read(stage/'launch-binding.json')
    require(binding['authorization_sha256']==sha(stage/'pg-GPU-authorization.json')
            and binding['central_reservation_sha256']==sha(stage/'central-reservation.json'),
            'Original launch/envelope binding differs')
    return scope,registration,authority


def check_collection(scope,result):
    """Technical collection acceptance, including a stopped numeric preview."""
    require(result['CPU_fixture'] is False and result['actual_CUDA'] is True
            and result['scope_counts']==scope['scope_counts']==COUNTS,'CPU or foreign collection cannot accept Q1 GPU')
    require(result['selections'] is None and result['partial_state_selection'] is False,
            'GPU-held collection selected bit directions')
    evidence=result['input_evidence']
    require(evidence['checkpoint_sha256']==CHECKPOINT_SHA and evidence['manifest_sha256']==MANIFEST_SHA
            and evidence['original_B1_files_verified']==32
            and evidence['condition_schema']=='ACTUAL_RUNTIME_MODULE','Original model/assets/schema not verified')
    calls=result['head_calls']
    require(set(calls)=={'warm','controls','formal'} and all(
        type(v['started']) is int and type(v['completed']) is int
        and 0<=v['completed']==v['started'] for v in calls.values()),'Incomplete or invalid head calls')
    require(all(result[key]==0 for key in ('new_deep_pairs','new_parent_paths','new_videos')),
            'Q1 scope acquired deep calls, parents or videos')
    states=result['states'];completed=result['completed_states']
    require(type(completed) is int and 0<=completed<=12 and len(states)==completed
            and [(r['prompt'],r['step']) for r in states]==list(STATE_KEYS[:completed]),
            'Original ordered Q1 prefix required')
    for row in states:
        require(row['original_C_exact'] and row['state_roundtrip_equal'] and row['formal_C_pairs']==8
                and [r['role'] for r in row['rows']]==scope['formal_roles'],'Formal C/control roles differ')
    if result['complete_Q1_cohort']:
        require(result['status']=='Q1_COMPLETE_ACTUAL_OUTPUTS_PENDING_INDEPENDENT_ACCEPTANCE'
                and result['failure'] is None and result['completed_states']==12,'Incomplete Q1 terminal')
        require(calls=={k:dict(started=n,completed=n) for k,n in (('warm',4),('controls',26),('formal',192))},
                'Complete Q1 actual head denominator differs')
        return dict(kind='COMPLETE_NUMERIC_COLLECTION',complete=True,selection_allowed_after_release=True)
    require(result['status']=='Q1_ORIGINAL_PARITY_NOT_ACCEPTED_NO_CODEC_SELECTION'
            and result['failure'] is not None and 0<=result['completed_states']<12,
            'Unknown partial Q1 outcome')
    failure=result['failure'];kind=failure['kind']
    require((failure['prompt'],failure['step'])==STATE_KEYS[completed],
            'Stopped original-control state does not follow the completed prefix')
    formal=16*completed
    if kind=='ORIGINAL_C_AND_DENSE_HEAD':
        require(completed==0,'Preview may only fail before any formal state')
    elif kind=='STORED_DENSE_HIDDEN_HEAD':
        require(completed>0,'First state uses the combined preview')
    elif kind=='FORMAL_ORIGINAL_C':formal+=2
    else:raise ValueError('Unknown original numerical gate failure')
    require(calls=={k:dict(started=n,completed=n) for k,n in (
        ('warm',4),('controls',4+2*completed),('formal',formal))},
        'Stopped original-control actual head denominator differs')
    return dict(kind='ORIGINAL_NUMERIC_GATE_NOT_ACCEPTED',complete=False,selection_allowed_after_release=False)


def settle_central(pool,authority,billing,release,guardian,*,billing_sha256):
    """Settle the original host bill once; numerical failure is not free work."""
    require(release['GPU_released'] and release['original_process_exited']
            and guardian['mode_restoration']['restored'],'Original GPU/context/mode release is not proven')
    require(release['billing_sha256']==billing_sha256,'Original captured billing bytes differ')
    require(finite(billing['wall_seconds']) and billing['wall_seconds']>=0
            and billing['actual_GPUh']==billing['wall_seconds']/3600,'Exact finite original wall bill required')
    for key in ('run_id','launch_id','host','gpu_uuid','source_revision','scope_sha256'):
        require(billing[key]==release[key]==authority[key],'Original bill/release/authority differs: '+key)
    require(billing['run_id']==RUN and billing['billed_limit_GPUh']==authority['whole_GPUh'],
            'Wrong Q1 bill or whole limit')
    before=pool.read();job=before['jobs'][RUN]
    for key in ('run_id','launch_id','host','gpu_uuid','source_revision','scope_sha256'):
        require(job[key]==authority[key],'Wrong original central job: '+key)
    require(job['billed_limit_GPUh']==authority['whole_GPUh'],'Original central limit changed')
    after=pool.settle(RUN,billing['actual_GPUh'],billing_sha256)
    require(all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN),
            'Unrelated central reservations changed')
    return dict(central_ledger_host='four_card',run_id=RUN,launch_id=authority['launch_id'],
        billing_sha256=release['billing_sha256'],actual_GPUh=billing['actual_GPUh'],
        job=after['jobs'][RUN],cap_GPUh=after['cap_gpu_hours'],cost_settled=True,
        central_before=before,central_after=after,
        scientific_acceptance_implied=False)
