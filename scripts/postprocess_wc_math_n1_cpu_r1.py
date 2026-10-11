#!/usr/bin/env python3
"""Released-GPU raw audit and related-error fitting; no generator or CUDA."""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from statistics import mean


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.math_n1_production_r1 import RUN,CONFIG,sha,write
    from wcomr.math_source_fusion_r1 import fusion_gain,fusion_risk
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('N1 CPU audit prohibits CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    c=json.loads((a.stage/CONFIG).read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert not Path('/proc/'+str(sup['pid'])).exists() and not Path('/proc/'+str(sup['child_pid'])).exists()
    assert sup['status']=='MATH_N1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    ledger_sha=sha(a.project/'reports/budget.json');runner=json.loads((root/'runner.json').read_text())
    assert sha(root/'runner.json')==sup['runner_sha256']
    dest=a.stage/'CPU-final-results.json';assert not dest.exists();start=time.perf_counter()
    result={'status':'N1_CPU_RAW_AUDIT_RUNNING','scope_counts':c['scope_counts'],'parents':[],
        'points':[],'source_revision':sup['source_revision'],'GPU_supervisor':sup,
        'budget_before_sha256':ledger_sha,'GPU_submissions':0,'ledger_written':False}
    save=lambda:write(dest,result);save()
    index=json.loads((a.stage/c['state_index_ref']).read_text())
    originals=json.loads((a.stage/c['original_guided_bindings_ref']).read_text())['bindings']
    def load(bound):
        path=Path(bound['path']).resolve();assert path.is_relative_to(root)
        assert sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        return torch.load(path,weights_only=True,map_location='cpu')
    try:
        if sup['child_exit_code']!=0 or len(runner['runs'])!=4 or any(r['status']!='COMPLETE' for r in runner['runs']):
            result['status']='N1_INCOMPLETE_TECHNICAL_SCOPE_RETAINED';save();return
        for row in runner['runs']:
            assert row['old_final_equal'] and row['old_actions_equal'] and row['old_all36_guided_equal']
            raw=load(row['parent_vectors']);final=raw['final_latent'];guided=raw['guided']
            assert bool(torch.isfinite(final).all()) and len(guided)==36
            assert tree_digest(final)==index['original_parent_bindings'][row['scene']]['final_latent_sha256']
            assert [tree_digest(g) for g in guided]==originals[row['scene']]['guided_sha256']
            oldvideo=index['original_parent_bindings'][row['scene']]['video_artifact']
            assert sha(oldvideo['path'])==oldvideo['sha256']
            hashes=[]
            for video in (row['video_path'],oldvideo['path']):
                h=hashlib.sha256();count=0;probe=probe_video(video)
                with decoded_video(video) as frames:
                    for f,pts,tbase in frames:h.update(f.tobytes());count+=1
                assert count==93;hashes.append(h.hexdigest())
            assert hashes[0]==hashes[1]
            result['parents'].append({'scene':row['scene'],'all36_guided_final_actions_and93RGB_equal':True,
                'actual_pair_computations':row['actual_pair_computations'],'video_RGB_sha256':hashes[0]})
            for record in row['diagnostic_points']:
                payload=load(record['artifact']);assert tree_digest(payload)==record['artifact']['tensor_sha256']
                assert record['teacher_head_calls']==2 and len(record['serial_restores'])==3
                assert record['deployed_variant']=='D_REFERENCE_UNIT' and not record['teacher_committed_to_parent']
                teacher=payload['DENSE_SAME_STATE'];energy=(8*teacher[0]-7*teacher[1]).double().square().mean().item()
                denominator=max(energy,c['fit_target_energy_epsilon']);errors={};losses={};grams={}
                for name in ('OFFICIAL_C','D_REFERENCE_UNIT','P_REFERENCE_UNIT','FUSION_HALF_UNIT'):
                    pair=payload[name];assert len(pair)==2 and all(t.dtype==torch.float32 and t.shape==teacher[0].shape and bool(torch.isfinite(t).all()) for t in pair)
                    ec,eu=(pair[b]-teacher[b] for b in (0,1));eg=(8*ec-7*eu).double()
                    loss=eg.square().mean().item();assert math.isclose(loss,record['guided_moments'][name]['base_guided_MSE'],rel_tol=2e-5,abs_tol=1e-8)
                    mc,mu,cross=ec.double().square().mean().item(),eu.double().square().mean().item(),(ec.double()*eu.double()).mean().item()
                    assert math.isclose(64*mc+49*mu-112*cross,loss,rel_tol=2e-5,abs_tol=1e-8)
                    grams[name]=[mc/denominator,mu/denominator,cross/denominator]
                    losses[name]={'MSE':loss,'normalized_guided_MSE':loss/denominator}
                    errors[name]=eg
                old,working=errors['D_REFERENCE_UNIT'],errors['P_REFERENCE_UNIT']
                A=old.square().mean().item()/denominator;B=working.square().mean().item()/denominator
                C=(old*working).mean().item()/denominator
                assert math.isclose(fusion_risk(A,B,C,.5),losses['FUSION_HALF_UNIT']['normalized_guided_MSE'],rel_tol=2e-5,abs_tol=1e-8)
                if record['point']['source']=='D':
                    assert all(torch.equal(x,y) for x,y in zip(payload['D_REFERENCE_UNIT'],payload['P_REFERENCE_UNIT']))
                point={'selection':record['point'],'sigma':record['sigma'],'sigma_index':record['sigma_index'],
                    'teacher_guided_energy':energy,'losses':losses,'normalized_CFG_grams':grams,
                    'related_error_moments':{'A':A,'B':B,'C':C},'local_oracle_gain':fusion_gain(A,B,C),
                    'raw_artifact':record['artifact'],'all_candidate_and_teacher_tensors_read':True}
                result['points'].append(point);save()
        assert len(result['points'])==12 and sum(r['actual_pair_computations'] for r in result['parents'])==180
        P=[r for r in result['points'] if r['selection']['source']=='P'];D=[r for r in result['points'] if r['selection']['source']=='D']
        assert len(P)==8 and len(D)==4
        moments={k:mean(p['related_error_moments'][k] for p in P) for k in ('A','B','C')}
        fit=fusion_gain(**moments);gain=fit['gamma']
        fit.update(target=c['fit_target'],energy_epsilon=c['fit_target_energy_epsilon'],
            training_scenes=4,primary_states=8,moments=moments,
            expected_old_loss=moments['A'],expected_fitted_loss=fusion_risk(**moments,gamma=gain))
        folds=[]
        for scene in index['scenes']:
            train=[p for p in P if p['selection']['scene']!=scene];test=[p for p in P if p['selection']['scene']==scene]
            m={k:mean(p['related_error_moments'][k] for p in train) for k in ('A','B','C')};g=fusion_gain(**m)['gamma']
            folds.append({'held_scene':scene,'trained_on_other_scenes_gamma':g,
                'held_old_loss':mean(p['related_error_moments']['A'] for p in test),
                'held_fused_loss':mean(fusion_risk(**p['related_error_moments'],gamma=g) for p in test)})
        fit['leave_one_scene_out']=folds
        result.update(status='N1_ALL4_PARENTS12_POINTS48_READOUTS180_PAIRS_CPU_AUDITED',
            global_related_gain=fit,CPU_wall_seconds=time.perf_counter()-start,
            CUDA_initialized=False,budget_after_sha256=sha(a.project/'reports/budget.json'),
            method_endpoint_or_new_policy_claim=False)
        assert result['budget_after_sha256']==ledger_sha;save()
    except BaseException as e:
        result.update(status='N1_CPU_AUDIT_TECH_FAILED_FULL12_RETAINED',error_type=type(e).__name__,error=str(e))
        save();raise

if __name__=='__main__':main()
