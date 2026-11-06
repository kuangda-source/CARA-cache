#!/usr/bin/env python3
"""Independent scalar/holdout/attribution reconstruction from saved receipts."""
import argparse,collections,gzip,hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(value):
 original=json.loads(gzip.decompress((ROOT/value['original_capture_ref']).read_bytes()))['capture']
 runner=next(v['data'] for k,v in original['receipts'].items() if k.endswith('/runner.json'))
 index={r['id']+':'+str(p['step']):(r,p) for r in runner['runs'] for p in r.get('diagnostic_points',[])}
 cfg=json.loads((ROOT/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json').read_text());table=json.loads((ROOT/cfg['references']['H1']['ref']).read_text())
 lam=table['lambda_seconds_per_weighted_absolute_MSE'];order={'C':0,'A':1,'D':2};outputs=[]
 assert digest(ROOT/value['original_capture_ref'])==value['original_capture_sha256'] and digest(ROOT/value['repair_capture_ref'])==value['repair_capture_sha256']
 for cohort in value['cohorts']:
  points=cohort['point_predictions'];groups=cohort['groups'];n=len(groups)*8
  assert len(points)==4*n
  folds={(f['model'],f['held_group']):f for f in cohort['folds']};assert len(folds)==2*len(groups)
  for f in folds.values():
   assert f['held_group'] not in f['training_groups'] and set(f['training_groups'])==set(groups)-{f['held_group']}
   assert set(f['training_prompts']).isdisjoint(f['held_observation_prompts']) and f['ridge']==1 and f['window']==4
  for row in points:
   parent,p=index[row['id']];h=parent['source_history'][row['step']-1];obs=parent['feature_rows'][row['step']-1]['observation'];q=p['label'];g2=obs['gain']**2
   costs={'C':table['cost_seconds']['C'],'A':table['source_A_cost_seconds'][obs['source_kind']],'D':table['cost_seconds']['D']}
   truth={a:costs[a]+lam*(g2*q['q_'+a] if a!='D' else 0.) for a in ('C','A','D')}
   assert all(near(row['true_scores'][a],truth[a]) for a in truth)
   oracle=min(truth,key=lambda a:(truth[a],order[a]));assert row['oracle']==oracle
   assert near(row['local_regret'],truth[row['action']]-truth[oracle])
   target=[g2*q['q_A'],g2*(q['q_C']-q['q_A'])];assert all(near(a,b) for a,b in zip(row['weighted_targets'],target))
   pred=row['raw_prediction'];risk={'C':max(0.,sum(pred)),'A':max(0.,pred[0]),'D':0.}
   predicted={a:costs[a]+lam*risk[a] for a in costs}
   assert all(near(row['predicted_scores'][a],predicted[a]) for a in costs)
   if row['model']=='T0_H1_ORIGINAL':assert row['action']==p['parent_readout']
   else:assert row['action']==min(predicted,key=lambda a:(predicted[a],order[a]))
   if row['model'] in ('T1','T2'):
    fold=folds[row['model'],row['group']];features=parent['feature_rows'][row['step']-1]['features'][row['model']]
    assert features['names']==fold['feature_names']
    z=[1.]+[(x-mean)/std for x,mean,std in zip(features['values'],fold['mean'],fold['std'])]
    reconstructed=[math.fsum(x*w[j] for x,w in zip(z,fold['weights'])) for j in (0,1)]
    assert all(near(a,b) for a,b in zip(pred,reconstructed))
  base={r['id']:r for r in points if r['model']=='T0_CAD'};attribution=[]
  for model in cohort['models']:
   rows=[r for r in points if r['model']==model['model']]
   per_prompt=[statistics.fmean(r['local_regret'] for r in rows if r['group']==g) for g in groups]
   mean=statistics.fmean(per_prompt);assert near(model['prompt_equal_mean_regret'],mean)
   assert near(model['prompt_equal_oracle_error_rate'],statistics.fmean(r['action']!=r['oracle'] for r in rows))
   assert model['actions_changed_vs_T0_CAD']==sum(r['action']!=base[r['id']]['action'] for r in rows)
   if model['model'] in ('T1','T2'):
    bystep=[]
    for step in sorted({r['step'] for r in rows}):
     subset=[r for r in rows if r['step']==step]
     gain=math.fsum(base[r['id']]['local_regret']-r['local_regret'] for r in subset)
     bystep.append(dict(step=step,points=len(subset),sum_regret_reduction=gain,contribution_to_all_point_mean=gain/n,
         changes=[dict(group=r['group'],before=base[r['id']]['action'],after=r['action']) for r in subset if base[r['id']]['action']!=r['action']]))
    total=math.fsum(s['sum_regret_reduction'] for s in bystep)
    assert near(total/n,cohort['models'][1]['prompt_equal_mean_regret']-mean)
    attribution.append(dict(model=model['model'],steps=bystep,total_regret_reduction_sum=total,
       step23_fraction_of_signed_total=next(s['sum_regret_reduction'] for s in bystep if s['step']==23)/total if total else None,
       biggest_regret_points=sorted(rows,key=lambda r:r['local_regret'],reverse=True)[:3]))
  outputs.append(dict(cohort=cohort['cohort'],points=n,prompt_groups=len(groups),metrics_and_predictions_independently_reconstructed=True,
      attribution_type='EXPLORATORY_DECOMPOSITION_OF_REGISTERED_RESULTS_NOT_A_NEW_POLICY_RUN',step_attribution=attribution))
 return dict(status='W3_GROUPED_PREDICTIONS_COST_UNITS_HOLDOUT_AND_METRICS_INDEPENDENTLY_VERIFIED',cohorts=outputs,
     original_H1_bridge_unchanged_on_sampled_points=all(c['original_H1_to_CAD_bridge_changed_points']==0 for c in value['cohorts']),
     new_GPU_submissions=0,actual_policy_or_speed_improvement_claim=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 result=verify(json.loads(a.input.read_text()));result.update(input_ref=str(a.input),input_sha256=digest(a.input))
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cohorts=[{k:c[k] for k in ('cohort','points','prompt_groups')} for c in result['cohorts']])))
if __name__=='__main__':main()
