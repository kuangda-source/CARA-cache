"""Strict D/D then two adaptive-WC/window/cadence comparisons: eight outputs."""
from .light_output import run_light_dense_control
from .light_sampling import run_light_pair
from .prepared_input import RNGState
from .stage_refresh import StageRefreshAdapter
from .stage_refresh_policy import StageRefreshPolicy


def run_stage_output(inference, samples, wc, settings, policies, *, state, save,
                     output, inference_module, contexts, mode_setup, fallback=(6,23,27),
                     kernel=None, expected_video=(93,432,768), expected_D_sha256=None):
    group = tuple(v for v in range(settings['probe_depth'], len(inference.pipe.model.net.blocks))
                  if v not in fallback)
    if (type(policies) is not tuple or len(policies) != 2
            or any(type(p) is not StageRefreshPolicy or p.sparse_layers != group for p in policies)
            or [p.every for p in policies] != [1,2]
            or any((p.first_solver_step,p.last_solver_step) != (23,27) for p in policies)
            or len(samples) != 2 or len(contexts) != 2
            or len({s.name for s in samples}) != 2
            or any(type(c) is not tuple or len(c) != 3 for c in contexts)
            or any(any(type(v) is not str or not v for v in c) for c in contexts)
            or any(not c[0].endswith(':'+s.name) for c,s in zip(contexts,samples))
            or contexts[0][1] != contexts[1][1]
            or len({c[0] for c in contexts}) != 2
            or state.get('dense_control') or state.get('measurements')):
        raise ValueError('Explicit two-CAL online window/cadence scope differs')
    if expected_D_sha256 is not None and (type(expected_D_sha256) is not dict
            or set(expected_D_sha256) != {s.name for s in samples}
            or any(type(v) is not str or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                   for v in expected_D_sha256.values())):
        raise ValueError('Historical D bridge needs both explicit sample SHAs')
    entry = RNGState()
    state.update(planned_total_phases=8, planned_output_files=8,
        role='TWO_EXPOSED_CAL_CURRENT_STAGE_ADAPTIVE_WC_NOT_CONF_OR_FRONTIER',
        online_policy=True, uses_future_trace=False, official_skip_predicate_replaced=False,
        stage_policies=[p.to_dict() for p in policies],
        dense_control={'status':'NOT_STARTED','phases':[]},
        measurements={'status':'NOT_STARTED_DD_PENDING','requests':[]})
    save()
    try:
        entry.restore()
        run_light_dense_control(inference,samples[0],wc,settings,state=state['dense_control'],
            save=save,output=output/'dense-control',inference_module=inference_module,
            context=contexts[0],mode_setup=mode_setup,fallback=fallback,expected_video=expected_video,
            adapter_factory=lambda kind,ctx: None if kind=='official' else
                StageRefreshAdapter(ctx,policies[0],fallback_layers=fallback))
        for sample,ctx in zip(samples,contexts):
            entry.restore()
            request={'sample_name':sample.name,'status':'STARTED','phases':[],
                     'diagnostic_observers':False,'performance_sample':True,
                     'variant_names':['adaptive_WC','stage_every1','stage_every2']}
            state['measurements']['requests'].append(request);save()
            counter=[0]
            def factory(kind,context):
                if kind=='official':return None
                if expected_D_sha256 is not None and request['phases'][0]['artifacts'][0]['sha256'] != expected_D_sha256[sample.name]:
                    raise ValueError('Historical adaptive D output failed before sparse candidates')
                policy=policies[counter[0]];counter[0]+=1
                return StageRefreshAdapter(context,policy,sparse=True,
                                           fallback_layers=fallback,kernel=kernel)
            run_light_pair(inference,sample,wc,settings,state=request,save=save,
                output=output/'measurement'/sample.name,inference_module=inference_module,
                context=ctx,mode_setup=mode_setup,adapter_factory=factory,
                sequence=('official','candidate','candidate'),
                sequence_policy='reference_then_candidates',expected_video=expected_video)
            if expected_D_sha256 is not None and request['phases'][0]['artifacts'][0]['sha256'] != expected_D_sha256[sample.name]:
                raise ValueError('Historical adaptive D output failed; stop before next request')
            request['status']='THREE_ONLINE_STAGE_OUTPUTS_REQUIRE_METRICS';save()
        state['measurements']['status']='SIX_ADAPTIVE_WC_AND_STAGE_OUTPUTS_REQUIRE_METRICS'
        state['status']='EIGHT_ONLINE_STAGE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    except BaseException as exc:
        state.update(status='TECH_BLOCKED_ONLINE_STAGE_EIGHT_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(exc).__name__,error=str(exc));raise
    finally:save()
