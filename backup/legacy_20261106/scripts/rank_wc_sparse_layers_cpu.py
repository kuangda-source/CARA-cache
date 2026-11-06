#!/usr/bin/env python3
"""Rank exposed r4 operators for a small-group proposal; no video prediction."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def analyze(receipt):
    assert len(receipt['cases']) == 312 and all(receipt['all_gate_checks'].values())
    grouped = {(c['call'], c['layer']):{} for c in receipt['cases']}
    for c in receipt['cases']:
        assert c['finite'] and c['arm'] not in grouped[c['call'],c['layer']]
        assert len(c['wall_ms']) == 3 and statistics.median(c['wall_ms']) == c['median_wall_ms']
        grouped[c['call'],c['layer']][c['arm']] = c
    assert len(grouped) == 104
    rows=[]
    for layer in range(2,28):
        points=[]
        for call in (25,26,35,36):
            arms=grouped[call,layer]
            assert set(arms) == {'dense','matched_full','sparse'}
            d,s=arms['dense'],arms['sparse']
            assert d['input_sha256'] == s['input_sha256']
            points.append({'call':call,'rmse_vs_dense':s['rmse_vs_dense'],
                'dense_over_sparse':d['median_wall_ms']/s['median_wall_ms'],
                'operator_saved_ms':d['median_wall_ms']-s['median_wall_ms']})
        rows.append({'layer':layer,'points':points,
            'worst_RMSE':max(v['rmse_vs_dense'] for v in points),
            'minimum_speed_ratio':min(v['dense_over_sparse'] for v in points),
            'median_saved_operator_ms':statistics.median(v['operator_saved_ms'] for v in points),
            'all_four_original_local_screens_pass':all(v['rmse_vs_dense']<=.05 and v['dense_over_sparse']>=1.1 for v in points)})
    eligible=sorted((v for v in rows if v['all_four_original_local_screens_pass']),
        key=lambda v:(v['worst_RMSE'],-v['median_saved_operator_ms'],v['layer']))
    return {'status':'EXPOSED_R4_LAYER_SHORTLIST_CPU_NOT_VIDEO_OR_GENERALIZATION',
        'CPU_only':True,'new_GPU_submission':False,'original_local_screens':{'max_RMSE':.05,'min_speed_ratio':1.1},
        'rows':rows,'eligible_all_four_layers':[v['layer'] for v in eligible],
        'lowest_worst_error_three_layer_draft':[v['layer'] for v in eligible[:3]],
        'scope':'Four operator inputs per layer from one already exposed CAL; no independent holdout.',
        'limits':['Sorting is a conservative proposal, not an error propagation or video quality guarantee.',
            'Saved ms is hot attention operator timing, not whole pipeline acceleration.',
            'No trained router, new thresholds, online current/future truth, or next GPU selection.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=a.receipt.read_bytes();r=analyze(json.loads(raw))
    r.update(receipt_sha256=hashlib.sha256(raw).hexdigest(),analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:r[k] for k in ('status','eligible_all_four_layers','lowest_worst_error_three_layer_draft')}))
