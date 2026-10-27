"""Independently bind saved-tensor CPU diagnostics and aggregate fixed strata."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import time

ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def analyze(cap,pre,old):
    c=cap['container_state'];r=cap['result']
    assert c['Status']=='exited' and c['ExitCode']==0 and not c['OOMKilled'] and not c['Error']
    assert cap['source_hashes_equal'] and not cap['device_requests'] and cap['cpuset']=='4,5'
    assert cap['memory_bytes']==8*2**30 and cap['nano_cpus']==2*10**9
    assert any(m['Destination']==pre['assets'].rsplit('/assets',1)[0] and not m['RW'] for m in cap['mounts'])
    assert cap['original_result_sha256']==old['files']['B1-results.json']['sha256']
    assert cap['original_billing_sha256']==old['files']['billing']['sha256']
    assert r['manifest_sha256']==pre['manifest_sha256']
    assert len(pre['verified'])==32 and len({x['name'] for x in pre['verified']})==32
    assert not any(r[k] for k in ('CUDA_initialized','thresholds_fitted','policy_selected','IG_reopened','DEV128_used','new_GPU_submissions'))
    assert r['CPU_wall_seconds']<=1800 and r['platform']=='linux'
    assert r['peak_rss_platform_units']*1024<8*2**30
    saved=read(ROOT/'reports/cara_IG_B1_saved_CPU_finished_20261027.json')['result']
    originals={(v['prompt'],v['step']):v for v in saved['rows']}
    assert saved['assets_manifest_sha256']==r['manifest_sha256']
    rows=r['rows'];prompts=sorted({v['prompt'] for v in rows});steps=(22,23,25,33,34,35)
    assert len(prompts)==2 and len(rows)==12 and {(v['prompt'],v['step']) for v in rows}=={(p,s) for p in prompts for s in steps}
    for row in rows:
        assert row['artifact'] in pre['verified']
        assert row['original_actual_guided_scores']==originals[(row['prompt'],row['step'])]['original_readout_summary']
        for b in row['branches']:
            for k in ('A_identity_residual','R4_identity_residual'):assert b[k]<1e-10
            assert math.isclose(b['raw_R4_MSE']-b['raw_A_MSE'],b['R4_extra_norm']+b['R4_cross'],rel_tol=1e-9,abs_tol=1e-10)
        for d in row['actual_guided_decomposition'].values():
            assert math.isclose(d['delta_MSE'],d['change_norm']+d['cross_with_base_error'],rel_tol=1e-9,abs_tol=1e-10)
    def agg(selected):
        # Equal number of states per prompt; show prompt means explicitly.
        def avg(f):return st.mean(st.mean(f(x) for x in selected if x['prompt']==p) for p in sorted({x['prompt'] for x in selected}))
        guided={key:{field:avg(lambda x:x['actual_guided_decomposition'][key][field]) for field in
             ('base_MSE','candidate_MSE','delta_MSE','change_norm','cross_with_base_error')} for key in selected[0]['actual_guided_decomposition']}
        raw={}
        for b in (0,1):
            vals={k:avg(lambda x:x['branches'][b][k]) for k in ('raw_copy_MSE','raw_A_MSE','raw_R4_MSE','A_gain_dp2','A_gain_cross','R4_extra_norm','R4_cross')}
            vals['aggregate_R4_cosine_to_desired_change']=-vals['R4_cross']/(2*math.sqrt(vals['raw_A_MSE']*vals['R4_extra_norm']))
            vals['aggregate_R4_change_to_A_error_norm_ratio']=math.sqrt(vals['R4_extra_norm']/vals['raw_A_MSE'])
            vals['R4_direction_helpful_count']=sum(x['branches'][b]['R4_cross']<0 for x in selected)
            vals['R4_better_count']=sum(x['branches'][b]['raw_R4_MSE']<x['branches'][b]['raw_A_MSE'] for x in selected)
            vals['A_better_than_raw_copy_count']=sum(x['branches'][b]['raw_A_MSE']<x['branches'][b]['raw_copy_MSE'] for x in selected)
            raw[str(b)]=vals
        for k,d in guided.items():
            d['relative_change']=d['candidate_MSE']/d['base_MSE']-1
            d['direction_helpful_count']=sum(x['actual_guided_decomposition'][k]['cross_with_base_error']<0 for x in selected)
            d['better_count']=sum(x['actual_guided_decomposition'][k]['delta_MSE']<0 for x in selected)
            cos=[x['actual_guided_decomposition'][k]['cosine_to_desired_change'] for x in selected]
            cos=[x for x in cos if x is not None];d['cosine_range']=[min(cos),max(cos)] if cos else None
        return dict(states=len(selected),guided=guided,raw=raw)
    groups={}
    for name,ss in [('all',steps),('short',(22,23,25)),('long',(33,34,35))]:
        sel=[x for x in rows if x['step'] in ss]
        groups[name]=dict(aggregate=agg(sel),by_prompt={p:agg([x for x in sel if x['prompt']==p]) for p in prompts})
    return dict(status='SAVED_TENSOR_CPU_MECHANISM_ACCEPTED_NOT_NEW_GPU_OR_E2_GATE',observed_unix=time.time(),
        groups=groups,rows=rows,CPU_wall_seconds=r['CPU_wall_seconds'],peak_RSS_GiB=r['peak_rss_platform_units']/2**20,
        source_revision=cap['launch']['source_revision'],manifest_sha256=r['manifest_sha256'],
        result_sha256=cap['result_sha256'],new_GPUh=0,ledger_writes=0,IG_reopened=False,j1=None,
        scope='Two exposed CAL, same C-policy states, saved outputs; raw formulas are unshrunk and raw copy is not WC-C. No head replay, endpoint test or fitted candidate.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    old=ROOT/'reports/cara_IG_B1_R2_terminal_20261027.json'
    result=analyze(read(a.capture),read(a.preflight),read(old))
    result['evidence']={str(x.relative_to(ROOT) if x.is_absolute() else x):sha(x) for x in (a.capture,a.preflight,old)}
    result['auditor_sha256']=sha(__file__)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])
