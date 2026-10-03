import ast
from pathlib import Path
import pytest
from wcomr.mid_full_scope import validate_full_scope, cost_gate


def config():
    return {'card':'WC-MID-FULL-COVERAGE-R4-20261003-A', 'max_gpu_wall_seconds':1800,
            'capture_calls':[25,26,35,36], 'capture_layers':list(range(2,28)),
            'stop_after_solver_steps':18, 'state_steps':[13,18],
            'phases':['baseline_prefix','observed_prefix'], 'policy':{'sim':.1,'cdf':.98},
            'warmups':1, 'repeats':3, 'pv_skipping':False, 'deployment_sparse':False,
            'cost_admission':{'planning_envelope_seconds':1801,'shutdown_settlement_margin_seconds':30}}


def test_full104_scope_refuses_partial_old_scope_and_protocol_changes():
    c=config(); expected=validate_full_scope(c)
    assert len(expected)==104 and {(call,2) for call in [25,26,35,36]} <= expected
    for key,value in [('card','WC-INPUT-STATE-PARITY-R3-20261003-A'),('capture_calls',[25,26]),
                      ('capture_layers',[2]),('stop_after_solver_steps',13),('state_steps',[13]),
                      ('deployment_sparse',True),('pv_skipping',True),('max_gpu_wall_seconds',1200),
                      ('policy',{'sim':.2,'cdf':.98}),('repeats',1)]:
        with pytest.raises(ValueError): validate_full_scope(dict(c,**{key:value}))


def test_measured_cost_failure_blocks_gpu_without_extending_window():
    c=config()
    with pytest.raises(ValueError,match='no GPU submission'):cost_gate(c)
    c['cost_admission']['planning_envelope_seconds']=1770
    cost_gate(c)
    c['cost_admission']['planning_envelope_seconds']=1770.001
    with pytest.raises(ValueError):cost_gate(c)


def test_full_runner_keeps_all_nine_original_fieldwise_gates():
    root=Path(__file__).resolve().parents[1]
    def original_gates(path):
        tree=ast.parse(path.read_text())
        return next({x.value for x in n.generators[0].iter.elts} for n in ast.walk(tree)
                    if isinstance(n,ast.DictComp) and isinstance(n.generators[0].iter,ast.List)
                    and all(isinstance(x,ast.Constant) for x in n.generators[0].iter.elts)
                    and any(x.value=='field_signatures' for x in n.generators[0].iter.elts))
    assert original_gates(root/'scripts/run_wc_mid_full.py')==original_gates(root/'scripts/run_wc_mid_parity.py')=={
        'input_hashes','output_hashes','trace','block_counts','state_fingerprints','sampling',
        'named_inputs','conditions','field_signatures'}


def test_full_supervisor_reservation_refuses_inflight_old_cap_or_exhaustion():
    import importlib.util
    path=Path(__file__).resolve().parents[1]/'scripts/supervise_wc_mid_full.py'
    spec=importlib.util.spec_from_file_location('full_supervisor_cpu',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    b={'cap_gpu_hours':12,'used_gpu_hours':4.390463858430222,'budget_authorization_ref':'record'}
    m.scope_gate(b,1800)
    for change,seconds in [({'cap_gpu_hours':4},1800),({},1200),
                           ({'other_inflight':{}},1800),({'used_gpu_hours':11.5},1800)]:
        with pytest.raises(ValueError):m.scope_gate(dict(b,**change),seconds)


def test_actual_full_prefix_state13_and18_restore_next_update_when_source_available():
    import os,importlib.util
    import torch
    from types import SimpleNamespace
    from wcomr.mid_coverage import StateRoundtrip,tree_digest
    source=os.environ.get('WC_UNIPC_SOURCE')
    if not source:
        pytest.skip('Pinned UniPC source required by deployment CPU gate')
    import hashlib
    assert hashlib.sha256(Path(source).read_bytes()).hexdigest()=='f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3'
    spec=importlib.util.spec_from_file_location('full_actual_unipc',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    s=m.FlowUniPCMultistepScheduler(num_train_timesteps=1000,shift=1,use_dynamic_shifting=False)
    s.set_timesteps(35,device='cpu',shift=5,use_kerras_sigma=True)
    x=torch.arange(64,dtype=torch.float32).reshape(1,4,4,4)/64
    for step,t in enumerate(s.timesteps[:18],1):
        x=s.step(torch.ones_like(x)*.02,t,x,return_dict=False)[0]
        if step not in [13,18]:continue
        generator=torch.Generator().manual_seed(12+step)
        net=SimpleNamespace(cnt=2*step,residual_cache=[x,x+1])
        saved=StateRoundtrip(net,s,x,generators=[generator]);before=saved.fingerprint()
        value=torch.rand(x.shape,generator=generator)*.01
        left=s.step(value,s.timesteps[step],x,return_dict=False)[0];solver=tree_digest(vars(s))
        restored=saved.restore();assert saved.fingerprint()==before
        value=torch.rand(x.shape,generator=generator)*.01
        right=s.step(value,s.timesteps[step],restored,return_dict=False)[0]
        assert torch.equal(left,right) and solver==tree_digest(vars(s))
        x=saved.restore()
    assert not torch.cuda.is_initialized()
