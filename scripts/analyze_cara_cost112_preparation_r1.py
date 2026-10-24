#!/usr/bin/env python3
"""Reproduce attribution and frozen coefficients from complete accepted104 only."""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.historical_terminal import accept,record

def main():
 capref=ROOT/'reports/cara_history104_R2_terminal_20261024_2315.json';accref=ROOT/'reports/cara_history104_R2_accepted_20261024_2315.json';manifest=ROOT/'manifests/cara_cost112_scope_quote_r1_20261025.json'
 v=json.loads(capref.read_text());a=json.loads(accref.read_text());assert a['capture_sha256']==hashlib.sha256(capref.read_bytes()).hexdigest();assert all(a[k]==value for k,value in accept(v).items())
 card=json.loads(manifest.read_text());old=record(v,'card');by={(r['slot']['section'],r['slot']['member'],r['slot']['role']):r['result'] for r in v['requests'].values()}
 analysis=json.loads((ROOT/'reports/cara_history104_R2_complete_analysis_20261024.json').read_text());t=analysis['timing']['frozen_result'];worst=max(t['validation'],key=lambda x:x['underestimate_seconds']);m=worst['member']
 comp={(r['section'],r['role']):r for r in analysis['timing']['formal_component_rows'] if r['member']==m}
 keys=['method_install_seconds','guarded_pipeline_without_write_seconds','video_write_seconds','method_cleanup_seconds','core_seconds','outside_core_seconds'];pairs={}
 for s in ('CALIBRATION','VALIDATION'):
  pairs[s]={k:comp[s,'PG_ALL_D'][k]-comp[s,'NATIVE'][k] for k in keys};pairs[s]['full_seconds']=by[s,m,'PG_ALL_D']['full_request_seconds']-by[s,m,'NATIVE']['full_request_seconds']
 x=[];y=[]
 for (s,m,role),r in by.items():
  if s in ('CALIBRATION','VALIDATION') and role not in ('NATIVE','PG_ALL_D'):
   c=old['policies'][role]['counts'];x.append([c['D']-36,c['A']]);y.append(r['full_request_seconds']-by[s,m,'PG_ALL_D']['full_request_seconds'])
 coef,_,rank,_=np.linalg.lstsq(x,y,rcond=None);assert len(x)==64 and rank==2
 assert card['cost_model']['coefficients']==coef.tolist() and card['cost_model']['fit_capture_sha256']==hashlib.sha256(capref.read_bytes()).hexdigest()
 assert all(card['policies'][r]==p for r,p in old['policies'].items()) and card['budget']==old['budget']
 out=dict(status='COMPLETE104_ATTRIBUTION_AND_COST112_FROZEN_DEVELOPMENT_MODEL',observed_unix=time.time(),original_model_still_failed=True,original_maximum_underestimate=worst,fullD_minus_native_components=pairs,native_adjusted_round_shift={k:pairs['VALIDATION'][k]-pairs['CALIBRATION'][k] for k in pairs['VALIDATION']},frozen_model=card['cost_model'],development_only_maximum_underestimate_seconds=float(max(np.array(y)-np.dot(x,coef))),new_independent_validation_passed=False,causal_thermal_attribution_proven=False,scope=card['scope'],quote=card['quote'],original_alpha_and_strong_baselines_equal=True,GPU_submissions=0,bindings={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (capref,accref,manifest,Path(__file__))})
 target=Path(sys.argv[1]);
 with target.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(out['native_adjusted_round_shift']));print('development_model_not_accepted',out['development_only_maximum_underestimate_seconds'])
if __name__=='__main__':main()
