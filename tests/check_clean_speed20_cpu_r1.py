"""Declared Toy weights, actual native blocks/RF/UniPC; audit/clean controls."""
import copy
import inspect
from pathlib import Path
from textwrap import dedent
import types

import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name(name+'.py');s=spec_from_file_location(name,p)
    m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    net=inference.pipe.model.net
    calibration=Calibration('SYNTHETIC_CLEAN_SPEED_FULL36',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},
        {s:1. for s in range(1,37)})
    base={'threshold':.07,'costs':Costs('SYNTHETIC_RA',1.,4.),'partial_prior':None,
        'working_epoch_strategy':clean.STRATEGY}
    part={'threshold':2.,'costs':Costs('SYNTHETIC_P',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_P_FLOOR',.005,.3,
            early_creation_floor=.005,late_creation_floor=.02),
        'working_epoch_strategy':clean.STRATEGY}
    specs={'SOURCE_RA':base,'A_CPD_BETA1_ONE_PHASE':part}
    def native(self,*a,**kw):
        thresh=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=thresh
    net0=net.forward;pipe0=inference.pipe.worldcache_enabled
    initial=CompleteStateRoundtrip(net,inference.pipe.model.sample_scheduler,torch.zeros(1))
    origins=initial.fingerprint();checks=[]
    try:
        for index,sample in enumerate(selected[:2]):
            sample.name=clean.SCENES[index]
            originals={}
            for method in clean.METHODS:
                initial.restore()
                r=clean.execute(inference,sample,method,runtime=runtime,wc=wc,rf=rf,settings=settings,
                    calibration=calibration,specs=specs,inference_module=inference_module,
                    output=Path(artifact_root)/str(flow)/str(index)/('audit_'+method),
                    expected_shape=config['expected_shape'],audit=True,CPU_native=native)
                assert r['status']=='COMPLETE' and len(r['guided'])==36
                originals[method]=r
            for rep in (1,2):
                for method in clean.METHODS if rep==1 else clean.METHODS[::-1]:
                    initial.restore()
                    r=clean.execute(inference,sample,method,runtime=runtime,wc=wc,rf=rf,settings=settings,
                        calibration=calibration,specs=specs,inference_module=inference_module,
                        output=Path(artifact_root)/str(flow)/str(index)/f'clean_{rep}_{method}',
                        expected_shape=config['expected_shape'],CPU_native=native)
                    old=originals[method]
                    assert r['status']=='COMPLETE' and r['in_timing_guided_copies']==0
                    assert r['research_checkpoints']==r['in_timing_hashes']==0
                    assert r['actions']==old['actions'] and r['A_history']==old['A_history']
                    assert torch.equal(r['final_latent'],old['final_latent'])
                    assert Path(r['video_path']).read_bytes()==Path(old['video_path']).read_bytes()
                    checks.append({'scene':sample.name,'method':method,'round':rep,'flow':flow,
                        'audit_clean_final_and_video_equal':True,'actions_equal':True,
                        'A_history_equal':True,'guided_pairs':r['guided_pairs'],
                        'copies_in_clean_timer':r['in_timing_guided_copies']})
        assert len(checks)==20
        initial.restore();assert initial.fingerprint()==origins
        assert net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':30,
            'all20_clean_vs10_audit_controls_equal':True,'initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:')
    end=source.index('\n    finally:\n',start)+1
    replacement='    try:\n        return _clean_body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'
    changed=source[:start]+replacement+source[end:]
    ns={**vars(original),'_clean_body':body};exec(compile(changed,__file__+'#accepted-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(value['checks'])==2 and {c['flow'] for c in value['checks']}=={True,False}
    assert len(clean.matrix())==40
    value.update(status='CLEAN_SPEED20_CPU_PASS_NOT_GPU',actual_CPU_paths=60,
        clean_paths=40,audit_paths=20,implementation_only=True)
    return value
