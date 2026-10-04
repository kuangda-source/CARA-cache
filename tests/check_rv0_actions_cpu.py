"""Actual pinned CPU C/C, D/D, swapped C/D and parent restoration controls."""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.prepared_input import PreparedInputReplay, RNGState, input_signatures
from wcomr.rv0_fork import WC_CONFIGURATION, official_suffix
from wcomr.rv0_actions import OneAction, OneActionRouter, OneActionSuffixControl


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow, runtime):
    model, net, scheduler = inference.pipe.model, inference.pipe.model.net, inference.pipe.model.sample_scheduler
    original_forward, original_prepare = net.forward, net.prepare_embedded_sequence
    caller = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    caller_sha = caller.fingerprint()
    config = {k: copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    keys = {k for k in WC_FIELDS if hasattr(net,k)}
    net.prepare_embedded_sequence = lambda x, **kwargs: (x.movedim(1,-1).contiguous(),None,None)
    source = runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    checks = []
    try:
        for threshold, kind in [(-1.0,'full'), (1e6,'cache')]:
            entry = RNGState(); prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            observations, branches = [], []
            for instrumented in (False,True):
                entry.restore()
                with torch.no_grad():
                    for name, value in net.named_buffers(): value.copy_(caller.buffers[name][1])
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'):v for k,v in {**settings,'worldcache_rel_l1_thresh':threshold}.items()})
                router = OneActionRouter(('CPU_ACTION:'+kind, 'toy_model', 'condition:'+samples[0].name)) if instrumented else None
                if router: router.install(net,wc,source)
                hooks = Hooks(); current = {'inputs':[],'outputs':[],'deep':[],'banks':[],'solver':[]}
                observations.append(current)
                stage = {'inside':False}; count = [0]
                prior_prepare = inference.pipe._get_data_batch_input
                inference.pipe._get_data_batch_input = prepared
                hooks.wrap(model,'get_velocity_fn_from_batch',after=lambda v:stage.update(velocity=v))
                hooks.wrap(model,'denoise',before=lambda a,k:stage.update(noise=a[0]))
                handles = [b.register_forward_hook(lambda *a:count.__setitem__(0,count[0]+1)) for b in list(net.blocks)[1:]]
                def before_forward(a,k):
                    current['inputs'].append(input_signatures(a,k));count[0]=0
                def after_forward(v):
                    current['outputs'].append(tree_digest(v));current['deep'].append(count[0])
                    current['banks'].append(tree_digest([net.residual_cache,net.probe_residual_cache,
                        net.residual_window,net.probe_residual_window,net.accumulated_rel_l1_distance,
                        net.resume_flag,net.worldcache_step_skipped_count]))
                hooks.wrap(net,'forward',before=before_forward,after=after_forward)
                def after_step(value):
                    if stage['inside']:return
                    current['solver'].append(tree_digest(value))
                    if scheduler._step_index!=22 or not router:return
                    fork = OneActionSuffixControl(model,value[0].squeeze(0),stage['noise'],stage['generator'],
                        stage['velocity'],suffix,router=router,context=router.context)
                    current['snapshot_storage'] = fork.snapshot_storage()
                    before = copy.deepcopy(current)
                    stage['inside'] = True
                    try:
                        for slot in (0,1):
                            for action,label in [('OFF','OFF1'),('OFF','OFF2'),('C','C_first'),('D','D_second'),('D','D_first'),('C','C_second')]:
                                start = len(current['inputs'])
                                latent = fork.run_action(str(slot)+'_'+label, OneAction(action,45+slot,slot,32))
                                branches.append({'slot':slot,'action':action,'label':label,
                                    'inputs':copy.deepcopy(current['inputs'][start:]),
                                    'outputs':current['outputs'][start:].copy(),'deep':current['deep'][start:].copy(),
                                    'banks':current['banks'][start:].copy(),'latent':tree_digest(latent),
                                    'record':copy.deepcopy(fork.records[-1])})
                        # Both candidate actions require a feasible C/D pair;
                        # short max-age rejects the stale forced-cache control.
                        rejected_age = False
                        if kind=='cache':
                            try:fork.run_action('invalid_age',OneAction('C',45,0,1))
                            except ValueError:rejected_age=True
                            else:raise AssertionError('Stale C/D source accepted')
                            assert fork.records[-1]['status']=='TECH_BLOCKED' and fork.records[-1]['parent_restored']
                        original_arm = router.arm
                        def missing_history(plan):
                            original_arm(plan);router.history[plan.cfg_slot]=[]
                        router.arm = missing_history
                        try:
                            try:fork.run_action('missing_history',OneAction('C',45,0,32))
                            except ValueError:pass
                            else:raise AssertionError('Missing true-full history accepted')
                            assert fork.records[-1]['status']=='TECH_BLOCKED' and fork.records[-1]['parent_restored']
                        finally:router.arm=original_arm
                        def wrong_mode(plan):
                            original_arm(plan);net.blocks[0].training=True
                        router.arm=wrong_mode
                        try:
                            try:fork.run_action('changed_eval',OneAction('D',45,0,32))
                            except ValueError:pass
                            else:raise AssertionError('Changed eval mode accepted')
                            assert fork.records[-1]['status']=='TECH_BLOCKED' and fork.records[-1]['parent_restored']
                            assert not any(m.training for m in net.modules())
                        finally:router.arm=original_arm
                        current['failed_attempts_preserved'] = True
                    finally:
                        stage['inside']=False
                        for key in list(current):
                            if key not in before:del current[key]
                        for key in before:current[key]=before[key]
                hooks.wrap(scheduler,'step',before=lambda a,k:stage.update(generator=k['generator']),after=after_step)
                hooks.wrap(model,'generate_samples_from_batch',after=lambda v:current.update(latent=tree_digest(v)))
                try:
                    with tempfile.TemporaryDirectory(prefix='rv0-actions-cpu-') as directory:
                        paths=inference.generate([samples[0]],output_dir=Path(directory))
                        current['artifact']=Path(paths[0]).read_bytes().hex()
                    current['rng']=RNGState().signatures()
                    current['state']=CompleteStateRoundtrip(net,scheduler,torch.zeros(1)).fingerprint()
                finally:
                    hooks.close();inference.pipe._get_data_batch_input=prior_prepare
                    for h in handles:h.remove()
                    if router:router.close()
            storage = observations[1].pop('snapshot_storage')
            assert observations[0]==observations[1] # Original vs router OFF + restored shadows.
            by={(b['slot'],b['label']):b for b in branches}
            assert len(branches)==12
            for slot in (0,1):
                off=by[(slot,'OFF1')]
                assert off['inputs']==observations[0]['inputs'][44:]
                assert off['outputs']==observations[0]['outputs'][44:]
                assert off['banks']==observations[0]['banks'][44:]
                assert off['deep']==observations[0]['deep'][44:] and off['latent']==observations[0]['latent']
                for a,b in [('OFF1','OFF2'),('C_first','C_second'),('D_second','D_first')]:
                    left,right=by[(slot,a)],by[(slot,b)]
                    assert all(left[k]==right[k] for k in ('inputs','outputs','banks','deep','latent'))
                    assert left['record']['final_state_components']==right['record']['final_state_components']
                c,d=by[(slot,'C_first')],by[(slot,'D_second')]
                assert c['inputs'][:slot+1]==d['inputs'][:slot+1] # Same input through target; CFG1 has identical CFG0 prefix.
                assert c['deep'][slot]==0 and d['deep'][slot]==len(net.blocks)-settings['probe_depth']
                if slot: assert c['banks'][0]==d['banks'][0]
                for branch in (c,d):
                    record=branch['record'];report=record['action_report']
                    assert record['parent_restored'] and not record['counterfactual_label']
                    assert len(report['suffix_events'])==28 and report['decision_interventions']==1
                    target=report['suffix_events'][slot]
                    assert target['paid_probe'] and target['requested']==branch['action']
                    assert not target['current_deep_truth_used'] and target['cfg_slot']==slot
                    history=target['true_full_history'][slot]
                    assert (history[-1]==23)==(branch['action']=='D')
                    assert report['remaining_policy']=='ORIGINAL_WC_ADAPTIVE' and not report['budget_matched']
                native=by[(slot,'D_first' if kind=='full' else 'C_first')]
                assert all(native[k]==off[k] for k in ('inputs','outputs','banks','deep','latent'))
            invalid=[OneAction('C',14,1,32),OneAction('D',70,1,32),OneAction('C',45,1,32),
                     OneAction('C',True,0,32),OneAction('C',45,0,0),OneAction('S',45,0,32)]
            for plan in invalid:
                try:plan.validate()
                except ValueError:pass
                else:raise AssertionError('Invalid protected/CFG/age/action plan accepted')
            checks.append({'flow':flow,'native_control':kind,
                'original_vs_OFF_all72_inputs_outputs_cache_banks_latent_state_RNG_artifact_equal':True,
                'CFG0_and_CFG1_same_input_current_CD_deep0_vs_full':True,
                'CC_DD_swapped_CD_full_suffix_and_state_equal':True,
                'native_matching_action_equals_OFF':True,
                'current_CD_uses_paid_probe_past_own_CFG_true_full_only':True,
                'cache_full_side_effects_left_to_pinned_body':True,
                'six_invalid_plans_and_missing_history_refused':True,
                'changed_eval_mode_refused_and_restored':True,
                'stale_age_refused_when_infeasible':kind=='cache',
                'TECH_BLOCKED_attempts_and_parent_restore_verified':True,
                'suffix_controls':12,'suffix_updates':14,'suffix_CFG_calls':28,
                'snapshot_storage_CPU_Toy_only':storage,
                'budget_matched_or_real_GPU_labels':False})
        return checks
    finally:
        net.forward=original_forward;net.prepare_embedded_sequence=original_prepare
        for key in set(WC_FIELDS)-keys:
            if hasattr(net,key):delattr(net,key)
        for key,value in config.items():setattr(net,key,value)
        caller.restore();assert caller.fingerprint()==caller_sha


def run(runtime):
    def load(name):
        spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    regression=load('check_rv0_fork_cpu').run(runtime)
    fixture=load('check_full_sampling')
    current=fixture.run(runtime,exercise=lambda **k:exercise(runtime=Path(runtime),**k))
    assert not torch.cuda.is_initialized()
    return {'status':'CPU_ONE_ACTION_C_D_INTERFACE_PASS_NOT_REAL_RV_LABELS',
            'unchanged_suffix_regression':regression,'current':current,
            'CUDA_initialized':False,'GPU_submissions':0,'RV_labels':0}
