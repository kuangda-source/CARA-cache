"""Full8 requests x5 methods x audit/lean/legacy in both native flow loops; seed identities."""
import copy,inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_conditional_confirmation_batch_r1 import execute,METHODS
from wcomr.source_phase_absolute_h1_batch_r1 import execute as legacy_execute
from wcomr.source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller,VERSION,fingerprint
from wcomr.math_n2_batch_r1 import execute as previous_execute


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,requests):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    prototype=type(selected[0]);selected=[]
    for request in requests:
        sample=prototype(request['name'])
        for key,value in request.items():setattr(sample,key,value)
        # The pinned CPU fixture has explicit tiny spatial/token stand-ins.
        # Actual production request geometry is separately schema-validated.
        sample.resolution='16,16'
        selected.append(sample)
    assert len(selected)==8 and [s.seed for s in selected]==[17]*4+[43]*4
    cal=Calibration('SYNTHETIC_H1_ACTUAL_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_H1',1.,4.,3.5),
        'partial_prior':CreationPhasePrior('SYNTHETIC_H1',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec}
    old={'fingerprint':'SYNTHETIC_PRIOR_UNCHANGED','gamma':.5}
    tables={}
    for group in ('SOURCE_PHASE','SOURCE'):
        keys=[s+'_'+phase for s in ('D','P') for phase in ('EARLY','LATE')] if group=='SOURCE_PHASE' else ['D','P']
        cells={key:{'status':'FIT','C_scale':1. if key.startswith('P') else 100.,'A_ratios':{'FUSION_A':.02},'actual_NEW_P_birth_mean':.0001} for key in keys}
        p={'version':VERSION,'gamma':.5,'table_model':{'grouping':group,'target':'absolute_guided_MSE',
            'current_teacher_energy_is_online_feature':False,'cells':cells},
            'cost_seconds':{'C':1.,'A':1.3,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.3},
            'lambda_seconds_per_weighted_absolute_MSE':100.}
        p['fingerprint']=fingerprint(p);tables[group]=p
    def native(self,*a,**kw):
        value=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=value
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    old_forward,old_enabled=net.forward,inference.pipe.worldcache_enabled;checks=[];readouts=set();sources=set()
    try:
        for index,sample in enumerate(selected):
            for method in METHODS:
                common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                    inference_module=inference_module,expected_shape=config['expected_shape'],CPU_native=native)
                initial.restore();assert initial.fingerprint()==origin
                calls={}
                for label,auditing,entry in [('AUDIT',True,execute),('LEAN',False,execute),('LEGACY',True,legacy_execute)]:
                    initial.restore();seen=[];native_step=scheduler.step
                    def seed_step(*args,**kwargs):
                        generator=kwargs.get('generator')
                        assert generator is not None
                        seen.append(generator.initial_seed())
                        return native_step(*args,**kwargs)
                    from wcomr import clean_speed20_r1 as clean
                    with clean.patched(scheduler,'step',seed_step):
                        value,_=entry(inference,sample,method,table_parameters=tables,previous_parameters=old,
                            output=Path(artifact_root)/str(flow)/str(index)/(method+'_'+label),audit=auditing,**common)
                    assert seen==[sample.seed]*36
                    calls[label]=value
                audit,lean,legacy=(calls[k] for k in ('AUDIT','LEAN','LEGACY'))
                assert audit['actions']==legacy['actions']
                assert torch.equal(audit['final_latent'],legacy['final_latent'])
                assert all(torch.equal(a,b) for a,b in zip(audit['guided'],legacy['guided']))
                assert Path(audit['video_path']).read_bytes()==Path(legacy['video_path']).read_bytes()
                for value in (audit,lean):
                    assert value['actual_request_seed']==sample.seed
                    assert value['request_context_seed_tag']=='fixed-seed'+str(sample.seed)+'-request'
                    assert value['request_context_derivation']['only_context_seed_tag_and_run_namespace_changed']
                    if method in ('P_OFF','TABLE_PHASE_H1'):
                        assert all(source['context'][2]==value['request_context_seed_tag']
                            for row in value['source_history'] for source in row['working_sources'])
                assert audit['status']==lean['status']=='COMPLETE' and len(audit['guided'])==36
                assert audit['actions']==lean['actions'] and audit['A_history']==lean['A_history']
                assert torch.equal(audit['final_latent'],lean['final_latent'])
                assert Path(audit['video_path']).read_bytes()==Path(lean['video_path']).read_bytes()
                assert lean['in_timing_hashes']==lean['in_timing_guided_copies']==lean['research_checkpoints']==0
                assert all(h['teacher_calls']==h['extra_deep_blocks']==0 for h in (audit['A_history'] or []))
                if method in METHODS[4:]:
                    history=audit['source_history'];assert len(history)==36
                    group='SOURCE_PHASE' if method=='TABLE_PHASE_H1' else 'SOURCE'
                    c=SourcePhaseH1Controller(cal,2.,spec['costs'],spec['partial_prior'],strategy=spec['working_epoch_strategy'],
                        table_parameters=tables[group],math_parameters=old,horizon=1,sigma_at=lambda n:float(scheduler.sigmas[n-1]))
                    for row in history:
                        d=row['joint_decision'];packets=tuple(tuple(p) for p in d['packets'])
                        decision=c._choice(d['step'],packets,d['both_sources_ready'],d['partial_ready'],protected=d['reason']=='actual_protected_dense')
                        assert decision.reason==d['reason'] and decision.action*2==row['action']
                        c.commit(decision,actual_action=decision.action,pair_completed=True)
                        event=row['source_policy']['event_math'];h=row['A_readout']
                        assert event['source_before']==d['state_before'][1] and not event['absolute_error_written_into_root_accumulator']
                        assert event['risk_unit']=='AMPLITUDE_GAIN_SQUARED_ABSOLUTE_GUIDED_MSE_PROXY'
                        if row['action']!='DD':assert row['true_D_before']==row['true_D_after']
                        if row['action']=='PP':assert row['source_policy']['creation_floor_proxy_after']>0
                        if row['action']=='CC':
                            selected_readout=decision.reason.rsplit(':',1)[-1];assert selected_readout==h['readout_action']
                            assert h['extra_heads']==(0 if selected_readout=='C' else 2 if event['source_before']=='D' else 4)
                            readouts.add(selected_readout);sources.add(event['source_before'])
                    snap=c.state_dict();c.accumulated=999.;c.restore(snap);assert c.state_dict()==snap
                checks.append({'scene':sample.name,'seed':sample.seed,'method':method,'complete36':True,'clean_parity':True,'legacy_all36_guided_actions_final_video_equal':True,'all_three36_generators_actual_seed':True,'actual_context_seed_tag':audit['request_context_seed_tag'],'actions':audit['actions']})
        initial.restore();assert initial.fingerprint()==origin and net.forward==old_forward and inference.pipe.worldcache_enabled==old_enabled
        assert len(checks)==40 and 'A' in readouts and sources=={'D','P'}
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':120,'all36_clean_outputs_actions_video_equal':True,
            'actual_rho_age_max':6,'readouts_exercised':sorted(readouts),'sources_exercised':sorted(sources),'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=old_forward;inference.pipe.worldcache_enabled=old_enabled


def run(runtime,tensor_loader,artifact_root,requests):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,requests)\n'+source[end:]
    ns={**vars(original),'_body':body,'requests':requests};exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='SOURCE_CONFIRMATION_TWO_FLOW_ALL80_AUDIT80_LEAN80_LEGACY_SEED17_43_CPU_PASS_NOT_GPU',actual_CPU_paths=240,
        complete_method_paths=80,clean_control_paths=80,legacy_control_paths=80,confirmation_requests=8,methods=5,
        actual_GPU_or_real_video_claim=False,candidate_template_only_not_frozen_GPU_choice=True)
    return value
