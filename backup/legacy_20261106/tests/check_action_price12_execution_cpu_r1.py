"""Actual12-parent adapter x two flows;8 extra Toy-only selector reference paths."""
import copy
import gzip
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.action_price12_execution_r1 import execute_one,archive_output,run_registered_batch,full_rows
from wcomr.action_price16_collection_r1 import COUNTS
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.mid_coverage import tree_digest
from check_source_phase16_sampling_cpu_r1 import load,select


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_PRICE12_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('SYNTHETIC_PRICE12',3.,4.,1.),
        partial_prior=CreationPhasePrior('SYNTHETIC_PRICE12',.005,.3,
            early_creation_floor=.005,late_creation_floor=10.),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'A_CPD_BETA1_ONE_PHASE':spec};params=dict(gamma=.5,fingerprint='SYNTHETIC_ONLY')
    config={**config,'paired_prefix_reserve_bytes':config.get('paired_prefix_reserve_bytes',0)}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    base=Path(artifact_root)/str(flow);references={};states=[]
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
        inference_module=inference_module,expected_shape=config['expected_shape'])
    try:
        # These four additional paths select Toy fixture states only. Real
        # production uses the already frozen16 and does not rerun selection.
        for index,sample in enumerate(selected):
            initial.restore();holder={}
            def factory(*a,**kw):
                owner=MathSamplingOwner(*a,math_parameters=params,source_mode='P_OFF',**kw)
                holder['owner']=owner;return owner
            with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
                original=clean.execute(inference,sample,'KEEP_A_P',output=base/'reference'/str(index),audit=True,**common)
            states.extend(select(sample.name,holder['owner'].history));references[sample.name]=original
            holder.clear()
        matrix=[]
        for sample in selected:
            for mode in ('BASELINE','AUDIT','LEAN'):
                matrix.append(dict(id=sample.name+'__'+mode,scene=sample.name,mode=mode,parent_method='P_OFF',
                    complete_updates=36,new_output_positions=1,readout='BETA1_ONE_PHASE',gamma=.5,
                    measured_steps=[] if mode=='BASELINE' else sorted(s['chosen']['step'] for s in states if s['scene']==sample.name)))
        scope=dict(complete_parent_matrix=matrix,states=states,scope_counts=COUNTS)
        observed=[]
        def restore():
            initial.restore();assert initial.fingerprint()==origin
            return dict(original_state_sha256=origin,restored_state_sha256=initial.fingerprint(),shared_eval_verified=True)
        def one(planned,sample):
            result=execute_one(inference,sample,planned,scope=scope,parameters=params,
                checkpoint_reserves=config,restore_request_state=restore,
                output=base/'registered'/planned['id'],**common)
            ref=references[sample.name]
            assert result['status']=='COMPLETE' and result['actions']==ref['actions']
            assert torch.equal(result['final_latent'],ref['final_latent'])
            assert all(torch.equal(a,b) for a,b in zip(result['guided'],ref['guided']))
            assert Path(result['video_path']).read_bytes()==Path(ref['video_path']).read_bytes()
            assert result['request_memory_lifecycle']['components_alive_after']==0
            result.update(full36_reference_parity=True,Toy_video_reference_parity=True)
            observed.append(dict(id=planned['id'],actual_pairs=result['actual_pair_computations'],
                observed_components=result['request_memory_lifecycle']['observed_components']))
            return archive_output(result,base/'registered'/planned['id'],base,expected_shape=config['expected_shape'])
        state=run_registered_batch(scope,{s.name:s for s in selected},one)
        if state['status']!='N09_ACTION12_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT':
            (base/'failed-runner.json.gz').write_bytes(gzip.compress(json.dumps(state,allow_nan=False).encode()))
            raise AssertionError(dict(status=state['status'],rows=[{k:r[k] for k in
                ('id','status','error_type','error') if k in r} for r in state['runs']]))
        assert len(state['runs'])==12 and len(full_rows(state['runs'],scope))==12
        assert sum(r['actual_pair_computations'] for r in state['runs'])==944
        initial.restore();assert initial.fingerprint()==origin
        return [dict(flow=flow,status='PASS',registered_adapter_paths=12,additional_Toy_selection_reference_paths=4,
            actual_complete_CPU_paths=16,actual_ordinary_pairs=576,trial_pairs=512,actual_pairs=1088,
            observed=observed,runner=state,all_full36_reference_outputs_actions_Toy_video_equal=True,
            all_request_components_released=True,ordinary_initial_state_restored=True)]
    finally:initial.restore()


def run(runtime,tensor_loader,artifact_root):
    accepted=load('check_paper_baseline_grid_sampling_cpu_r1');source=dedent(inspect.getsource(accepted.run))
    marker="    assert {r['flow'] for r in value['checks']}=={False,True}\n"
    assert source.count(marker)==1
    namespace={**vars(accepted),'body':body}
    exec(compile(source[:source.index(marker)]+'    return value\n',__file__+'#accepted-local-harness','exec'),namespace)
    value=namespace['run'](runtime,tensor_loader,artifact_root)
    assert {r['flow'] for r in value['checks']}=={False,True}
    value.update(status='N09_ACTION12_ADAPTER_FULL32_CPU_PASS_NOT_PRODUCTION',
        registered_adapter_CPU_paths=24,additional_Toy_selection_reference_paths=8,
        actual_complete_CPU_paths=32,actual_ordinary_pairs=1152,trial_pairs=1024,
        actual_pairs=2176,actual_CFG_calls=4352,actual_model_or_GPU_price_result=False)
    return value
