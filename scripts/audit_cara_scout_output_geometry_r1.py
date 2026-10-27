"""Offline complete-output audit and fixed-stratum summary; no fitted gains."""
import argparse,json,hashlib,math,statistics as st,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(c,pre,first):
 s=c['container_state'];r=c['result']
 assert s['Status']=='exited' and s['ExitCode']==0 and not s['OOMKilled'] and not s['Error']
 assert c['source_hashes_equal'] and not c['device_requests'] and c['cpuset']=='4,5'
 assert c['memory_bytes']==8*2**30 and c['nano_cpus']==2*10**9
 assert any(m['Destination']==pre['assets'].rsplit('/assets',1)[0] and not m['RW'] for m in c['mounts'])
 assert r['manifest_sha256']==pre['manifest_sha256']==first['manifest_sha256']
 assert len(pre['verified'])==32
 assert not any(r[k] for k in ('new_GPU_submissions','IG_reopened','fitted','head_replayed','CUDA_initialized'))
 assert r['CPU_wall_seconds']<1800 and r['peak_RSS_KiB']<8*2**20
 originals={(x['prompt'],x['step']):x for x in first['rows']}
 assert len(r['rows'])==12 and {(x['prompt'],x['step']) for x in r['rows']}==set(originals)
 for row in r['rows']:
  assert row['alpha']==(1 if row['step']<25 else .5)
  for label,x in row['errors'].items():
   assert math.isclose(x['outputs']['canonical_guided_MSE'],originals[(row['prompt'],row['step'])]['original_actual_guided_scores'][label]['MSE'],abs_tol=1e-12)
 groups={}
 for group,steps in [('short',(22,23,25)),('long',(33,34,35)),('all',(22,23,25,33,34,35))]:
  rows=[x for x in r['rows'] if x['step'] in steps];v={}
  for phase in ('component_outputs','outputs'):
   vals={label:{k:st.mean(x['errors'][label][phase][k] for x in rows) for k in rows[0]['errors'][label][phase]} for label in ('WC_C','A_PHASE','R4_GLOBAL','R4_LONG','FULL','DCTA')}
   for label,x in vals.items():
    ec,eu,cov=x['branch_c_MSE'],x['branch_u_MSE'],x['cross_covariance']
    x.update(common_error_MSE=(ec+eu+2*cov)/4,difference_error_MSE=ec+eu-2*cov,
      guided_difference_term=56.25*(ec+eu-2*cov),guided_common_difference_cross=7.5*(ec-eu))
   comparisons={k:dict(delta=vals['R4_GLOBAL'][k]-vals['A_PHASE'][k],better_states=sum(x['errors']['R4_GLOBAL'][phase][k]<x['errors']['A_PHASE'][phase][k] for x in rows)) for k in ('branch_c_MSE','branch_u_MSE','canonical_guided_MSE')}
   v[phase]=dict(means=vals,R4_vs_A=comparisons)
  groups[group]=v
 return dict(status='SAVED_OUTPUT_GEOMETRY_CPU_ACCEPTED',observed_unix=time.time(),groups=groups,rows=r['rows'],CPU_wall_seconds=r['CPU_wall_seconds'],peak_RSS_GiB=r['peak_RSS_KiB']/2**20,
   manifest_sha256=r['manifest_sha256'],GPU_submissions=0,ledger_writes=0,IG_reopened=False,fitted=False,
   limitation=r['caveat'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 pre=ROOT/'reports/cara_scout_output_geometry_preflight_20261027.json';first=ROOT/'reports/cara_scout_mechanism_CPU_accepted_analysis_20261027.json'
 result=audit(read(a.capture),read(pre),read(first))
 result['evidence']={str(x.relative_to(ROOT) if x.is_absolute() else x):sha(x) for x in (a.capture,pre,first)};result['auditor_sha256']=sha(__file__)
 with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
 print(result['status'])
