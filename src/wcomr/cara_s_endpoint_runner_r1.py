"""Loaded-model endpoint runner using the accepted collection pipeline."""
from collections import Counter
from pathlib import Path

from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_pipeline_r1 import collect
from .cara_s_uniform_endpoint_execution_r1 import make_requests
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_runner_r1.py'


def observed_precision(model):
    import torch
    net=model.net
    return dict(model_precision=str(model.precision),
        net_parameter_dtypes=dict(Counter(str(p.dtype) for p in net.parameters())),
        use_wan_fp32_strategy=net.use_wan_fp32_strategy,
        conditional_frame_timestep=model.config.conditional_frame_timestep,
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,cudnn_benchmark=torch.backends.cudnn.benchmark,
        cudnn_deterministic=torch.backends.cudnn.deterministic,outer_autocast=torch.is_autocast_enabled())


def collect_loaded(inference,samples,card,bound,common,ra_binding,host,output,context,storage,mode_types,*,cpu_validation=False):
    import torch
    from .full_sampling import CompleteStateRoundtrip
    from .h0_mode import establish_shared_eval,verify_shared_eval
    model=inference.pipe.model;net=model.net
    require(host==context['host']=='two_card' and context['CPU_fixture_only'] is cpu_validation
            and bool(mode_types), 'Exact admitted host, mode contract and fixture boundary required')
    precision=observed_precision(model)
    require(digest(precision)==context['model_precision_sha256'], 'Original shared model precision differs')
    if not cpu_validation:
        require(precision['model_precision']=='torch.bfloat16' and precision['use_wan_fp32_strategy'] is True
                and precision['conditional_frame_timestep']==.1 and precision['outer_autocast'] is False,
                'Original production precision/backend required')
    parameters=list(net.named_parameters())
    versions=[(name,p,p._version,str(p.dtype)) for name,p in parameters]
    mode=establish_shared_eval(net,mode_types)
    common['wc'].apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in card['roles']['ALLD']['settings'].items()})
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint();checks=0
    def verify_parameters():
        current=list(net.named_parameters())
        require(len(current)==len(versions) and all(name==old_name and p is original and p._version==version and str(p.dtype)==dtype
            for (name,p),(old_name,original,version,dtype) in zip(current,versions)), 'Original model parameters changed')
        require(observed_precision(model)==precision,'Original precision/backend changed during collection')
    def before(slot):
        nonlocal checks
        storage.check();initial.restore()
        require(initial.fingerprint()==origin,'Original complete request reset differs')
        verify_shared_eval(net,mode);verify_parameters()
        checks+=1
    adapter=make_requests(card,bound,cpu_validation=cpu_validation,production_context=context,
        inference=inference,samples=samples,common=common,ra_binding=ra_binding,host=host)
    try:
        collection=collect(adapter,Path(output),context,before_request=before,precision=precision)
    finally:
        initial.restore()
        require(initial.fingerprint()==origin,'Final complete model state restoration differs')
        verify_shared_eval(net,mode);verify_parameters()
    storage.check()
    return collection,dict(precision_sha256=digest(precision),request_boundary_checks=checks,
        final_state_restored=True,shared_eval_verified=True,CPU_fixture_only=cpu_validation,
        GPU_dispatch_allowed=False,scientific_accepted=False)
