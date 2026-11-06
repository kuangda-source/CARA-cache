#!/usr/bin/env python3
"""Reconstruct all four signed endpoint effects from complete scored originals."""
import argparse,hashlib,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]


def effects(final,states):
    assert len(final['parents'])==4 and len(final['outputs'])==12 and len(final['comparisons'])==4
    assert sum(p['actual_pair_computations'] for p in final['parents'])==266
    assert all(p['all36_guided_actions_final_and93RGB_original_equal'] and p['default_suffix_all_remaining_original_equal'] for p in final['parents'])
    assert len({s['scene'] for s in states})==4
    result=[]
    for point in states:
        scene=point['scene'];rows=[r for r in final['outputs'] if r['scene']==scene]
        assert len(rows)==3 and {r['label'] for r in rows}=={'PARENT_PI0','DEFAULT_PI0','ALTERNATIVE'}
        by={r['label']:r for r in rows};default,other=by['DEFAULT_PI0'],by['ALTERNATIVE']
        assert default['first_readout']==point['default_readout'] and other['first_readout']==point['alternative_readout']
        assert {default['first_readout'],other['first_readout']}=={'C','A'}
        for row in rows:
            f=row['LPIPS']['frame_distances'];assert len(f)==93 and all(math.isfinite(x) and x>=0 for x in f)
            assert math.isclose(mean(f),row['LPIPS']['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        assert default['LPIPS']['frame_distances']==by['PARENT_PI0']['LPIPS']['frame_distances']
        stored=next(x for x in final['comparisons'] if x['scene']==scene)
        yq=default['LPIPS']['mean_LPIPS']-other['LPIPS']['mean_LPIPS']
        yt=default['instrumented_remaining_main_seconds']-other['instrumented_remaining_main_seconds']
        assert math.isclose(yq,stored['Y_quality_default_minus_alternative'],rel_tol=1e-12,abs_tol=1e-12)
        assert math.isclose(yt,stored['Y_instrumented_time_default_minus_alternative'],rel_tol=1e-12,abs_tol=1e-12)
        readouts={x['first_readout']:x for x in (default,other)};c,a=readouts['C'],readouts['A']
        frame_gains=[x-y for x,y in zip(c['LPIPS']['frame_distances'],a['LPIPS']['frame_distances'])]
        gain=c['LPIPS']['mean_LPIPS']-a['LPIPS']['mean_LPIPS']
        # D default=A, P default=C: converting to A relative to C changes
        # sign for D only. Never pool unlabelled default/alternative effects.
        assert math.isclose(gain,yq*(-1 if point['source']=='D' else 1),rel_tol=1e-12,abs_tol=1e-12)
        counts={}
        for name,row in readouts.items():
            actual=row['actual_suffix_actions'];assert len(actual)==37-point['chosen']['step']
            counts[name]={action:actual.count(action) for action in ('CC','PP','DD')}
            assert sum(counts[name].values())==len(actual)
            assert counts[name]=={k:row['actual_suffix_counts'].get(k,0) for k in counts[name]}
        result.append({'point':point,'Yq_default_minus_alternative':yq,'Yt_compute_interval_default_minus_alternative':yt,
            'C_LPIPS':c['LPIPS']['mean_LPIPS'],'A_LPIPS':a['LPIPS']['mean_LPIPS'],
            'A_quality_gain_relative_C':gain,'A_relative_LPIPS_reduction_percent':100*gain/c['LPIPS']['mean_LPIPS'] if c['LPIPS']['mean_LPIPS'] else None,
            'C_instrumented_sampling_plus_decoder_seconds':c['instrumented_remaining_main_seconds'],'A_instrumented_sampling_plus_decoder_seconds':a['instrumented_remaining_main_seconds'],
            'A_compute_interval_time_gain_relative_C':c['instrumented_remaining_main_seconds']-a['instrumented_remaining_main_seconds'],
            'C_guardrail_and_encoding_save_combined_seconds':c.get('video_write_seconds'),
            'A_guardrail_and_encoding_save_combined_seconds':a.get('video_write_seconds'),
            'A_instrumented_sampling_decoder_and_guarded_writer_gain_relative_C':
                (c['instrumented_remaining_main_seconds']+c['video_write_seconds']-a['instrumented_remaining_main_seconds']-a['video_write_seconds'])
                if 'video_write_seconds' in c and 'video_write_seconds' in a else None,
            'A_better_frames':sum(x>0 for x in frame_gains),'A_worse_frames':sum(x<0 for x in frame_gains),'equal_frames':sum(x==0 for x in frame_gains),
            'all93_signed_frame_gains':frame_gains,'full_future_counts':counts})
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=R/'reports/wc_pi0_suffix8_live_or_terminal_capture_20261013.json')
    p.add_argument('--output',type=Path,default=R/'reports/wc_pi0_suffix8_complete_effects_analysis_20261013.json');a=p.parse_args()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    capture=json.loads(a.input.read_text());final=capture['final'];sup=capture['supervisor']
    assert final['status']=='PI0_SUFFIX8_ALL4_PARENTS8_SUFFIXES12_OUTPUTS_AUDITED_ALL93_SCORED'
    assert capture['post_exit']['exit_code']==sup['child_exit_code']==0 and not any(capture['original_processes'].values())
    assert capture['kernel_lock_free'] and all(capture['payload_verified'].values())
    assert final['accepted_videos']==final['scored_videos']==12
    assert final['budget_before_sha256']==final['budget_after_sha256']==capture['ledger_sha256']
    config=R/'configs/wc_pi0_suffix8_full266_production_r1_20261013.json';states=json.loads(config.read_text())['states']
    rows=effects(final,states)
    timing_path=R/'reports/wc_pi0_suffix8_timing_source_boundary_cpu_20261013.json';timing=json.loads(timing_path.read_text())
    assert timing['status']=='PI0_SUFFIX8_DECODER_GUARDED_WRITER_SOURCE_BOUNDARY_CPU_VERIFIED' and timing['source_revision']==capture['source_revision']
    for r in final['outputs']:
        if r['label']=='PARENT_PI0':continue
        assert math.isclose(r['instrumented_remaining_main_seconds'],r['instrumented_sampling_seconds']+r['VAE_guardrail_seconds'],rel_tol=1e-12)
        assert math.isfinite(r['video_write_seconds']) and r['video_write_seconds']>=0
    local_path=R/'reports/wc_source_phase16_complete_scalar_and_cell_analysis_20261012.json';local=json.loads(local_path.read_text())
    for row in rows:
        s=row['point'];matches=[x for x in local['points'] if x['selection']['scene']==s['scene'] and x['selection']['chosen']['step']==s['chosen']['step']]
        assert len(matches)<=1
        if matches:
            target=matches[0];assert target['selection']['source']==s['source'] and target['selection']['chosen']['source_birth']==s['chosen']['source_birth']
            loss=target['losses'];qc,qa=loss['C']['absolute_guided_MSE'],loss['FUSION_A']['absolute_guided_MSE']
            row['matched_same_state_cal16_local_A_gain_percent']=100*(qc-qa)/qc
        else:
            row['matched_same_state_cal16_local_A_gain_percent']=None
            row['local_match_boundary']='No exact same-step teacher label; AV51 suffix27 is not cal16 P26'
    result={'status':'PI0_SUFFIX8_ALL4_SIGNED_ENDPOINT_EFFECTS_INDEPENDENTLY_RECONSTRUCTED',
        'capture_ref':str(a.input),'capture_sha256':sha(a.input),'config_sha256':sha(config),'cal16_analysis_sha256':sha(local_path),
        'source_revision':capture['source_revision'],'timing_source_proof_ref':str(timing_path),'timing_source_proof_sha256':sha(timing_path),
        'timing_original_fields_retained_but_correctly_mapped':timing['original_field_actual_intervals'],
        'registered_sampling_VAE_guardrail_without_encoding_save_time_identifiable':False,
        'states':rows,'A_quality_improving_states':sum(r['A_quality_gain_relative_C']>0 for r in rows),
        'mean_A_quality_gain_relative_C':mean(r['A_quality_gain_relative_C'] for r in rows),
        'mean_default_relative_Yq':mean(r['Yq_default_minus_alternative'] for r in rows),
        'GPU_cost_hours':sup['wall_seconds']/3600,'ledger_used':capture['ledger']['used_gpu_hours'],
        'remaining_GPUh':capture['ledger']['cap_gpu_hours']-capture['ledger']['used_gpu_hours'],
        'four_selected_CAL_states_not_independent_policy_confirmation':True,'source_phase_and_scene_not_separately_identifiable_from_four_events':True,
        'instrumented_suffix_time_not_clean_speed':True,'GPU_submissions':0,'ledger_written':False}
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','A_quality_improving_states','mean_A_quality_gain_relative_C','GPU_cost_hours','remaining_GPUh')}))


if __name__=='__main__':main()
