"""Independently reconstruct full H1 quality/time/actual action comparisons."""
import argparse,hashlib,json,math
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
METHODS=('NATIVE','RA','A_NO_P','P_OFF','TABLE_PHASE_H1','TABLE_POOLED_H1')
PAIRS=(('TABLE_PHASE_H1','RA'),('TABLE_PHASE_H1','A_NO_P'),('TABLE_PHASE_H1','P_OFF'),
    ('TABLE_PHASE_H1','TABLE_POOLED_H1'),('TABLE_POOLED_H1','RA'),
    ('TABLE_POOLED_H1','A_NO_P'),('TABLE_POOLED_H1','P_OFF'),('P_OFF','A_NO_P'),('A_NO_P','RA'))


def reconstruct(capture):
    final=capture.get('final');sup=capture.get('supervisor')
    if not final or final['status']!='SOURCE_PHASE_H1_FULL24_SCIENCE_ALL36_AUDITED_93FRAME_SCORED':
        raise ValueError('Complete36 raw/24 scientific/all93 scored evidence required')
    if (sup['child_exit_code']!=0 or capture['post_exit']['exit_code']!=0
            or any(capture['original_processes'].values()) or not capture['kernel_lock_free']
            or not all(capture['payload_verified'].values())):
        raise ValueError('Original source and complete terminal/release controls required')
    assert final['scored_scientific_paths']==24 and final['accepted_paths']==36
    assert final['budget_before_sha256']==final['budget_after_sha256']==capture['ledger_sha256']
    assert len(final['warm_repeat_controls'])==6 and all(c['warm_repeats_outputs_actions_RGB_equal'] and c['same_scene_formal_repeat_equal'] for c in final['warm_repeat_controls'])
    assert len(final['original_baseline_controls'])==16 and all(c['status']=='PASS_ORIGINAL_FINAL_ACTIONS_FULL93RGB_EQUAL' for c in final['original_baseline_controls'])
    timed=[r for r in final['rows'] if r['section']=='TIMED'];scenes=list(dict.fromkeys(r['scene'] for r in timed))
    assert len(timed)==24 and len(scenes)==4
    assert len({(r['scene'],r['method']) for r in timed})==24
    counts=[]
    for row in timed:
        assert row['status']=='COMPLETE' and row['endpoint_audit']=='PASS'
        assert row['decoded_video']['frames']==93
        assert row['core_seconds']>0 and math.isfinite(row['core_seconds'])
        assert row['in_timing_hashes']==row['in_timing_guided_copies']==row['research_checkpoints']==0
        frames=row['LPIPS']['frame_distances'];assert len(frames)==93 and all(math.isfinite(x) and x>=0 for x in frames)
        assert math.isclose(mean(frames),row['LPIPS']['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        if row['method']=='NATIVE':assert all(x==0 for x in frames) and row['actions']==['DD']*36
        if row['method'].startswith('TABLE_'):
            hist=row['compact_source_history'];assert len(hist)==36
            assert [h['action'] for h in hist]==row['actions']
            actual=Counter(h['action'] for h in hist)
            readouts=Counter(h['readout'] for h in hist if h['action']=='CC')
            assert set(readouts)<={'C','A'}
            reasons=Counter(h['decision']['reason'] for h in hist)
            for h in hist:
                d=h['decision'];event=h['event']
                assert d['action']*2==h['action'] and d['step']==h['step']
                assert not event['absolute_error_written_into_root_accumulator']
                assert event['actual_online_candidate_evaluations']==event['actual_online_teacher_calls']==0
                assert event['source_before']==d['state_before'][1]
                if h['action']=='CC':assert h['heads']==(0 if h['readout']=='C' else 2 if event['source_before']=='D' else 4)
            rebuilt={'DD':actual['DD'],'PP':actual['PP'],'C_plain':readouts['C'],'A':readouts['A']}
            assert sum(rebuilt.values())==36
            assert all(row['counts'][key]==value for key,value in rebuilt.items())
            counts.append({'scene':row['scene'],'method':row['method'],**rebuilt,
                'protected_D':sum(h['action']=='DD' and h['protected'] for h in hist),
                'optimizer_D':sum(h['event']['optimizer_selected_D'] for h in hist),
                'nonprotected_nonoptimizer_D':sum(h['action']=='DD' and not h['protected'] and not h['event']['optimizer_selected_D'] for h in hist),
                'actual_extra_candidate_heads':sum(h['heads'] for h in hist),'reasons':dict(reasons)})
    summaries=[]
    for method in METHODS:
        rows=[r for r in timed if r['method']==method];assert len(rows)==4
        summaries.append({'method':method,'mean_core_seconds':mean(r['core_seconds'] for r in rows),
            'mean_LPIPS':mean(r['LPIPS']['mean_LPIPS'] for r in rows),
            'per_scene':[{'scene':r['scene'],'core_seconds':r['core_seconds'],
                'LPIPS':r['LPIPS']['mean_LPIPS'],
                'speedup_Native_over_method':next(v['core_seconds'] for v in timed if v['scene']==r['scene'] and v['method']=='NATIVE')/r['core_seconds']} for r in rows]})
    comparisons=[]
    for candidate,base in PAIRS:
        stored=next(c for c in final['comparisons'] if c['candidate']==candidate and c['baseline']==base)
        assert stored['denominator']==stored['scored_scenes']==4
        values=[]
        for scene in scenes:
            by={r['method']:r for r in timed if r['scene']==scene};a,b=by[candidate],by[base]
            qa,qb=a['LPIPS']['mean_LPIPS'],b['LPIPS']['mean_LPIPS'];ta,tb=a['core_seconds'],b['core_seconds']
            old=next(v for v in stored['scene_rows'] if v['scene']==scene)
            change=100*(qa/qb-1);speedup=tb/ta
            assert math.isclose(change,old['LPIPS_change_percent'],rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(speedup,old['speedup_baseline_over_candidate'],rel_tol=1e-12,abs_tol=1e-12)
            frame_gains=[x-y for x,y in zip(b['LPIPS']['frame_distances'],a['LPIPS']['frame_distances'])]
            values.append({'scene':scene,'baseline_LPIPS':qb,'candidate_LPIPS':qa,
                'LPIPS_reduction_percent':-change,'baseline_seconds':tb,'candidate_seconds':ta,
                'seconds_saved':tb-ta,'speedup_baseline_over_candidate':speedup,
                'better_frames':sum(x>0 for x in frame_gains),'worse_frames':sum(x<0 for x in frame_gains),
                'equal_frames':sum(x==0 for x in frame_gains),'all93_frame_gains':frame_gains})
        qa,qb=mean(v['candidate_LPIPS'] for v in values),mean(v['baseline_LPIPS'] for v in values)
        ta,tb=mean(v['candidate_seconds'] for v in values),mean(v['baseline_seconds'] for v in values)
        assert math.isclose(qa,stored['scene_equal_candidate_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        assert math.isclose(qb,stored['scene_equal_baseline_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        comparisons.append({'candidate':candidate,'baseline':base,'denominator':4,'per_scene':values,
            'scene_equal_LPIPS_reduction_percent':100*(1-qa/qb),'scene_equal_seconds_saved':tb-ta,
            'speedup_ratio_of_scene_equal_times':tb/ta,'quality_improved_scenes':sum(v['candidate_LPIPS']<v['baseline_LPIPS'] for v in values),
            'faster_scenes':sum(v['candidate_seconds']<v['baseline_seconds'] for v in values)})
    return {'methods':summaries,'comparisons':comparisons,'actual_candidate_action_and_reason_counts':counts,
        'source_and_operator_semantics_verified_without_new_teacher':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'reports/wc_source_phase_h1_live_or_terminal_capture_20261013.json')
    p.add_argument('--output',type=Path,default=ROOT/'reports/wc_source_phase_h1_complete_independent_analysis_20261013.json');a=p.parse_args()
    capture=json.loads(a.input.read_text());analysis=reconstruct(capture)
    analysis.update(status='SOURCE_PHASE_H1_COMPLETE36_ALL24_FULL93_NINE_CONTRASTS_INDEPENDENTLY_RECONSTRUCTED',
        capture_ref=str(a.input),capture_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
        source_revision=capture['source_revision'],GPU_cost_hours=capture['supervisor']['wall_seconds']/3600,
        ledger_used_GPUh=capture['ledger']['used_gpu_hours'],remaining_GPUh=capture['ledger']['cap_gpu_hours']-capture['ledger']['used_gpu_hours'],
        four_CAL_single_seed_not_independent_confirmation=True,single_formal_time_not_repeated_speed=True,
        LPIPS_not_physics_quality=True,GPU_submissions=0,ledger_written=False)
    assert not a.output.exists();a.output.write_text(json.dumps(analysis,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:analysis[k] for k in ('status','GPU_cost_hours','remaining_GPUh')}))


if __name__=='__main__':main()
