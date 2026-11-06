#!/usr/bin/env python3
"""Read every isolated F/B raw tensor and unchanged parent; then CPU F analysis."""
import argparse,hashlib,json,math,os,statistics,subprocess,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    from wcomr.fb_probe_production_r1 import RUN,CONFIG,sha,write,COUNTS,validate_contract
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import decoded_video,probe_video
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbid(*a,**k):raise RuntimeError('F/B CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    c=json.loads((a.stage/CONFIG).read_text());validate_contract(c)
    reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    root=(a.project/'outputs'/RUN).resolve();sup=json.loads((root/'supervisor.json').read_text())
    assert sup['status']=='FB_PROBE_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    # This CPU process is a child of the settled supervisor, which waits for
    # CPU completion. Only the original GPU child must already be absent.
    assert not Path('/proc/'+str(sup['child_pid'])).exists()
    runner=json.loads((root/'runner.json').read_text());assert sha(root/'runner.json')==sup['runner_sha256']
    before=sha(a.project/'reports/budget.json');dest=a.stage/'CPU-final-results.json';assert not dest.exists()
    result={'status':'FB_PROBE_RAW_CPU_AUDIT_RUNNING','scope_counts':COUNTS,'parents':[],'points':[],
        'B_points':[],'source_revision':sup['source_revision'],'GPU_submissions':0,'ledger_written':False,
        'budget_before_sha256':before,'isolated_not_mainline_or_endpoint_acceleration':True}
    save=lambda:write(dest,result);save();start=time.perf_counter()
    baseline=json.loads((a.stage/c['baseline_ref']).read_text())['bindings'];controls={}
    old392=json.loads((a.stage/c['old_labels_capture_ref']).read_text())
    old392_parents={v['scene']:v for v in old392['runner']['runs'] if v['kind']=='BASELINE'}
    oldpoints={(v['selection']['scene'],v['selection']['chosen']['step']):v for v in c['old_points']}
    raw_files=raw_tensors=0
    def load(bound):
        path=Path(bound['path']).resolve()
        assert path.is_relative_to(root) and sha(path)==bound['sha256'] and path.stat().st_size==bound['bytes']
        raw=torch.load(path,weights_only=True,map_location='cpu')
        if 'tensor_sha256' in bound:assert tree_digest(raw)==bound['tensor_sha256']
        return raw
    def rgb(path):
        h=hashlib.sha256();n=0;probe=probe_video(path)
        with decoded_video(path) as frames:
            for frame,pts,tbase in frames:h.update(frame.tobytes());n+=1
        assert n==93 and probe['HWC']==[432,768,3];return h.hexdigest()
    try:
        if sup['child_exit_code']!=0 or len(runner['runs'])!=8 or any(r['status']!='COMPLETE' for r in runner['runs']):
            raise ValueError('Incomplete full432 scope retained; no partial success')
        for row in runner['runs']:
            raw=load(row['parent_vectors']);assert len(raw['guided'])==36 and torch.isfinite(raw['final_latent']).all()
            bind=baseline[row['scene']]
            assert row['old_final_equal'] and row['old_actions_equal'] and tree_digest(raw['final_latent'])==bind['final_latent_sha256']
            assert [tree_digest(g) for g in raw['guided']]==row['guided_sha256']
            oldrow=old392_parents[row['scene']]
            assert row['all36_guided_final_actions_equal_original392'] and row['guided_sha256']==oldrow['guided_sha256']
            assert row['actions']==oldrow['actions'] and row['final_latent_sha256']==oldrow['final_latent_sha256']
            video=Path(row['video_path']).resolve();assert video.is_relative_to(root)
            assert sha(bind['video_artifact']['path'])==bind['video_artifact']['sha256']
            h=rgb(video);assert h==bind['decoded_video']['RGB_sha256']==rgb(bind['video_artifact']['path'])
            if row['kind']=='BASELINE':controls[row['scene']]=raw
            else:
                old=controls[row['scene']]
                assert all(torch.equal(x,y) for x,y in zip(old['guided'],raw['guided'])) and torch.equal(old['final_latent'],raw['final_latent'])
                assert row['all36_guided_final_actions_equal'] and len(row['diagnostic_points'])==4
                expected=36+36*sum(v['scene']==row['scene'] for v in c['b_points'])
                assert row['actual_pair_computations']==expected
                for r in row['diagnostic_points']:
                    op=oldpoints[(r['scene'],r['step'])]
                    assert r['parent_control_pass'] and r['input_sha256']==op['input_sha256']
                    assert list(r['parent_pre_action'])==op['parent_pre_action'] and r['raw_label_artifact']==op['raw_artifact']
                    assert not r['offline_committed_to_parent']
                    tensors=load(r['artifact']);raw_files+=1
                    flat=[t for pair in tensors.values() for t in pair]
                    assert all(isinstance(t,torch.Tensor) and torch.isfinite(t).all() for t in flat)
                    raw_tensors+=len(flat)
                    assert all(k in tensors for k in ('F_current','F_source'))
                    if r['b_trials']:
                        assert len(r['b_trials'])==36 and len(r['restores'])==36
                        assert set(tensors)=={'F_current','F_source'}|{f'{m}_repeat{j}' for m in c['B_config']['modes'] for j in range(4)}
                        oldpath=Path(op['raw_artifact']['path']).resolve()
                        assert oldpath.is_relative_to((a.project/'outputs').resolve()) and sha(oldpath)==op['raw_artifact']['sha256']
                        oldraw=torch.load(oldpath,weights_only=True,map_location='cpu')
                        assert tree_digest(oldraw)==op['raw_artifact']['tensor_sha256']
                        truth=tensors['DENSE_PLAIN_repeat0'];summaries=[]
                        assert all(torch.equal(x,y) for x,y in zip(truth,oldraw['DENSE_SAME_STATE']))
                        for mode in c['B_config']['modes']:
                            rows=[v for v in r['b_trials'] if v['mode']==mode]
                            assert {v['repeat'] for v in rows}==set(range(4))
                            assert sum(v['warmup'] for v in rows)==1
                            timings=[v['full_pair_seconds'] for v in rows if not v['warmup']]
                            assert len(timings)==3 and all(math.isfinite(x) and x>0 for x in timings)
                            value=tensors[f'{mode}_repeat0']
                            for rep in range(4):
                                target=truth if mode.startswith('DENSE_') else value
                                assert all(torch.equal(x,y) for x,y in zip(tensors[f'{mode}_repeat{rep}'],target))
                            ec,eu=(value[b].double()-truth[b].double() for b in (0,1))
                            mse=(8*ec-7*eu).square().mean().item()
                            summaries.append({'mode':mode,'absolute_guided_MSE':mse,'timed_seconds':timings,
                                'median_seconds':statistics.median(timings),'min_seconds':min(timings),'max_seconds':max(timings),
                                'warmup_seconds':next(v['full_pair_seconds'] for v in rows if v['warmup']),
                                'all_four_trial_receipts':rows,
                                'not_clean_video_speed':True})
                        dense=next(x for x in summaries if x['mode']=='DENSE_PLAIN')['median_seconds']
                        for s in summaries:
                            s['DENSE_PLAIN_over_candidate_median']=dense/s['median_seconds']
                            mode=s['mode']
                            baseline_mode=('DENSE_P0_STATE' if mode.startswith('P0_') else
                                'DENSE_M8_STATE' if mode.startswith('M8_') else
                                'DENSE_L2_STATE' if mode=='L2' else mode)
                            price=next(x for x in summaries if x['mode']==baseline_mode)['median_seconds']
                            s['matching_stateful_D_baseline']=baseline_mode
                            s['matching_stateful_D_over_candidate_median']=price/s['median_seconds']
                        result['B_points'].append({'scene':r['scene'],'step':r['step'],'summaries':summaries,
                            'source_state_sha256':r['source_state_sha256'],'true_D_state_sha256':r['true_D_state_sha256'],
                            'same_state_DENSE_PLAIN_matches_original392_teacher_exact':True})
                    else:assert set(tensors)=={'F_current','F_source'} and not r['restores']
                    result['points'].append(r)
            result['parents'].append({'scene':row['scene'],'kind':row['kind'],
                'actual_pair_computations':row['actual_pair_computations'],'old_final_actions_all36_guided_and93RGB_equal':True,
                'video_RGB_sha256':h});save()
        assert len(result['points'])==16 and len(result['B_points'])==4 and raw_files==16
        assert raw_tensors==16*4+4*36*2 and sum(v['actual_pair_computations'] for v in result['parents'])==432
        result.update(status='FB_PROBE_ALL8_PARENTS_F16_B4_432PAIRS_RAW_CPU_AUDITED',
            raw_files=raw_files,raw_tensors=raw_tensors);save()
        command=[sys.executable,str(a.stage/'scripts/analyze_wc_spectral_probe_r1.py'),
            '--capture',str(dest),'--labels',str(a.stage/c['old_labels_capture_ref']),
            '--parameters',str(a.stage/c['F_analysis_parameters_ref']),'--project',str(a.project),
            '--output',str(a.stage/'F-analysis.json')]
        subprocess.run(command,check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
        analysis=json.loads((a.stage/'F-analysis.json').read_text())
        assert analysis['status']=='F16_CPU_RAW_VERIFIED_PROMPT_LOPO_CA_SCREEN_NOT_DEPLOYMENT'
        result.update(status='FB_PROBE_ALL432_F16_B4_RAW_AND_LOCAL_ANALYSIS_COMPLETE_NOT_ENDPOINT',
            F_analysis_sha256=sha(a.stage/'F-analysis.json'),CPU_wall_seconds=time.perf_counter()-start,
            CUDA_initialized=False,budget_after_sha256=sha(a.project/'reports/budget.json'))
        assert result['budget_after_sha256']==before;save()
    except BaseException as e:
        result.update(status='FB_PROBE_CPU_AUDIT_TECH_FAILED_FULL_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise


if __name__=='__main__':main()
