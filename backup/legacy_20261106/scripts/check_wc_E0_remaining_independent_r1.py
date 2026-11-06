#!/usr/bin/env python3
"""Independent saved-frame/action/score arithmetic; no fit, weights or server."""
import argparse,collections,gzip,hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):
    b=(ROOT/p).read_bytes();return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    ref='reports/wc_E0_remaining_seed_layout_phase_CPU_complete_20261017.json';r=read(ref)
    for n,h in r['input_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    raw=read('reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz')
    rows={(q['case_id'],q['method']):q for q in raw['final']['rows'] if q['section']=='TIMED'}
    cases={q['id']:q for q in raw['runner']['cases']};seed_rows=[]
    for q in r['readout_seed_stability']['prompts']:
        gains=[]
        for seed in q['seeds']:
            values=[rows[(seed['case_id'],m)] for m in ['FRONT_DENSE_C','FRONT_DENSE_A']]
            assert all(x['endpoint_audit']=='PASS' and len(x['LPIPS']['frame_distances'])==93 for x in values)
            gain=statistics.mean(values[0]['LPIPS']['frame_distances'])-statistics.mean(values[1]['LPIPS']['frame_distances'])
            assert gain==seed['gain_C_minus_A'] and cases[seed['case_id']]['prompt_id']==q['prompt']
            gains.append(gain)
        assert len(gains)==2 and statistics.mean(gains)==q['prompt_equal_gain']
        seed_rows.append((all(g>0 for g in gains),all(g<0 for g in gains)))
    assert len(seed_rows)==6 and sum(q[0] for q in seed_rows)==3 and sum(q[1] for q in seed_rows)==2
    same=different=0
    for row in r['RA_A_layout_divergences']:
        x,y=[rows[(row['case_id'],m)].get('actions') or [] for m in ['RA_DEFAULT','A_NO_P']]
        complete=len(x)==len(y)==36;assert row['comparable_complete36']==complete
        if complete:
            positions=[i+1 for i,(v,w) in enumerate(zip(x,y)) if v!=w]
            assert positions==row['physical_disagreement_positions']
            assert row['physical_layouts_identical']==(not positions)
            same+=not positions;different+=bool(positions)
    assert (same,different)==(2,12)
    phase=read('reports/wc_w3_phase_vs_state_CPU_primary_and_sensitivity_r1_20261016.json')
    checks=[]
    for c,old in zip(r['phase_state_remaining'],phase['cohorts']):
        assert c['groups']==old['groups']
        all_points=collections.defaultdict(list)
        for q in old['point_predictions']:all_points[q['model']].append(q)
        all_points.update(c['controlled_point_predictions'])
        for agg in c['aggregate']:
            points=[q for q in all_points[agg['model']] if not agg['exclude_step23'] or q['step']!=23]
            per=collections.defaultdict(list)
            for q in points:
                loss=q['true_scores'][q['action']]-min(q['true_scores'].values())
                assert math.isclose(loss,q['local_regret'],abs_tol=1e-12)
                per[q['group']].append(loss)
            value=statistics.mean(statistics.mean(v) for v in per.values())
            assert len(points)==agg['points'] and math.isclose(value,agg['prompt_equal_mean_regret'],abs_tol=1e-12)
            checks.append(dict(cohort=c['cohort'],model=agg['model'],exclude23=agg['exclude_step23'],points=len(points),regret=value))
    result=dict(status='E0_INDEPENDENT_FRAME_ACTION_OBJECTIVE_ARITHMETIC_ACCEPTED',analysis_ref=ref,
        analysis_sha256=hashlib.sha256((ROOT/ref).read_bytes()).hexdigest(),double_seed_prompts=6,both_positive=3,both_negative=2,mixed=1,
        complete_layout_pairs=14,identical_layouts=same,different_layouts=different,phase_aggregate_checks=checks,
        GPU_submissions=0,SSH_queries=0,weights_loaded=0,original_raw_or_thresholds_written=False)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='phase_aggregate_checks'}))
if __name__=='__main__':main()
