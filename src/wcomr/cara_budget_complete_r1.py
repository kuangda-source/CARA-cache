"""Complete calibration acceptance after original release and unique settlement."""
import math
import re
from pathlib import Path

from .cara_budget_calibration_r1 import Calibration,PRODUCTION_CONFIG
from .cara_budget_lifecycle_r1 import IDENTITY,released_lifecycle
from .cara_budget_runner_binding_r1 import validate,PROFILE
from .cara_budget_search_journal_r1 import create_record,read_record
from .cara_fast_spec_r1 import digest,policy_from_mask,profile_from
from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import record,require

SOURCE='src/wcomr/cara_budget_complete_r1.py'
PRODUCER='src/wcomr/cara_budget_calibration_r1.py'


def accept(project,stage,capture,expected_launch_sha256,settlement,*,cpu_validation=False):
    # No collection, RGB, query return or candidate is opened before this gate.
    lifecycle=released_lifecycle(capture,expected_launch_sha256,settlement,cpu_validation=cpu_validation)
    require(lifecycle['container_exit_success'] is True,'Successful original release/settlement required before scientific read')
    launch=record(capture,'launch');registration=record(capture,'registration')
    require(registration['payload_sha256'].get(SOURCE)==sha(__file__)
            and registration['payload_sha256'].get(PRODUCER)==sha(Path(__file__).with_name('cara_budget_calibration_r1.py')),
            'Original registered complete-reader and producer source required')
    card,bound_launch,profile,limits,context=validate(project,stage)
    require(bound_launch==launch and context['CPU_fixture_only'] is cpu_validation
            and context['launch_sha256']==expected_launch_sha256
            and context['registration_sha256']==launch['registration_sha256']
            and context['runner_profile_sha256']==registration['payload_sha256'][PROFILE]
            and all(context[k]==launch[k] for k in IDENTITY)
            and context['scope_sha256']==card['scope_sha256'],
            'Original captured/staged launch and producer context differ')
    output=Path(project)/'outputs'/launch['run_id']
    intent=read_record(output/'calibration-runner-intent.json')
    require(intent==dict(identity=record(capture,'runner_start')['identity'],context=context),
            'Original runner identity and context differ')
    state=read_record(output/'calibration-runner.json')
    status=('CALIBRATION_CPU_' if cpu_validation else 'CALIBRATION_')+'COMPLETE'
    require(state['phase']=='CALIBRATION' and state['status']==status
            and state['source_revision']==launch['source_revision']
            and state['scope_sha256']==card['scope_sha256'] and state['context_sha256']==digest(context)
            and all(type(state[k]) in (int,float) and math.isfinite(state[k]) for k in ('started_unix','ended_unix'))
            and state['ended_unix']>=state['started_unix'] and 'error_type' not in state
            and state['scientific_freeze_written'] is False,
            'Original complete runner terminal required')
    precision=read_record(output/'calibration-model-precision.json')
    require(precision==state['precision'] and precision['model_precision']=='torch.bfloat16'
            and precision['use_wan_fp32_strategy'] is True
            and precision['conditional_frame_timestep']==.1 and precision['outer_autocast'] is False,
            'Original model precision/condition receipt differs')
    collection=read_record(output/'calibration-collection.json')
    require(collection['status']==status and collection['complete'] is True
            and collection['CPU_fixture_only'] is cpu_validation
            and collection['expected_physical_paths']==collection['complete_physical_paths']==112
            and collection['new_physical_calls']==112 and collection['scientific_freeze_written'] is False,
            'Original complete112 collection required; no accepted partial winner')

    root=output/'calibration'
    completed={p.parent.name for p in root.glob('*/complete.json')}
    attempted={p.parent.name for p in root.glob('*/intent.json')}
    require(len(completed)==112 and attempted==completed
            and {p.name for p in root.iterdir() if p.is_dir()}==completed|{'queries'},
            'Every original physical attempt must be complete; no extra partial paths')
    for name in sorted(completed):
        proof=read_record(root/name/'complete.json');slot=proof['identity']['slot']
        require(proof['CPU_fixture_only'] is cpu_validation
                and proof['solver_steps']==proof['guided_pairs']==36
                and proof['actual_D']==(19 if slot['role'] in ('SEARCH_CANDIDATE','UNIFORM19_C') else 36)
                and re.fullmatch(r'[0-9a-f]{64}',proof['rng_sha256'])
                and type(proof['T_request']) in (int,float) and math.isfinite(proof['T_request']) and proof['T_request']>0
                and ((slot['timing_enabled'] and type(proof['T_DD']) in (int,float)
                    and math.isfinite(proof['T_DD']) and proof['T_DD']>0)
                    or (not slot['timing_enabled'] and proof['T_DD'] is None)),
                'Original full36/fixedD/RNG/timing proof differs: '+name)

    def forbidden(*args):
        raise RuntimeError('Complete acceptance cannot execute any physical request')

    entry=Calibration(root=output/'calibration',card=card,config=PRODUCTION_CONFIG,
        context_sha256=digest(context),RGB_shape=card['calibration']['RGB_shape'],execute=forbidden,
        storage_limits=limits,cpu_validation=cpu_validation,
        production_context=None if cpu_validation else context)
    recovered=entry.run(allow_new=False)
    require(recovered['complete'] and recovered['complete_physical_paths']==112
            and recovered['new_physical_calls']==0,'All112 original physical artifacts required')
    actual,saved=recovered['search'],collection['search']
    require({k:v for k,v in actual.items() if k!='journal'}=={k:v for k,v in saved.items() if k!='journal'}
            and actual['journal']['binding_sha256']==saved['journal']['binding_sha256']
            and actual['journal']['new_callback_calls']==0 and actual['journal']['reused_callback_returns']==51
            and saved['journal']['new_callback_calls']==51 and saved['journal']['reused_callback_returns']==0
            and actual['completed_cohort_evaluations']==actual['attempted_cohort_evaluations']==51
            and actual['SA_iterations_completed']==30 and actual['HC_iterations_completed']==1,
            'Complete original51-query deterministic replay differs')
    best=actual['best_complete_candidate']
    policy=policy_from_mask(profile_from(card['profile']),best['dense'])
    require(policy['fingerprint']==best['policy_fingerprint'],'Original selected policy identity differs')
    return dict(status='CPU_FIXTURE_COMPLETE_CALIBRATION_ACCEPTED' if cpu_validation else 'COMPLETE_CALIBRATION_ACCEPTED',
        launch_id=launch['launch_id'],run_id=launch['run_id'],scope_sha256=card['scope_sha256'],
        source_revision=launch['source_revision'],launch_sha256=expected_launch_sha256,
        context_sha256=digest(context),collection_sha256=sha(output/'calibration-collection.json'),
        reader_sha256=sha(__file__),billing_sha256=capture['files']['billing']['sha256'],
        actual_GPUh=lifecycle['actual_GPUh'],complete_physical_paths=112,complete_two_FIT_queries=51,
        selected=best,policy=policy,selection_scope='TWO_OLD_CAL_FIT_SEED0_ONLY',
        full_RGB_revalidated=True,original_artifacts_recovered_without_generation=True,
        CPU_fixture_only=cpu_validation,complete_search_accepted=not cpu_validation,
        scientific_freeze_written=False,quality_or_latency_gain_claimed=False,
        GPU_submissions=0,ledger_written=False,dispatch_allowed=False,authorizes_replay=False)


def freeze_once(project,stage,capture,expected_launch_sha256,settlement,*,cpu_validation=False):
    accepted=accept(project,stage,capture,expected_launch_sha256,settlement,cpu_validation=cpu_validation)
    name='CPU-calibration-frozen-mask.json' if cpu_validation else 'calibration-frozen-mask.json'
    path=Path(project)/'outputs'/accepted['run_id']/name
    frozen={k:accepted[k] for k in ('launch_id','run_id','scope_sha256','source_revision','launch_sha256',
        'context_sha256','collection_sha256','reader_sha256','billing_sha256','actual_GPUh',
        'complete_physical_paths','complete_two_FIT_queries','selected','policy','selection_scope','CPU_fixture_only')}
    frozen.update(schema='CARA_BUDGET_COMPLETE_MASK_FREEZE_R1',new_GPU_authority=False)
    if path.exists():
        require(read_record(path)==frozen,'Original calibration freeze differs; never overwrite it')
        created=False
    else:
        create_record(path,frozen);created=True
    return dict(accepted,freeze_path=str(path),freeze_sha256=sha(path),new_freeze_created=created,
        scientific_freeze_written=not cpu_validation,CPU_fixture_freeze_written=cpu_validation)
