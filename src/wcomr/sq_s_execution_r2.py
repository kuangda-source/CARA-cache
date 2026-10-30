"""Torch-free S source/authority validation and a single central envelope.

R2 runs the complete ten-role alternative. Preparation and Q1 approval cannot
authorize it. Failed allocations retain their bill and cannot retry.
"""
import copy
import json
from pathlib import Path
import socket
import time

from .gpu_budget_pool_v2 import finite,sha
from .sq_s_data_terminal_r2 import digest,require
from .sq_s_spec_r2 import (RUN,SCOPE,PROFILE,IDENTITY,RESOURCE,ASSETS,MODE,RISK,HISTORY,PHYSICAL,
    QUOTES,LIMITS,COUNTS,IDENTITY_SHA,RESOURCE_SHA,UPPER_SHA,OTHER_A6000,EXECUTION_CRITICAL,stage_path)
from .wc73_execution_r1 import Pool as CentralPool,admit_host


def read(path):return json.loads(Path(path).read_text())


def make_check_schedule(authority,guardian,quote,profile):
    """Derive both checks only from the original host guardian start."""
    require(guardian['billing_clock_owner']=='HOST_GUARDIAN' and all(guardian[key]==authority[key]
        for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'))
        and authority['run_id']==RUN and quote['host']==authority['host']
        and 0<quote['forecast_complete_GPUh']<=authority['whole_GPUh']==LIMITS[authority['host']],
        'Original S guardian identity and complete forecast required for checks')
    start=guardian['started_unix'];monotonic=guardian['started_monotonic']
    require(finite(start) and finite(monotonic) and min(start,monotonic)>=0,'Actual S allocation start required')
    return dict(run_id=RUN,launch_id=authority['launch_id'],gpu_uuid=authority['gpu_uuid'],
        source_revision=authority['source_revision'],started_unix=start,billing_clock_owner='HOST_GUARDIAN',
        allocation_started_monotonic=monotonic,
        halfway_unix=start+quote['forecast_complete_GPUh']*1800,
        expected_GPU_terminal_unix=start+quote['forecast_complete_GPUh']*3600,
        expected_terminal_unix=start+quote['forecast_complete_GPUh']*3600+profile['CPU_post_wall_seconds_max'],
        hard_GPU_terminal_unix=start+authority['whole_GPUh']*3600,scheduler_created=False,
        midway_scope='Original identity/progress/thermal/exclusivity/budget only, no partial scientific scores',
        terminal_scope='Original exit, retained failures, complete artifacts, release, exact central bill, then CPU analysis',
        authorizes_retry=False)


class Pool(CentralPool):
    def reserve(self,job,gpu):
        host=job['host'];limit=LIMITS[host]
        require(job['job_id']==job['run_id']==RUN and job['scope_counts']==COUNTS
            and job['billed_limit_GPUh']==limit and 0<job['forecast_GPUh']<=limit,
            'Exact complete S whole envelope required')
        name,cap={'two_card':('RTX A6000','8.6'),'four_card':('RTX 6000 Ada','8.9')}[host]
        require(gpu['uuid']==job['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==cap
            and not gpu['pids'] and gpu['utilization_percent']==0
            and 0<=gpu['memory_used_mib']<=1024 and 0<=time.time()-gpu['unix']<=60
            and finite(gpu['temperature_C']) and 0<=gpu['temperature_C']<70
            and (host!='two_card' or gpu['uuid']==OTHER_A6000),'Fresh selected S GPU required')
        with self.transaction() as value:
            require(value is not None and value['cap_gpu_hours']==226
                and not value.get('budget_overrun_recorded') and RUN not in value['jobs'],
                'Original S reservation exists or central cap differs; recover only')
            admit_host(value,host)
            require(self.accounting(value)['available_gpu_hours']>=limit,'Whole S limit exceeds available funds')
            value['jobs'][RUN]=dict(copy.deepcopy(job),kind='V2',status='RESERVED_OR_RUNNING',
                reserved_unix=time.time(),central_ledger_host='four_card')
            self.commit(value,dict(type='SQ_S_COMPLETE_ONCE_ONLY_RESERVATION_R2',job_id=RUN))
            return copy.deepcopy(value)


def validate_source(project,stage):
    project,stage=Path(project),Path(stage);reg=read(stage/'registration.json');host=reg['host']
    require(reg['namespace']=='SQ_S_COMPLETE_EXECUTION_R2' and stage==stage_path(project,host)
        and not stage.is_symlink() and reg['stage']==str(stage)
        and reg['native_hostname']==socket.gethostname(),'Original independent S host/stage required')
    required=set(EXECUTION_CRITICAL)|{SCOPE,PROFILE,IDENTITY,RESOURCE,ASSETS,MODE,RISK,HISTORY,PHYSICAL[host],QUOTES[host]}
    require(required<=set(reg['payload_sha256']),'S source registration is incomplete')
    for name,expected in reg['payload_sha256'].items():
        relative=Path(name);path=stage/relative
        require(not relative.is_absolute() and '..' not in relative.parts and not path.is_symlink()
            and stage.resolve() in path.resolve().parents and sha(path)==expected,'Staged S source differs: '+name)
    runtime=(project/'runtime').resolve()
    for name,expected in reg['runtime_source_sha256'].items():
        relative=Path(name);path=project/'runtime'/relative
        require(not relative.is_absolute() and '..' not in relative.parts
            and runtime in path.resolve().parents and sha(path)==expected,'Pinned S runtime differs')
    upper,physical,identity,contract,profile=(read(stage/name) for name in
        (SCOPE,PHYSICAL[host],IDENTITY,RESOURCE,PROFILE))
    require(identity['identity_sha256']==IDENTITY_SHA==digest({k:v for k,v in identity.items() if k!='identity_sha256'})
        and upper['scope_sha256']==UPPER_SHA==digest({k:v for k,v in upper.items() if k!='scope_sha256'})
        and contract['contract_sha256']==RESOURCE_SHA==digest({k:v for k,v in contract.items() if k!='contract_sha256'})
        and not upper['CPU_fixture_only'] and not physical['CPU_fixture_only'] and not contract['CPU_fixture_only'],
        'Original real S scientific/resource identities differ')
    require(all(reg['payload_sha256'].get(name)==value for name,value in identity['numerical_source_sha256'].items())
        and all(reg['runtime_source_sha256'].get(name)==value for name,value in identity['runtime_source_sha256'].items())
        and reg['payload_sha256'][MODE]==identity['shared_eval_mode_sha256'],
        'Original S numerical, runtime or shared-eval source is incomplete')
    require(physical['physical_scope_sha256']==digest({k:v for k,v in physical.items() if k!='physical_scope_sha256'})
        and physical['host']==host and physical['upper_scope_sha256']==UPPER_SHA
        and physical['execution_identity_sha256']==IDENTITY_SHA and physical['counts']==COUNTS
        and physical['reused_slot_ids']==[] and physical['physical_slots']==upper['slots'],
        'Only the complete all-new ten-role S alternative is admitted')
    require(all(profile[key]==value for key,value in dict(host_CPUs=2,host_RAM_GiB=40,
        CUDA_allocator_fraction_max=.9,output_image_GiB=32,streaming_tensor_artifact_cap_GiB=28,
        output_file_GiB_max=2,monitor_file_MiB_max=512,control_journal_MiB=48,billing_clock_owner='HOST_GUARDIAN',
        supervisor_interval_diagnostic_only=True,one_owned_GPU_job_per_host=True).items())
        and profile['guardian_release_margin_seconds']>=180 and profile['stop_release_margin_seconds']>=180
        and profile['minimum_host_MemAvailable_GiB']>=52 and profile['minimum_output_free_MiB']>=512
        and profile['minimum_storage_host_free_GiB']>=4 and profile['maximum_idle_admission_temperature_C']<=70
        and profile['CPU_pre_wall_seconds_max']==7200 and profile['CPU_post_wall_seconds_max']==3600,
        'Original S whole-allocation resource boundary differs')
    quote=read(stage/QUOTES[host])
    require(quote['host']==host and quote['physical_counts']==COUNTS
        and quote['physical_scope_sha256']==physical['physical_scope_sha256']
        and quote['upper_scope_sha256']==UPPER_SHA and quote['S_execution_identity_sha256']==IDENTITY_SHA
        and quote['resources_proposed']['resource_contract_sha256']==RESOURCE_SHA
        and quote['proposed_hard_limit_GPUh']==LIMITS[host]
        and 0<quote['forecast_complete_GPUh']<=LIMITS[host]
        and all(reg['payload_sha256'].get(name)==value for name,value in quote['source_evidence_sha256'].items()),
        'Complete original S whole quote or source inventory differs')
    from .sq_s_risk_post_r3 import validated_domain
    rule=read(stage/RISK);history=read(stage/HISTORY);validated_domain(upper,rule,history)
    require(history['rule_sha256']==rule['rule_sha256'] and history['GPU_submissions']==0
        and history['producer_sha256']==reg['payload_sha256']['scripts/prepare_cara_sq_s_history_support_r3.py']
        and all(reg['payload_sha256'].get(rule['legacy_source_ref'][key])==value
            for key,value in rule['legacy_source_sha256'].items())
        and reg['payload_sha256'].get(rule['method_ref'])==rule['method_sha256']
        and reg['payload_sha256'].get(rule['support_ref'])==rule['support_sha256'],
        'Original pre-data S risk rule/history source binding differs')
    return dict(upper=upper,physical=physical,identity=identity,resource_contract=contract,
        execution_profile=profile,quote=quote,mode_types=read(stage/MODE)['module_types']),reg


def assets_current(project,stage):
    """Recheck the complete prior streaming digest receipt by current file identity."""
    project,stage=Path(project),Path(stage);reg=read(stage/'registration.json')
    specification=read(stage/ASSETS);proof=read(stage/'S-asset-verification.json')
    require(proof['status']=='S_MODEL_AND_AUXILIARY_ASSETS_SHA_VERIFIED_CPU_ONLY'
        and proof['host']==reg['host'] and proof['asset_contract_sha256']==sha(stage/ASSETS)
        and proof['GPU_submissions']==0 and len(proof['files'])==len(specification['files'])==20,
        'Complete same-host S model/auxiliary digest receipt required')
    for descriptor,row in zip(specification['files'],proof['files']):
        path=project/descriptor['path'];stat=path.stat()
        require(not path.is_symlink() and row['path']==descriptor['path'] and row['digest']==descriptor['digest']
            and row['stamp']==[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns],
            'S asset changed after its full digest')
    for link in specification['snapshot_links']:
        path=project/link['path']
        require(path.is_symlink() and path.resolve(strict=True)==(project/link['target']).resolve(strict=True),
            'Original S asset snapshot link differs')
    return True


def validate_authority(project,stage,bundle,reg,*,authority=None):
    stage=Path(stage);auth=read(stage/'pg-GPU-authorization.json') if authority is None else authority
    host=reg['host']
    require(auth.get('direct_user_authorization') is True and bool(auth.get('user_quote'))
        and auth.get('authorizes_S_collection') is True and auth.get('authorizes_Q1_collection') is False
        and auth.get('authorizes_retry') is False and auth.get('whole_quote_frozen_by_this_approval') is True
        and auth.get('engineering_allowances_accepted_for_this_card') is True,
        'Separate complete S approval required; Q1 or preparation does not grant it')
    expected=dict(run_id=RUN,host=host,scope_counts=COUNTS,whole_GPUh=LIMITS[host],
        scope_sha256=sha(stage/SCOPE),physical_scope_sha256=bundle['physical']['physical_scope_sha256'],
        execution_identity_sha256=IDENTITY_SHA,S_resource_contract_sha256=RESOURCE_SHA,
        source_revision=reg['source_revision'],registration_sha256=sha(stage/'registration.json'),
        quote_sha256=sha(stage/QUOTES[host]),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),
        asset_proof_sha256=sha(stage/'S-asset-verification.json'),
        storage_contract_sha256=sha(stage/'history104-storage.json'))
    require(all(auth.get(key)==value for key,value in expected.items()) and bool(auth.get('launch_id'))
        and bool(auth.get('gpu_uuid')) and (host!='two_card' or auth['gpu_uuid']==OTHER_A6000),
        'Exact source, host, whole-quote and single S approval binding required')
    proof=read(stage/'execution-CPU-proof.json')
    require(proof['passed'] is True and proof['GPU_submissions']==0 and proof['host']==host
        and proof['source_revision']==reg['source_revision']
        and proof['actual_platform']['system']=='Linux' and proof['skipped']==0
        and proof['full_S_entry_CPU_accepted'] is True and proof['native_parser_accepted'] is True
        and proof['payload_sha256']==reg['payload_sha256']
        and set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256'])
        and all(reg['payload_sha256'].get(name)==value for name,value in proof['critical_source_sha256'].items()),
        'Full same-host affected S production-entry CPU proof required')
    profile=bundle['execution_profile'];storage=read(stage/'history104-storage.json');selected=profile['hosts'][host]
    require(storage['run_id']==RUN and storage['output_mount']==str(Path(project)/'outputs'/RUN)==selected['output_mount']
        and storage['image_path']==selected['image_path'] and storage['journal_path']==selected['journal_path']
        and storage['image_bytes']==32*2**30 and storage['journal_bytes']==48*2**20
        and storage['minimum_output_free_bytes']>=profile['minimum_output_free_MiB']*2**20
        and storage['minimum_host_free_bytes']>=profile['minimum_storage_host_free_GiB']*2**30
        and storage['minimum_free_inodes']>=1024,
        'Original S private output and independent journal required')
    assets_current(project,stage)
    return auth


def validate(project,stage):
    bundle,reg=validate_source(project,stage);auth=validate_authority(project,stage,bundle,reg)
    stage=Path(stage);envelope=read(stage/'central-reservation.json');job=envelope['job']
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
        and job['status']=='RESERVED_OR_RUNNING','Original central S envelope is not held')
    for key,value in dict(job_id=RUN,run_id=RUN,host=auth['host'],gpu_uuid=auth['gpu_uuid'],
        launch_id=auth['launch_id'],scope_counts=COUNTS,billed_limit_GPUh=auth['whole_GPUh'],
        scope_sha256=auth['scope_sha256'],physical_scope_sha256=auth['physical_scope_sha256'],
        source_revision=reg['source_revision'],registration_sha256=auth['registration_sha256'],
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        forecast_GPUh=bundle['quote']['forecast_complete_GPUh']).items():
        require(job.get(key)==value,'Original central S envelope differs: '+key)
    binding=read(stage/'launch-binding.json')
    require(binding['authorization_sha256']==sha(stage/'pg-GPU-authorization.json')
        and binding['central_reservation_sha256']==sha(stage/'central-reservation.json'),
        'Original S launch/envelope bytes differ')
    return bundle,reg,auth


def check_host_bill(authority,billing,release,guardian,*,billing_sha256):
    require(release['GPU_released'] is True and release['original_process_exited'] is True
        and release['allocation_release_accepted'] is True and guardian['mode_restoration']['restored'] is True
        and guardian['container_terminal_witness']['complete'] is True,'Original S allocation closure required')
    require(release['billing_sha256']==guardian['billing_sha256']==billing_sha256
        and billing['billing_clock_owner']==guardian['billing_clock_owner']=='HOST_GUARDIAN'
        and billing['status']=='SQ_S_ORIGINAL_WALL_BILL' and billing['wall_interval_complete'] is True
        and billing['supervisor_bill_is_diagnostic_only'] is True
        and guardian['status']=='SQ_S_HOST_GUARDIAN_TERMINAL','Original complete S host allocation bill required')
    start,end=billing['started_monotonic'],billing['ended_monotonic']
    require(finite(start) and finite(end) and 0<=start<=end
        and (start,end)==(guardian['started_monotonic'],guardian['ended_monotonic'])
        and billing['started_unix']==guardian['started_unix'] and billing['ended_unix']==guardian['ended_unix']
        and billing['wall_seconds']==end-start and billing['actual_GPUh']==(end-start)/3600,
        'Exact full S admission-through-release interval differs')
    require(release['container_terminal_witness']==guardian['container_terminal_witness']
        and release['mode_restoration']==guardian['mode_restoration']
        and release['cost_settled'] is False and release['authorizes_retry'] is False,
        'Original S allocation release witness differs')
    for key in ('run_id','launch_id','host','gpu_uuid','source_revision','scope_sha256'):
        require(billing[key]==release[key]==guardian[key]==authority[key],'Original S financial identity differs: '+key)
    require(billing['run_id']==RUN and billing['billed_limit_GPUh']==authority['whole_GPUh']==LIMITS[authority['host']],
        'Original whole S limit differs')


def settle_central(pool,authority,billing,release,guardian,*,billing_sha256):
    check_host_bill(authority,billing,release,guardian,billing_sha256=billing_sha256)
    before=pool.read();job=before['jobs'][RUN]
    require(all(job[key]==authority[key] for key in
        ('run_id','launch_id','host','gpu_uuid','source_revision','scope_sha256'))
        and job['billed_limit_GPUh']==authority['whole_GPUh'],'Wrong original S central reservation')
    after=pool.settle(RUN,billing['actual_GPUh'],billing_sha256)
    require(all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN),
        'S settlement changed another central job')
    return dict(central_ledger_host='four_card',run_id=RUN,launch_id=authority['launch_id'],
        actual_GPUh=billing['actual_GPUh'],billing_sha256=billing_sha256,cost_settled=True,
        central_before=before,central_after=after,job=after['jobs'][RUN],scientific_acceptance_implied=False)
