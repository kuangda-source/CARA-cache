"""Sparse-history diagnostics beside a frozen policy; shadow state never commits."""
import copy
import random
import numpy as np
from pathlib import Path
import torch
from .production_sampling import PolicyOwner, _cache_snapshot, execute as policy_execute
from .interval_grammar import Edge, compile_policy
from .continuation_preparation import history_points
from ..policy_interval_readout_r1 import ReadoutKernel, guided
from ..mid_coverage import tree_digest, WC_FIELDS
from ..partial_mlp_deployment_state import plain
from ..source_aware_phase_sampling import bind_globals
from ..policy_interval_assets_r1 import sha


def cpu(v):
    if isinstance(v,torch.Tensor):return v.detach().cpu().clone()
    if isinstance(v,dict):return {k:cpu(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return type(v)(cpu(x) for x in v)
    return copy.deepcopy(v)


class HistoryOwner(PolicyOwner):
    def __init__(self,*args,directory,**kw):
        super().__init__(*args,**kw)
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=False)
        self.plan=history_points(self.profile,self.policy);self.bank={};self.adjacent={};self.records=[];self.shadow_calls=0
        self.needed={n for p in self.plan['points'] for n in (p['previous'],p['source'])}
        self.shadow_steps=set(self.plan['shadow_pair_steps'])
        self.kw=kw
        dense=compile_policy(self.profile,[Edge(t,t+1) for t in range(1,37)])
        self.shadow=PolicyOwner(self.model,policy=dense,profile=self.profile,context=kw['context']+('SHADOW_ONLY',),runtime=kw['runtime'],wc=kw['wc'],rf=kw['rf'])
        self.features={};old=self.shadow.readout.hidden
        def capture(net,skipped,b,original,probe,hidden,kwargs,embedding,adaln):
            if skipped:raise ValueError('Shadow must run both full branches')
            self.features[b]=dict(original=original,probe=probe,embedding=embedding,adaln=adaln)
            return old(net,skipped,b,original,probe,hidden,kwargs,embedding,adaln)
        self.shadow.readout.hidden=capture
        self.kernel=ReadoutKernel(self.model,kw['runtime'],kw['wc'],kw['rf'],self.shadow.readout.warp)

    def state(self,inputs):
        return tree_digest(plain((inputs,{k:getattr(self.net,k) for k in WC_FIELDS if hasattr(self.net,k)},
            {k:v for k,v in vars(self.model.sample_scheduler).items() if not callable(v)},[vars(c) for c in self.readout.calibrators],self.readout.completed,
            self.history,random.getstate(),np.random.get_state(),torch.get_rng_state(),torch.cuda.get_rng_state_all() if inputs[1].is_cuda else [])))

    def anchors(self):
        return [dict(probe=self.net.probe_residual_cache[b].detach().cpu().clone(),
                     residual=self.net.residual_cache[b].detach().cpu().clone()) for b in (0,1)]

    def source(self,previous,latest,device):
        result=[]
        for p,s in zip(previous,latest):
            probe=s['probe'].to(device);residual=s['residual'].to(device)
            result.append(dict(probe=probe,residual=residual,probe_window=[p['probe'].to(device),probe],
                               residual_window=[p['residual'].to(device),residual]))
        return result

    @torch.no_grad()
    def pair(self,noise,latent,timestep,conditions,choose):
        t=self.readout.completed+1;inputs=(noise,latent,timestep,conditions)
        if t in self.shadow_steps:
            before=self.state(inputs);saved,versions=_cache_snapshot(self.net)
            rng=torch.get_rng_state();gpu=torch.cuda.get_rng_state_all() if latent.is_cuda else []
            pyrng=random.getstate();nprng=np.random.get_state()
            try:
                self.shadow.readout.completed=t-1
                self.shadow.history.clear();self.shadow.readout.history.clear()
                for c in self.shadow.readout.calibrators:c.reset(self.shadow.readout.context)
                self.features={}
                D=self.shadow.pair(*inputs,self.shadow.choose);self.shadow_calls+=1
                shadow_anchor=self.anchors()
                if t in {p['adjacent_anchor_shadow_step'] for p in self.plan['points']}:
                    self.adjacent[t]=shadow_anchor
                for point in (p for p in self.plan['points'] if p['target']==t):
                    s,p=point['source'],point['previous']
                    if s not in self.bank or p not in self.bank or s-1 not in self.adjacent:
                        raise ValueError('Missing exact own-trajectory diagnostic anchor')
                    outputs={};mse={}
                    for name,older in [('actual',self.bank[p]),('adjacent',self.adjacent[s-1])]:
                        source=self.source(older,self.bank[s],latent.device);values={}
                        for label in ('C','A_HALF','A_ONE'):
                            returned,C,Phi=self.kernel.run(label,source=source,current=self.features,pair_inputs=inputs)
                            values[label]=cpu(returned)
                        outputs[name]=values
                        mse[name]={k:float((guided(v).double()-guided(cpu(D)).double()).square().mean()) for k,v in values.items()}
                    if any(not torch.equal(a,b) for a,b in zip(outputs['actual']['A_ONE'],outputs['adjacent']['A_ONE'])):
                        raise ValueError('A_ONE unexpectedly depends on older history')
                    raw=dict(D=cpu(D),windows=outputs,point=point,input_sha256=tree_digest(plain(inputs)))
                    path=self.directory/f'target-{t}-branches.pt'
                    with path.open('xb') as f:torch.save(raw,f)
                    self.records.append(dict(point=point,guided_MSE=mse,branch_artifact=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size),
                        A_ONE_window_invariant=True,shadow_writes_parent=False,input_sha256=raw['input_sha256']))
            finally:
                if any(v is not None and x._version!=v for x,v in versions):raise ValueError('Shadow mutated retained parent tensor')
                for k,v in saved.items():setattr(self.net,k,v)
                torch.set_rng_state(rng)
                random.setstate(pyrng);np.random.set_state(nprng)
                if gpu:torch.cuda.set_rng_state_all(gpu)
                self.features.clear()
            if self.state(inputs)!=before:raise ValueError('Shadow changed input/solver/cache/anchors/condition/RNG')
            if self.records and self.records[-1]['point']['target']==t:self.records[-1]['parent_state_before_after_equal']=True
        result=super().pair(*inputs,choose)
        if t in self.needed:
            if self.history[-1]['actual']!='D':raise ValueError('Diagnostic source must be actual D')
            self.bank[t]=self.anchors()
        # Retain only anchors referenced by a future target.
        future=[p for p in self.plan['points'] if p['target']>t]
        self.bank={k:v for k,v in self.bank.items() if k in {n for p in future for n in (p['previous'],p['source'])}}
        self.adjacent={k:v for k,v in self.adjacent.items() if k in {p['source']-1 for p in future}}
        return result

    def close(self):
        self.bank.clear();self.adjacent.clear();self.features.clear();self.shadow.close();self.kernel=None
        super().close()


def execute(inference,sample,*,policy,profile,**kw):
    holder={}
    def owner(*a,**k):
        v=HistoryOwner(*a,directory=Path(kw['output'])/'history-branches',**k);holder['owner']=v;return v
    run=bind_globals(policy_execute,{'PolicyOwner':owner})
    result=run(inference,sample,policy=policy,profile=profile,**kw)
    v=holder.get('owner')
    result.update(history_plan=v.plan if v else history_points(profile,policy),history_records=v.records if v else [],
        shadow_D_pairs=v.shadow_calls if v else 0,clean_deployment_timing=False,
        full_request_seconds=None,timing_boundary='DIAGNOSTIC_REQUEST_SHADOW_INCLUDED_NOT_DEPLOYMENT_LATENCY')
    if result['status']=='COMPLETE' and (v.shadow_calls!=v.plan['shadow_D_pairs'] or len(v.records)!=len(v.plan['points'])):
        raise ValueError('Incomplete registered history diagnosis')
    return result
