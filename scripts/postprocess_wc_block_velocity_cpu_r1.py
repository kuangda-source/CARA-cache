"""Audit all16 saved-velocity endpoints and every compatible full93 pair on CPU."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.block_velocity_production_r1 import CONFIG,RUN,COUNTS,sha,write,LABELS,validate_contract
    from wcomr.block_saved_reference_r1 import load_reference
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    from wcomr.rv0_lpips import score_pair
    from wcomr.lpips_resource_identity import audit
    import torch
    torch.set_num_threads(2)
    def forbid(*args,**kw):raise RuntimeError('B endpoint scoring prohibits CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    assert not torch.cuda.is_initialized()
    c=json.loads((a.stage/CONFIG).read_text());validate_contract(c)
    reg=json.loads((a.stage/'registration.json').read_text());assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='BLOCK_SAVED_VELOCITY_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not Path('/proc',str(sup['pid'])).exists() and not Path('/proc',str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    dest=a.stage/'CPU-final-results.json';assert not dest.exists();started=time.perf_counter();before=sha(a.project/'reports/budget.json')
    result=dict(status='B_SAVED_VELOCITY_ALL16_RAW_AND_ENDPOINT_CPU_RUNNING',scope_counts=COUNTS,outputs=[],parents=[],comparisons=[],
        source_revision=sup['source_revision'],GPU_submissions=0,ledger_written=False,budget_before_sha256=before,
        instrumented_time_not_clean_speed=True,not_actual_B_refresh_or_closed_loop=True,all_four_development_states=True)
    save=lambda:write(dest,result);save()
    binds=json.loads((a.stage/c['baseline_ref']).read_text())['bindings']
    def load(bound):
        path=Path(bound['path']).resolve();assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        return torch.load(path,weights_only=True,map_location='cpu')
    def video(bound):
        path=Path(bound['path']).resolve();assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        digest=hashlib.sha256();count=0;metadata=probe_video(path)
        with decoded_video(path) as frames:
            for frame,pts,tbase in frames:digest.update(frame.tobytes());count+=1
        assert count==93 and metadata['HWC']==[432,768,3]
        return dict(artifact=bound,frames=count,RGB_sha256=digest.hexdigest(),probe=metadata)
    try:
        actual={i:r for i,r in enumerate(runner['runs'])}
        for i,point in enumerate(c['states']):
            row=actual.get(i);step=point['chosen']['step'];scene=point['scene']
            if row is None or row.get('status') not in ('COMPLETE','VIDEO_REJECTED'):
                for label in ('PARENT_PI0',)+LABELS:
                    result['outputs'].append(dict(index=i,scene=scene,step=step,label=label,status='NOT_REACHED_OR_FAILED_FULL_SCOPE_RETAINED'))
                save();continue
            assert row['scene']==scene and row['point']==point
            parent=load(row['parent_vectors']);bind=binds[scene]
            assert [tree_digest(g) for g in parent['guided']]==bind['guided_sha256'] and len(parent['guided'])==36
            assert tree_digest(parent['final_latent'])==bind['final_latent_sha256'] and row['actions']==bind['actions']
            assert all(torch.isfinite(v).all() for v in [parent['final_latent']]+parent['guided'])
            out=dict(index=i,scene=scene,step=step,label='PARENT_PI0',status=row['status'],raw_artifact=row['parent_vectors'])
            if row['status']=='COMPLETE':
                path=Path(row['video_path']);out['video']=video(dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size))
                assert out['video']['RGB_sha256']==bind['parent_RGB_sha256']
            result['outputs'].append(out)
            reference=load_reference(c['point_records'][i],a.project);event=row['event']
            assert event['point']==point and event['first_physical_action']=='CC'
            assert event['actual_teacher_calls']==event['actual_B_executor_calls']==0
            assert event['only_first_returned_velocity_changed'] and event['offline_saved_vectors_not_new_D_or_P_anchor']
            assert len(event['serial_restores'])==6 and row['actual_pair_computations']==36+3*(37-step)
            by={b['label']:b for b in event['branches']};assert set(by)==set(LABELS)
            assert len({b['first_C_cache_state_sha256'] for b in by.values()})==1
            assert len({b['first_C_velocity_sha256'] for b in by.values()})==1
            expected=LABELS[::-1] if c['mirror_order'][i] else LABELS
            assert [b['label'] for b in event['branches']]==list(expected)
            for label,branch in by.items():
                raw=load(branch['artifact']);assert set(raw)=={'final_latent','guided','first_C_velocity'}
                assert tree_digest(raw)==branch['artifact']['tensor_sha256']
                assert len(raw['guided'])==len(branch['actions'])==len(branch['source_policy_tail'])==37-step
                assert [tree_digest(v) for v in raw['guided']]==branch['guided_sha256']
                assert tree_digest(raw['final_latent'])==branch['final_latent_sha256']
                assert tree_digest(raw['first_C_velocity'])==branch['first_C_velocity_sha256']
                assert all(torch.isfinite(v).all() for v in [raw['final_latent']]+raw['guided']+list(raw['first_C_velocity']))
                assert branch['actions'][0]=='CC' and branch['readout_actions'][0]=='C'
                first=branch['source_policy_tail'][0];assert first['true_D_before']==first['true_D_after']
                if label=='C_REPLAY':
                    assert branch['first_returned_velocity_sha256']==branch['first_C_velocity_sha256']
                else:
                    v=reference['vectors'][label];assert branch['first_returned_velocity_sha256']==tree_digest(v)
                    assert torch.equal(raw['guided'][0],v[0]+7*(v[0]-v[1]))
                for h in branch['source_policy_tail']:
                    if h['action']!='DD':assert h['true_D_before']==h['true_D_after']
                    if h['action']=='PP':assert h['source_policy']['creation_floor_proxy_after']>0
                artifact=branch['artifact'];out=dict(index=i,scene=scene,step=step,label=label,status=artifact['video_status'],raw_artifact=artifact,
                    actual_suffix_counts=dict(Counter(branch['actions'])),instrumented_sampling_seconds=branch['instrumented_suffix_sampling_seconds'],VAE_decoder_seconds=artifact['VAE_decoder_seconds'])
                if artifact['video_artifact'] is not None:out['video']=video(artifact['video_artifact'])
                result['outputs'].append(out)
            result['parents'].append(dict(index=i,scene=scene,step=step,actual_pair_computations=row['actual_pair_computations'],all_parent_controls=True,first_C_states_equal=True));save()
        assert len(result['outputs'])==16
        if sup['child_exit_code']!=0 or len(result['parents'])!=4:
            result['status']='B_SAVED_VELOCITY_INCOMPLETE_FULL16_SCOPE_RETAINED';save();return
        assert sum(p['actual_pair_computations'] for p in result['parents'])==312
        resource=a.project/c['LPIPS_resource'];result['LPIPS_resource_identity']=audit(resource,sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0,str(resource/'site'));import lpips
        assert importlib.metadata.version('lpips')=='0.1.4'
        metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
        for v in metric.parameters():v.requires_grad_(False)
        for row in result['outputs']:
            if 'video' not in row:continue
            native=binds[row['scene']]['native_video_artifact'];assert sha(native['path'])==native['sha256']
            with decoded_video(native['path']) as left,decoded_video(row['video']['artifact']['path']) as right:
                row['LPIPS']=score_pair(left,right,metric,reference_sha256=native['sha256'],candidate_sha256=row['video']['artifact']['sha256'])
            save()
        for candidate,baseline in [('DENSE_VELOCITY','C_REPLAY'),('L2_VELOCITY','C_REPLAY'),('L2_VELOCITY','DENSE_VELOCITY')]:
            vals=[]
            for i,point in enumerate(c['states']):
                lookup={r['label']:r for r in result['outputs'] if r['index']==i and 'LPIPS' in r}
                if candidate not in lookup or baseline not in lookup:
                    vals.append(dict(index=i,scene=point['scene'],step=point['chosen']['step'],status='MISSING_OR_REJECTED_RETAINED'));continue
                x,y=lookup[candidate]['LPIPS']['mean_LPIPS'],lookup[baseline]['LPIPS']['mean_LPIPS']
                vals.append(dict(index=i,scene=point['scene'],step=point['chosen']['step'],status='SCORED',candidate_LPIPS=x,baseline_LPIPS=y,LPIPS_change_percent=100*(x/y-1) if y>0 else None))
            done=[v for v in vals if v['status']=='SCORED']
            result['comparisons'].append(dict(candidate=candidate,baseline=baseline,states=vals,denominator=4,scored_states=len(done),
                complete_four_state_equal_candidate_LPIPS=mean(v['candidate_LPIPS'] for v in done) if len(done)==4 else None,
                complete_four_state_equal_baseline_LPIPS=mean(v['baseline_LPIPS'] for v in done) if len(done)==4 else None))
        scored=sum('LPIPS' in r for r in result['outputs'])
        result.update(status='B_SAVED_VELOCITY_ALL4_PARENTS12_SUFFIXES16_VIDEOS_AUDITED_ALL93_SCORED' if scored==16 else 'B_SAVED_VELOCITY_ALL16_SCOPE_REJECTIONS_RETAINED',
            scored_videos=scored,CPU_wall_seconds=time.perf_counter()-started,CUDA_initialized=False,budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert result['budget_after_sha256']==before;save()
    except BaseException as error:
        result.update(status='B_SAVED_VELOCITY_CPU_AUDIT_FAILED_FULL16_RETAINED',error_type=type(error).__name__,error=str(error));save();raise


if __name__=='__main__':main()
