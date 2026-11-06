"""Four Toy scenes, both real UniPC flows, baseline/audit/lean full36 parity."""
import copy
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.action_price16_collection_r1 import price16_install,ROUNDS
from wcomr.mid_coverage import tree_digest
from check_source_phase16_sampling_cpu_r1 import load,select


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_PRICE16_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('SYNTHETIC_PRICE16',3.,4.,1.),
        partial_prior=CreationPhasePrior('SYNTHETIC_PRICE16',.005,.3,
            early_creation_floor=.005,late_creation_floor=10.),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'A_CPD_BETA1_ONE_PHASE':spec};params=dict(gamma=.5,fingerprint='SYNTHETIC_ONLY')
    config={**config,'paired_prefix_reserve_bytes':config.get('paired_prefix_reserve_bytes',0)}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    net0,pipe0=net.forward,inference.pipe.worldcache_enabled;results=[];natural_P=0
    try:
        for index,sample in enumerate(selected):
            initial.restore();holder={}
            def parent(*a,**kw):
                owner=MathSamplingOwner(*a,math_parameters=params,source_mode='P_OFF',**kw)
                holder['parent']=owner;return owner
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'],audit=True)
            base=Path(artifact_root)/str(flow)/str(index)
            with clean.patched(clean,'CurrentBirthSamplingOwner',parent):
                original=clean.execute(inference,sample,'KEEP_A_P',output=base/'baseline',**common)
            states=select(sample.name,holder['parent'].history)
            natural_P+=sum(s['chosen']['actual_pi0_action']=='P' for s in states)
            records={}
            for mode in ('AUDIT','LEAN'):
                initial.restore();holder={};artifacts=[]
                def writer(step,payload):
                    p=base/mode/('action16_'+str(step)+'.pt');p.parent.mkdir(parents=True,exist_ok=True)
                    torch.save(payload,p);artifacts.append(p)
                    return dict(path=str(p),tensor_sha256=tree_digest(payload))
                with price16_install(clean,scheduler,states,
                        {**config,'action_price_observation_mode':mode},writer,params,holder):
                    new=clean.execute(inference,sample,'KEEP_A_P',output=base/mode,**common)
                owner=holder['owner']
                assert len(owner.records)==len(artifacts)==4 and owner.actual_pair_computations==100
                assert original['status']==new['status']=='COMPLETE'
                assert original['actions']==new['actions'] and torch.equal(original['final_latent'],new['final_latent'])
                assert len(original['guided'])==len(new['guided'])==36
                assert all(torch.equal(x,y) for x,y in zip(original['guided'],new['guided']))
                assert Path(original['video_path']).read_bytes()==Path(new['video_path']).read_bytes()
                for record in owner.records:
                    assert record['observation_mode']==mode and len(record['restores'])==16
                    assert len(record['trials'])==16 and not record['offline_trial_committed_to_parent']
                    assert not record['new_prices_used_in_parent']
                    assert [(t['round'],t['action']) for t in record['trials']]==[
                        (r,a) for r,order in ROUNDS for a in order]
                    assert all(t['interval']['status']=='PASS' and not t['interval']['shared_probe_seconds_included']
                        for t in record['trials'])
                    assert all(t['heads_observed']==(mode=='AUDIT') for t in record['trials'])
                    if mode=='LEAN':assert all(t['actual_heads'] is None for t in record['trials'])
                    else:
                        for trial in record['trials']:
                            expected=4 if trial['action']=='A' and record['point']['source']=='D' else (
                                6 if trial['action']=='A' else 2)
                            assert trial['actual_heads']==expected
                records[mode]=copy.deepcopy(owner.records)
            for a,b in zip(records['AUDIT'],records['LEAN']):
                assert a['point']==b['point']
                for left,right in zip(a['trials'],b['trials']):
                    assert left['output_tree_sha256']==right['output_tree_sha256']
                    assert left['interval']['paid_packets']==right['interval']['paid_packets']
                    assert left['actual_action']==right['actual_action']
            results.append(dict(scene=sample.name,states=states,records=records,complete_CPU_paths=3,
                trial_pairs=128,all36_guided_actions_final_and_Toy_video_equal=True,
                audit_lean_all16_trial_outputs_and_paid_packets_equal=True))
        initial.restore()
        assert initial.fingerprint()==origin and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        assert len(results)==4 and natural_P>=4
        return [dict(flow=flow,status='PASS',checks=results,complete_CPU_paths=12,
            distinct_natural_states=16,state_mode_positions=32,trial_pairs=512,
            ordinary_pairs=432,pre_parent_P_points=natural_P,ordinary_initial_state_restored=True)]
    finally:
        initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    # Reuse the accepted local harness's explicit pinned RF/WC extraction;
    # this machine deliberately has no installed Cosmos Python package.
    original=load('check_paper_baseline_grid_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.run))
    marker="    assert {r['flow'] for r in value['checks']}=={False,True}\n"
    assert source.count(marker)==1
    changed=source[:source.index(marker)]+'    return value\n'
    namespace={**vars(original),'body':body}
    exec(compile(changed,__file__+'#accepted-local-Toy-setup','exec'),namespace)
    result=namespace['run'](runtime,tensor_loader,artifact_root)
    assert {r['flow'] for r in result['checks']}=={False,True}
    result.update(status='N09_ACTION16_TWO_FLOW_FULL24_CPU_PASS_NOT_GPU_PRICES',actual_CPU_paths=24,
        distinct_Toy_states=32,state_mode_positions=64,actual_ordinary_pairs=864,trial_pairs=1024,
        total_pairs=1888,CFG_calls=3776,actual_GPU_or_real_video_or_price_claim=False)
    return result
