"""Independent scalar reconstruction from the already raw-audited N1 receipt."""
import hashlib,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def q(p,g):
    m=p['related_error_moments'];return (1-g)**2*m['A']+g*g*m['B']+2*g*(1-g)*m['C']
def fit(points):
    m={k:mean(p['related_error_moments'][k] for p in points) for k in ('A','B','C')}
    den=m['A']+m['B']-2*m['C']
    return 0. if den<=1e-12*max(1.,m['A']+m['B']) else max(0.,min(1.,(m['A']-m['C'])/den))
def main():
    ref=R/'reports/wc_math_n1_live_or_terminal_capture_20261012.json';captured=json.loads(ref.read_text())
    result=captured['final'];sup=captured['supervisor'];points=result['points']
    assert result['status']=='N1_ALL4_PARENTS12_POINTS48_READOUTS180_PAIRS_CPU_AUDITED'
    assert captured['post_exit']['exit_code']==sup['child_exit_code']==0
    assert all(captured['payload_verified'].values()) and not any(captured['original_processes'].values())
    assert result['budget_before_sha256']==result['budget_after_sha256']==captured['ledger_sha256']
    assert len(points)==12 and len(result['parents'])==4
    P=[p for p in points if p['selection']['source']=='P'];D=[p for p in points if p['selection']['source']=='D']
    assert len(P)==8 and len(D)==4 and all(p['all_candidate_and_teacher_tensors_read'] for p in points)
    gamma=fit(P);assert math.isclose(gamma,result['global_related_gain']['gamma'],rel_tol=1e-12)
    rows=[]
    for p in points:
        s=p['selection'];loss=p['losses'];normalized=q(p,gamma)
        assert math.isclose(q(p,.5),loss['FUSION_HALF_UNIT']['normalized_guided_MSE'],rel_tol=2e-5,abs_tol=1e-8)
        rows.append({'scene':s['scene'],'step':s['step'],'source':s['source'],'alpha':s['shared_alpha'],
            'C_MSE':loss['OFFICIAL_C']['MSE'],'oldD_A_MSE':loss['D_REFERENCE_UNIT']['MSE'],
            'P_A_MSE':loss['P_REFERENCE_UNIT']['MSE'],'half_A_MSE':loss['FUSION_HALF_UNIT']['MSE'],
            'fitted_A_MSE':normalized*p['teacher_guided_energy'],
            'fitted_A_normalized_MSE':normalized,'fitted_A_vs_C_percent':
                100*(normalized/loss['OFFICIAL_C']['normalized_guided_MSE']-1),
            'readouts_raw_checked':4})
    old=mean(p['related_error_moments']['A'] for p in P);base=mean(p['losses']['OFFICIAL_C']['normalized_guided_MSE'] for p in P)
    fused=mean(q(p,gamma) for p in P)
    folds=[]
    for f in result['global_related_gain']['leave_one_scene_out']:
        g=fit([p for p in P if p['selection']['scene']!=f['held_scene']])
        hold=[p for p in P if p['selection']['scene']==f['held_scene']]
        value=mean(q(p,g) for p in hold)
        assert math.isclose(g,f['trained_on_other_scenes_gamma'],rel_tol=1e-12)
        assert math.isclose(value,f['held_fused_loss'],rel_tol=1e-12)
        folds.append({'scene':f['held_scene'],'gamma':g,'held_fused_loss':value,
                      'held_oldD_A_loss':f['held_old_loss'],'held_C_loss':mean(p['losses']['OFFICIAL_C']['normalized_guided_MSE'] for p in hold)})
    summary={'status':'N1_COMPLETE_SCALAR_RECONSTRUCTION_PASS_NOT_NEW_POLICY_ENDPOINT',
        'raw_checked_receipt_ref':str(ref.relative_to(R)),'raw_checked_receipt_sha256':sha(ref),
        'P_points':8,'D_controls':4,'all48_readout_scores_checked':True,'gamma':gamma,
        'P_scene_equal_oldD_A':old,'P_scene_equal_C':base,'P_scene_equal_fusion':fused,
        'P_fusion_reduction_vs_oldD_A_percent':100*(1-fused/old),
        'P_fusion_reduction_vs_C_percent':100*(1-fused/base),
        'P_P_reference_better_than_oldD_count':sum(p['related_error_moments']['B']<p['related_error_moments']['A'] for p in P),
        'P_fusion_better_than_C_count':sum(q(p,gamma)<p['losses']['OFFICIAL_C']['normalized_guided_MSE'] for p in P),
        'D_original_A_worse_than_C_count':sum(p['related_error_moments']['A']>p['losses']['OFFICIAL_C']['normalized_guided_MSE'] for p in D),
        'all4_parent_controls_equal':all(p['all36_guided_final_actions_and93RGB_equal'] for p in result['parents']),
        'leave_one_scene_out':folds,'states':rows,'GPU_cost_hours':sup['wall_seconds']/3600,
        'ledger_used':captured['ledger']['used_gpu_hours'],'remaining_GPUh':captured['ledger']['cap_gpu_hours']-captured['ledger']['used_gpu_hours'],
        'GPU_submissions':0,'ledger_written':False,'new_method_final_video_claim':False}
    dest=R/'reports/wc_math_n1_complete_independent_scalar_reconstruction_20261012.json'
    assert not dest.exists();dest.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:summary[k] for k in ('status','gamma','P_fusion_reduction_vs_oldD_A_percent','P_fusion_reduction_vs_C_percent','P_fusion_better_than_C_count','remaining_GPUh')}))
if __name__=='__main__':main()
