#!/usr/bin/env python3
"""Separate paired sampling, decoder and guarded-writer order observations."""
import hashlib,json,math
from pathlib import Path
from statistics import mean
R=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    path=R/'reports/wc_pi0_suffix8_live_or_terminal_capture_20261013.json';v=json.loads(path.read_text());f=v['final']
    assert f['status']=='PI0_SUFFIX8_ALL4_PARENTS8_SUFFIXES12_OUTPUTS_AUDITED_ALL93_SCORED' and v['post_exit']['exit_code']==0
    assert v['kernel_lock_free'] and not any(v['original_processes'].values())
    rows=[]
    for parent in v['runner']['runs']:
        order=[b['label'] for b in parent['event']['branches']]
        outputs=[next(o for o in f['outputs'] if o['scene']==parent['scene'] and o['label']==label) for label in order]
        assert len(outputs)==2
        by={o['first_readout']:o for o in outputs};c,a=by['C'],by['A'];first,second=outputs
        rows.append({'scene':parent['scene'],'first_readout':first['first_readout'],'second_readout':second['first_readout'],
            'C_sampling_seconds':c['instrumented_sampling_seconds'],'A_sampling_seconds':a['instrumented_sampling_seconds'],
            'A_sampling_gain_relative_C_seconds':c['instrumented_sampling_seconds']-a['instrumented_sampling_seconds'],
            'A_relative_sampling_reduction_percent':100*(c['instrumented_sampling_seconds']-a['instrumented_sampling_seconds'])/c['instrumented_sampling_seconds'],
            'first_decoder_seconds':first['VAE_guardrail_seconds'],'second_decoder_seconds':second['VAE_guardrail_seconds'],
            'second_decoder_faster':second['VAE_guardrail_seconds']<first['VAE_guardrail_seconds'],
            'first_guarded_writer_seconds':first['video_write_seconds'],'second_guarded_writer_seconds':second['video_write_seconds'],
            'C_future_updates_D_plus_P':sum(c['actual_suffix_counts'].get(k,0) for k in ('DD','PP')),
            'A_future_updates_D_plus_P':sum(a['actual_suffix_counts'].get(k,0) for k in ('DD','PP')),
            'C_counts':c['actual_suffix_counts'],'A_counts':a['actual_suffix_counts'],
            'C_LPIPS':c['LPIPS']['mean_LPIPS'],'A_LPIPS':a['LPIPS']['mean_LPIPS']})
    assert len(rows)==4 and all(math.isfinite(r['A_sampling_gain_relative_C_seconds']) for r in rows)
    result={'status':'PI0_SUFFIX8_FULL4_SAMPLING_DECODER_GUARDED_WRITER_COMPONENTS_CPU_RECONSTRUCTED',
        'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows,
        'second_decoder_faster_states':sum(r['second_decoder_faster'] for r in rows),
        'mean_first_decoder_seconds':mean(r['first_decoder_seconds'] for r in rows),
        'mean_second_decoder_seconds':mean(r['second_decoder_seconds'] for r in rows),
        'single_instrumented_suffix_sampling_not_clean_full_video_speed':True,
        'order_residency_or_warmup_causal_mechanism_not_uniquely_established':True,'GPU_submissions':0,'ledger_written':False}
    dest=R/'reports/wc_pi0_suffix8_time_component_analysis_20261013.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'second_decoder_faster_states':result['second_decoder_faster_states'],
        'mean_first_decoder':result['mean_first_decoder_seconds'],'mean_second_decoder':result['mean_second_decoder_seconds']}))
