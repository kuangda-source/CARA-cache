"""CPU-only exact-source C prediction check; no model load, labels or GPU work."""
import ast, copy, hashlib, json, pathlib, textwrap, time
from enum import Enum
from types import SimpleNamespace
from typing import List, Optional, Tuple, Union


def extract_cached_branch(source):
    tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worldcache_mini_train_dit_forward')
    body=ast.get_source_segment(source,fn)
    start='    # --- Execution Branching ---\n    if skip_forward:\n'
    end='    else:\n        # CACHE MISS or PROBE PHASE'
    if body.count(start)!=1 or body.count(end)!=1:raise ValueError('Pinned branch anchors differ')
    cached=textwrap.dedent(body.split(start,1)[1].split(end,1)[0])
    if 'previous_output' in cached or 'unpass_blocks' in cached:raise ValueError('C may not read current truth')
    function='def cached_prediction(self, ori_x, test_x, current_idx):\n'
    function+='    x_B_T_H_W_D=ori_x\n    T=ori_x.shape[1]\n    residual_x=self.residual_cache[current_idx]\n'
    function+=textwrap.indent(cached,'    ')+'\n    return x_B_T_H_W_D\n'
    ast.parse(function)
    return body,function


def run(source_path, expected_sha):
    import torch
    from einops import rearrange
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**kw):raise RuntimeError('CPU card forbids CUDA initialization')
    torch.cuda._lazy_init=forbidden
    data=pathlib.Path(source_path).read_bytes();assert hashlib.sha256(data).hexdigest()==expected_sha
    source=data.decode();body,prediction=extract_cached_branch(source)
    tree=ast.parse(source);tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'compute_optimal_gamma','estimate_optical_flow','warp_feature','worldcache_mini_train_dit_forward','apply_worldcache'}]
    class DataType(Enum):VIDEO=1
    ns=dict(torch=torch,amp=torch.amp,F=torch.nn.functional,rearrange=rearrange,DataType=DataType,List=List,Optional=Optional,Tuple=Tuple,Union=Union,log=SimpleNamespace(info=lambda *a:None))
    exec(compile(tree,str(source_path),'exec'),ns)
    exec(compile(prediction,'<h0-exact-cache-branch>','exec'),ns)
    records=[]
    def capture(net,*,skipped,branch,ori,probe):
        if net.cnt<6 or net.residual_cache[branch] is None:return
        assert net.cnt%2==branch
        proxy=copy.copy(net)
        # The pinned skip body writes only these two lists; isolate those writes.
        proxy.previous_internal_states=list(net.previous_internal_states)
        proxy.previous_input=list(net.previous_input)
        before=copy.deepcopy({k:getattr(net,k) for k in ['previous_internal_states','previous_input','residual_cache','residual_window','probe_residual_window','cnt']})
        rng=torch.random.get_rng_state().clone()
        candidate=ns['cached_prediction'](proxy,ori,probe,branch)
        assert torch.equal(rng,torch.random.get_rng_state())
        def equal(a,b):
            if isinstance(a,torch.Tensor):return torch.equal(a,b)
            if isinstance(a,(list,tuple)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
            return a==b
        assert all(equal(v,getattr(net,k)) for k,v in before.items())
        records.append({'counter':net.cnt,'branch':branch,'skipped':skipped,'prediction':candidate})
    anchor='    # --- Execution Branching ---'
    instrumented=body.replace(anchor,'    capture(self, skipped=skip_forward, branch=current_idx, ori=ori_x, probe=test_x)\n'+anchor)
    ns['capture']=capture;exec(compile(instrumented,'<h0-cpu-shadow-source>','exec'),ns)
    class Block(torch.nn.Module):
        def __init__(self,factor):super().__init__();self.factor=factor
        def forward(self,x,**kwargs):return x*self.factor+.01
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__();self.blocks=torch.nn.ModuleList([Block(1.02),Block(1.03),Block(1.04)])
            self.use_crossattn_projection=False;self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1),None);self.t_embedding_norm=lambda t:t
            self.final_layer=lambda x,*a,**kw:x;self.unpatchify=lambda x:x
        def prepare_embedded_sequence(self,x,**kwargs):return x,None,None
    checks=[]
    for flow in [False,True]:
        # Capture before the full/skip branch; paired plain upstream is untouched.
        pure={k:v for k,v in ns.items()};exec(compile(tree,str(source_path),'exec'),pure)
        for thresh in [1.,-1.]:
            kw=dict(num_steps=20,ret_ratio=.3,rel_l1_thresh=thresh,probe_depth=1,osi_enabled=True,flow_enabled=flow,flow_scale=1)
            plain=pure['apply_worldcache'](Toy(),**kw).eval();observed=ns['apply_worldcache'](Toy(),**kw).eval()
            records.clear()
            spatial=torch.linspace(.7,1.3,72).reshape(1,2,3,4,3)
            for i in range(12):
                x=spatial+i*.0001*(1+spatial.square());args=(x,torch.ones(1),torch.ones(1))
                a=plain(*args);b=observed(*args);assert torch.equal(a,b)
                if records and records[-1]['counter']==i and records[-1]['skipped']:assert torch.equal(records[-1]['prediction'],b)
            assert len(records)==6
            checks.append({'flow_enabled':flow,'threshold':thresh,'paired_calls':12,'captured':6,'branches':sorted({x['branch'] for x in records}),'captured_skip_count':sum(x['skipped'] for x in records),'non_mutating_c_predictions':True,'skip_predictions_bitwise_match_official':True})
    assert not torch.cuda.is_initialized()
    return {'status':'H0_EXACT_PINNED_C_CPU_INTERFACE_PASS_NOT_S_OR_REAL_MODEL_ACCEPTANCE','source_sha256':expected_sha,'prediction_function_sha256':hashlib.sha256(prediction.encode()).hexdigest(),'checks':checks,'torch':torch.__version__,'cuda_initialized':False,'model_weights_loaded':False,'gpu_jobs_added':0,'limits':'CPU toy wiring with exact official branch; no recorded r4 QKV converted to residual, no TECH/FIT/CAL/CONF labels, no real-model closure or sparse kernel result','observed_unix':time.time()}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    print(json.dumps(run(a.source,a.sha256)))
