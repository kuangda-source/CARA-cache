"""Strict WC D/D followed by all six workpoints on each of two exposed CALs."""
from .fair_sampling import run_fair_request
from .fair_workpoints import FAIR_WORKPOINTS
from .light_output import run_light_dense_control
from .prepared_input import RNGState
from .stage_refresh import StageRefreshAdapter
from .stage_refresh_policy import StageRefreshPolicy


def run_fair_output(inference, samples, wc, settings, policy, *, state, save, output,
                    inference_module, contexts, mode_setup, fallback=(6,23,27),
                    kernel=None, expected_video=(93,432,768), expected_WC_sha256=None):
    group = tuple(v for v in range(settings['probe_depth'],len(inference.pipe.model.net.blocks)) if v not in fallback)
    if (type(policy) is not StageRefreshPolicy or policy.sparse_layers != group
            or (policy.every,policy.first_solver_step,policy.last_solver_step) != (1,23,27)
            or len(samples) != 2 or len(contexts) != 2
            or len({s.name for s in samples}) != 2
            or any(type(c) is not tuple or len(c) != 3 for c in contexts)
            or any(any(type(v) is not str or not v for v in c) for c in contexts)
            or any(not c[0].endswith(':'+s.name) for c,s in zip(contexts,samples))
            or contexts[0][1] != contexts[1][1] or state.get('dense_control') or state.get('measurements')):
        raise ValueError('Explicit two-CAL six-workpoint fair output scope differs')
    if expected_WC_sha256 is not None and (type(expected_WC_sha256) is not dict
            or set(expected_WC_sha256) != {s.name for s in samples}
            or any(type(v) is not str or len(v) != 64
                   or any(c not in '0123456789abcdef' for c in v) for v in expected_WC_sha256.values())):
        raise ValueError('Historical fair WC006 bridge requires both sample SHAs')
    entry = RNGState()
    enabled = inference.pipe.worldcache_enabled
    net = inference.pipe.model.net
    missing = object()
    configuration = {name:getattr(net,name,missing) for name in
                     set(settings) | {'worldcache_enabled'}}
    state.update(planned_total_phases=14,planned_output_files=14,
        role='TWO_EXPOSED_CAL_NATIVE_FEWER_STEP_TUNED_WC_STAGE_FAIR_COMPARISON_NOT_CONF',
        workpoints=[p.to_dict() for p in FAIR_WORKPOINTS],stage_policy=policy.to_dict(),
        dense_control={'status':'NOT_STARTED','phases':[]},
        measurements={'status':'NOT_STARTED_DD_PENDING','requests':[]})
    save()
    try:
        entry.restore(); inference.pipe.worldcache_enabled=True
        run_light_dense_control(inference,samples[0],wc,settings,state=state['dense_control'],
            save=save,output=output/'dense-control',inference_module=inference_module,
            context=contexts[0],mode_setup=mode_setup,fallback=fallback,expected_video=expected_video,
            adapter_factory=lambda kind,ctx: None if kind=='official' else
                StageRefreshAdapter(ctx,policy,fallback_layers=fallback))
        for sample,ctx in zip(samples,contexts):
            entry.restore()
            request={'sample_name':sample.name,'status':'STARTED','phases':[],
                     'diagnostic_observers':False,'performance_sample':True}
            state['measurements']['requests'].append(request);save()
            run_fair_request(inference,sample,wc,settings,FAIR_WORKPOINTS,policy,
                state=request,save=save,output=output/'measurement'/sample.name,
                inference_module=inference_module,context=ctx,mode_setup=mode_setup,
                fallback=fallback,kernel=kernel,expected_video=expected_video,
                expected_WC_sha256=expected_WC_sha256[sample.name] if expected_WC_sha256 is not None else None)
        state['measurements']['status']='TWELVE_FAIR_CAL_OUTPUTS_REQUIRE_INDEPENDENT_AUDIT_METRICS'
        state['status']='FOURTEEN_COMPLETE_FAIR_OUTPUTS_REQUIRE_AUDIT_NOT_FRONTIER_ACCEPTANCE'
    except BaseException as exc:
        state.update(status='TECH_BLOCKED_FAIR_FOURTEEN_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(exc).__name__,error=str(exc));raise
    finally:
        inference.pipe.worldcache_enabled=enabled
        for name,value in configuration.items():
            if value is missing:
                if hasattr(net,name): delattr(net,name)
            else: setattr(net,name,value)
        save()
