"""Check cross-request restoration and the explicit two-seed denominator.

Native/WC callbacks deliberately mutate state; real generation belongs to the
unchanged Native implementation and separately checked pinned WC CPU fixture.
"""
import copy
from types import SimpleNamespace
from pathlib import Path

import torch
from wcomr.rv0_d46_seed_portfolio import run_portfolio
from wcomr.rv0_d46_seed_scope import COUNTS


def run():
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__();self.register_buffer('visits',torch.zeros(()));self.cnt=0
            self.worldcache_num_steps=70;self.worldcache_enabled=True
    net=Net().eval();solver=SimpleNamespace(_step_index=0,model_outputs=[None,None],timesteps=torch.arange(36))
    inf=SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(net=net,sample_scheduler=solver)))
    samples=[]
    for seed in (1,2):
        s=SimpleNamespace(seed=seed,name='human_199_seed'+str(seed));s.model_dump=lambda mode,s=s:{'name':s.name,'seed':s.seed};samples.append(s)
    calls=[]
    def assert_initial(sample):
        assert net.cnt==0 and float(net.visits)==0 and solver._step_index==0 and net.worldcache_enabled
    def native(inference,sample,**k):
        assert_initial(sample);calls.append(('Native',sample.seed));net.visits.add_(3);net.cnt=71;solver._step_index=36;net.worldcache_enabled=False
        k['state']['status']='CPU_CALLBACK_NOT_NATIVE_GENERATION'
    def causal(inference,samples,wc,settings,**k):
        assert_initial(samples[0]);calls.append(('WC',samples[0].seed));net.visits.add_(5);net.cnt=2;solver._step_index=36
        k['state']['status']='CPU_CALLBACK_NOT_WC_GENERATION'
    state={'model_context':'CPU_ONLY'};scope={'seed_values':[1,2],'scope_counts':COUNTS,'run_id':'CPU_PORTFOLIO'}
    run_portfolio(inf,samples,None,{},state=state,save=lambda:None,output=Path('CPU_CALLBACK_NO_FILES'),inference_module=None,
        mode_setup=None,runtime=None,scope=scope,sampling_policy=None,native_runner=native,causal_runner=causal)
    assert calls==[('Native',1),('WC',1),('Native',2),('WC',2)] and len(state['cases'])==2
    assert_initial(samples[0]);assert all(c['pre_Native_initial_fingerprint']==c['pre_WC_initial_fingerprint'] for c in state['cases'])
    return {'status':'D46_TWO_SEED_CALLBACK_STATE_ISOLATION_CPU_PASS_NOT_GENERATION','restored_initial_state_four_calls':True,
            'explicit_callbacks_not_native_or_WC_sampling':True,'CUDA_initialized':False,'GPU_submissions':0}
