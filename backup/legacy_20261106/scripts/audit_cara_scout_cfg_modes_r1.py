"""Complete fixed-set CPU mode decomposition acceptance and aggregation."""
import argparse,hashlib,json,math,statistics as st,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(c,pre,old):
 s=c['container_state'];r=c['result']
 assert s['Status']=='exited' and s['ExitCode']==0 and not s['OOMKilled'] and not s['Error']
 assert c['source_hashes_equal'] and not c['device_requests'] and c['cpuset']=='4,5'
 assert c['memory_bytes']==8*2**30 and c['nano_cpus']==2*10**9
 assert any(m['Destination']==pre['assets'].rsplit('/assets',1)[0] and not m['RW'] for m in c['mounts'])
 assert r['manifest_sha256']==pre['manifest_sha256']==old['manifest_sha256'] and len(pre['verified'])==32
 assert not any(r[k] for k in ('CUDA_initialized','GPU_submissions','head_replayed','IG_reopened','fitted','DEV_used'))
 assert r['CPU_wall_seconds']<1800 and r['peak_RSS_platform_units']<8*2**20
 previous={(x['prompt'],x['step']):x for x in old['rows']}
 rows=r['rows'];assert len(rows)==12 and {(x['prompt'],x['step']) for x in rows}==set(previous)
 for x in rows:
  assert x['alpha']==(1. if x['step']<25 else .5)
  prev=previous[(x['prompt'],x['step'])]
  for key in ('outputs','component_outputs'):
   v=x['outputs'][key]
   for label,col in [('A_PHASE','canonical_A_MSE'),('R4_GLOBAL','canonical_R4_MSE')]:
    assert math.isclose(v[col],prev['errors'][label][key]['canonical_guided_MSE'],rel_tol=1e-12,abs_tol=1e-12)
   assert math.isclose(v['after_guided']-v['base_guided'],v['common_gain']+v['weighted_diff_gain']+v['cross_gain'],abs_tol=1e-9)
 groups={}
 for group,steps in [('short',(22,23,25)),('long',(33,34,35)),('all',(22,23,25,33,34,35))]:
  chosen=[x for x in rows if x['step'] in steps]
  def agg(sel):
   scopes={}
   for name in ('raw','component_outputs','outputs'):
    vs=[x['raw']['decomposition'] if name=='raw' else x['outputs'][name] for x in sel]
    means={k:st.mean(x[k] for x in vs) for k in vs[0] if all(x[k] is not None for x in vs)}
    counts={mode:sum(x[mode+'_guided']<x['base_guided'] for x in vs) for mode in ('common_only','diff_only','after')}
    for mode in ('common_only','diff_only','after'):means[mode+'_relative_change']=means[mode+'_guided']/means['base_guided']-1
    scopes[name]=dict(means=means,better_count=counts)
   return dict(states=len(sel),scopes=scopes)
  groups[group]=dict(aggregate=agg(chosen),by_prompt={p:agg([x for x in chosen if x['prompt']==p]) for p in sorted({x['prompt'] for x in chosen})})
 return dict(status='SAVED_CFG_MODE_CPU_ACCEPTED_EXPLANATORY',observed_unix=time.time(),rows=rows,groups=groups,
    CPU_wall_seconds=r['CPU_wall_seconds'],peak_RSS_GiB=r['peak_RSS_platform_units']/2**20,
    manifest_sha256=r['manifest_sha256'],result_sha256=c['result_sha256'],source_revision=c['launch']['source_revision'],
    GPU_submissions=0,ledger_writes=0,IG_reopened=False,j1=None,
    scope='Retrospective same C-policy state analysis on two exposed CAL. Fixed output substitutions are not deployed latency or own-policy video evidence.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 pre=ROOT/'reports/cara_scout_cfg_modes_preflight_20261027.json';old=ROOT/'reports/cara_scout_output_geometry_CPU_accepted_20261027.json'
 v=audit(read(a.capture),read(pre),read(old));v['evidence']={str(x.relative_to(ROOT) if x.is_absolute() else x):sha(x) for x in (a.capture,pre,old)};v['auditor_sha256']=sha(__file__)
 with a.output.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
 print(v['status'])
