"""Explicit whole-card host port, with unchanged scientific post/accept code."""
import ast
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from four_card_bank24_execution_adapter_r1 import exact_patch,digest,read,require,adapt_runner,adapt_budget_pool

ROOT='/data20t/gaokuangda/worldcache_workspace'
SCIENCE_RUN='wc-scout-dev6-paired-native-full24-r1'
FULL_CPU_STATUS='BANK24_FOURCARD_FULL_EXECUTION_TOOLS_CPU_INDEPENDENTLY_ACCEPTED'
ALEX_SHA='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
LINEAR_SHA='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'


def sha(path):return digest(Path(path).read_bytes())


def full_quote(original, scope_counts):
    """A conservative complete planning quote, explicitly not measured Ada time."""
    require(original['scope_counts']==scope_counts and len(original['positions'])==24,
            'Full original whole24 quote evidence required')
    terms=original['terms_seconds'];names=['load','whole_requests','projected_unattributed',
        'full_warm_trace','setup','additional_A_planning_proxy','observer_copy_hash_allowance']
    require(set(terms)==set(names) and all(type(terms[k]) in (int,float) and math.isfinite(terms[k]) and terms[k]>=0 for k in names),
            'Every original whole-card planning term required')
    projected={k:2.*terms[k] for k in names}
    projected['container_start_and_exit']=180.
    projected['charged_SM89_setup_failure_allowance']=300.
    total=math.ceil(sum(projected.values())*1.2)
    forecast=total/3600;limit=math.ceil(forecast*1.25*4)/4
    require(0<forecast<=limit<12,'Complete conservative BANK24 quote needs specific approval')
    return dict(status='BANK24_ADA_WHOLE24_CONSERVATIVE_PLANNING_QUOTE_NOT_MEASURED',
        scope_counts=scope_counts,positions=original['positions'],planning_terms_seconds=projected,
        old_host_terms_seconds=terms,old_host_multiplier=2.,margin=1.2,
        forecast_complete_GPUh=forecast,billed_limit_GPUh=limit,
        actual_new_host_terms_seconds={k:None for k in projected},
        actual_new_host_measured_quote_accepted=False,actual_CUDA_compatibility_accepted=False,
        all24_including6_Native6_warm_observers_A_copies_and_exit_priced=True,
        old_quote_is_Ada_measurement=False,runtime_upper_bound_guarantee=False,
        GPU_submissions=0,ledger_written=False)


def validate_handoff(project, proof):
    """Consume an external, independently verified handoff; never create one."""
    project=Path(project).resolve()
    require(isinstance(proof,dict) and proof.get('status')=='WC_V2_UNIQUE_WRITER_HANDOFF_INDEPENDENTLY_ACCEPTED'
        and proof.get('old_host_new_GPU_dispatch_fenced') is True
        and proof.get('new_unique_writer')=='four_card' and proof.get('checks')
        and all(v is True for v in proof['checks'].values())
        and proof.get('cap_GPUh')==226 and proof.get('origin_used_GPUh')==79.99637737158223
        and proof.get('reset_history') is False,'An actual full authoritative handoff is still required')
    snapshot=project/proof['old_authoritative_snapshot_ref']
    require(project in snapshot.resolve().parents and sha(snapshot)==proof['old_authoritative_snapshot_sha256'],
            'Original complete authoritative snapshot missing')
    frozen=read(snapshot);current=read(project/'reports/gpu-budget-v2.json')
    require(frozen['schema']==current['schema']=='WC_GPU_BUDGET_POOL_V2'
        and frozen['cap_gpu_hours']==current['cap_gpu_hours']==226
        and frozen['origin_used_gpu_hours']==current['origin_used_gpu_hours']==79.99637737158223,
        'Handoff cannot reset origin or cap')
    require(all(j['status']=='SETTLED' for j in frozen['jobs'].values()),
            'Old active reservations require an explicit quiescent handoff')
    require(all(current['jobs'].get(k)==j for k,j in frozen['jobs'].items()),
            'Original settlement history changed or was truncated')
    require(current.get('writer_epoch')==proof.get('writer_epoch') and proof.get('writer_epoch'),
            'Unique current writer epoch missing')
    return dict(handoff_accepted=True,all_original_jobs_preserved=len(frozen['jobs']),
                writer_epoch=proof['writer_epoch'])


def require_full_CPU(stage, source_revision):
    stage=Path(stage);accepted=read(stage/'scout-lifecycle-CPU-independent-acceptance.json')
    require(accepted.get('status')==FULL_CPU_STATUS and accepted.get('full_new_host_scope_production_CPU_accepted') is True
        and accepted.get('source_revision')==source_revision and accepted.get('checks')
        and all(v is True for v in accepted['checks'].values()), 'Actual full new-host lifecycle CPU required')
    require(sha(stage/'scout-lifecycle-CPU-proof.json')==accepted['proof_sha256'], 'Actual full CPU proof bytes differ')
    proof=read(stage/'scout-lifecycle-CPU-proof.json')
    require(proof.get('status')=='BANK24_FULL_EXECUTION_TOOLS_CPU_PASS_NOT_NEURAL_OR_GPU'
        and proof.get('source_revision')==source_revision
        and proof.get('target_registration_sha256')==sha(stage/'registration.json')
        and accepted.get('registration_sha256')==sha(stage/'registration.json')
        and proof.get('target_stage')==str(stage.resolve())
        and accepted.get('actual_CUDA_compatibility_accepted') is False,
        'Real complete CPU proof must bind this host registration and target stage')
    return accepted


def readonly_budget_source():
    """Use the original accounting under an existing shared read lock.

    CPU readers have a read-only workspace. They must never create a lock,
    initialize a pool, or use the writer's append-mode transaction helper.
    """
    return '''
class ReadOnlyBudgetPool:
 def __init__(self,project):
  self.project=Path(project).resolve()
  self.path=self.project/'reports/gpu-budget-v2.json'
  self.lock_path=self.project/'.sync/gpu-budget-v2.lock'
 def read(self):
  import copy,fcntl
  from wcomr.gpu_budget_pool_v2 import BudgetPool as OriginalBudgetPool
  require(self.path.is_file() and not self.path.is_symlink(),'Existing physical pool required; CPU reader never initializes')
  require(self.lock_path.is_file() and not self.lock_path.is_symlink(),'Existing physical budget lock required; CPU reader never creates')
  with self.lock_path.open('rb') as handle:
   fcntl.flock(handle,fcntl.LOCK_SH|fcntl.LOCK_NB)
   value=read(self.path)
   require(all(value[k]==v for k,v in OriginalBudgetPool.accounting(value).items()),'Stored pool totals disagree with original accounting')
   return copy.deepcopy(value)
'''


def contract_source():
    return '''import json,os,sys
from pathlib import Path
from four_card_bank24_execution_adapter_r1 import reconstruct,verify_inputs,read,require,digest
from four_card_bank24_gpu_port_r1 import require_full_CPU,validate_handoff,sha,ALEX_SHA,LINEAR_SHA,FULL_CPU_STATUS
from wcomr.scout_gpu_lifecycle_r1 import counts,RUNS,VECTORS,audit_registered_rows,repeat_and_prefix
from wcomr.scout_production_entry_r1 import METHODS,RUN,STRATEGY,COUNTS,write,execute,matrix,audit_row,validate_contract
from wcomr.drop1_full18_r1 import MODE_REF as ORIGINAL_MODE_REF
CONFIG='inputs/configs/wc_scout_bank24_production_entry_r1_20261018.json'
MODE_REF='inputs/'+ORIGINAL_MODE_REF
PRODUCTION_CPU_STATUS=FULL_CPU_STATUS
def bound_dependency(project,stage):
 stage=Path(stage);reg=read(stage/'registration.json');meta=read(stage/'host-lifecycle-dependency.json')
 require(reg['source_revision']==meta['host_source_revision'],'Actual host source required')
 require(meta['namespace']=='BANK24_FOURCARD_GPU_PORT_R1' and meta['entry_stage']==str(stage),'Wrong host namespace')
 require(meta['scientific_lifecycle_source']=='2bd41dc8fa19f42353e03a7c78b7264b4b2695c6' and meta['scientific_entry_source']=='c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9','Frozen science changed')
 for name,expected in reg['payload_sha256'].items():
  path=stage/name
  require(not path.is_symlink() and path.resolve().is_relative_to(stage.resolve()) and sha(path)==expected,'Registered host payload changed')
 for name,expected in reg['runtime_source_sha256'].items():require(sha(Path(project)/'runtime'/name)==expected,'Frozen runtime changed')
 c=read(stage/CONFIG);validate_contract(c)
 accepted=require_full_CPU(stage,reg['source_revision'])
 require(meta['config_sha256']==sha(stage/CONFIG) and meta['scope_counts']==c['scope_counts'],'Whole24 identity changed')
 meta=dict(meta,entry_source_revision=reg['source_revision'],entry_registration_sha256=sha(stage/'registration.json'))
 return meta,c,reg,None,accepted
def validate(project,stage):
 stage=Path(stage);meta,c,reg,_,accepted=bound_dependency(project,stage)
 authorization=read(stage/'scout-GPU-authorization.json')
 require(authorization['source_revision']==reg['source_revision'] and authorization['gpu_uuid']==os.environ['CUDA_VISIBLE_DEVICES'],'Wrong GPU authority')
 validate_handoff(project,read(stage/'unique-v2-handoff.json'))
 data,evidence=reconstruct(stage/'inputs');c,old,inputs,tables,prior=data
 return c,reg,old,inputs,tables,prior
def lpips_identity(project,stage):
 env=Path(project)/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages'
 alex=Path(project)/'cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth';linear=env/'lpips/weights/v0.1/alex.pth'
 require(sha(alex)==ALEX_SHA and sha(linear)==LINEAR_SHA,'Accepted fixed LPIPS weights changed')
 return dict(status='ACCEPTED_FIXED_TWO_LPIPS_FILES_REUSED',alexnet_sha256=ALEX_SHA,linear_sha256=LINEAR_SHA,version='0.1.4',metric_version='0.1',net='alex')
'''+readonly_budget_source()


def generate(inputs):
    inputs=Path(inputs)
    runner,binding=adapt_runner((inputs/'scripts/run_wc_drop1_full18_r1.py').read_text())
    runner=exact_patch(runner,[('from bank24_sm89_entry_contract import','from bank24_fourcard_lifecycle_r1 import',4)])
    runner=exact_patch(runner,[("""    proof=json.loads((a.stage/'scout-entry-production-CPU-result.json').read_text())
    assert proof['status']==PRODUCTION_CPU_STATUS and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
""","""    from bank24_fourcard_lifecycle_r1 import require_full_CPU
    proof=require_full_CPU(a.stage,a.source_revision)
    assert proof['registration_sha256']==sha(a.stage/'registration.json')
""",1)])
    post=(inputs/'scripts/postprocess_wc_scout_gpu_r1.py').read_text()
    old_lpips="""        from wcomr.lpips_resource_identity import audit
        resource = a.project/'.sync/wc-rv0-lpips-resource-v2'
        result['LPIPS_resource_identity'] = audit(resource, sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0, str(resource/'site')); import lpips
        assert importlib.metadata.version('lpips') == '0.1.4' and Path(lpips.__file__).resolve() == (resource/'site/lpips/__init__.py').resolve()
"""
    new_lpips="""        from bank24_fourcard_lifecycle_r1 import lpips_identity
        result['LPIPS_resource_identity'] = lpips_identity(a.project,a.stage)
        import lpips
        site=a.project/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages'
        assert importlib.metadata.version('lpips') == '0.1.4' and Path(lpips.__file__).resolve() == (site/'lpips/__init__.py').resolve()
"""
    post=exact_patch(post,[
        ("TORCH_HOME='/home/gaokuangda/.cache/torch'","TORCH_HOME=str(a.project/'cache/torch')",1),
        ("sys.path.insert(0, str(a.stage/'src'))","sys.path[:0]=[str(a.stage),str(a.stage/'inputs/src')]",1),
        ('from wcomr.scout_gpu_lifecycle_r1 import bound_dependency','from bank24_fourcard_lifecycle_r1 import bound_dependency',1),
        ('from wcomr.gpu_budget_pool_v2 import BudgetPool, atomic_json, same_live_process',
         'from wcomr.gpu_budget_pool_v2 import atomic_json, same_live_process\n    from bank24_fourcard_lifecycle_r1 import ReadOnlyBudgetPool as BudgetPool',1),
        (old_lpips,new_lpips,1)])
    accept=(inputs/'src/wcomr/scout_gpu_lifecycle_r1.py').read_text()
    start=accept.index('def accept_terminal(');end=accept.index('\ndef freeze_cal_gate(',start)
    accept=exact_patch(accept[start:end],[
        ("v['runner']['source_revision'] == ENTRY_SOURCE and",
         "v['runner']['source_revision'] == launch['entry_source_revision'] and v['runner']['scientific_entry_source_revision'] == ENTRY_SOURCE and",1)])
    result={'bank24-fourcard-runner.py':runner,'bank24_fourcard_lifecycle_r1.py':contract_source(),
            'bank24-fourcard-post.py':post,'bank24-fourcard-accept-terminal-function.py':accept,
            'bank24_sm89_budget_pool.py':adapt_budget_pool((inputs/'src/wcomr/gpu_budget_pool_v2.py').read_text())}
    for name,body in result.items():compile(body,name,'exec')
    return result,dict(component_binding=binding,full_post93_RGB_LPIPS_and_owner_logic_preserved=True,
        full_acceptance24_denominator_and_all_errors_preserved=True,
        actual_entry_source_and_original_scientific_entry_separately_bound=True,
        CPU_post_uses_existing_readonly_budget_lock_and_original_accounting=True,
        GPU_branch_uses_actual_full_new_host_CPU_acceptance_without_fabricating_legacy_entry_proof=True,
        original_code_modifications=0,old_physical_Native_artifacts_required=False)


def accept_capture(capture,launch,inputs):
    """Delegate every original fidelity/control check; handle pre-run failures."""
    require(capture['launch']==launch and capture['mode']=='terminal'
        and capture['observed_unix']>=launch['next_check_not_before_unix'],'Original terminal and actual ETA required')
    if any(capture['original_live_handles'].values()):
        return dict(status='ORIGINAL_STILL_RUNNING_REESTIMATE_ONCE',full_protocol_accepted=False)
    import sys
    sys.path.insert(0,str(Path(inputs)/'src'))
    from wcomr import scout_gpu_lifecycle_r1 as original
    fin=original.finance(capture,launch)
    if not capture.get('runner',{}).get('source_revision'):
        return dict(status='GPU_FAILED_BEFORE_RUNNER_FULL24_RETAINED',full_protocol_accepted=False,
            registered_paths=24,formal_denominator=18,finance=fin,
            all_paths=[dict(row,status='NOT_REACHED_RETAINED') for row in launch['matrix']],
            actual_GPUh=fin['actual_GPUh'],GPU_submissions=0,ledger_written=False)
    generated,_=generate(inputs);namespace=original.__dict__.copy()
    exec(compile(generated['bank24-fourcard-accept-terminal-function.py'],'<host-bound-original-full24-acceptance>','exec'),namespace)
    result=namespace['accept_terminal'](capture,launch)
    if result.get('scored_nonNative_formal',0):
        identity=capture['final'].get('LPIPS_resource_identity') or {}
        require(identity.get('alexnet_sha256')==ALEX_SHA and identity.get('linear_sha256')==LINEAR_SHA,
                'Actual scored LPIPS must use the accepted fixed files')
    return result
