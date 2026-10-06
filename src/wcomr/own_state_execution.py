"""A separate three-scene scope, actual CPU bindings and inclusive expense."""
import copy
import hashlib
import json
import math
from pathlib import Path

PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
CARD='WC-W1-OWN-STATE-SHADOW-R1-20261006-A'
RUN='wc-w1-own-state-shadow-r1'
INDICES=[4,7,0]
NAMES=['misc_13398218_3840_2160_60fps','av_51b45829-502e-4143-9c32-c026bd6ab191',
       'av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632']
CALLS=[45,46,67,68]
AUTH24='manifests/budget_authorization_20261005_wc_24gpuh.json'
APPROVAL='manifests/wc_w1_own_state_gpu_authorization_20261006.json'
INFLIGHT='wc_w1_own_state_inflight'
LIMITS={'timeout_seconds':1800,'child_timeout_seconds':1770,'kill_grace_seconds':5,
        'admission_allowance_seconds':30,'minimum_disk_free_bytes':4*1024**3}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def valid_sha(s,n=64):return type(s) is str and len(s)==n and all(c in '0123456789abcdef' for c in s)


def validate_config(c,*,selected=False):
    if (c['card']!=CARD or c['run_id']!=RUN or c['expected_project_root']!=PROJECT
            or c['sample_indices']!=INDICES or c['sample_names']!=NAMES or c['fixed_CFG_calls']!=CALLS
            or c['planned_scenes']!=3 or c['planned_observations']!=12 or c['seed']!=0
            or c['execution_limits']!=LIMITS or c['new_training_or_human_review'] is not False
            or c['independent_confirmation'] is not False or c['teacher_written_to_deployment'] is not False
            or c['historical_OFF_bridge_required'] is not True or c['all_scenes_must_improve'] is not False):
        raise ValueError('Registered complete three-scene diagnostic scope differs')
    required={'src/wcomr/own_state_sampling.py','src/wcomr/own_state_shadow.py',
        'src/wcomr/own_state_execution.py','src/wcomr/own_state_summary.py',
        'scripts/run_w1_own_state.py','scripts/supervise_w1_own_state.py',
        'scripts/audit_w1_own_state_terminal.py','scripts/summarize_w1_own_state.py',
        'tests/check_w1_own_state_production_cpu.py',AUTH24}
    payload=c['payload_sha256'];core=c['core_cpu_payload_sha256']
    if (len(core)!=13 or not required.issubset(payload)
            or any(payload.get(n)!=d for n,d in core.items())
            or any(not valid_sha(d) for d in payload.values())
            or not all(valid_sha(c[k]) for k in ['core_cpu_receipt_sha256','prereg_sha256','old_replay_sha256','cost_report_sha256'])):
        raise ValueError('Passed core and production source bindings incomplete')
    for n in payload:
        p=Path(n)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Payload escapes isolated stage')
    binding=c.get('execution_scope_authority')
    if selected:
        expected={'approved_card':CARD,'run_id':RUN,'single_run_inclusive_cap_seconds':1800,
            'sample_indices':INDICES,'fixed_CFG_calls':CALLS,'planned_scenes':3,'planned_observations':12,
            'usage_reset':False}
        cpu=c.get('production_cpu_payload_sha256',{})
        if (c['GPU_execution_selected'] is not True or not isinstance(binding,dict)
                or set(binding)!=set(expected)|{'source_user_text','approval_ref','approval_sha256'}
                or any(type(binding.get(k)) is not type(v) or binding[k]!=v for k,v in expected.items())
                or binding['approval_ref']!=APPROVAL or not valid_sha(binding['approval_sha256'])
                or payload.get(APPROVAL)!=binding['approval_sha256']
                or type(binding['source_user_text']) is not str or not binding['source_user_text'].strip()
                or type(c['gpu_uuid']) is not str or not c['gpu_uuid'].startswith('GPU-')
                or not valid_sha(c.get('production_cpu_receipt_sha256'))
                or set(cpu)!=(set(payload)-{APPROVAL})|{'own-state-config.json'}
                or any(payload.get(n)!=d for n,d in cpu.items() if n!='own-state-config.json')):
            raise ValueError('Separate human scope and unchanged production CPU proof required')
    elif (c['GPU_execution_selected'] is not False or binding is not None
            or c['gpu_uuid'] is not None or APPROVAL in payload):
        raise ValueError('Unselected CPU draft has no GPU authority')
    return {'status':'OWN_STATE_COMPLETE_SCOPE_PASS_NOT_GPU','scenes':3,'observations':12,'selected':selected}


def validate_stage(project,stage,runtime,c,*,selected=False):
    validate_config(c,selected=selected)
    if (project.resolve()!=Path(PROJECT).resolve() or runtime.resolve()!=(project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Existing project/runtime and independent stage required')
    for n,d in c['payload_sha256'].items():
        if sha(stage/n)!=d:raise ValueError('Production payload drift: '+n)
    for n,d in c['upstream_source_sha256'].items():
        if sha(runtime/n)!=d:raise ValueError('Runtime drift: '+n)
    for n,d in c['project_input_sha256'].items():
        if n!='reports/budget.json' and sha(project/n)!=d:raise ValueError('Project input drift: '+n)
    prereg=read(stage/c['prereg_ref']);old=read(stage/'reports/w1_replay_r1_runner.json')
    if (sha(stage/c['prereg_ref'])!=c['prereg_sha256'] or prereg['future_measurement']['scenes']!=NAMES
            or prereg['future_measurement']['fixed_CFG_calls']!=CALLS
            or sha(stage/'reports/w1_replay_r1_runner.json')!=c['old_replay_sha256']):
        raise ValueError('Original registration or old OFF changed')
    for i,name in zip(INDICES,NAMES):
        r=old['cases'][i];off=r['scalar_off'];entry=old['protocol']['samples'][i]
        if (r['name']!=name or off['outcome']!='ACCEPTED' or r['sample']['seed']!=0
                or off['trace']!=entry['schedule'] or any(off['trace'][k-1]['deep_executed'] for k in CALLS)
                or sha(off['video_path'])!=off['video_sha256']):
            raise ValueError('Actual historical candidate/mask/video differs')
    corepath=project/c['core_cpu_stage']/'receipt.json'
    core=read(corepath)
    if (sha(corepath)!=c['core_cpu_receipt_sha256'] or core['exit_code']!=0
            or core['payload_sha256']!=c['core_cpu_payload_sha256'] or core['GPU_submissions']!=0
            or not core['budget_unchanged']):raise ValueError('Actual passed core original differs')
    if sha(stage/c['cost_report_ref'])!=c['cost_report_sha256']:raise ValueError('Cost proxy changed')
    b=read(project/'reports/budget.json');auth=read(project/AUTH24)
    if (b['cap_gpu_hours']!=24 or b['budget_authorization_ref']!=AUTH24
            or sha(project/AUTH24)!=c['payload_sha256'][AUTH24]
            or auth['cumulative_cap_gpu_hours']!=24 or auth['usage_reset'] is not False):
        raise ValueError('Existing cumulative24 authority differs')
    if selected:
        p=project/c['production_cpu_stage']/'receipt.json';proof=read(p)
        if (sha(p)!=c['production_cpu_receipt_sha256'] or proof['exit_code']!=0
                or proof['payload_sha256']!=c['production_cpu_payload_sha256']
                or proof['CUDA_initialized'] or proof['GPU_submissions']!=0 or not proof['budget_unchanged']):
            raise ValueError('Actual production CPU proof differs')
        if read(stage/APPROVAL)!={k:v for k,v in c['execution_scope_authority'].items()
            if k not in ['approval_ref','approval_sha256']}:
            raise ValueError('Direct approval original differs')
    return {'status':'OWN_STATE_REAL_ROOT_ASSETS_BINDING_PASS_NO_TORCH','scenes':3,
            'observations':12,'budget_snapshot':b,'new_GPU_authority_verified':selected}


def admission_budget(b,c):
    validate_config(c,selected=True);used=b['used_gpu_hours']
    if (b['cap_gpu_hours']!=24 or b['budget_authorization_ref']!=AUTH24
            or type(used) not in (int,float) or not math.isfinite(used) or not 0<=used<=24
            or any(k.endswith('_inflight') for k in b) or (24-used)*3600<1830):
        raise ValueError('Whole card, existing ledger and admission do not fit')


def reserve_budget(b,c,pid):
    admission_budget(b,c)
    if type(pid) is not int or pid<=0:raise ValueError('Supervisor PID required')
    out=copy.deepcopy(b);out['used_gpu_hours']+=.5;out['gpu_jobs_launched']+=1
    out[INFLIGHT]={'run_id':RUN,'supervisor_pid':pid,'reserved_seconds':1800}
    out['status']='OWN_STATE_PREPAID_NOT_ACTUAL';return out


def settle_budget(current,b,c,seconds,pid):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0:
        raise ValueError('Inclusive actual expense required including failure')
    if current!=reserve_budget(b,c,pid):raise ValueError('Reservation changed; preserve current ledger')
    out=copy.deepcopy(current);out['used_gpu_hours']=b['used_gpu_hours']+seconds/3600
    out.pop(INFLIGHT);out['status']='OWN_STATE_SETTLED_REQUIRES_AUDIT';return out
