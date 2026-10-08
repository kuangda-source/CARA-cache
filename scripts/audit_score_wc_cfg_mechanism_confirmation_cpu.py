#!/usr/bin/env python3
"""Released-GPU CPU reconstruction of all actual local teachers and both full videos."""
import argparse
import copy
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cfg_teacher_confirmation_production import validate,sha
    c,_=validate(args.project,args.stage)
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**kw):raise RuntimeError('Actual teacher CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    from wcomr.cfg_teacher_metrics import score_four_cells,SPACE
    from wcomr.cfg_teacher_measurement import validate_net_binding
    from wcomr.rv0_video_reader import decoded_video,probe_video
    spec=importlib.util.spec_from_file_location('standalone_CPU_reconstruction',args.stage/'scripts/audit_wc_cfg_teacher_collection_cpu.py')
    independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent);digest=independent.digest
    run=args.project/'outputs'/c['execution_run_id'];sup=json.loads((run/'supervisor.json').read_text());raw_path=run/'diagnostic/receipt.json'
    runner=json.loads(raw_path.read_text());budget=json.loads((args.project/'reports/budget.json').read_text())
    assert sup['exit_code']==0 and runner['status']=='TEACHER_GPU_COMPLETE_REQUIRES_CPU_RAW_AUDIT_AND_LOCAL_SCORING'
    assert all(not Path('/proc/'+str(sup[k])).exists() for k in ('pid','child_pid'))
    assert sup['source_revision']==runner['source_revision'] and sup['budget_after']==budget
    assert math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
    with (args.project/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
    state=runner['teacher'];assert (state['planned_parents'],state['planned_origins'],state['planned_CFG_pairs'],state['planned_videos'])==(2,5,40,2)
    assert state['status']=='CFG_GUIDED_TEACHER_TWO_PARENT_FIVE_ORIGIN_CORE_COMPLETE_REQUIRES_AUDIT'
    off,on=state['parents'];trace=('inputs','outputs','deep','banks','solver_outputs')
    for key in trace+('net_measurements','solver_measurements','final_components','final_solver_configuration','sample_return_sha256','final_latent_sha256','flags_before','flags_after','pipeline'):assert off[key]==on[key],key
    assert len(off['inputs'])==72 and len(off['solver_outputs'])==36 and off['artifact']['sha256']==on['artifact']['sha256']
    net_count=0;solver_count=0
    for parent in (off,on):
        assert len(parent['net_measurements'])==72 and len(parent['solver_measurements'])==36
        for witness,signature in zip(parent['net_measurements'],parent['inputs']):
            validate_net_binding(witness,signature);net_count+=1
        for witness,raw_sha in zip(parent['solver_measurements'],parent['solver_outputs']):
            assert witness['raw_return_tree_sha256']==raw_sha;solver_count+=1
    expected_components=set(off['final_components']);assert len(expected_components)==c['expected_real_components']
    assert {'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'}<=expected_components
    result={'status':'TEACHER_CPU_COMPLETE_SCOPE_AUDIT_AND_SCORING_STARTED','runner_sha256':sha(raw_path),'scope':c['preregistration']['scope_counts'],
        'source_revision':sup['source_revision'],'original_GPU_PIDs_absent':[sup[k] for k in ('pid','child_pid')],
        'budget':budget,'full_parent_parity':True,'strict_repeat_groups':0,'videos':[],'origins':[],
        'old_seed2_video_is_not_a_seed3_control':runner['old_seed2_video_is_not_a_seed3_control'],'historical_full_state_acceptance':False,
        'endpoint_or_absolute_physics_quality_claim':False,'formal_RV_labels':False,'independent_CONF':False,'clean_speed_measurement':False,'CUDA_initialized':False,'GPU_submissions':0}
    def save():
        tmp=args.output.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(args.output)
    assert not args.output.exists();save()
    for parent in (off,on):
        assert parent['status']=='COMPLETE_PARENT' and parent['flags_before']==parent['flags_after']
        item=parent['artifact'];path=Path(item['path']);assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
        assert (run/'diagnostic').resolve() in path.resolve().parents
        meta=probe_video(path)
        with decoded_video(path) as frames:assert sum(1 for _ in frames)==93
        result['videos'].append({**item,'probe':meta,'full93_decode':True});save()
    assert [o['label'] for o in on['origins']]==c['preregistration']['origins']
    modes=c['preregistration']['modes'];tensor_count=0
    for index,origin in enumerate(on['origins']):
        assert origin['status']=='COMPLETE_LOCAL_ORIGIN' and len(origin['pairs'])==8
        rows=origin['pairs'];assert [r['label'] for r in rows]==[m+'_'+repeat for m in modes for repeat in ('first','second')]
        actual={}
        for row in rows:
            assert row['status']=='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT' and row['parent_restored']
            assert row['origin_completed_updates']==(22 if index==0 else 23)
            assert set(row['origin_components'])==set(row['pair_end_components'])==expected_components
            assert row['origin_fingerprint']==digest(row['origin_components']) and row['pair_end_fingerprint']==digest(row['pair_end_components'])
            assert row['origin_components']==rows[0]['origin_components'] and row['inputs']==rows[0]['inputs']
            assert row['origin_solver_configuration']==row['pair_end_solver_configuration']
            for key in ('inputs','outputs','deep','banks','post_denoise_branch_sha256','denoise_arguments'):assert len(row[key])==2
            assert len(row['net_measurements'])==len(row['post_denoise_measurements'])==2
            assert row['origin_measurement']['sampler_latent']['tree_sha256']==row['origin_components']['output']
            for witness,signature in zip(row['net_measurements'],row['inputs']):
                validate_net_binding(witness,signature);net_count+=1
            step=row['origin_completed_updates']+1;expected=copy.deepcopy(row['origin_own_history']);events=row['action_report']['events']
            assert len(events)==2 and row['action_report']['plan']['mode']==row['mode']
            for slot,event in enumerate(events):
                assert event['call']==2*(step-1)+slot+1 and event['cfg_slot']==slot and event['requested']==event['actual_action']==row['mode'][slot]
                assert event['paid_probe'] and not event['current_deep_truth_used']
                assert len(expected[slot])==2 and event['age_solver_steps']==step-expected[slot][-1] and 1<=event['age_solver_steps']<=32
                assert row['deep'][slot]==(26 if row['mode'][slot]=='D' else 0)
                if row['mode'][slot]=='D':expected[slot]=(expected[slot]+[step])[-2:]
                assert event['true_full_history']==expected
            art=row['artifact'];path=Path(art['path']);assert path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
            assert (run/'diagnostic').resolve() in path.resolve().parents and art['space']==SPACE
            tensors=torch.load(path,weights_only=True,map_location='cpu');assert set(tensors)=={'conditional','unconditional','guided'}
            for name,tensor in tensors.items():
                assert tensor.device.type=='cpu' and tensor.dtype==torch.float32 and list(tensor.shape)==c['expected_real_shape'] and torch.isfinite(tensor).all()
                assert digest(tensor)==art['tensor_sha256'][name] and art['shape'][name]==c['expected_real_shape'];tensor_count+=1
            assert row['post_denoise_branch_sha256']==[digest(tensors[k]) for k in ('conditional','unconditional')]
            for witness,name in zip(row['post_denoise_measurements'],('conditional','unconditional')):
                assert witness['tree_sha256']==digest(tensors[name]) and witness['dtype']==str(tensors[name].dtype)
                assert witness['shape']==list(tensors[name].shape)
            assert row['actual_guided_sha256']==digest(tensors['guided'])
            assert torch.equal(tensors['guided'],tensors['conditional']+7*(tensors['conditional']-tensors['unconditional']))
            actual[row['label']]=tensors
        for mode in modes:
            a,b=[r for r in rows if r['mode']==mode]
            ignore={'label','wall_seconds','artifact','solver_outputs','solver_measurements','child_latent_sha256','solver_step_reused_measured_velocity_without_net_call'}
            assert {k:v for k,v in a.items() if k not in ignore}=={k:v for k,v in b.items() if k not in ignore}
            for name in actual[mode+'_first']:assert torch.equal(actual[mode+'_first'][name],actual[mode+'_second'][name])
            if index==0:
                assert a['solver_step_reused_measured_velocity_without_net_call'] and len(a['solver_outputs'])==1 and not b['solver_outputs']
                assert len(a['solver_measurements'])==1 and not b['solver_measurements']
                assert a['solver_measurements'][0]['raw_return_tree_sha256']==a['solver_outputs'][0]
                assert a['solver_measurements'][0]['next_sampler_latent']['tree_sha256']==a['child_latent_sha256']
                solver_count+=1
                child=next(o for o in on['origins'] if o['label']=='S23_after_'+mode)
                assert all(r['origin_components']['output']==a['child_latent_sha256'] for r in child['pairs'])
            else:assert not a['solver_outputs'] and not b['solver_outputs']
            result['strict_repeat_groups']+=1
        cells={mode:{k:actual[mode+'_first'][k] for k in ('conditional','unconditional')} for mode in modes}
        metrics=score_four_cells(cells,guidance=7,measurement_space=SPACE)
        teacher=actual['DD_first']['guided'].double();manual={mode:float((actual[mode+'_first']['guided'].double()-teacher).square().mean()) for mode in modes}
        assert all(math.isclose(manual[m],metrics['cells'][m]['guided_velocity_MSE_to_DD'],rel_tol=1e-12,abs_tol=1e-12) for m in modes)
        e0=cells['CC']['conditional'].double()-cells['DD']['conditional'].double();e1=cells['CC']['unconditional'].double()-cells['DD']['unconditional'].double()
        a,b,dot=float(e0.square().mean()),float(e1.square().mean()),float((e0*e1).mean())
        direct=float((8*e0-7*e1).square().mean());energy=64*a+49*b-112*dot
        assert math.isclose(direct,energy,rel_tol=1e-10,abs_tol=1e-10)
        result['origins'].append({'label':origin['label'],'metrics':metrics,'independent_guided_MSE':manual,'independent_signed_energy':energy,
            'actual_capture_gate':origin['capture_gate'],'snapshot_storage':origin['snapshot_storage'],'strict_pair_repeats_and_own_history_verified':True});save()
    assert len(result['origins'])==5 and result['strict_repeat_groups']==20 and tensor_count==120 and len(result['videos'])==2
    assert net_count==224 and solver_count==76
    assert not torch.cuda.is_initialized()
    result.update(net_condition_witnesses_verified=net_count,solver_space_witnesses_verified=solver_count,
        measurement_contract='CFG_MEASUREMENT_SPACES_AND_ACTIVE_CONDITION_V1',status='TEACHER_COMPLETE_TWO_VIDEO_FIVE_STATE_FOUR_CELL_TWO_REPEAT_RAW_AUDIT_AND_CPU_SCORES_NOT_ENDPOINT',
        raw_tensor_count=120,local_CFG_pairs=40,diagnostic_net_calls=80,complete_real_components=1216);save()


if __name__=='__main__':main()
