#!/usr/bin/env python3
"""Reconstruct all four complete teacher-first interventions from 93 frames.

Consumes saved accepted CPU terminal receipts only. Does not inspect a live
job, load weights/tensors, score new frames or write a GPU ledger.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def mean(xs): return math.fsum(xs)/len(xs)


def analyse(capture, original):
    c,old=capture['final'],original['final']
    if (c['status']!='TEACHER_FIRST_ALL4_PARENTS8_SUFFIXES4_TEACHERS12_OUTPUTS_AUDITED_ALL93_SCORED'
            or old['status']!='PI0_SUFFIX8_ALL4_PARENTS8_SUFFIXES12_OUTPUTS_AUDITED_ALL93_SCORED'
            or c['accepted_videos']!=12 or c['scored_videos']!=12
            or old['accepted_videos']!=12 or old['scored_videos']!=12):
        raise ValueError('Both original full four-scene cards and all93 scoring required')
    for source in (capture,original):
        verified=source.get('payload_all_verified',source.get('payload_verified'))
        if isinstance(verified,dict):verified=bool(verified) and all(verified.values())
        if (source['supervisor']['child_exit_code']!=0 or source['post_exit']['exit_code']!=0
                or any(source['original_processes'].values()) or verified is not True):
            raise ValueError('Original terminal/raw/payload acceptance absent')
    assert c['scope_counts']['pairs']==270 and c['scope_counts']['teacher_pairs']==4
    assert c['raw_files']==16 and c['raw_tensors']==314
    assert old['scope_counts']['pairs']==266 and old['scope_counts']['teacher_pairs']==0
    current={(r['scene'],r['label']):r for r in c['outputs']}
    previous={(r['scene'],r['label']):r for r in old['outputs']}
    scenes=[r['scene'] for r in c['parents']]
    assert len(set(scenes))==4 and len(current)==len(previous)==12
    assert set(scenes)=={r['scene'] for r in old['parents']}
    teachers={r['scene']:r for r in c['teachers']}
    runs={r['scene']:r for r in capture['runner']['runs']}
    stored={r['scene']:r for r in c['comparisons']}
    rows=[]
    def frames(r):
        d=r['LPIPS'];v=d['frame_distances']
        assert len(v)==d['frames']==r['video']['frames']==93
        assert all(math.isfinite(x) and x>=0 for x in v)
        assert math.isclose(mean(v),d['mean_LPIPS'],abs_tol=1e-14)
        assert d['candidate_sha256']==r['video']['artifact']['sha256']
        return v
    for parent in c['parents']:
        scene=parent['scene'];point=parent['point']
        assert parent['all36_parent_guided_actions_final_and93RGB_original_equal']
        assert parent['C_REPLAY_all_remaining_original396_equal']
        assert teachers[scene]['strict_same_state_restore_and_first_C_cache_controls_passed']
        run=runs[scene];event=run['event'];branches={b['label']:b for b in event['branches']}
        assert event['only_first_returned_velocity_changed'] and event['physical_first_action']=='CC'
        assert not event['teacher_committed_to_parent_or_suffix'] and event['actual_teacher_pairs']==1
        cb,tb=branches['C_REPLAY'],branches['TEACHER_FIRST']
        assert cb['first_C_cache_state_sha256']==tb['first_C_cache_state_sha256']
        assert cb['first_C_velocity_sha256']==tb['first_C_velocity_sha256']
        assert tb['teacher_velocity_injected'] and not cb['teacher_velocity_injected']
        assert tb['first_returned_velocity_sha256']==teachers[scene]['teacher_velocity_sha256']
        C=current[(scene,'C_REPLAY')];T=current[(scene,'TEACHER_FIRST')]
        A=previous[(scene,'DEFAULT_PI0' if point['default_readout']=='A' else 'ALTERNATIVE')]
        originalC=previous[(scene,'ALTERNATIVE' if point['default_readout']=='A' else 'DEFAULT_PI0')]
        assert C['video']['RGB_sha256']==originalC['video']['RGB_sha256']
        assert C['final_latent_sha256']==originalC['final_latent_sha256']
        fC,fT,fA=frames(C),frames(T),frames(A)
        assert C['LPIPS']['pts']==T['LPIPS']['pts']==A['LPIPS']['pts']
        assert len({r['LPIPS']['reference_sha256'] for r in (C,T,A,originalC)})==1
        lc,lt,la=mean(fC),mean(fT),mean(fA)
        gains=[x-y for x,y in zip(fC,fT)]
        d=stored[scene]
        assert all(math.isclose(v,d[k],abs_tol=1e-14) for v,k in
            [(lc,'C_LPIPS'),(lt,'T_LPIPS'),(la,'original_A_LPIPS')])
        assert gains==d['all93_C_minus_teacher_frame_gains']
        countsC={a:cb['actions'].count(a) for a in sorted(set(cb['actions']))}
        countsT={a:tb['actions'].count(a) for a in sorted(set(tb['actions']))}
        assert countsC==d['C_counts'] and countsT==d['T_counts']
        rows.append(dict(scene=scene,source=point['source'],phase=point['phase'],
            step=point['chosen']['step'],source_age=point['chosen']['age'],
            plain_C_LPIPS=lc,source_aligned_A_LPIPS=la,teacher_first_LPIPS=lt,
            teacher_distortion_drop_vs_C_percent=100*(lc-lt)/lc,
            teacher_distortion_drop_vs_A_percent=100*(la-lt)/la,
            teacher_better_frames=sum(v>0 for v in gains),
            teacher_worse_frames=sum(v<0 for v in gains),equal_frames=sum(v==0 for v in gains),
            all93_C_minus_teacher=gains,C_suffix_counts=countsC,teacher_suffix_counts=countsT,
            C_deep_pairs=sum(countsC.get(a,0) for a in ('DD','PP')),
            teacher_deep_pairs=sum(countsT.get(a,0) for a in ('DD','PP')),
            first_C_cache_control_passed=True,teacher_velocity_only_intervention=True,
            matched_Native_sha256=C['LPIPS']['reference_sha256']))
    aggregate={name:mean([r[key] for r in rows]) for name,key in
        [('C','plain_C_LPIPS'),('A','source_aligned_A_LPIPS'),('TEACHER','teacher_first_LPIPS')]}
    gain=aggregate['C']-aggregate['TEACHER']
    assert math.isclose(gain,c['mean_Y_quality'],abs_tol=1e-14)
    groups=[]
    for source in ('D','P'):
        subset=[r for r in rows if r['source']==source]
        assert len(subset)==2
        qC=mean([r['plain_C_LPIPS'] for r in subset]);qT=mean([r['teacher_first_LPIPS'] for r in subset])
        groups.append(dict(source=source,states=2,C_LPIPS=qC,teacher_LPIPS=qT,
            teacher_distortion_drop_percent=100*(qC-qT)/qC,
            source_effect_not_identified_separately_from_scene_phase=True))
    return dict(status='TEACHER_FIRST_COMPLETE4_ALL93_RECONSTRUCTED_CPU_NOT_NEW_GPU',
        scope_counts=c['scope_counts'],rows=rows,scene_equal_mean_LPIPS=aggregate,
        teacher_distortion_drop_vs_C_percent=100*gain/aggregate['C'],
        teacher_distortion_drop_vs_A_percent=100*(aggregate['A']-aggregate['TEACHER'])/aggregate['A'],
        teacher_better_scenes_vs_C=sum(r['teacher_first_LPIPS']<r['plain_C_LPIPS'] for r in rows),
        teacher_better_scenes_vs_A=sum(r['teacher_first_LPIPS']<r['source_aligned_A_LPIPS'] for r in rows),
        source_condition_descriptive_groups=groups,
        completed_card_GPUh=capture['supervisor']['wall_seconds']/3600,
        original_raw_and_tensor_audit_from_accepted_terminal_post=True,
        all93_statistics_recomputed_in_this_analysis=True, live_job_inspected=False,
        GPU_submissions=0,ledger_written=False,unseen_or_matched_cost_or_physics_claim=False)


def main():
    p=argparse.ArgumentParser()
    for n in ('capture','original','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    result=analyse(json.loads(a.capture.read_text()),json.loads(a.original.read_text()))
    result['inputs_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in (a.capture,a.original)}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','scene_equal_mean_LPIPS',
        'teacher_distortion_drop_vs_C_percent','teacher_better_scenes_vs_C',
        'teacher_better_scenes_vs_A','completed_card_GPUh')}))


if __name__=='__main__':main()
