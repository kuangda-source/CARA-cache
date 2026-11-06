"""CPU tests exercise exact official source with synthetic attention only."""
import ast, copy, pathlib, types, tempfile, hashlib
from enum import Enum
from typing import List,Optional,Tuple,Union
import torch
from einops import rearrange
from wcomr.h0_complement import H0ComplementProbe,build_h0_forward
from wcomr.measurement import BlockCounts


def run_cpu_controls(source_path):
    tree=ast.parse(pathlib.Path(source_path).read_text());tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['compute_optimal_gamma','estimate_optical_flow','warp_feature','worldcache_mini_train_dit_forward','apply_worldcache']]
    class DataType(Enum):VIDEO=1
    ns=dict(torch=torch,amp=torch.amp,F=torch.nn.functional,rearrange=rearrange,DataType=DataType,List=List,Optional=Optional,Tuple=Tuple,Union=Union,log=types.SimpleNamespace(info=lambda *a:None))
    exec(compile(tree,str(source_path),'exec'),ns)
    class Op(torch.nn.Module):
        def forward(self,q,k,v):return (q*1.002).reshape(1,128,2048)
    class Block(torch.nn.Module):
        def __init__(self):super().__init__();self.self_attn=types.SimpleNamespace(attn_op=Op());self.register_buffer('visits',torch.zeros(()))
        def forward(self,x,**kw):
            self.visits.add_(1)
            q=x.reshape(1,128,16,128)
            return self.self_attn.attn_op(q,q,q).reshape_as(x)+.002
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__();self.blocks=torch.nn.ModuleList([Block() for _ in range(4)])
            self.use_crossattn_projection=False;self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1),None);self.t_embedding_norm=lambda t:t
            self.final_layer=lambda x,*a,**kw:x;self.unpatchify=lambda x:x
        def prepare_embedded_sequence(self,x,**kw):return x,None,None
    calls=[]
    def mock_kernel(q,k,v,mask,sim,cdf,full):
        calls.append((sim,cdf,full));assert sim==.1 and cdf==.98
        return (q*1.002*(.999 if full else .99)).reshape(1,128,2048),{'selected_fraction':.7}
    checks=[]
    for flow in [False,True]:
        config={'eligible_call_range':[9,20],'warmups':1,'repeats':3,'dense_fallback_layers':[2],'policy':{'sim':.1,'cdf':.98}}
        temp=tempfile.TemporaryDirectory(prefix='wc-h0-cpu-raw-');p=H0ComplementProbe(config,kernel=mock_kernel,raw_output=temp.name);obsns=dict(ns);exec(compile(tree,str(source_path),'exec'),obsns)
        obsns['worldcache_mini_train_dit_forward']=build_h0_forward(obsns['worldcache_mini_train_dit_forward'],p)
        args=dict(num_steps=40,ret_ratio=.2,rel_l1_thresh=-1,probe_depth=1,osi_enabled=True,flow_enabled=flow,flow_scale=1)
        plain=ns['apply_worldcache'](Toy(),**args).eval();observed=obsns['apply_worldcache'](Toy(),**args).eval();p.install_operators(observed)
        counts=BlockCounts(observed.blocks,cache_model=observed)
        spatial=torch.linspace(.7,1.3,128*2048).reshape(1,2,8,8,2048)
        for i in range(20):
            x=spatial+i*.0001*(1+spatial.square());a=plain(x,torch.ones(1),torch.ones(1));b=observed(x,torch.ones(1),torch.ones(1));assert torch.equal(a,b)
        assert counts.result()=={'denoiser_calls':20,'full_calls':20,'skipped_deep_calls':0}
        assert len(p.attempts)==2 and len(p.records)==2 and p.pending is None, {'call':p.call,'histories':p.histories,'attempts':p.attempts,'net_count':observed.cnt,'resume':observed.resume_flag,'bound_forward':str(observed.forward),'ret_ratio':observed.worldcache_ret_ratio}
        assert {x['cfg_slot'] for x in p.records}=={0,1}
        for record in p.records:
            assert record['c_computed_before_current_dense']
            assert [x['arm'] for x in record['arms']]==['C_OFFICIAL_PAST_DENSE_GAMMA_WARP','dense','matched_full','sparse']
            assert all(len(x['wall_ms'])==3 for x in record['arms'])
            assert record['arms'][1]['dense_repeat_bitwise_matches_deployed']
            raw={}
            for row in record['arms']:
                snap=row['raw_snapshot'];path=pathlib.Path(snap['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==snap['sha256']
                raw[row['arm']]=torch.load(path,map_location='cpu',weights_only=True)
                assert set(raw[row['arm']])=={'postwarp_residual','velocity'}
            from wcomr.shadow_metrics import tensor_error
            for row in record['arms']:
                for field in ['postwarp_residual','velocity']:
                    assert tensor_error(raw[row['arm']][field],raw['dense'][field])==row[field]
            assert record['arms'][3]['velocity']['relative_rmse']>record['arms'][2]['velocity']['relative_rmse']>0
        from wcomr.mid_coverage import WC_FIELDS,tree_digest
        assert tree_digest({k:getattr(plain,k) for k in WC_FIELDS if hasattr(plain,k)})==tree_digest({k:getattr(observed,k) for k in WC_FIELDS if hasattr(observed,k)})
        for a,b in zip(plain.buffers(),observed.buffers()):assert torch.equal(a,b)
        assert any(x[-1] for x in calls) and any(not x[-1] for x in calls)
        p.close();counts.close();temp.cleanup();assert p.mode=='dense' and not p.restores
        checks.append({'flow':flow,'paired_full_calls':20,'shadow_records':2,'strict_output_cache_buffer_parity':True,'true_dense_replay_match':True,'C_strictly_past_cfg_separated':True,'dense_fallback_and_two_backend_arms_exercised':True,'eight_raw_output_files_hash_finite_and_independent_errors_recomputed':True})
    # A failed arm must retain its state in the planned denominator, restore buffers/RNG,
    # and never promote candidate outputs to the online cache.
    config={'eligible_call_range':[9,20],'warmups':1,'repeats':3,'dense_fallback_layers':[2],'policy':{'sim':.1,'cdf':.98}}
    def nonfinite_kernel(q,k,v,mask,sim,cdf,full):
        value=(q*1.002*.999).reshape(1,128,2048)
        return (value if full else value*float('nan')),{'selected_fraction':.7}
    p=H0ComplementProbe(config,kernel=nonfinite_kernel)
    failns=dict(ns);exec(compile(tree,str(source_path),'exec'),failns)
    failns['worldcache_mini_train_dit_forward']=build_h0_forward(failns['worldcache_mini_train_dit_forward'],p)
    m=failns['apply_worldcache'](Toy(),num_steps=40,ret_ratio=.2,rel_l1_thresh=-1,probe_depth=1,osi_enabled=True).eval();p.install_operators(m)
    failed=False
    for i in range(20):
        x=spatial+i*.0001*(1+spatial.square())
        try:m(x,torch.ones(1),torch.ones(1))
        except ValueError as error:
            assert 'Nonfinite/undefined' in str(error);failed=True;break
    assert failed and len(p.attempts)==1 and not p.records
    assert p.attempts[0]['status']=='FAILED_RETAINED_IN_DENOMINATOR'
    assert len(p.attempts[0]['completed_arms'])==4 and p.mode=='dense' and not m._w1_shadow_active
    p.close()
    checks.append({'nonfinite_sparse_failure_retained_with_partial_four_arms':True,'no_reselect_or_next_case_on_failure':True,'diagnostic_mode_and_buffers_restored':True})
    assert not torch.cuda.is_initialized()
    return checks
