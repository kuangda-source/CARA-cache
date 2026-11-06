"""Offline frozen R2 gate; no fitting, network, GPU or dispatch."""
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 refs={k:'reports/cara_common_long6_A6000_R2_'+v+'_20261027_2350.json' for k,v in [('terminal','terminal'),('settlement','central_settlement'),('acceptance','accepted')]}
 x=read(refs['terminal']);x['central_settlement']=read(refs['settlement'])
 import sys;sys.path.insert(0,str(ROOT/'src'))
 from wcomr.common_long_terminal_r2 import accept
 assert accept(x)==read(refs['acceptance'])
 for f in x['files'].values():
  if f.get('exists'):assert hashlib.sha256(f['raw_utf8'].encode()).hexdigest()==f['sha256']
 p=json.loads(x['files']['post']['raw_utf8']);c=json.loads(x['files']['collection']['raw_utf8']);v=p['values'];labels=list(v[0]['scores']);prompts=sorted({r['prompt'] for r in v})
 def means(rows,metric='MSE'):
  return {l:statistics.mean(statistics.mean(r['scores'][l][metric] for r in rows if r['prompt']==pr) for pr in prompts) for l in labels}
 long=[r for r in v if r['step'] in (33,34,35)];short=[r for r in v if r['step'] in (22,23,25)]
 q=means(long);baselines=['WC_C','A_PHASE','FULL','DCTA'];best=min(baselines,key=q.get);new='R4_COMMON_LONG';a='A_PHASE'
 details=[]
 for r in v:
  am=r['scores'][a]['MSE'];nm=r['scores'][new]['MSE'];details.append(dict(prompt=r['prompt'],step=r['step'],A_MSE=am,candidate_MSE=nm,gain=1-nm/am,strict_win=am-nm>1e-6*max(1,abs(am))))
 pg={pr:{l:statistics.mean(r['scores'][l]['MSE'] for r in long if r['prompt']==pr) for l in labels} for pr in prompts}
 gates=dict(gain_at_least_5pct=1-q[new]/q[best]>=.05,at_least_4_of_6_strict_A_wins=sum(r['strict_win'] for r in details if r['step']>=33)>=4,both_prompt_long_means_nonworse=all(z[new]<=z[a] for z in pg.values()),short_exact_A_verified_by_accepted_tensor_rescore=True)
 out=dict(status='FROZEN_LOCAL_GATE_FAILED_NO_E2',created_unix=time.time(),source_refs=refs,source_SHA256={k:sha(f) for k,f in refs.items()},contract_ref='manifests/cara_common_long_newstates_scope_quote_r1_20261027.json',contract_SHA256=sha('manifests/cara_common_long_newstates_scope_quote_r1_20261027.json'),long_MSE=q,short_MSE=means(short),all_MSE=means(v),best_fixed_baseline=best,gain_vs_best=1-q[new]/q[best],gates=gates,passed=all(gates.values()),per_prompt_long_MSE=pg,per_state=details,gradient_long=means(long,'gradient_residual_MSE'),energy_ratio_long=means(long,'energy_ratio'),diagnostic_long_seconds={l:statistics.mean(r['cost'][l]['diagnostic_readout_seconds'] for r in long) for l in labels},cumulative_peak_bytes=max(r['cost'][l]['device_peak_allocated_cumulative_bytes'] for r in v for l in labels),path_clocks=[{k:r[k] for k in ('id','prompt','section','full_request_seconds','paper_denoise_decode_seconds','timing_is_diagnostic')} for r in c['rows']],limitations=['2 old CAL prompts; same C-policy states, not candidate free running','long age confounded with late stage and anchor interval','clock includes copies/hash/roundtrip; peak cumulative, not candidate incremental','no final video quality or deployment budget claim'],IG='PAUSED',GPU_authorized=False)
 assert not out['passed']
 dest=ROOT/'reports/cara_common_long_R2_frozen_analysis_20261028.json';dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
