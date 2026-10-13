"""Full60 scope, output/refusal and complete-denominator post controls."""
import copy
from wcomr.h1_cost_curve_production_r1 import validate_contract, METHODS, matrix, CURVE, diagnostic_warm, previous_confirmation_contract
from wcomr.h1_cost_curve_post_r1 import audit_row, endpoint_identity, guided_identity, summaries
from wcomr.source_phase_fixed_mask_r1 import CAL_MASK_A, CAL_MASK_C


def refused(fn, *a):
    try: fn(*a)
    except (ValueError, AssertionError): return
    raise AssertionError('Changed complete scope/control unexpectedly accepted')


def run(config):
    validate_contract(config); scenes = [r['name'] for r in config['requests']]; plan = matrix(scenes)
    mutations = dict(methods=config['methods'][:-1], lambda_grid=[1., 2., 3.],
        scope_counts={**config['scope_counts'], 'scientific_paths': 39},
        forecast_complete_GPUh=8.01, automatic_single_job_GPUh=4, F_B_enabled=True,
        endpoint_tuning=True, training=True, online_teachers=True, head_elision=True,
        GPU_execution_selected=True, fixed_A_plan=list(CAL_MASK_C))
    for key, value in mutations.items():
        c=copy.deepcopy(config); c[key]=value; refused(validate_contract,c)
    c=copy.deepcopy(config);c['requests'][0]['seed']=17;refused(validate_contract,c)
    rows=[]
    for r in plan:
        method=r['method'];idx=list(METHODS).index(method);diag=diagnostic_warm(r)
        actions=None if method=='NATIVE' else ['DD']*36
        v={**r,'status':'COMPLETE','solver_steps':36,'guided_pairs':36,'audit':diag,
           'in_timing_guided_copies':36 if diag else 0,'in_timing_hashes':0,'research_checkpoints':0,
           'write_deferred_after_main_timer':True,'core_seconds':100.+idx,'warm_guided_outputs':36 if diag else 0,
           'actions':actions,'endpoint_audit':'PASS','final_latent_sha256':'a',
           'decoded_video':{'RGB_sha256':'b'},'LPIPS':{'mean_LPIPS':idx/10.}}
        if method.startswith('H1_'):v['curve_lambda']=dict(zip(METHODS[5:8],CURVE))[method]
        if method.startswith('FIXED_'):
            mask=CAL_MASK_A if method=='FIXED_A' else CAL_MASK_C
            v.update(semantic_plan=list(mask),input_adaptive_action_selection=False,
                     actions=['DD' if a=='D' else 'CC' for a in mask])
        if method.startswith(('H1_','FIXED_')):
            v['source_history']=[dict(action=a,teacher_calls=0,P_updates_true_D_or_zero_risk_RA_anchor=False,
                true_D_before='old',true_D_after='old') for a in v['actions']]
        audit_row(v,r);rows.append(v)
    summary=summaries(rows,scenes);assert len(summary['methods'])==10 and summary['full_scope_slots']==60
    assert all(r['scored_scenes']==4 for r in summary['methods'])
    assert len([r for r in rows if diagnostic_warm(r)])==4
    native_contrasts=[c for c in summary['contrasts'] if c['baseline']=='NATIVE']
    assert all(v['LPIPS_change_percent'] is None for c in native_contrasts for v in c['scene_rows'])
    bad=copy.deepcopy(rows);bad[20]['actions']=['DD']*36;refused(audit_row,bad[20],plan[20])
    bad=copy.deepcopy(rows);bad[21]['in_timing_guided_copies']=1;refused(audit_row,bad[21],plan[21])
    bad=copy.deepcopy(rows);bad[21]['id']='foreign';refused(audit_row,bad[21],plan[21])
    refused(summaries,rows[:-1],scenes)
    bad=copy.deepcopy(rows);bad[21]['LPIPS']['mean_LPIPS']=float('nan');refused(summaries,bad,scenes)
    missing=copy.deepcopy(rows);missing[21].pop('LPIPS')
    changed=summaries(missing,scenes);wc=next(x for x in changed['methods'] if x['method']=='WC')
    assert wc['denominator']==4 and wc['scored_scenes']==3 and wc['complete_four_scene_mean_LPIPS'] is None
    endpoint_identity(rows[0],copy.deepcopy(rows[0]))
    bad=copy.deepcopy(rows[0]);bad['decoded_video']['RGB_sha256']='changed';refused(endpoint_identity,rows[0],bad)
    import torch
    left=[torch.tensor([float(i),float(i+1)]) for i in range(36)]
    right=[v.clone() for v in left];guided_identity(left,right)
    right[29][0]+=1.;refused(guided_identity,left,right)
    refused(guided_identity,left,left[:-1])
    mid=next(i for i,r in enumerate(plan) if r['method']=='H1_MID')
    bad=copy.deepcopy(rows[mid]);bad['source_history']=[];refused(audit_row,bad,plan[mid])
    fixed=next(i for i,r in enumerate(plan) if r['method']=='FIXED_A')
    bad=copy.deepcopy(rows[fixed]);bad['source_history'][24]['true_D_after']='illegal';refused(audit_row,bad,plan[fixed])
    final={'status':'SOURCE_CONFIRMATION_FULL40_SCIENCE_ALL50_AUDITED_93FRAME_SCORED',
        'rows':[dict(section='WARMUP' if i<10 else 'TIMED',status='COMPLETE',endpoint_audit='PASS') for i in range(50)]}
    previous_confirmation_contract(final,{'exit_code':0})
    rejected=copy.deepcopy(final);rejected['status']='SOURCE_CONFIRMATION_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED'
    rejected['rows'][11]['status']='VIDEO_REJECTED';previous_confirmation_contract(rejected,{'exit_code':0})
    refused(previous_confirmation_contract,final,{'exit_code':1})
    incomplete=copy.deepcopy(final);incomplete['rows']=incomplete['rows'][:-1];refused(previous_confirmation_contract,incomplete,{'exit_code':0})
    return dict(status='FULL60_PRODUCTION_CONTRACT_POST_AND_REFUSALS_CPU_PASS',
                all60_slots_40_formal_20_warm=True, actual_guided_warm_controls=4,
                mutations_refused=list(mutations)+['seed','formal_copy','foreign_row','native_actions',
                'missing_scope','nonfinite_score','changed_RGB'],
                missing_rejected_denominators_preserved=True, GPU_submissions=0)
