"""One source-equal price/risk crossing lambda; no endpoint-based selection."""
import hashlib,json,math
from pathlib import Path
from statistics import median

R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    capture=R/'reports/wc_math_n2_live_or_terminal_capture_20261012.json'
    oldref=R/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json'
    old=json.loads(oldref.read_text());result=json.loads(capture.read_text())
    assert result['final']['status']=='MATH_N2_FULL36_SCIENCE_ALL54_AUDITED_93FRAME_SCORED'
    costs=old['cost_seconds'];Dhead=costs['C']+(costs['A']-costs['C'])/2
    p={k:v for k,v in old.items() if k not in ('fingerprint','lambda_seconds_per_normalized_error','sources','version')}
    p.update(version='SUPPORTED_SOURCE_GATE_SQUARED_GAIN_R1',
        source_A_cost_seconds={'D':Dhead,'P':costs['A']},
        propagation_rule='SQUARED_L2_AMPLITUDE_GAIN_TIMES_NORMALIZED_GUIDED_MSE',
        source_readout_rule='D_MINIMUM_A_P_MINIMUM_C_WITH_OPTIONAL_P_A',
        support_rule='CURRENT_AND_FUTURE_RHO_CELL_REQUIRED_D_FALLBACK_EXPLICIT',
        sources={str(f.relative_to(R)):sha(f) for f in (capture,oldref)})
    rows=[r for r in result['final']['rows'] if r['section']=='TIMED' and r['method']=='P_OFF'];assert len(rows)==4
    scene_rows=[]
    for row in rows:
        crossings=[];excluded=[];P_count=0
        for h in row['source_history']:
            d=h['source_policy']['decision']
            if d['action']!='P':continue
            P_count+=1;source=d['state_before'][1];floor=d['state_before'][3]
            local,g=d['local_proxy'],d['gain']
            if local is None or g is None:excluded.append({'step':d['step'],'reason':'NO_BOUND_PAID_PROXY'});continue
            qr=g*g*p['source'][source]['C_scale']*(floor+local)**2
            action='A' if source=='D' else 'C'
            if action=='A':qr*=p['source'][source]['A_over_C']
            qp=g*g*p['source']['P']['C_scale']*d['predicted_creation_floor']**2
            cost=p['source_A_cost_seconds'][source] if action=='A' else costs['C']
            delta=qr-qp;difference=costs['P']-cost
            if not math.isfinite(delta+difference) or min(delta,difference)<=1e-12:
                excluded.append({'step':d['step'],'reason':'NO_POSITIVE_PRICE_RISK_CROSSING','qR':qr,'qP':qp});continue
            value=difference/delta
            crossings.append({'step':d['step'],'source':source,'readout':action,'lambda_crossing':value,
                'qR':qr,'qP':qp,'reuse_cost':cost,'P_cost':costs['P'],'bound_actual_birth_floor':d['predicted_creation_floor']})
        assert P_count==len(crossings)+len(excluded) and crossings,'Every original CAL needs positive support; never fill zero'
        scene_rows.append({'scene':row['scene'],'actual_P_count':P_count,'crossings':crossings,
                           'excluded':excluded,'scene_median_crossing':median(x['lambda_crossing'] for x in crossings)})
    p['lambda_seconds_per_normalized_error']=median(s['scene_median_crossing'] for s in scene_rows)
    p['lambda_rule']='MEDIAN_OF_FOUR_CAL_SCENE_MEDIANS_ALL_ACTUAL_P_OFF_P_ACTIONS_NO_ENDPOINT_SELECTION'
    p['lambda_calibration_rows']=scene_rows
    p['endpoint_used_for_lambda_selection']=False
    p['fingerprint']=hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest()
    target=R/'manifests/wc_supported_gate_frozen_parameters_r1_20261012.json';assert not target.exists()
    target.write_text(json.dumps(p,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'lambda':p['lambda_seconds_per_normalized_error'],'source_A_cost_seconds':p['source_A_cost_seconds'],
                     'scene_support':[(x['actual_P_count'],len(x['crossings']),x['scene_median_crossing']) for x in scene_rows],
                     'GPU_submissions':0,'ledger_written':False}))
if __name__=='__main__':main()
