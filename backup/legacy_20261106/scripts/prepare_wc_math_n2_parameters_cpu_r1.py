"""Freeze source scales, related gain, cost and lambda from audited CAL data."""
import hashlib,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    receipt=R/'reports/wc_math_n1_live_or_terminal_capture_20261012.json'
    independent=R/'reports/wc_math_n1_complete_independent_scalar_reconstruction_20261012.json'
    costref=R/'reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json'
    thresholdref=R/'configs/wc_current_birth_full64_selected_r1_20261010.json'
    cap=json.loads(receipt.read_text());check=json.loads(independent.read_text())
    assert check['raw_checked_receipt_sha256']==sha(receipt)
    assert cap['final']['status']=='N1_ALL4_PARENTS12_POINTS48_READOUTS180_PAIRS_CPU_AUDITED'
    gamma=check['gamma'];points=cap['final']['points'];table={}
    for source in ('D','P'):
        pp=[p for p in points if p['selection']['source']==source]
        qc=mean(p['losses']['OFFICIAL_C']['normalized_guided_MSE'] for p in pp)
        proxy2=mean((p['selection']['risk_source_floor']+p['selection']['risk_local_proxy'])**2 for p in pp)
        def fitted(p):
            m=p['related_error_moments'];return (1-gamma)**2*m['A']+gamma*gamma*m['B']+2*gamma*(1-gamma)*m['C']
        qa=mean(fitted(p) for p in pp)
        assert min(qc,proxy2)>1e-12 and all(math.isfinite(x) for x in (qc,proxy2,qa))
        table[source]={'C_scale':qc/proxy2,'A_over_C':qa/qc,
            'CAL_states':len(pp),'mean_normalized_C':qc,'mean_normalized_A_fusion':qa,
            'mean_squared_root_proxy_plus_floor':proxy2,
            'new_noise_intervals_or_trajectory_support':'TRANSFER_NOT_ENDPOINT_BOUND'}
    costs=dict(json.loads(costref.read_text())['ranking']['global_means'])
    C=costs['C'];A=C+(costs['A_BETA1_ONE_PHASE']-C)*(2 if 0<gamma<1 else 1)
    threshold=json.loads(thresholdref.read_text())['preregistration']['RA_threshold']
    result={'version':'MATH_N2_SOURCE_SIGMA_H1_H2_PARAMETERS_R1','gamma':gamma,'source':table,
        'A_pair_cost_seconds':A,'original_RA_threshold':threshold,
        'lambda_seconds_per_normalized_error':costs['DENSE_WITH_P0']/(table['D']['C_scale']*threshold**2),
        'lambda_rule':'D_COST_OVER_D_SOURCE_SCALE_TIMES_ORIGINAL_RA_THRESHOLD_SQUARED',
        'cost_boundary':'AFTER_COMMON_PAID_PROBE_FULL_PAIR_OUTPUT_WITH_ALGORITHM_MAINTENANCE',
        'cost_seconds':{'C':C,'A':A,'P':costs['ROTATION_050'],'D':costs['DENSE_WITH_P0']},
        'interior_gamma_extra_head_cost':'TWO_CORRECTION_HEADS_LINEAR_INCREMENTAL_TRANSFER_NOT_NEW_TIMING',
        'N1_source_revision':cap['supervisor']['source_revision'],
        'sources':{str(p.relative_to(R)):sha(p) for p in (receipt,independent,costref,thresholdref)},
        'fitting_label':'CAL_ONLY_FOUR_SCENES_SEED0_NOT_INDEPENDENT_CONFIRMATION',
        'floor_and_current_drift_combination':'EMPIRICAL_SQUARED_SUM_NOT_INDEPENDENCE_ASSUMPTION',
        'actual_online_teachers':0,'future_drift':'CURRENT_SLOPE_TRANSFER_OVER_KNOWN_SIGMA',
        'GPU_submissions':0,'ledger_written':False}
    result['fingerprint']=hashlib.sha256(json.dumps(result,sort_keys=True,allow_nan=False).encode()).hexdigest()
    dest=R/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json';assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('gamma','lambda_seconds_per_normalized_error','cost_seconds','source')}))
if __name__=='__main__':main()
