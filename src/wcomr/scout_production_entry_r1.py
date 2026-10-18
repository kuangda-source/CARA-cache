"""Real request/price entry checks for two scouts; GPU lifecycle is separate."""
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path

from . import drop1_window24_production_r1 as previous
from . import scout_sampling_r1 as sampling
from .drop1_full18_r1 import MODE_REF, STRATEGY, sha, write

KIND=os.environ.get('WC_SCOUT_KIND')
if KIND not in ('CAL12','BANK24'):raise ValueError('An explicit registered scout kind is required')
CONFIG='configs/wc_scout_'+KIND.lower()+'_production_entry_r1_20261018.json'
BLUEPRINT='plans/scouts_20261018/'+('SCOUT_CAL12_CARD.json' if KIND=='CAL12' else 'SCOUT_DEV6_BANK24_CARD.json')
RUN={'CAL12':'wc-scout-cal4-g01-var26-full12-r1','BANK24':'wc-scout-dev6-paired-native-full24-r1'}[KIND]
METHODS=tuple(sampling.plans(KIND))
COUNTS=dict(requests=4 if KIND=='CAL12' else 6,methods=len(METHODS),
    formal_paths=8 if KIND=='CAL12' else 18,full_warmup_paths=4 if KIND=='CAL12' else 6,
    total_paths=12 if KIND=='CAL12' else 24,loads=1,new_teacher_pairs=0,new_Native_formal=0 if KIND=='CAL12' else 6)
COUNTS.update(ordinary_pairs=COUNTS['total_paths']*36,ordinary_CFG_calls=COUNTS['total_paths']*72)
CPU_RESULT='scout-entry-production-CPU-result.json'
PRODUCTION_CPU_STATUS='SCOUT_'+KIND+'_REAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU_LIFECYCLE'
TIMING=sampling.TIMING
REFERENCES=dict(window_config=previous.CONFIG,blueprint=BLUEPRINT,
    numeric_capture='reports/wc_scout_numeric248_actual_CPU_R1_collection_20261018.json.gz',
    numeric_acceptance='reports/wc_scout_numeric248_actual_CPU_R1_independent_acceptance_20261018.json',
    exposure_R1='reports/wc_scout_DEV6_fresh_project_exposure_R1_20261018.json',
    exposure_R2='reports/wc_scout_DEV6_fresh_project_exposure_R2_completion_20261018.json')


def plans():return sampling.plans(KIND)
def matrix(scenes):return sampling.matrix(KIND,scenes)
def execute(*args,**kwargs):return sampling.execute(*args,kind=KIND,**kwargs)


def validate_contract(c):
    if (c.get('kind')!=KIND or c.get('run_id')!=RUN or c.get('namespace')!='SCOUT_'+KIND
        or c.get('methods')!=list(METHODS) or c.get('scope_counts')!=COUNTS
        or c.get('plans')!={k:list(v) for k,v in plans().items()} or c.get('strategy')!=STRATEGY
        or c.get('A_method')!='BETA1_ONE_PHASE' or c.get('memory_policy')!='BOUNDARY_GC_ONLY_R2'
        or c.get('cumulative_cap_GPUh')!=226 or c.get('budget_origin_used_GPUh')!=79.99637737158223
        or c.get('autonomy_exclusive_upper_GPUh')!=12 or c.get('timing_claim')!=TIMING
        or c.get('warmup_repeats')!=2 or len(c.get('requests',[]))!=COUNTS['requests']
        or len({r['name'] for r in c['requests']})!=COUNTS['requests']
        or any(c.get(k) is not False for k in ('training','online_teachers','P_enabled','F_B_enabled','endpoint_tuning'))
        or c.get('new_native_generation')!=(KIND=='BANK24') or c.get('GPU_lifecycle_accepted') is not False
        or not 0<c.get('forecast_complete_GPUh',0)<=c.get('billed_limit_GPUh',0)<12
        or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
            or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])
        or set(c.get('references',{}))!=set(REFERENCES)|{'cost'}
        or any(c['references'][k]['ref']!=v for k,v in REFERENCES.items())):
        raise ValueError('Exact complete scout entry, readout, diagnostic and quote scope required')


def read(stage,c,key):return previous.read_reference(stage,c,key)


def quote(stage,window_config,blueprint):
    base=read(stage,window_config,'cost')
    n09=read(stage,window_config,'N09_capture')
    # Every complete request includes encoding/decoding/ordinary guardrails and
    # deferred writing. This deliberately prices every Native too at the max.
    times=[r['ended_unix']-r['started_unix'] for r in n09['runner']['runs']]
    if len(times)!=40 or any(not math.isfinite(v) or v<=0 for v in times):
        raise ValueError('All40 actual whole requests are required for scout planning')
    rows=matrix([r['name'] for r in blueprint['requests']])
    observed=sum(r['observer'] for r in rows)
    extra=sum(max(0,plans()[r['method']].count('A')-1) for r in rows)
    terms=dict(load=base['original_load_seconds'],whole_requests=len(rows)*max(times),
        projected_unattributed=max(0.,base['original_unattributed_seconds'])/18*len(rows),
        full_warm_trace=COUNTS['full_warmup_paths']*60.,setup=300.,
        additional_A_planning_proxy=extra*base['per_extra_A_planning_proxy_seconds'],
        observer_copy_hash_allowance=observed*60.)
    forecast=math.ceil(sum(terms.values())*1.2)/3600
    return dict(status='SCOUT_COMPLETE_ENTRY_PLANNING_QUOTE_NOT_MEASURED_SPEED',kind=KIND,
        scope_counts=COUNTS,positions=rows,terms_seconds=terms,observer_paths=observed,
        observer_allowance_seconds_per_path=60.,margin=1.2,forecast_complete_GPUh=forecast,
        billed_limit_GPUh=math.ceil(forecast*1.25*4)/4,
        source_whole_request_max_seconds=max(times),action_unit_prices_measured=False,
        exact_runtime_upper_bound_guarantee=False,extra_deep_or_teacher_calls=0,GPU_submissions=0)


def validate(project,stage):
    stage=Path(stage)
    _,reg,old,inputs,tables,prior=previous.validate(project,stage)
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    v={k:read(stage,c,k) for k in c['references']}
    if c['requests']!=v['blueprint']['requests'] or c['card']!=v['blueprint']['id']:
        raise ValueError('Frozen original scout input/seed/guardrail requests must survive')
    spec=importlib.util.spec_from_file_location('registered_scout248_acceptor',stage/'scripts/capture_wc_scout_numeric248_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    accepted=module.accept(v['numeric_capture'])
    if (any(v['numeric_acceptance'].get(k)!=x for k,x in accepted.items())
        or any(reg['payload_sha256'].get(n)!=h for n,h in v['numeric_capture']['registration']['payload_sha256'].items())
        or reg['runtime_source_sha256']!=v['numeric_capture']['registration']['runtime_source_sha256']):
        raise ValueError('Reuse only the unchanged accepted full248 numerical closure')
    exposure=v['exposure_R2']
    if (exposure['project_output_scope_accepted'] is not True
        or exposure['R1_sha256']!=c['references']['exposure_R1']['sha256']
        or exposure['input_manifest_sha256']!=v['exposure_R1']['result']['input_manifest_sha256']):
        raise ValueError('All project identity files, including retained oversized gaps, required')
    expected=quote(stage,v['window_config'],v['blueprint'])
    if v['cost']!=expected or any(c[k]!=expected[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh')):
        raise ValueError('Every full warmup, Native, load and observer position must be priced')
    cal=inputs[0]
    for method,plan in plans().items():
        anchor=None
        for step,action in enumerate(plan,1):
            if action=='D':anchor=step
            elif (anchor,step) not in cal.rho_at or step not in cal.gains:
                raise ValueError('Existing calibration does not cover this exact scout position')
    return c,reg,old,inputs,tables,prior


def audit_row(row,planned):
    if any(row.get(k)!=v for k,v in planned.items()):raise ValueError('Foreign scout position')
    if row['status']=='TEXT_REJECTED':return
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):raise ValueError('Retain incomplete paths explicitly')
    native=row['method']=='NATIVE35';warm=planned['section']=='WARMUP'
    if (row['solver_steps']!=36 or row['guided_pairs']!=36 or row['audit']!=warm
        or row['in_timing_guided_copies']!=(36 if warm else 0)
        or row['in_timing_hashes'] or row['research_checkpoints']
        or not row['write_deferred_after_main_timer'] or not math.isfinite(row['core_seconds']) or row['core_seconds']<=0
        or row['scout_observation']['observer_enabled']!=planned['observer']
        or row['request_memory_lifecycle']['owners_alive_after']
        or row['request_memory_lifecycle']['observed_owners']!=(0 if native else 1)):
        raise ValueError('Exact full36, observation, memory and diagnostic clocks required')
    if native:
        if row['actions'] is not None or row.get('source_history') or planned['observer']:
            raise ValueError('Native cannot acquire an algorithm owner or cache observations')
        return
    plan=plans()[row['method']]
    if row['semantic_plan']!=list(plan) or row['actions']!=['DD' if a=='D' else 'CC' for a in plan]:
        raise ValueError('Actual semantic actions differ from the frozen scout')
    for action,h in zip(plan,row['source_history']):
        readout=h['A_readout']
        if (h['teacher_calls'] or readout['teacher_calls'] or readout['extra_deep_blocks']
            or h['P_updates_true_D_or_zero_risk_RA_anchor'] or readout['readout_action']!=action
            or (action!='D' and h['true_D_before']!=h['true_D_after'])
            or (action=='C' and (readout['shared_alpha'] or readout['extra_heads']))
            or (action=='A' and readout['shared_alpha']!=1)):
            raise ValueError('No false dense source, teacher or unregistered readout')
    if planned['observer'] and (row['scout_observation']['probe_copies']!=4
        or row['scout_observation']['velocity_copies']!=2 or row['scout_observation']['teacher_calls']):
        raise ValueError('Exactly the four probes and two already computed outputs required')
