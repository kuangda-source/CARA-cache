"""Secondary DEV128 analysis; preserve original selection; no GPU/network."""
import json,sys,statistics as st
from pathlib import Path
from analyze_cara_dev128_complete_r1 import analyze,interval,sha,LIMITS,ROOT

def main():
 old=json.loads((ROOT/'reports/cara_DEV128_A6000_complete_analysis_20261027.json').read_text())
 paths=[ROOT/old['evidence'][k]['path'] for k in ('capture','acceptance','central_settlement')]
 for k,p in zip(('capture','acceptance','central_settlement'),paths):assert sha(p)==old['evidence'][k]['sha256']
 x=analyze(*paths);s=x['summaries'];a=s['SHARED25_A_PHASE_AGE3'];comparisons={}
 for ref in ['NATIVE35','SHARED25_C','S25_A_PHASE','S25_C','NATIVE26']:
  b=s[ref];pairs=list(zip(a['per_prompt'],b['per_prompt']));assert all(l['member']==r['member'] for l,r in pairs)
  quality={}
  for dim,margin in LIMITS.items():
   delta=[l['quality'][dim]-r['quality'][dim] for l,r in pairs];ci=interval(delta)
   quality[dim]=dict(**ci,margin=margin,point_noninferior=ci['mean']>=-margin,lower_bound_noninferior=ci['lower95']>=-margin,improved=sum(d>0 for d in delta),worst_delta=min(delta),worst_prompt=pairs[delta.index(min(delta))][0]['member'],per_prompt_delta=delta)
  lp=[l['LPIPS']-r['LPIPS'] for l,r in pairs]
  comparisons[ref]=dict(quality=quality,LPIPS_delta=interval(lp),relative_LPIPS_gain=None if b['LPIPS']==0 else 1-a['LPIPS']/b['LPIPS'],LPIPS_improved=sum(d<0 for d in lp),worst_LPIPS_increase=max(lp),seconds_delta=interval([l['seconds']-r['seconds'] for l,r in pairs]))
 o=dict(status='SECONDARY_POSTHOC_NO_RESELECTION',original_main_candidate='SHARED25_C',evaluated_role='SHARED25_A_PHASE_AGE3',cohort=x['cohort'],evidence=x['evidence'],candidate=a,comparisons=comparisons,formal_quality_references=['S25_A_PHASE','NATIVE35'],additional_comparator='SHARED25_C',all_formal_quality_lower_bounds_pass=all(q['lower_bound_noninferior'] for ref in ['S25_A_PHASE','NATIVE35'] for q in comparisons[ref]['quality'].values()),budget_pass=a['budget']['V_upper95']<=1,independent_confirmation=False,GPU_submissions=0,IG='PAUSED')
 (ROOT/'reports/cara_DEV128_age3_quality_tradeoff_20261028.json').write_text(json.dumps(o,indent=2)+'\n')
 print('budget',a['budget'])
 for ref,c in comparisons.items():
  print(ref,'LPIPS',c['LPIPS_delta'],'time',c['seconds_delta']['mean'])
  for dim,q in c['quality'].items(): print(dim, {k:q[k] for k in ['mean','lower95','lower_bound_noninferior','worst_delta']})
 print('formal_pass',o['all_formal_quality_lower_bounds_pass'])
if __name__=='__main__':main()
