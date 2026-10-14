"""Replay existing H1 scalar observations as causal prefixes, without fitting.

Existing timestep identifiers are recorded but never passed as sigma. No
teacher labels, predictions, altered schedules or new generation are produced.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.w3_causal_trend_r1 import CausalHistory,Observation,coherent_scores

INPUT='reports/wc_p_w3_e0_h1_decisions_20261014.json'
PARAM='manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    data=json.loads((ROOT/INPUT).read_text());params=json.loads((ROOT/PARAM).read_text())
    source_sha=hashlib.sha256((ROOT/INPUT).read_bytes()).hexdigest();paths=[]
    for path in data['paths']:
        if path['method']!='H1_MID':continue
        history=CausalHistory(path['scene'],0,window=4);rows=[]
        for row in path['rows']:
            packets=row['paid_packets'];paid=len(packets)==2;source=row['source']
            assert not paid or [x[0] for x in packets]==[0,1]
            o=Observation(path['scene'],0,row['step'],source_sha+':'+path['id']+':'+str(row['step']),None,
                source,source+':'+str(row['source_birth']) if source else None,row['source_age'],
                row['root_floor'],packets[0][2] if paid else None,packets[1][2] if paid else None,
                row['local_proxy'],row['gain'],row['protected'],row['category']=='OPTIMIZER')
            fs=history.push(o)
            assert all(n<=row['step'] for n in fs['T2'].prefix_steps)
            record={'step':row['step'],'source':source,'source_age':row['source_age'],'original_reason':row['reason'],
                    'actual_sigma_available':False,'original_timestep_identifier_not_sigma':row['scheduler_timestep'],
                    'state_identity_scope':'RECEIPT_ROW_ONLY_NOT_FULL_SNAPSHOT',
                    'features':{m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()}}
            if row['step']==31:
                decision=coherent_scores([-1.,-1.],o,costs={x:params['cost_seconds'][x] if x!='A' else params['source_A_cost_seconds']['D'] for x in ('C','A','D')},
                    lam=params['lambda_seconds_per_weighted_absolute_MSE'])
                assert decision['action']=='D' and decision['scores'] is None
                record['D31_old_support_fallback_preserved']=True
            rows.append(record)
        assert len(rows)==36
        paths.append({'scene':path['scene'],'rows':rows,'paid_pairs':sum(len(r['paid_packets'])==2 for r in path['rows']),
                      'supported_optimizer_rows':sum(r['category']=='OPTIMIZER' for r in path['rows']),
                      'current_teacher_or_prediction_or_labels_used':False})
    assert len(paths)==4 and sum(len(p['rows']) for p in paths)==144
    result={'status':'REAL_H1_4_PATHS144_CAUSAL_SCALAR_PREFIXES_REPLAYED_NO_LABEL_FIT',
        'input_sha256':source_sha,'paths':paths,'GPU_submissions':0,'new_teacher_calls':0,
        'real_model_predictor_fitted':False,'actual_sigma_available':False,
        'next_missing':'Real H1 same-state CAD labels, actual sigma history and paired ordinary-parent control'}
    with a.output.open('x') as out:json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='paths'}))


if __name__=='__main__':main()
