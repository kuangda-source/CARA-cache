"""Source-bound Euler E0 arithmetic and actual CFG-function CPU controls."""
import argparse,ast,hashlib,importlib.util,json,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_euler_protocol_r1 import ExplicitEuler,reconstructed_grid,remap_dense
from wcomr.cara_fast_spec_r1 import digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path,required=True);a=p.parse_args()
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(1)
    original=json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    observed=json.loads((ROOT/'reports/cara_endpoint7_readonly_assets_resources_r1_20261101.json').read_text())['result']['runtime_source_sha256']
    for path,h in observed.items():assert hashlib.sha256((a.source_dir/Path(path).name).read_bytes()).hexdigest()==h
    spec=importlib.util.spec_from_file_location('pinned_unipc',a.source_dir/'fm_solvers_unipc.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    solver=module.FlowUniPCMultistepScheduler();solver.set_timesteps(35,device='cpu',use_kerras_sigma=True)
    assert solver.sigmas.tolist()==original['schedule']['sigmas']
    assert solver.timesteps.tolist()==original['schedule']['timesteps']
    grid=reconstructed_grid(35)
    # Extract the unchanged video-conditioned CFG closure: the text-only superclass differs.
    tree=ast.parse((a.source_dir/'video2world_model_rectified_flow.py').read_text())
    fns=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='velocity_fn'];assert len(fns)==1
    body=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fns[0]],type_ignores=[])
    calls=[]
    def denoise(noise,x,t,condition):
        calls.append(condition);return .05*x+(.3 if condition=='C' else -.1)
    ns=dict(torch=torch,self=types.SimpleNamespace(denoise=denoise),condition='C',uncondition='U',guidance=7)
    exec(compile(ast.fix_missing_locations(body),'pinned-video-CFG','exec'),ns)
    x=torch.tensor([.4,.9],dtype=torch.float32);y=x.clone();euler=ExplicitEuler(grid)
    for i,t in enumerate(grid['timesteps']):
        v=ns['velocity_fn'](None,x,torch.tensor(t))
        expected_v=8*(.05*y+.3)-7*(.05*y-.1)
        y=y+(grid['sigmas'][i+1]-grid['sigmas'][i])*expected_v
        x=euler.step(v,t,x)
    assert calls==['C','U']*35 and torch.allclose(x,y,atol=2e-6,rtol=0)
    constant=ExplicitEuler(grid);z=1.0
    for t in grid['timesteps']:z=constant.step(2.0,t,z)
    assert abs(z-(1-2*grid['sigmas'][0]))<1e-12
    try:euler.step(x,grid['timesteps'][-1],x)
    except ValueError:pass
    else:raise AssertionError('Extra update accepted')
    shifted=ExplicitEuler(grid)
    try:shifted.step(1.,grid['timesteps'][1],1.)
    except ValueError:pass
    else:raise AssertionError('Wrong timestep accepted')
    masks={}
    for role in ('F19_C','UNIFORM19_C','SU19_BR_DIAG_C','SU19_CFG_C','BUDGET_SEARCH19_C','F19_RISKSWAP_C'):
        dense=[i+1 for i,x in enumerate(original['roles'][role]['policy']['actions']) if x=='D']
        target=remap_dense(original['schedule']['sigmas'],grid['sigmas'],dense)
        assert len(target)==len(set(target))==19 and target[:7]==list(range(1,8)) and target[-1]==35
        assert max(b-a for a,b in zip(target,target[1:]))<=28
        masks[role]=target
    contract=dict(status='CPU_PROTOCOL_PROTOTYPE_NOT_PAPER_EXACT_OR_GPU_READY',
        E_PAPER_reconstruction=grid,grid_sha256=digest(grid),
        E_SOLVER_control=dict(sigmas=solver.sigmas.tolist(),timesteps=solver.timesteps.tolist(),updates=36,CFG_calls=72,
            Euler_same_grid_supported=True,paired_real_UniPC_Euler_execution=False),
        velocity='dx/dsigma; sample_next=sample+(sigma_next-sigma)*velocity; no sign inversion',
        CFG='conditional first, unconditional second, guidance7 =>8C-7U',
        WC_paper_style=dict(threshold=.08,motion=2.0,saliency=.12,warp_spatial_scale=.5,ATS_beta=4,
            requested_steps=35,actual_CFG_calls=70,desired_cache_reset_after_calls=70,
            ATS_decoupling_from_call_horizon_required=True),
        runtime_source_sha256=observed,adapter_sha256=hashlib.sha256((ROOT/'src/wcomr/cara_euler_protocol_r1.py').read_bytes()).hexdigest(),
        mapped19D_examples_only=masks,scientific_method_chosen=False,
        real_weight_Native_wrapper_allD_equality=False,production_wrapper_Euler_CPU_accepted=False,
        GPU_authorized=False,GPU_submissions=0)
    out=ROOT/'plans/cara_next_stage_20261101/euler/sigma_grid_and_call_contract.json'
    out.write_text(json.dumps(contract,indent=2)+'\n')
    proof=dict(status='EULER_E0_SOURCE_GRID_CFG_AND_ARITHMETIC_CPU_ACCEPTED_ONLY',
        contract_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_UniPC_grid_exact=True,actual_Euler_updates=35,actual_CFG_calls=len(calls),CFG_order=calls,
        analytical_constant_velocity_error=abs(z-(1-2*grid['sigmas'][0])),manual_guided_max_error=float((x-y).abs().max()),
        invalid_timestep_and_extra_update_refused=True,mapping_examples=6,
        sigma_count=36,CUDA_initialized=torch.cuda.is_initialized(),model_weights_loaded=False,
        new_video_generation=0,full_pipeline_CPU_accepted=False,GPU_submissions=0)
    (ROOT/'reports/cara_euler35_E0_CPU_acceptance_r1_20261101.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='CFG_order'}))
if __name__=='__main__':main()
