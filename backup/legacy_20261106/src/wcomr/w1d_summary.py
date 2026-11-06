"""Sample-level CAL mechanism screen; no token-level statistical replication."""
from itertools import combinations
from statistics import mean
from .w1d import validate_pair

METRICS=['prewarp_residual','postwarp_residual','velocity']


def summarize(receipt,partial=False):
    expected=receipt['protocol']['samples']
    if not partial:
        assert receipt['status']=='W1D_CAL8_ATTEMPTED_ALL_PARITY_PASS'
        assert len(receipt['cases'])==len(expected)==8
    assert [c['name'] for c in receipt['cases']]==expected[:len(receipt['cases'])]
    rows=[]
    for case in receipt['cases']:
        if case['status']!='PAIR_PARITY_PASS':
            if partial:continue
            raise ValueError('Incomplete or failed pair')
        validate_pair(case['off'],case['on'],case['selection'])
        records=case['on']['shadow_records']
        row={'name':case['name'],'outcome':case['on']['outcome'],'coverage':case['coverage'],
             'selected_points':len(records),'candidates':{},'ranking_reversals':[],
             'truth_tail_seconds':sum(r['truth_tail_seconds'] for r in records),
             'diagnostic_seconds':sum(r['diagnostic_seconds'] for r in records)}
        for mode in ['scalar','shrink']:
            info={'fallback_count':sum(r['candidates'][mode]['reason']!=mode for r in records),'metrics':{}}
            for kind in METRICS:
                den=sum(r['candidates']['official'][kind]['mse'] for r in records)
                num=sum(r['candidates'][mode][kind]['mse'] for r in records)
                info['metrics'][kind]={'sum_mse_ratio':num/den if den>0 else None,
                    'improved_points':sum(r['candidates'][mode][kind]['mse']<r['candidates']['official'][kind]['mse'] for r in records)}
            row['candidates'][mode]=info
        for r in records:
            for a,b in combinations(['official','scalar','shrink'],2):
                residual=r['candidates'][a]['postwarp_residual']['mse']-r['candidates'][b]['postwarp_residual']['mse']
                velocity=r['candidates'][a]['velocity']['mse']-r['candidates'][b]['velocity']['mse']
                if residual*velocity<0:row['ranking_reversals'].append({'call':r['call'],'cfg_branch':r['cfg_branch'],
                    'modes':[a,b],'postwarp_residual_difference':residual,'velocity_difference':velocity})
        rows.append(row)
    full=len(rows)==8 and all(r['coverage']=='FULL_FOUR_PAIR_SCREEN' and r['selected_points']==8 for r in rows)
    aggregate={}
    for mode in ['scalar','shrink']:
        values=[r['candidates'][mode]['metrics']['velocity']['sum_mse_ratio'] for r in rows]
        post=[r['candidates'][mode]['metrics']['postwarp_residual']['sum_mse_ratio'] for r in rows]
        aggregate[mode]={'mean_sample_velocity_mse_ratio':mean(values) if values and all(v is not None for v in values) else None,
            'mean_sample_postwarp_mse_ratio':mean(post) if post and all(v is not None for v in post) else None,
            'velocity_improved_samples':sum(v is not None and v<1 for v in values),
            'joint_improved_samples':sum(v is not None and v<1 and p is not None and p<1 for v,p in zip(values,post)),
            'fallback_count':sum(r['candidates'][mode]['fallback_count'] for r in rows)}
    signals=[mode for mode,x in aggregate.items() if full and x['fallback_count']==0 and x['joint_improved_samples']>=6
             and x['mean_sample_velocity_mse_ratio'] is not None and x['mean_sample_postwarp_mse_ratio'] is not None
             and x['mean_sample_velocity_mse_ratio']<1 and x['mean_sample_postwarp_mse_ratio']<1]
    negative=full and all(x['fallback_count']==0 and x['mean_sample_velocity_mse_ratio'] is not None
                         and x['mean_sample_velocity_mse_ratio']>=1 for x in aggregate.values())
    status='LIVE_PARTIAL_NO_DECISION' if partial else 'MECHANISM_ONLY_CAL8' if signals else 'NO_GAIN_CAL8_IN_SCOPE' if negative else 'INCONCLUSIVE_CAL8'
    return {'status':status,'completed_pair_samples':len(rows),'planned_samples':8,
            'accepted':sum(r['outcome']=='ACCEPTED' for r in rows),'text_rejected':sum(r['outcome']=='TEXT_REJECTED' for r in rows),
            'video_rejected':sum(r['outcome']=='VIDEO_REJECTED' for r in rows),'full_sparse_coverage':full,
            'candidate_signals':signals,'aggregate':aggregate,'samples':rows,
            'limitation':'Reusable CAL development only. Equal sample weighting; points/branches/groups are dependent observations. Rejected videos remain denominator. No quality, deployed candidate efficacy, clean speed or independent confirmation.'}
