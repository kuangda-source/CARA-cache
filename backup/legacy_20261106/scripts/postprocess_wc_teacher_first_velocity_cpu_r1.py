"""All12 endpoints, four fresh teachers and original396 C/A controls; CPU only."""
import argparse,importlib.metadata,json,math,os,sys,time
from pathlib import Path
from collections import Counter
from statistics import mean


def main():
    parser=argparse.ArgumentParser()
    for name in ('project','stage'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.teacher_first_velocity_production_r1 import RUN,CONFIG,COUNTS,sha,write
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbid(*args,**kwargs):raise RuntimeError('Teacher CPU audit prohibits CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='TEACHER_FIRST_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not Path('/proc',str(sup['pid'])).exists() and not Path('/proc',str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    before=sha(a.project/'reports/budget.json');dest=a.stage/'CPU-final-results.json'
    assert not dest.exists();started=time.perf_counter()
    result={'status':'TEACHER_FIRST_RAW_AND_FRAME_CPU_RUNNING','scope_counts':COUNTS,
        'parents':[],'teachers':[],'outputs':[],'comparisons':[],'raw_files':0,'raw_tensors':0,'GPU_supervisor':sup,
        'source_revision':sup['source_revision'],'GPU_submissions':0,'ledger_written':False,
        'budget_before_sha256':before,'offline_teacher_not_online_accelerator':True,
        'four_CAL_seed0_not_unseen_confirmation':True,'instrumented_time_not_clean_latency':True}
    save=lambda:write(dest,result);save()
    bindings=json.loads((a.stage/c['baseline_ref']).read_text())['bindings']
    def load(bound):
        path=Path(bound['path']).resolve()
        assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        return torch.load(path,weights_only=True,map_location='cpu')
    def video(bound):
        path=Path(bound['path']).resolve()
        assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        import hashlib
        digest=hashlib.sha256();count=0;meta=probe_video(path)
        with decoded_video(path) as frames:
            for frame,pts,tbase in frames:digest.update(frame.tobytes());count+=1
        assert count==93 and meta['HWC']==[432,768,3]
        return {'artifact':bound,'RGB_sha256':digest.hexdigest(),'frames':count,'probe':meta}
    try:
        if sup['child_exit_code']!=0 or len(runner['runs'])!=4 or any(r['status']!='COMPLETE' for r in runner['runs']):
            result['status']='TEACHER_FIRST_INCOMPLETE_FULL270_SCOPE_RETAINED';save();return
        for parent in runner['runs']:
            scene=parent['scene'];bind=bindings[scene];point=parent['point'];step=point['chosen']['step']
            raw=load(parent['parent_vectors'])
            assert parent['original_parent_all36_guided_equal'] and parent['original_parent_final_actions_equal']
            assert tree_digest(raw['final_latent'])==bind['final_latent_sha256']
            assert [tree_digest(g) for g in raw['guided']]==bind['guided_sha256']
            assert all(bool(torch.isfinite(t).all()) for t in [raw['final_latent']]+raw['guided'])
            result['raw_files']+=1;result['raw_tensors']+=1+len(raw['guided'])
            path=Path(parent['video_path']);bound={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
            audited=video(bound);assert audited['RGB_sha256']==bind['parent_RGB_sha256']
            result['outputs'].append({'scene':scene,'label':'PARENT_PI0','video':audited,
                'final_latent_sha256':parent['final_latent_sha256']})
            event=parent['event'];teacher_record=event['teacher_record'];teacher=load(teacher_record['artifact'])
            assert set(teacher)=={'teacher_velocity','actual_latent','noise','timestep'}
            result['raw_files']+=1;result['raw_tensors']+=5
            assert tree_digest(teacher)==teacher_record['artifact']['tensor_sha256']
            assert tree_digest((teacher['noise'],teacher['actual_latent'],teacher['timestep']))==teacher_record['input_sha256']
            assert tree_digest(teacher['teacher_velocity'])==teacher_record['teacher_velocity_sha256']
            assert event['actual_teacher_pairs']==1 and event['actual_teacher_calls']==2
            assert not event['teacher_committed_to_parent_or_suffix'] and not teacher_record['teacher_committed']
            assert event['only_first_returned_velocity_changed'] and event['physical_first_action']=='CC'
            assert len(event['serial_restores'])==4 and len(teacher_record['serial_restores'])==1
            assert teacher_record['prefix_physical_sha256']==event['prefix_physical_sha256']
            assert teacher_record['prefix_owned_sha256']==event['prefix_owned_sha256']
            assert teacher_record['history']['action']=='DD'
            assert all(h[-1]==step for h in teacher_record['history']['true_D_after'])
            assert parent['actual_pair_computations']==36+2*(37-step)+1
            expected=['TEACHER_FIRST','C_REPLAY'] if c['mirror_order'][[r['name'] for r in c['requests']].index(scene)] else ['C_REPLAY','TEACHER_FIRST']
            assert [b['label'] for b in event['branches']]==expected
            by={b['label']:b for b in event['branches']}
            assert by['C_REPLAY']['first_C_velocity_sha256']==by['TEACHER_FIRST']['first_C_velocity_sha256']
            assert by['C_REPLAY']['first_C_cache_state_sha256']==by['TEACHER_FIRST']['first_C_cache_state_sha256']
            guided_teacher=teacher['teacher_velocity'][0]+7*(teacher['teacher_velocity'][0]-teacher['teacher_velocity'][1])
            for branch in event['branches']:
                tensors=load(branch['artifact'])
                assert set(tensors)=={'final_latent','guided','first_C_velocity'} and tree_digest(tensors)==branch['artifact']['tensor_sha256']
                result['raw_files']+=1;result['raw_tensors']+=3+len(tensors['guided'])
                leaves=[tensors['final_latent']]+tensors['guided']+list(tensors['first_C_velocity'])
                assert all(bool(torch.isfinite(t).all()) for t in leaves+list(teacher['teacher_velocity'])+[teacher['actual_latent'],teacher['noise'],teacher['timestep']])
                assert len(tensors['guided'])==len(branch['actions'])==len(branch['source_policy_tail'])==37-step
                assert [tree_digest(g) for g in tensors['guided']]==branch['guided_sha256']
                assert tree_digest(tensors['final_latent'])==branch['final_latent_sha256']
                assert tree_digest(tensors['first_C_velocity'])==branch['first_C_velocity_sha256']
                assert branch['actions'][0]=='CC' and branch['readout_actions'][0]==branch['first_readout']=='C'
                first=branch['source_policy_tail'][0];assert first['true_D_before']==first['true_D_after']
                assert all(h[-1]==point['chosen']['true_D_anchor'] for h in first['true_D_after'])
                assert first['source_policy']['decision']['reason']=='MATH_EVENT_SUFFIX_FIRST:C'
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in branch['source_policy_tail'][1:])
                for history in branch['source_policy_tail']:
                    if history['action']!='DD':assert history['true_D_before']==history['true_D_after']
                    if history['action']=='PP':assert history['source_policy']['creation_floor_proxy_after']>0 and all(s['kind']=='P' and not s['RA_zero_risk_reset_allowed'] for s in history['working_sources'])
                frames=video(branch['artifact']['video_artifact'])
                if branch['label']=='C_REPLAY':
                    oldC=bind['old_suffixes']['C']
                    assert branch['guided_sha256']==oldC['guided_sha256'] and branch['actions']==oldC['actions']
                    assert branch['final_latent_sha256']==oldC['final_latent_sha256'] and frames['RGB_sha256']==oldC['RGB_sha256']
                    assert not branch['teacher_velocity_injected']
                    assert branch['first_returned_velocity_sha256']==branch['first_C_velocity_sha256']
                else:
                    assert branch['teacher_velocity_injected'] and torch.equal(tensors['guided'][0],guided_teacher)
                    assert branch['first_returned_velocity_sha256']==teacher_record['teacher_velocity_sha256']
                sample=branch['instrumented_suffix_sampling_seconds'];decoder=branch['artifact']['VAE_decoder_seconds']
                assert all(math.isfinite(t) and t>=0 for t in (sample,decoder,branch['research_endpoint_export_seconds']))
                result['outputs'].append({'scene':scene,'label':branch['label'],'video':frames,
                    'final_latent_sha256':branch['final_latent_sha256'],'instrumented_sampling_seconds':sample,
                    'VAE_decoder_seconds':decoder,'sampling_plus_decoder_seconds':sample+decoder,
                    'guarded_writer_seconds':branch['artifact']['guarded_writer_seconds'],
                    'actual_suffix_actions':branch['actions'],'actual_suffix_counts':dict(Counter(branch['actions'])),
                    'raw_artifact':branch['artifact'],'first_returned_velocity_intervened':branch['teacher_velocity_injected']})
            result['teachers'].append({'scene':scene,'step':step,'raw_artifact':teacher_record['artifact'],
                'teacher_velocity_sha256':teacher_record['teacher_velocity_sha256'],
                'strict_same_state_restore_and_first_C_cache_controls_passed':True})
            result['parents'].append({'scene':scene,'point':point,'actual_pair_computations':parent['actual_pair_computations'],
                'all36_parent_guided_actions_final_and93RGB_original_equal':True,'C_REPLAY_all_remaining_original396_equal':True});save()
        assert len(result['outputs'])==12 and len(result['parents'])==len(result['teachers'])==4
        assert sum(p['actual_pair_computations'] for p in result['parents'])==270
        assert result['raw_files']==16 and result['raw_tensors']==314
        resource=a.project/c['LPIPS_resource'];result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        assert result['LPIPS_resource_identity']['server_receipt_sha256']==c['LPIPS_resource_receipt_sha256']
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4' and Path(lpips.__file__).resolve()==(resource/'site/lpips/__init__.py').resolve()
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for parameter in metric.parameters():parameter.requires_grad_(False)
        for output in result['outputs']:
            ref=bindings[output['scene']]['native_video_artifact'];assert sha(ref['path'])==ref['sha256']
            with decoded_video(ref['path']) as left,decoded_video(output['video']['artifact']['path']) as right:
                output['LPIPS']=score_pair(left,right,metric,reference_sha256=ref['sha256'],candidate_sha256=output['video']['artifact']['sha256'])
            save()
        for scene,bind in bindings.items():
            by={row['label']:row for row in result['outputs'] if row['scene']==scene}
            C=by['C_REPLAY'];T=by['TEACHER_FIRST'];A=bind['old_suffixes']['A']
            assert C['LPIPS']['frame_distances']==bind['old_suffixes']['C']['LPIPS']['frame_distances']
            gains=[x-y for x,y in zip(C['LPIPS']['frame_distances'],T['LPIPS']['frame_distances'])]
            result['comparisons'].append({'scene':scene,'point':bind['point'],
                'C_LPIPS':C['LPIPS']['mean_LPIPS'],'T_LPIPS':T['LPIPS']['mean_LPIPS'],'original_A_LPIPS':A['LPIPS']['mean_LPIPS'],
                'Y_quality_C_minus_teacher':C['LPIPS']['mean_LPIPS']-T['LPIPS']['mean_LPIPS'],
                'Y_quality_A_minus_teacher':A['LPIPS']['mean_LPIPS']-T['LPIPS']['mean_LPIPS'],
                'all93_C_minus_teacher_frame_gains':gains,'teacher_better_frames':sum(x>0 for x in gains),
                'teacher_worse_frames':sum(x<0 for x in gains),'equal_frames':sum(x==0 for x in gains),
                'C_counts':C['actual_suffix_counts'],'T_counts':T['actual_suffix_counts'],
                'all93_paired_frames':True,'future_actions_are_velocity_intervention_outcomes':True,
                'offline_teacher_getting_cost_not_free_or_online_acceleration':True,'single_pair_timing_NOT_repeated_clean_speed':True})
        result.update(status='TEACHER_FIRST_ALL4_PARENTS8_SUFFIXES4_TEACHERS12_OUTPUTS_AUDITED_ALL93_SCORED',
            accepted_videos=12,scored_videos=12,CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=False,
            mean_Y_quality=mean(row['Y_quality_C_minus_teacher'] for row in result['comparisons']),
            budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert before==result['budget_after_sha256'];save()
    except BaseException as error:
        result.update(status='TEACHER_FIRST_CPU_TECH_FAILED_FULL270_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise


if __name__=='__main__':main()
