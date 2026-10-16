"""Source-bound complete180 repair launch and read-only original-handle capture.

No approval, UUID, cost or method is selected here. A failed observation is
unknown, never permission to restart the original task.
"""
import ast
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import time

RUN='wc-paper-n07-refusal-repair180-r2'
CONFIG='configs/wc_paper_N07_refusal_repair180_r2_20261016.json'
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
ORIGINALS={
    'launch':('scripts/launch_wc_paper_N07_frozen_shared180_r1.py',
        '93b0bb8c1cef2c6cb6ba3d751683d97cc3ed531ce4611ab37b602050a1397a58'),
    'capture':('scripts/capture_wc_paper_N07_frozen_shared180_r1.py',
        '0f66689c42ec0f42d4d1987842107c485a17cd8a0a47060ae4942f6788d17d15'),
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_file(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def script_namespace(root,kind):
    root=Path(root);name,expected=ORIGINALS[kind];raw=(root/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('The original complete180 tool changed')
    source=raw.decode()
    if kind=='launch':
        edits=[('from wcomr.frozen_shared_production_r1 import CONFIG,RUN,sha,write,validate,validate_launch_authority',
                'from wcomr.frozen_repair180_r2 import CONFIG,RUN,sha,write,validate,validate_launch_authority',1),
            ('from wcomr.frozen_shared_cpu_acceptance_r1 import validate_bundle',
                'from wcomr.frozen_repair_cpu_acceptance_r2 import validate_bundle',1),
            ('run_wc_paper_N07_frozen_shared180_r1.py','run_wc_paper_N07_refusal_repair180_r2.py',1),
            ('supervise_wc_paper_N07_frozen_shared180_r1.py','supervise_wc_paper_N07_refusal_repair180_r2.py',2),
            ('watch_wc_paper_N07_post_cpu_r1.py','watch_wc_paper_N07_refusal_repair180_r2.py',1),
            ('next_check_not_before_unix=now+delay)',
                'next_check_not_before_unix=now+delay,midpoint_check_not_before_unix=now+delay/2)',1)]
    else:
        edits=[('from wcomr.frozen_shared_production_r1 import CONFIG,sha',
                "CONFIG='"+CONFIG+"'\nimport hashlib\nsha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()",1)]
    changed=source
    for before,after,count in edits:
        if changed.count(before)!=count:raise ValueError('Exact GPU tool metadata replacement required: '+before)
        changed=changed.replace(before,after)
    restored=changed
    for before,after,count in reversed(edits):
        if restored.count(after)!=count:raise ValueError('Ambiguous GPU tool inverse')
        restored=restored.replace(after,before)
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('An undeclared complete180 operation changed')
    ns={'__name__':'independent_N07_repair_'+kind,'__file__':str(root/name)}
    exec(compile(changed,name+'#repair-gpu-bindings-r2','exec'),ns)
    return ns,dict(original_entry=name,original_sha256=expected,replacements=sum(e[2] for e in edits),
        inverse_bytes_and_AST_equal=True,original_source_written=False)


def accepted_CPU(path):
    from .frozen_repair_cpu_acceptance_r2 import accept
    receipt=json_file(path);capture_path=Path(receipt['capture_ref'])
    if not capture_path.is_absolute():capture_path=Path(__file__).resolve().parents[2]/capture_path
    if sha(capture_path)!=receipt['capture_sha256']:raise ValueError('Original repair CPU capture changed')
    raw=json_file(capture_path);actual=accept(raw)
    if not actual.get('CPU_accepted') or any(receipt.get(k)!=v for k,v in actual.items()):
        raise ValueError('Use the independently accepted original complete repair CPU')
    config=raw['files']['config']['data']
    if config['run_id']!=RUN or config['scope_counts']['total_paths']!=180:
        raise ValueError('Original complete180 repair configuration required')
    return receipt,raw


def original_stage(raw,relative):
    path=PurePosixPath(relative)
    actual=PurePosixPath(raw['launch']['stage'])
    if (path.is_absolute() or '..' in path.parts or len(path.parts)!=2 or path.parts[0]!='.sync'
            or actual.parent.name!='.sync' or actual.name!=path.name):
        raise ValueError('Bind the exact independent CPU-accepted stage')
    return str(actual)


def preflight_launch(stage,authority,cpu_acceptance):
    from .frozen_repair180_r2 import validate_launch_authority
    receipt,raw=accepted_CPU(cpu_acceptance);original_stage(raw,stage)
    validate_launch_authority(raw['files']['config']['data'],raw['files']['bound_inputs']['data'],
        raw['registration'],raw['files']['proof']['data'],authority,
        revision=receipt['source_revision'],gpu_uuid=authority['gpu_uuid'],
        config_sha256=receipt['config_sha256'],proof_sha256=receipt['production_CPU_sha256'],
        registration_sha256=receipt['registration_sha256'])
    return receipt


def launch_once(root,stage,authority,cpu_acceptance,output,*,execute=None):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve the original dispatch receipt; never retry a submitted launch')
    accepted=preflight_launch(stage,authority,cpu_acceptance)
    ns,derivation=script_namespace(root,'launch')
    command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen',PYTHON+' -c '+shlex.quote(ns['remote_code'](stage,authority))]
    execute=subprocess.run if execute is None else execute
    try:
        call=execute(command,capture_output=True,timeout=180)
        value=dict(transport_exit_code=call.returncode,stderr=call.stderr.decode(errors='replace'),
            CPU_acceptance_ref=str(cpu_acceptance),CPU_acceptance_sha256=sha(cpu_acceptance),derivation=derivation)
        try:
            reply=json.loads(call.stdout)
            if not isinstance(reply,dict):raise ValueError('An original structured dispatch receipt is required')
            bind_launch(reply,cpu_acceptance)
            if any(reply.get(k)!=authority[k] for k in ('source_revision','launch_id','gpu_uuid')):
                raise ValueError('Dispatch reply belongs to another authority')
            value['dispatch']=reply
        except (ValueError,UnicodeDecodeError,KeyError,TypeError):
            value.update(status='N07_REPAIR_DISPATCH_REPLY_UNKNOWN_READ_ORIGINAL_STAGE_NO_RETRY',
                stdout=call.stdout.decode(errors='replace'),GPU_retry_authorized=False,original_task_terminal=False)
    except (subprocess.TimeoutExpired,OSError) as error:
        value=dict(status='N07_REPAIR_DISPATCH_TRANSPORT_UNKNOWN_READ_ORIGINAL_STAGE_NO_RETRY',
            stage=stage,source_revision=authority['source_revision'],launch_id=authority['launch_id'],gpu_uuid=authority['gpu_uuid'],
            error_type=type(error).__name__,error=str(error),GPU_retry_authorized=False,original_task_terminal=False,
            original_readonly_recovery_refs=[stage+'/'+n for n in ('GPU-launch-request.json','GPU-launch.json','supervisor-admission-failure.json')])
    with output.open('x') as h:json.dump(value,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    return value


def bind_launch(launch,cpu_acceptance):
    accepted,raw=accepted_CPU(cpu_acceptance)
    fields={'source_revision':accepted['source_revision'],'scope_counts':accepted['scope_counts'],
        'config_sha256':accepted['config_sha256'],'registration_sha256':accepted['registration_sha256'],
        'production_CPU_sha256':accepted['production_CPU_sha256'],'bound_input_fingerprint':accepted['bound_input_fingerprint'],
        'run_id':RUN,'stage':raw['launch']['stage'],'project':raw['files']['bundle']['data']['project']}
    if any(launch.get(k)!=v for k,v in fields.items()):raise ValueError('GPU launch differs from the accepted original repair CPU')
    start,mid,end=(launch[k] for k in ('started_unix','midpoint_check_not_before_unix','next_check_not_before_unix'))
    if (not start<mid<end or mid!=(start+end)/2
            or end-start!=raw['files']['config']['data']['first_collection_delay_seconds']):
        raise ValueError('Original halfway and final observation times required')
    return accepted,raw


def accept_admission(value,launch,cpu_acceptance):
    from .frozen_shared_acceptance_r1 import original_alive
    from .gpu_budget_pool_v2 import BudgetPool
    accepted,raw=bind_launch(launch,cpu_acceptance)
    if value.get('status')=='N07_REPAIR_ORIGINAL_OBSERVATION_UNKNOWN_NO_RESTART':
        return dict(status='N07_REPAIR_ADMISSION_OBSERVATION_UNKNOWN_NO_RESTART',GPU_admitted=False,
            original_task_terminal=False,GPU_submissions=0)
    if (value.get('mode')!='admission' or value.get('launch')!=launch
            or value.get('registration')!=raw['registration']
            or value.get('registration_sha256')!=launch['registration_sha256']
            or set(value.get('payload_verified',{}))!=set(raw['registration']['payload_sha256'])
            or not all(v is True for v in value['payload_verified'].values())):
        raise ValueError('Original complete source and admission-only observation required')
    sup=value.get('supervisor');processes=value['original_processes']
    if not sup:
        return dict(status='N07_REPAIR_ORIGINAL_ADMISSION_PENDING_OR_FAILURE_RETAINED',GPU_admitted=False,
            original_supervisor_live=original_alive(launch['supervisor_identity'],processes.get('supervisor_pid')),
            original_admission_failure=value.get('admission_failure'),no_GPU_relaunch_authorized=True,GPU_submissions=0)
    for k in ('source_revision','launch_id','run_id','gpu_uuid','config_sha256','registration_sha256','scope_counts'):
        if sup[k]!=launch[k]:raise ValueError('Original supervisor identity or complete scope differs')
    if sup['status']=='N07_SHARED180_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT':
        return dict(status='N07_REPAIR_GPU_ALREADY_TECHNICALLY_TERMINAL_KEEP_ORIGINAL_FINAL_ETA',GPU_admitted=False,
            original_GPU_child_exit_code=sup.get('child_exit_code'),no_GPU_relaunch_authorized=True,GPU_submissions=0)
    if sup['status']!='N07_SHARED180_GPU_RUNNING':raise ValueError('Unknown original admission status')
    ids={'supervisor_pid':launch['supervisor_identity'],'child_pid':sup.get('child_identity'),
         'post_watcher_pid':launch.get('post_watcher_identity')}
    if not all(original_alive(record,processes.get(k)) for k,record in ids.items()):
        return dict(status='N07_REPAIR_ORIGINAL_ADMISSION_HANDLES_NOT_READY_REESTIMATE_ONCE',GPU_admitted=False,
            no_GPU_relaunch_authorized=True,GPU_submissions=0)
    config=raw['files']['config']['data'];pool=value['pool'];job=pool['jobs'][RUN]
    if (pool['cap_gpu_hours']!=config['cumulative_cap_GPUh']
            or pool['origin_used_gpu_hours']!=config['budget_origin_used_GPUh']
            or any(pool[k]!=v for k,v in BudgetPool.accounting(pool).items())
            or job['status']!='RESERVED_OR_RUNNING' or job['kind']!='V2_SPECIFIC_WHOLE_CARD_APPROVAL'
            or job['billed_limit_GPUh']!=config['billed_limit_GPUh']
            or job['forecast_GPUh']!=config['forecast_complete_GPUh']
            or job['scope_counts']!=config['scope_counts']
            or any(job[k]!=launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256',
                'production_CPU_sha256','bound_input_fingerprint','authorization_sha256'))
            or value['own_UUID_lock_free'] or value['own_GPU'].split(',')[0].strip()!=launch['gpu_uuid']):
        raise ValueError('Fresh original UUID ownership and whole-card additive reservation required')
    return dict(status='N07_REPAIR_ORIGINAL_GPU_ADMISSION_INDEPENDENTLY_ACCEPTED',GPU_admitted=True,
        source_revision=launch['source_revision'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],
        supervisor_pid=ids['supervisor_pid']['pid'],runner_pid=ids['child_pid']['pid'],post_watcher_pid=ids['post_watcher_pid']['pid'],
        config_sha256=launch['config_sha256'],scope_counts=launch['scope_counts'],
        original_live_identities=ids,scientific_results_read=False,quality_or_acceleration_confirmed=False,GPU_submissions=0)


def health_expected(launch,admission,cpu_acceptance):
    bind_launch(launch,cpu_acceptance)
    if (admission.get('mode')!='admission' or admission.get('launch')!=launch
            or admission['registration_sha256']!=launch['registration_sha256']
            or not admission['payload_verified'] or not all(admission['payload_verified'].values())):
        raise ValueError('Use the original admitted raw observation for midpoint identities')
    sup=admission['supervisor'];processes={}
    for name,record in (('supervisor',launch['supervisor_identity']),('runner',sup['child_identity']),
                        ('CPU_post',launch['post_watcher_identity'])):
        if any(type(record.get(k)) is not int or record[k]<=0 for k in ('pid','start_ticks')):
            raise ValueError('Every original process needs a PID and start ticks')
        processes[name]={k:record[k] for k in ('pid','start_ticks')}
    if any(sup[k]!=launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','config_sha256')):
        raise ValueError('The original supervisor belongs to another launch')
    return dict(project=launch['project'],stage=launch['stage'],run_id=RUN,
        **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','registration_sha256','scope_counts')},
        processes=processes,health_not_before_unix=launch['midpoint_check_not_before_unix'],final_not_before_unix=launch['next_check_not_before_unix'])


def health_code(expected):
    from . import frozen_shared_health_r1 as old
    path=Path(old.__file__)
    if sha(path)!='a1690331e1e4cffa6a77fa751ad34cfe36f4c67b810984d3069d4ad525735a0f':
        raise ValueError('Original technical-only midpoint observer changed')
    source=old.remote_code(expected);changed=source
    for before,after in ((old.RUN,RUN),(old.CONFIG,CONFIG)):
        if changed.count(before)!=1:raise ValueError('Only the explicit original health run/config literals may differ')
        changed=changed.replace(before,after)
    if changed.replace(RUN,old.RUN).replace(CONFIG,old.CONFIG)!=source:
        # EXPECTED itself already contains the new run/config values; its
        # serialised binding is not an original literal to reverse globally.
        prefix='EXPECTED='+repr(expected)+'\n'
        tail=changed[len(prefix):].replace(RUN,old.RUN).replace(CONFIG,old.CONFIG)
        if prefix+tail!=source:raise ValueError('Undeclared midpoint observer operation changed')
    return changed


def collect_once(root,launch,mode,cpu_acceptance,output,*,admission=None,now=None,execute=None):
    bind_launch(launch,cpu_acceptance);output=Path(output)
    if output.exists():
        saved=json_file(output)
        identity=saved.get('launch',saved.get('expected',{}))
        if identity.get('launch_id')!=launch['launch_id'] or identity.get('source_revision')!=launch['source_revision']:
            raise ValueError('An existing observation belongs to another original launch')
        return saved,False
    now=time.time() if now is None else now
    if mode=='terminal' and now<launch['next_check_not_before_unix']:
        raise ValueError('Before original final ETA; no SSH')
    if mode=='health':
        if not launch['midpoint_check_not_before_unix']<=now<launch['next_check_not_before_unix']:
            raise ValueError('Outside the original midpoint window; no SSH')
        expected=health_expected(launch,admission,cpu_acceptance);code=health_code(expected)
    elif mode in ('admission','terminal'):
        ns,_=script_namespace(root,'capture');code=ns['remote_code'](launch,mode)
    else:raise ValueError('Only admission, technical halfway or final capture is supported')
    import os
    with output.with_name(output.name+'.attempt').open('x') as h:
        json.dump(dict(launch_id=launch['launch_id'],source_revision=launch['source_revision'],mode=mode,collector_pid=os.getpid()),h)
    execute=subprocess.run if execute is None else execute
    try:
        call=execute(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=150)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace')[-4096:])
        value=json.loads(call.stdout if mode=='health' else gzip.decompress(call.stdout))
        identity=value.get('launch',value.get('expected',{}))
        if identity.get('launch_id')!=launch['launch_id'] or identity.get('source_revision')!=launch['source_revision']:
            raise ValueError('The original observation identity changed')
        if mode=='health':
            if (value.get('expected')!=expected or value.get('status')!='N07_MIDPOINT_READONLY_TECHNICAL_HEALTH'
                    or value.get('final_scientific_results_read') is not False
                    or value.get('no_quality_or_method_latency_readout') is not True
                    or set(value.get('original_processes',{}))!={'supervisor','runner','CPU_post'}
                    or not expected['health_not_before_unix']<=value.get('observed_unix',0)<expected['final_not_before_unix']):
                raise ValueError('Midpoint must retain all original identities, time and technical-only scope')
        elif value.get('launch')!=launch or value.get('mode')!=mode or value.get('status')!='N07_SHARED180_ORIGINAL_ONCE_CAPTURE':
            raise ValueError('Original complete admission or terminal observation required')
    except (subprocess.TimeoutExpired,OSError,RuntimeError,ValueError,EOFError) as error:
        value=dict(status='N07_REPAIR_ORIGINAL_OBSERVATION_UNKNOWN_NO_RESTART',launch=launch,mode=mode,
            observed_local_unix=time.time(),error_type=type(error).__name__,error=str(error),
            original_task_terminal=False,GPU_submissions=0)
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
    with output.open('xb') as h:h.write(gzip.compress(raw) if output.suffix=='.gz' else raw)
    return value,True
