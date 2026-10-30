"""Published source preparation and admission; never submit a GPU or reserve funds."""
import hashlib
from pathlib import Path
import re
import shutil
import time

from .cara_budget_central_r1 import RUN,STAGES,original_absence
from .cara_budget_dispatch_r1 import REQUIRED as DISPATCH_REQUIRED,ready_inputs,fresh_resources,central_binding,ASSETS
from .cara_budget_runner_binding_r1 import REQUIRED,SPEC,PROFILE,LIMITS
from .cara_budget_lifecycle_capture_r1 import inspect_container
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_b36_dispatch_r2 import create,assets_check
from .gpu_budget_pool_v2 import sha,atomic_json
from .immutable_stage_payload_r1 import local_python_closure,configuration_closure,overlay_bytes,source_bytes
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_budget_prepare_r1.py'
# The accepted CPU bases differ on these inherited files. Overlay the same
# published bytes on both hosts before freezing the complete payload identity.
COMMON_BASE_OVERLAY=(
    'scripts/check_cara_fast_f18_cpu_r1.py','scripts/check_cara_q5_native50_cpu_r1.py',
    'src/wcomr/cara_q5_native50_r1.py','tests/check_cara_fast_f18_routes_r1.py',
    'tests/check_cara_q5_native50_routes_r1.py','tests/test_cara_q5_native50_source_r1.py',
    'src/wcomr/sq_q1_readout_r1.py','src/wcomr/sq_readout_subgraph_r1.py',
    'tests/test_sq_readout_subgraph_r1.py')
EXTRA=COMMON_BASE_OVERLAY+(SOURCE,'src/wcomr/cara_budget_central_r1.py','src/wcomr/immutable_stage_payload_r1.py',
    'scripts/cara_budget_prepare_r1.py','scripts/cara_budget_central_r1.py',
    'scripts/cara_budget_calibration_cpu_hosts_r3.py',
    'configs/f1_setup.json','configs/wc_ra_comparison_production_r2_20261010.json',
    'manifests/wc_h0_eval_mode_contract_20261003.json',
    'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_14GPUH_DESIGN_R1.json',
    'reports/cara_fast_B36_actual_central_reservation_r1_20261029.json')


def source_plan(root,base_registration_sha256,base_source_revision,base_revision_field='source_revision'):
    """The existing Git archive writer subsequently checks every overlay byte."""
    root=Path(root)
    require(base_revision_field in ('source_revision','parent_git_revision'), 'Explicit original revision field required')
    names=set(REQUIRED)|set(DISPATCH_REQUIRED)|set(EXTRA)
    names.update(str(p.relative_to(root)) for p in (root/'src/wcomr').glob('cara_budget*.py'))
    names.update(str(p.relative_to(root)) for p in (root/'tests').glob('*cara_budget*.py'))
    names.update(str(p.relative_to(root)) for p in (root/'scripts').glob('check_cara_budget*.py'))
    # Script/test imports are ordinary module names, outside wcomr's static
    # package closure. Include their declared local modules, never third parties.
    import ast
    pending=list(names)
    while pending:
        name=pending.pop()
        if not name.endswith('.py'):continue
        for node in ast.walk(ast.parse(source_bytes(root,name).decode(),filename=name)):
            modules=[]
            if isinstance(node,ast.ImportFrom) and node.level==0 and node.module:modules=[node.module]
            elif isinstance(node,ast.Import):modules=[a.name for a in node.names]
            for module in modules:
                for folder in ('scripts','tests'):
                    target=folder+'/'+module.replace('.','/')+'.py'
                    if (root/target).is_file() and target not in names:names.add(target);pending.append(target)
    hashes=local_python_closure(root,[n for n in names if n.endswith('.py')])
    hashes.update(configuration_closure(root,[n for n in names if not n.endswith('.py')]))
    return dict(status='CALIBRATION_SOURCE_PLAN_NO_GPU_AUTHORITY',overlay_sha256=dict(sorted(hashes.items())),
        base_registration_sha256=base_registration_sha256,base_source_revision=base_source_revision,
        base_revision_field=base_revision_field,
        GPU_submissions=0,execution_authorized=False)


def observe_original(project,host):
    require(host in STAGES,'Registered host required')
    stage=Path(project)/'.sync'/STAGES[host]
    require(not stage.is_symlink(),'Original stage must not be a symlink')
    records=[name for name in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json')
             if (stage/name).exists()]
    # UNKNOWN daemon/transport failures propagate; only exact absence is None.
    container=inspect_container(stage.name+'-gpu')
    return dict(host=host,stage=str(stage),run_id=RUN,stage_exists=stage.exists(),
        dispatch_records=records,container=container,observation_complete=True,observed_unix=time.time())


def prepare(project,host,base,archive,plan,revision,observations):
    project,base=Path(project),Path(base)
    require(host in STAGES and re.fullmatch('[0-9a-f]{40}',revision),'Registered host and published revision required')
    stage=project/'.sync'/STAGES[host]
    require(not stage.is_symlink(),'Original stage must not be a symlink')
    original_absence(observations,project)
    require(sha(base/'registration.json')==plan['base_registration_sha256'],'Original base registration differs')
    registered=read_record(base/'registration.json')
    require(plan['base_revision_field'] in ('source_revision','parent_git_revision')
            and registered[plan['base_revision_field']]==plan['base_source_revision'] and registered['host']==host,
            'Original host/base source differs')
    raw=overlay_bytes(archive,plan)
    require(set(REQUIRED)|set(DISPATCH_REQUIRED)|set(EXTRA)<=set(raw),'Complete preparation/dispatch overlay required')
    combined={**registered['payload_sha256'],**plan['overlay_sha256']}
    require(base.parent==project/'.sync' and base!=stage and not base.is_symlink(),'Independent original sibling base required')
    runtime=registered['runtime_source_sha256']
    require(runtime and all(hashlib.sha256(source_bytes(project/'runtime',n)).hexdigest()==h for n,h in runtime.items()),
            'Pinned actual runtime differs')
    if stage.exists():
        registration=read_record(stage/'registration.json')
        require(registration['host']==host and registration['stage']==str(stage)
                and registration['source_revision']==revision and registration['payload_sha256']==combined
                and registration['read_only_base_registration_sha256']==plan['base_registration_sha256']
                and all(sha(stage/n)==h for n,h in combined.items()),
                'Existing or partial stage differs; recover it without replacement')
        return registration
    for name,expected in registered['payload_sha256'].items():
        require(hashlib.sha256(source_bytes(base,name)).hexdigest()==expected,'Original base source differs')
    stage.mkdir(mode=0o700)
    for name in combined:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True)
        if name in raw:target.write_bytes(raw[name])
        else:shutil.copyfile(base/name,target)
    require(all(sha(stage/n)==h for n,h in combined.items()),'Installed source bytes differ')
    profile=read_record(stage/PROFILE)
    registration=dict(host=host,stage=str(stage),source_revision=revision,payload_sha256=combined,
        runtime_source_sha256=runtime,container_image=profile['GPU_container']['image'],
        read_only_base_registration_sha256=plan['base_registration_sha256'],base_stage=str(base),
        CPU_scope='CALIBRATION_PREPARATION_NO_GPU_AUTHORITY',GPU_submissions_by_installer=0)
    create(stage/'registration.json',registration)
    return registration


def bind_authority(project,stage,authority,proof,quote):
    """New direct approval is supplied externally after the reviewable CPU work."""
    project,stage=Path(project),Path(stage)
    require(authority['run_id']==RUN and authority['host'] in STAGES
            and stage==project/'.sync'/STAGES[authority['host']] and authority['stage']==str(stage)
            and authority['CPU_fixture_only'] is False and authority['execution_authorized'] is True
            and authority['direct_user_authorization'] is True and bool(authority['user_quote'])
            and authority['authorizes_replay'] is False and authority['billed_limit_GPUh']==14,
            'Separate single-card direct human approval required')
    require(not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','GPU-dispatch.json')),
            'Original dispatch exists; recover it before binding')
    for name,value in [('execution-CPU-proof.json',proof),('whole-quote.json',quote)]:
        if (stage/name).exists():require(read_record(stage/name)==value,'Original binding differs; do not overwrite')
        else:create(stage/name,value)
    bound=dict(authority,CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),quote_sha256=sha(stage/'whole-quote.json'))
    path=stage/'GPU-authorization.json'
    if path.exists():require(read_record(path)==bound,'Original authority differs; do not overwrite')
    else:create(path,bound)
    ready_inputs(project,stage)
    return bound


def admit(project,stage):
    project,stage=Path(project),Path(stage)
    _,registration,authority,profile,_=ready_inputs(project,stage)
    require(authority['run_id']==RUN and stage==project/'.sync'/STAGES[authority['host']], 'Registered whole stage required')
    require(not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','GPU-dispatch.json')),
            'Original intent must be recovered, never admitted again')
    assets=assets_check(project,read_record(stage/ASSETS))
    proof=dict(registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
        asset_spec_sha256=sha(stage/ASSETS),assets=assets)
    atomic_json(stage/'fresh-admission.json',proof)
    _,resources=fresh_resources(project,stage,authority,profile)
    quote=read_record(stage/'whole-quote.json')['host_quotes'][authority['host']]
    result=dict(proof,status='CALIBRATION_COMPLETE_FRESH_ADMISSION_NO_GPU',authorization=authority,
        central_operator_sha256=registration['payload_sha256']['src/wcomr/cara_budget_central_r1.py'],
        authorization_raw_utf8=(stage/'GPU-authorization.json').read_text(),resources=resources,
        forecast_GPUh=quote['forecast_GPUh'],physical_paths=112,candidate_queries=51,
        dual_host_whole_card_CPU_accepted=True,observed_unix=time.time(),GPU_submissions=0)
    atomic_json(stage/'fresh-admission.json',result)
    return result


def bind_reservation(project,stage,envelope,snapshot):
    _,_,authority,_,_=ready_inputs(project,stage);stage=Path(stage)
    job=envelope['job']
    require(job['job_id']==RUN and job['status']=='RESERVED_OR_RUNNING'
            and all(job[k]==authority[k] for k in ('run_id','launch_id','host','gpu_uuid','stage',
                'source_revision','scope_sha256','billed_limit_GPUh'))
            and job['registration_sha256']==sha(stage/'registration.json')
            and job['authorization_sha256']==sha(stage/'GPU-authorization.json'),
            'Only the original exact central envelope can bind this stage')
    path=stage/'central-reservation.json'
    if path.exists():require(read_record(path)==envelope,'Original envelope differs; preserve it')
    else:create(path,envelope)
    central_binding(stage,authority,snapshot)
    return dict(status='ORIGINAL_CENTRAL_ENVELOPE_BOUND_NO_GPU',launch_id=authority['launch_id'],GPU_submissions=0)
