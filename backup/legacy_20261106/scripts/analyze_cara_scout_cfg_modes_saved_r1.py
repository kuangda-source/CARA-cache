"""Saved pair-mode diagnostics. No fitting, model execution or GPU.

Output hybrids are algebraic component-removal diagnostics, not independently
validated predictors or cheap deployed implementations.
"""
import argparse,json,math,os,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import torch
from wcomr.innovation_gain_assets_r1 import load_state,sha
from wcomr.policy_interval_readout_r1 import guided
from wcomr.scout_readout_v22 import STATE_STEPS,PARENT_FINGERPRINT

def dot(a,b):return float((a*b).sum())
def modes(c,u):return (c+u)/2,c-u

def pieces(ec,eu,qc,qu):
    em,ed=modes(ec,eu);qm,qd=modes(qc,qu)
    # Sums allow exact streaming in raw hidden coordinates.
    z=dict(n=ec.numel(),base_common=dot(em,em),base_diff=dot(ed,ed),base_cross=15*dot(em,ed),
      update_common=dot(qm,qm),update_diff=dot(qd,qd),update_cross=15*dot(qm,qd),
      common_alignment=2*dot(em,qm),diff_alignment=2*dot(ed,qd),
      common_to_base_diff=15*dot(ed,qm),diff_to_base_common=15*dot(em,qd))
    z['after_common']=dot(em+qm,em+qm);z['after_diff']=dot(ed+qd,ed+qd)
    z['after_cross']=15*dot(em+qm,ed+qd)
    z['base_guided']=dot(em+7.5*ed,em+7.5*ed)
    z['after_guided']=dot(em+qm+7.5*(ed+qd),em+qm+7.5*(ed+qd))
    z['common_only_guided']=dot(em+qm+7.5*ed,em+qm+7.5*ed)
    z['diff_only_guided']=dot(em+7.5*(ed+qd),em+7.5*(ed+qd))
    return z

def normalized(z):
    n=z['n'];v={k:x/n for k,x in z.items() if k!='n'}
    v['common_gain']=v['common_alignment']+v['update_common']
    v['weighted_diff_gain']=56.25*(v['diff_alignment']+v['update_diff'])
    v['cross_gain']=v['common_to_base_diff']+v['diff_to_base_common']+v['update_cross']
    assert math.isclose(v['after_guided']-v['base_guided'],v['common_gain']+v['weighted_diff_gain']+v['cross_gain'],rel_tol=1e-8,abs_tol=1e-9)
    for mode in ('common','diff'):
        b,q=v['base_'+mode],v['update_'+mode]
        v[mode+'_cosine_to_desired']=-v[mode+'_alignment']/(2*math.sqrt(b*q)) if b*q>0 else None
        v[mode+'_update_to_error_norm']=math.sqrt(q/b) if b else None
    return v

def raw(value):
    sums={};visible={};count=0
    k=(value['xi']-value['anchors'][0][1]['xi'])/(value['anchors'][0][1]['xi']-value['anchors'][0][0]['xi'])
    for t in range(value['current'][0]['probe'].shape[1]):
        sl=lambda x:x[:,t:t+1].double()
        errors=[];qs=[];dps=[]
        for b in (0,1):
            old,last=value['anchors'][b];cur=value['current'][b]
            p=sl(cur['probe'])-sl(cur['original']);r=sl(value['teacher_hidden'][b])-sl(cur['original'])
            db=sl(last['residual'])-sl(last['probe']);do=sl(old['residual'])-sl(old['probe'])
            errors.append(db-(r-p));qs.append(k*(db-do));dps.append(p-sl(last['probe']))
        v=pieces(*errors,*qs)
        for key,x in v.items():sums[key]=sums.get(key,0)+x
        pm,pd=modes(*dps);qm,qd=modes(*qs)
        for key,x in dict(probe_common_energy=dot(pm,pm),probe_diff_energy=dot(pd,pd),
          probe_common_history_dot=dot(pm,qm),probe_diff_history_dot=dot(pd,qd)).items():visible[key]=visible.get(key,0)+x
        count+=pm.numel()
    result=normalized(sums);visible={k:v/count for k,v in visible.items()}
    for mode in ('common','diff'):
        den=math.sqrt(visible['probe_'+mode+'_energy']*result['update_'+mode])
        visible[mode+'_probe_history_cosine']=visible['probe_'+mode+'_history_dot']/den if den else None
    return dict(decomposition=result,visible_no_teacher=visible,kappa=k)

def output(value,key):
    A=value['readouts']['A_PHASE'][key];R=value['readouts']['R4_GLOBAL'][key];teacher=value['teacher']
    errors=[a.double()-d.double() for a,d in zip(A,teacher)]
    qs=[r.double()-a.double() for a,r in zip(A,R)]
    v=normalized(pieces(*errors,*qs))
    v['canonical_A_MSE']=float((guided(A).double()-guided(teacher).double()).square().mean())
    v['canonical_R4_MSE']=float((guided(R).double()-guided(teacher).double()).square().mean())
    return v

def run(assets,manifest_sha):
    assert sha(assets/'manifest.json')==manifest_sha
    m=json.loads((assets/'manifest.json').read_text());rows=[]
    assert len(m['states'])==12
    for row in m['states']:
        v=load_state(assets,row['artifact']);assert v['context'][-1]==PARENT_FINGERPRINT
        assert all(v[k] for k in ('P0_actual_dense','P1_dense_head_RF_equal','P2_C_actual_parent_equal'))
        item=dict(prompt=row['prompt'],step=row['step'],source_anchor_steps=v['source_anchor_steps'],alpha=v['readouts']['A_PHASE']['alpha'],raw=raw(v),outputs={})
        for key in ('component_outputs','outputs'):
            item['outputs'][key]=output(v,key)
        for l,k in [('A_PHASE','canonical_A_MSE'),('R4_GLOBAL','canonical_R4_MSE')]:
            assert abs(item['outputs']['outputs'][k]-v['summary'][l]['MSE'])<1e-12
        rows.append(item);del v
        print(json.dumps(dict(completed_states=len(rows),total_states=12)),flush=True)
    assert {(x['prompt'],x['step']) for x in rows}=={(p,s) for p in {x['prompt'] for x in rows} for s in STATE_STEPS}
    return dict(status='SAVED_CFG_COMMON_DIFF_COMPLETE',rows=rows,manifest_sha256=manifest_sha,GPU_submissions=0,
      head_replayed=False,IG_reopened=False,fitted=False,DEV_used=False,
      diagnostics='Fixed common-only/difference-only output substitutions; retrospective exposed-CAL diagnosis, not frozen candidate confirmation.')

def self_test():
    g=torch.Generator().manual_seed(720)
    for i in range(4):
        xs=[torch.randn((2,3),generator=g,dtype=torch.float64) for _ in range(4)]
        v=normalized(pieces(*xs));e=8*xs[0]-7*xs[1];q=8*xs[2]-7*xs[3]
        assert abs(v['after_guided']-float((e+q).square().mean()))<1e-10
        m,d=modes(xs[2],xs[3]);assert torch.allclose(m+d/2,xs[2]) and torch.allclose(m-d/2,xs[3])
    x=torch.ones((2,3),dtype=torch.float64);z=torch.zeros_like(x)
    v=normalized(pieces(z,z,x,x));assert v['update_diff']==0 and v['after_guided']==1
    v=normalized(pieces(z,z,x,-x));assert v['update_common']==0 and v['after_guided']==225
    return dict(status='CFG_MODE_ALGEBRA_CPU_PASS',random_cases=4,common_diff_controls=2,GPU_submissions=0)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path);p.add_argument('--manifest-sha256');p.add_argument('--output',type=Path,required=True);p.add_argument('--self-test',action='store_true');a=p.parse_args();assert not a.output.exists()
    assert os.environ.get('CUDA_VISIBLE_DEVICES','')=='';torch.set_num_threads(2)
    def forbid(*a,**kw):raise RuntimeError('CUDA forbidden')
    torch.cuda._lazy_init=forbid;start=time.monotonic();r=self_test() if a.self_test else run(a.assets,a.manifest_sha256);assert not torch.cuda.is_initialized()
    r.update(CPU_wall_seconds=time.monotonic()-start,peak_RSS_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,CUDA_initialized=False)
    with a.output.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    print(r['status'])
