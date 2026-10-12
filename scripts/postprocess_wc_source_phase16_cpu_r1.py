#!/usr/bin/env python3
"""Read all eight parent outputs and all192 real tensors after GPU release."""
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
from collections import Counter


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.source_phase16_production_r1 import RUN,CONFIG,sha,write,COUNTS
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbid(*a,**k):raise RuntimeError('Raw CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='SOURCE_PHASE16_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not Path('/proc/'+str(sup['pid'])).exists() and not Path('/proc/'+str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    before=sha(a.project/'reports/budget.json');dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    result={'status':'SOURCE_PHASE16_RAW_CPU_AUDIT_RUNNING','scope_counts':COUNTS,'parents':[],'points':[],
        'GPU_supervisor':sup,'source_revision':sup['source_revision'],'GPU_submissions':0,'ledger_written':False,
        'budget_before_sha256':before,'real_local_labels_not_endpoint_policy_or_acceleration':True}
    save=lambda:write(dest,result);save();start=time.perf_counter()
    baseline=json.loads((a.stage/c['baseline_ref']).read_text())['bindings'];controls={};cells=Counter();raw_files=raw_tensors=0
    def load(bound):
        path=Path(bound['path']).resolve();assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        return torch.load(path,weights_only=True,map_location='cpu')
    def rgb(path):
        h=hashlib.sha256();n=0;probe=probe_video(path)
        with decoded_video(path) as frames:
            for f,pts,tbase in frames:h.update(f.tobytes());n+=1
        assert n==93 and probe['HWC']==[432,768,3];return h.hexdigest()
    try:
        if sup['child_exit_code']!=0 or len(runner['runs'])!=8 or any(r['status']!='COMPLETE' for r in runner['runs']):
            result['status']='SOURCE_PHASE16_INCOMPLETE_FULL368_SCOPE_RETAINED';save();return
        for row in runner['runs']:
            raw=load(row['parent_vectors']);assert len(raw['guided'])==36 and bool(torch.isfinite(raw['final_latent']).all())
            bind=baseline[row['scene']]
            assert row['old_final_equal'] and row['old_actions_equal'] and tree_digest(raw['final_latent'])==bind['final_latent_sha256']
            assert [tree_digest(g) for g in raw['guided']]==row['guided_sha256']
            video=Path(row['video_path']).resolve();assert video.is_relative_to(root)
            assert sha(bind['video_artifact']['path'])==bind['video_artifact']['sha256']
            h=rgb(video);assert h==bind['decoded_video']['RGB_sha256']==rgb(bind['video_artifact']['path'])
            if row['kind']=='BASELINE':controls[row['scene']]=raw
            else:
                old=controls[row['scene']];assert all(torch.equal(x,y) for x,y in zip(old['guided'],raw['guided'])) and torch.equal(old['final_latent'],raw['final_latent'])
                assert row['all36_guided_final_actions_equal'] and len(row['diagnostic_points'])==4 and row['actual_pair_computations']==56
                for r in row['diagnostic_points']:
                    tensors=load(r['artifact']);assert tree_digest(tensors)==r['artifact']['tensor_sha256']
                    assert set(tensors)=={'DENSE_SAME_STATE','C','D_REFERENCE_A','FUSION_A','NEW_P','actual_latent','timestep'}
                    flat=[t for v in tensors.values() for t in (v if isinstance(v,tuple) else (v,))]
                    assert len(flat)==12 and all(isinstance(t,torch.Tensor) and bool(torch.isfinite(t).all()) for t in flat)
                    raw_files+=1;raw_tensors+=12
                    teacher=tensors['DENSE_SAME_STATE'];energy=(8*teacher[0].double()-7*teacher[1].double()).square().mean().item()
                    losses={}
                    for name in c['labels']:
                        pair=tensors[name];assert len(pair)==2 and all(t.dtype==torch.float32 and t.shape==teacher[b].shape for b,t in enumerate(pair))
                        ec,eu=(pair[b].double()-teacher[b].double() for b in (0,1));mc=ec.square().mean().item();mu=eu.square().mean().item();cross=(ec*eu).mean().item()
                        mse=(8*ec-7*eu).square().mean().item();assert math.isclose(mse,64*mc+49*mu-112*cross,rel_tol=1e-7,abs_tol=1e-10)
                        receipt=next(x for x in r['trial_receipts'] if x['label']==name)
                        losses[name]={'absolute_guided_MSE':mse,'normalized_guided_MSE':mse/max(energy,1e-12),
                            'CFG_gram_absolute':[mc,mu,cross],'full_pair_research_seconds':receipt['full_pair_research_seconds'],
                            'actual_heads':receipt['actual_heads']}
                    point=r['point'];cells[point['source']+'_'+point['phase']]+=1
                    assert len(r['restores'])==len(r['trial_receipts'])==5 and not r['offline_teacher_or_candidates_committed_to_parent']
                    if point['source']=='D':assert all(torch.equal(x,y) for x,y in zip(tensors['D_REFERENCE_A'],tensors['FUSION_A']))
                    P=next(x for x in r['trial_receipts'] if x['label']=='NEW_P')['history']
                    assert P['true_D_before']==P['true_D_after'] and P['source_policy']['creation_floor_proxy_after']>0
                    assert all(s['kind']=='P' and s['created_step']==point['chosen']['step'] and not s['RA_zero_risk_reset_allowed'] for s in P['working_sources'])
                    result['points'].append({'selection':point,'sigma':r['sigma'],'sigma_index':r['sigma_index'],
                        'teacher_guided_energy':energy,'losses':losses,'parent_continues':r['parent_continues'],
                        'raw_artifact':r['artifact'],'input_sha256':r['input_sha256'],
                        'parent_pre_action':r['parent_pre_action'],'cost_boundary':r['cost_boundary'],
                        'actual_C_paid_proxy':next(x for x in r['trial_receipts'] if x['label']=='C')['history']['source_policy']['decision'],
                        'all_candidate_and_teacher_tensors_read':True})
            result['parents'].append({'scene':row['scene'],'kind':row['kind'],'actual_pair_computations':row['actual_pair_computations'],
                'all36_guided_final_actions_equal_to_new_baseline':row['kind']=='BASELINE' or row['all36_guided_final_actions_equal'],
                'old_final_actions_and93RGB_equal':True,'video_RGB_sha256':h});save()
        assert len(result['points'])==16 and raw_files==16 and raw_tensors==192 and all(n==4 for n in cells.values()) and len(cells)==4
        assert sum(r['actual_pair_computations'] for r in result['parents'])==368
        result.update(status='SOURCE_PHASE16_ALL8_PARENTS16_POINTS64_LABELS368_PAIRS192_TENSORS_CPU_AUDITED',
            raw_files=raw_files,raw_tensors=raw_tensors,source_phase_cells=dict(cells),CPU_wall_seconds=time.perf_counter()-start,
            CUDA_initialized=False,budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert result['budget_after_sha256']==before;save()
    except BaseException as e:result.update(status='SOURCE_PHASE16_CPU_AUDIT_TECH_FAILED_FULL_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise


if __name__=='__main__':main()
