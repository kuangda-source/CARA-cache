"""Preregistered fixed-quota simple schedules, using the accepted H1 executor."""
import hashlib,json,math
from pathlib import Path
from .source_phase_fixed_mask_r1 import CAL_MASK_A,CAL_MASK_C,mask_fingerprint

CONFIG='configs/wc_simple26d_full36_r1_20261015.json'
RUN='wc-simple26d-cal4-full36-r1'
CARD='WC-SIMPLE26D-CAL4-SIXMETHOD-FULL36-R1-20261015-A'
METHODS=('FIXED_A','FIXED_PLAIN','UNIFORM_A','UNIFORM_C','FRONT_DENSE_A','FRONT_DENSE_C')
COUNTS=dict(requests=4,methods=6,scientific_paths=24,full_warmup_paths=12,total_paths=36,
    ordinary_pairs=1296,ordinary_CFG_calls=2592,loads=1,teacher_pairs=0,score_videos=24)
CPU_STATUS='SIMPLE26D_TWO_FLOW_FULL96_CPU_PASS_NOT_GPU'
PRODUCTION_CPU_STATUS='SIMPLE26D_FULL36_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
MODE_REF='manifests/wc_h0_eval_mode_contract_20261003.json'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    from .gpu_budget_pool_v2 import atomic_json
    atomic_json(path,value)

def plans():
    protected=set(range(1,8))|{36}
    uniform=protected|{8+math.floor((k+.5)*28/18) for k in range(18)}
    front=set(range(1,22))|{24,27,30,33,36}
    make=lambda dense,a:tuple('D' if n in dense else a for n in range(1,37))
    return dict(zip(METHODS,(CAL_MASK_A,CAL_MASK_C,make(uniform,'A'),make(uniform,'C'),make(front,'A'),make(front,'C'))))

def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:raise ValueError('All four original CAL inputs required')
    rows=[]
    for repeat in (1,2):
        for method in METHODS if repeat==1 else METHODS[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}',scene=scenes[0],method=method,section='WARMUP',round=repeat))
    for i,scene in enumerate(scenes):
        for method in METHODS if i%2==0 else METHODS[::-1]:
            rows.append(dict(id=f'timed_{i}_{method}',scene=scene,method=method,section='TIMED',round=1))
    return rows

def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['methods']!=list(METHODS) or c['scope_counts']!=COUNTS
        or c['plans']!={k:list(v) for k,v in plans().items()} or c['strategy']!=STRATEGY
        or c['A_method']!='BETA1_ONE_PHASE' or c['warmup_repeats']!=2
        or c['cumulative_cap_GPUh']!=104.97136333301378 or c['autonomy_exclusive_upper_GPUh']!=12
        or not 0<c['forecast_complete_GPUh']<=c['billed_limit_GPUh']<12
        or c['timing_claim']!='CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY'
        or any(c[k] for k in ('training','online_teachers','F_B_enabled','P_enabled','endpoint_tuning','new_native_generation'))
        or len(c['requests'])!=4 or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
            or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])):
        raise ValueError('Complete frozen same26D six-method contract changed')
    for plan in plans().values():
        mask_fingerprint(plan)
        if plan.count('D')!=26 or 'P' in plan:raise ValueError('Exactly26 shared dense pairs required')
        last=0
        for n,action in enumerate(plan,1):
            if action=='D':last=n
            elif not 1<=n-last<=6:raise ValueError('Fixed non-D outside frozen age support')

def execute(inference,sample,method,*,table_parameters,previous_parameters,**kw):
    from .source_phase_fixed_mask_r1 import execute_fixed
    if method not in METHODS or sample.seed!=0:raise ValueError('Frozen CAL simple26D identity required')
    value=execute_fixed(inference,sample,replay_plan=plans()[method],table_parameters=table_parameters['SOURCE_PHASE'],
        previous_parameters=previous_parameters,**kw)
    value.update(bridge_method=value['method'],method=method,timing_claim='CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY')
    return value

def audit_row(row,planned):
    if any(row.get(k)!=v for k,v in planned.items()):raise ValueError('Foreign row or changed original order')
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):return
    plan=plans()[row['method']];diag=planned['section']=='WARMUP'
    if (row['solver_steps']!=36 or row['guided_pairs']!=36 or row['semantic_plan']!=list(plan)
        or row['actions']!=[('DD' if a=='D' else 'CC') for a in plan]
        or row['mask_sha256']!=mask_fingerprint(plan) or row['input_adaptive_action_selection']
        or row['online_teacher_calls'] or row['in_timing_hashes'] or row['research_checkpoints']
        or row['in_timing_guided_copies']!=(36 if diag else 0) or bool(row['audit'])!=diag
        or not row['write_deferred_after_main_timer'] or not row['core_seconds']>0
        or len(row['source_history'])!=36):raise ValueError('Actual full36/26D source/readout receipt failed')
    for action,h in zip(plan,row['source_history']):
        if h['teacher_calls'] or h['P_updates_true_D_or_zero_risk_RA_anchor']:raise ValueError('False teacher or D anchor')
        if h['action']!='DD' and h['true_D_before']!=h['true_D_after']:raise ValueError('C/A wrote D history')
        r=h['A_readout']
        if r['readout_action']!=action or r['teacher_calls'] or r['extra_deep_blocks']:raise ValueError('Readout differs from frozen action')
        if action=='C' and (r['shared_alpha'] or r['extra_heads']):raise ValueError('Plain reuse paid A')

def validate(project,stage):
    from .p_acr_profile528_production_r1 import validate as physical
    pc,reg,old,inputs,values=physical(project,stage)
    c=json.loads((Path(stage)/CONFIG).read_text());validate_contract(c)
    if c['requests']!=pc['requests']:raise ValueError('Original four CAL inputs changed')
    for key in ('cost','baseline'):
        ref=c['references'][key]
        if sha(Path(stage)/ref['ref'])!=ref['sha256']:raise ValueError('Frozen reference changed: '+key)
    baseline=json.loads((Path(stage)/c['references']['baseline']['ref']).read_text())
    if len(baseline['rows'])!=12:raise ValueError('All12 prior Native/fixedA/plain bindings required')
    for r in baseline['rows']:
        for key in ('video_artifact','final_artifact'):
            asset=r[key];path=Path(asset['path'])
            if sha(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes']:raise ValueError('Original endpoint artifact changed')
    proof=json.loads((Path(stage)/'simple26d-sampling-CPU-result.json').read_text())
    if (proof['status']!=CPU_STATUS or proof['actual_CPU_paths']!=96 or proof['GPU_submissions']
        or proof['CUDA_initialized'] or len(proof['checks'])!=2
        or not all(x['complete_CPU_paths']==48 and x['all36_clean_outputs_actions_video_equal'] for x in proof['checks'])):
        raise ValueError('Complete two-flow96 audit/lean sampling CPU required')
    for name,digest in proof['payload_sha256'].items():
        if reg['payload_sha256'].get(name)!=digest:raise ValueError('Sampling-tested payload changed')
    return c,reg,old,inputs,{'SOURCE_PHASE':values['H1']},values['previous']
