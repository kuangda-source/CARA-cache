"""Independently reconstruct all scene comparisons, counts and whole fees."""
import hashlib,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
METHODS=('NATIVE','RA','A_NO_P','P_OFF','SOURCE_H1','SOURCE_H2','SUPPORTED_GATE_H1','SUPPORTED_GATE_H2','PLUS_P_A_H2')
def main():
    path=R/'reports/wc_supported_gate_live_or_terminal_capture_20261012.json'
    r=json.loads(path.read_text());final=r['final'];sup=r['supervisor']
    assert sup['child_exit_code']==r['post_exit']['exit_code']==0
    assert final['status']=='SUPPORTED_GATE_FULL36_SCIENCE_ALL54_AUDITED_93FRAME_SCORED'
    assert not any(r['original_processes'].values()) and all(r['payload_verified'].values())
    assert final['budget_before_sha256']==final['budget_after_sha256']==r['ledger_sha256']
    rows=final['rows'];assert len(rows)==54
    scored=[x for x in rows if x['section']=='TIMED'];assert len(scored)==36
    scenes=list(dict.fromkeys(x['scene'] for x in scored));assert len(scenes)==4
    tables=[]
    for scene in scenes:
        group={x['method']:x for x in scored if x['scene']==scene};assert set(group)==set(METHODS)
        for method in METHODS:
            x=group[method];metric=x['LPIPS']
            assert x['decoded_video']['frames']==metric['frames']==len(metric['frame_distances'])==93
            lp=mean(metric['frame_distances'])
            assert math.isclose(lp,metric['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
            counts=x.get('counts')
            if counts:assert counts['DD']+counts['PP']+counts['C_plain']+counts['A']==36
            tables.append({'scene':scene,'method':method,'core_seconds':x['core_seconds'],'LPIPS':lp,
                'speedup_Native':group['NATIVE']['core_seconds']/x['core_seconds'],
                'speedup_RA':group['RA']['core_seconds']/x['core_seconds'],'counts':counts,
                'guarded_pipeline_seconds':x['guarded_pipeline_without_write_seconds'],
                'install_seconds':x['method_install_seconds'],'write_seconds':x['video_write_seconds']})
    contrasts=[]
    for comparison in final['comparisons']:
        a,b=comparison['candidate'],comparison['baseline'];ca=[x for x in tables if x['method']==a];ba=[x for x in tables if x['method']==b]
        aLP,bLP=mean(x['LPIPS'] for x in ca),mean(x['LPIPS'] for x in ba)
        assert math.isclose(aLP,comparison['scene_equal_candidate_LPIPS'],rel_tol=1e-12)
        assert math.isclose(bLP,comparison['scene_equal_baseline_LPIPS'],rel_tol=1e-12)
        paired=[]
        for scene in scenes:
            x=next(x for x in ca if x['scene']==scene);y=next(x for x in ba if x['scene']==scene)
            previous=next(v for v in comparison['scene_rows'] if v['scene']==scene)
            ratio=y['core_seconds']/x['core_seconds'];change=100*(x['LPIPS']/y['LPIPS']-1)
            assert math.isclose(ratio,previous['speedup_baseline_over_candidate'],rel_tol=1e-12)
            assert math.isclose(change,previous['LPIPS_change_percent'],rel_tol=1e-12)
            paired.append({'scene':scene,'LPIPS_change_percent':change,'speedup':ratio,
                'seconds_saved':y['core_seconds']-x['core_seconds']})
        contrasts.append({'candidate':a,'baseline':b,'candidate_LPIPS':aLP,'baseline_LPIPS':bLP,
            'scene_equal_LPIPS_change_percent':100*(aLP/bLP-1),'improved_scenes':sum(v['LPIPS_change_percent']<0 for v in paired),
            'faster_scenes':sum(v['speedup']>1 for v in paired),'scenes':paired,
            'one_timed_run_per_scene_not_stable_latency':True})
    output={'status':'SUPPORTED_GATE_ALL36_SCENE_ROWS_ALL9_CONTRASTS_COUNTS_FEES_INDEPENDENT_PASS',
        'input_receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_revision':sup['source_revision'],'scene_rows':tables,'contrasts':contrasts,
        'full_R2_GPUh':sup['wall_seconds']/3600,'used_GPUh':r['ledger']['used_gpu_hours'],
        'remaining_GPUh':r['ledger']['cap_gpu_hours']-r['ledger']['used_gpu_hours'],
        'warming_output_repeat_controls':len(final['warm_repeat_controls']),
        'new_input_confirmation':False,'physics_quality_claim':False,'GPU_submissions':0,'ledger_written':False}
    assert math.isclose(sup['budget_before']['used_gpu_hours']+output['full_R2_GPUh'],output['used_GPUh'],rel_tol=1e-12)
    dest=R/'reports/wc_supported_gate_complete_independent_reconstruction_20261012.json';assert not dest.exists()
    dest.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':output['status'],'contrasts':contrasts,'remaining_GPUh':output['remaining_GPUh']}))
if __name__=='__main__':main()
