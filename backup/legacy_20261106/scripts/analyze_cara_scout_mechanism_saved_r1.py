"""CPU-only explanatory decomposition on retained E1/B1 branch tensors.

No model/head execution, fitting, Fourier features, GPU or admission. Raw
hidden residuals are not guided velocities. Actual guided scores are retained
alongside them, never substituted by this algebra.
"""
import argparse
import json
import math
import os
import resource
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def algebra(p, pb, po, r, rb, ro, k):
    # p is the residual of the shallow prefix (h1-h0), not hidden h1.
    dp=p-pb
    dd=(r-p)-(rb-pb)
    history=(rb-pb)-(ro-po)
    ea=-dd
    correction=k*history
    direct_A=(pb+dp+(rb-pb))-r
    direct_R4=p+(rb-pb)+correction-r
    base=rb-r
    return dict(
        raw_copy_MSE_sum=base.square().sum(),raw_A_MSE_sum=ea.square().sum(),
        raw_R4_MSE_sum=direct_R4.square().sum(),
        A_gain_dp2_sum=dp.square().sum(),A_gain_cross_sum=2*(dp*dd).sum(),
        R4_extra_norm_sum=correction.square().sum(),R4_cross_sum=2*(ea*correction).sum(),
        A_identity_residual=(direct_A-ea).abs().max(),
        R4_identity_residual=(direct_R4-ea-correction).abs().max(),elements=p.numel())


def output_delta(base, candidate, teacher):
    """Exact squared-error decomposition after the real stored conversion."""
    e=base.double()-teacher.double();delta=candidate.double()-base.double()
    mse=float(e.square().mean());norm=float(delta.square().mean())
    cross=float(2*(e*delta).mean());new=float((candidate.double()-teacher.double()).square().mean())
    assert math.isclose(new-mse,norm+cross,rel_tol=1e-9,abs_tol=1e-10)
    return dict(base_MSE=mse,candidate_MSE=new,delta_MSE=new-mse,
        change_norm=norm,cross_with_base_error=cross,
        cosine_to_desired_change=-cross/(2*math.sqrt(mse*norm)) if mse*norm>0 else None,
        change_to_base_error_norm_ratio=math.sqrt(norm/mse) if mse>0 else None)


def run(assets, expected_sha):
    import torch
    from wcomr.innovation_gain_assets_r1 import load_state,sha
    from wcomr.scout_readout_v22 import PARENT_FINGERPRINT,STATE_STEPS
    from wcomr.policy_interval_readout_r1 import guided
    manifest_path=assets/'manifest.json'
    assert sha(manifest_path)==expected_sha
    manifest=json.loads(manifest_path.read_text())
    rows=manifest['states'];prompts=sorted({r['prompt'] for r in rows})
    assert len(prompts)==2 and len(rows)==12
    assert {(r['prompt'],r['step']) for r in rows}=={(p,s) for p in prompts for s in STATE_STEPS}
    out=[]
    for row in rows:
        value=load_state(assets,row['artifact']) # hashes every state and true anchor
        assert value['context'][-1]==PARENT_FINGERPRINT
        assert all(value[k] for k in ('P0_actual_dense','P1_dense_head_RF_equal','P2_C_actual_parent_equal'))
        branches=[]
        for b in (0,1):
            old,last=value['anchors'][b];cur=value['current'][b]
            assert old['xi']<last['xi']<value['xi']
            k=(value['xi']-last['xi'])/(last['xi']-old['xi'])
            shape=cur['probe'].shape
            assert len(shape)==5
            sums={};count=0;errors={}
            for t in range(shape[1]):
                sl=lambda x:x[:,t:t+1].double()
                # Prefix h0 is present in current hidden tensors but anchors
                # already store residuals. Center current only, exactly once.
                p=sl(cur['probe'])-sl(cur['original'])
                r=sl(value['teacher_hidden'][b])-sl(cur['original'])
                v=algebra(p,sl(last['probe']),sl(old['probe']),r,sl(last['residual']),sl(old['residual']),k)
                count+=v.pop('elements')
                for name,x in v.items():
                    z=float(x);assert math.isfinite(z)
                    if name.endswith('_residual'):errors[name]=max(errors.get(name,0),z)
                    else:sums[name]=sums.get(name,0)+z
            normalized={n.removesuffix('_sum'):v/count for n,v in sums.items()}
            assert math.isclose(normalized['raw_copy_MSE']-normalized['raw_A_MSE'],
                normalized['A_gain_dp2']+normalized['A_gain_cross'],rel_tol=1e-9,abs_tol=1e-10)
            assert math.isclose(normalized['raw_R4_MSE']-normalized['raw_A_MSE'],
                normalized['R4_extra_norm']+normalized['R4_cross'],rel_tol=1e-9,abs_tol=1e-10)
            branches.append(dict(branch=b,kappa=k,**normalized,**errors))
        outputs={label:guided(item['outputs']) for label,item in value['readouts'].items()}
        teacher=guided(value['teacher'])
        for label,tensor in outputs.items():
            mse=float((tensor.double()-teacher.double()).square().mean())
            assert math.isclose(mse,value['summary'][label]['MSE'],rel_tol=1e-12,abs_tol=1e-12)
        conversions={left+'_vs_'+right:output_delta(outputs[right],outputs[left],teacher)
            for left,right in [('A_PHASE','WC_C'),('R4_GLOBAL','A_PHASE'),('R4_LONG','A_PHASE')]}
        out.append(dict(prompt=row['prompt'],step=row['step'],source_anchor_steps=value['source_anchor_steps'],
            xi=value['xi'],sigma=value['sigma'],branches=branches,
            actual_guided_decomposition=conversions,
            original_actual_guided_scores=value['summary'],artifact=row['artifact']))
        del value,outputs,teacher
        print(json.dumps(dict(completed_states=len(out),total_states=12)),flush=True)
    return dict(status='SAVED_BRANCH_MECHANISM_DIAGNOSTIC_NOT_CANDIDATE_GATE',rows=out,
        manifest_sha256=expected_sha,raw_space='prewarp hidden residual FP64 algebra; no CFG synthesis before nonlinear head',
        no_full_pipeline_resume=True,policy_selected=False,thresholds_fitted=False,
        new_GPU_submissions=0,IG_reopened=False,DEV128_used=False)


def self_test():
    import torch
    gen=torch.Generator().manual_seed(20261027)
    for k in (.4,1.,2.6):
        tensors=[torch.randn((1,2,3,4,5),generator=gen,dtype=torch.float64) for _ in range(6)]
        a=algebra(*tensors,k)
        assert a['A_identity_residual']<1e-12 and a['R4_identity_residual']<1e-12
        assert torch.allclose(a['raw_copy_MSE_sum']-a['raw_A_MSE_sum'],a['A_gain_dp2_sum']+a['A_gain_cross_sum'])
        assert torch.allclose(a['raw_R4_MSE_sum']-a['raw_A_MSE_sum'],a['R4_extra_norm_sum']+a['R4_cross_sum'])
    # A common change to hidden h0 cannot change correctly centered p/r.
    h0=torch.full((1,1,2,2,3),10.,dtype=torch.float64);p=torch.ones_like(h0);r=3*p
    assert torch.equal((h0+p)-h0,p) and torch.equal((h0+r)-h0,r)
    assert output_delta(p,2*p,3*p)['delta_MSE']<0
    assert output_delta(p,-p,3*p)['delta_MSE']>0
    assert output_delta(p,p,3*p)['cosine_to_desired_change'] is None
    return dict(status='SYNTHETIC_ALGEBRA_CPU_PASS_NOT_REAL_ASSET_RESULT',span_cases=3,
        centered_hidden_control=True,actual_output_decomposition_cases=3,GPU_submissions=0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--assets',type=Path);ap.add_argument('--manifest-sha256')
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    assert os.environ.get('CUDA_VISIBLE_DEVICES','')=='' and not a.output.exists()
    import torch
    torch.set_num_threads(2)
    def forbid(*args,**kwargs):raise RuntimeError('Saved CPU diagnostics forbid CUDA')
    torch.cuda._lazy_init=forbid
    start=time.monotonic()
    if not a.self_test and (not a.assets or not a.manifest_sha256):ap.error('Bound assets and SHA required')
    result=self_test() if a.self_test else run(a.assets,a.manifest_sha256)
    assert not torch.cuda.is_initialized()
    result.update(CPU_wall_seconds=time.monotonic()-start,CUDA_initialized=False,
        peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform=sys.platform)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])
