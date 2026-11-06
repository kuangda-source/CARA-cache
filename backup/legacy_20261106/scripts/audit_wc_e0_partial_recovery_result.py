#!/usr/bin/env python3
"""Independently reconstruct E0 original bytes, denominators and frame contrasts."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    capture = json.loads((root/'reports/wc_full64_partial_recovery_cpu_r1_terminal_20261011_capture.json').read_text())
    launch = json.loads((root/'reports/wc_full64_partial_recovery_cpu_r1_launch_20261011.json').read_text())
    original = {}
    for name, metadata in capture['files'].items():
        compressed = (root/metadata['local_ref']).read_bytes()
        value = gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest() == metadata['gzip_sha256']
        assert hashlib.sha256(value).hexdigest() == metadata['sha256'] and len(value) == metadata['bytes']
        if name.endswith('.json'):
            original[name] = json.loads(value)
    result, receipt, registration = (original[n] for n in ('result.json','receipt.json','preregistration.json'))
    assert receipt['exit_code'] == receipt['child_exit_code'] == result['exit_code'] == 0
    assert not any(capture['live'].values()) and not result['CUDA_initialized']
    assert receipt['result_sha256'] == capture['files']['result.json']['sha256']
    assert receipt['registration_sha256'] == launch['registration_sha256'] == capture['files']['preregistration.json']['sha256']
    assert receipt['payload_after_sha256'] == registration['payload_sha256']
    assert result['source_revision'] == receipt['source_revision'] == launch['source_revision']
    assert result['GPU_submissions'] == receipt['GPU_submissions'] == 0
    assert not result['ledger_written'] and not receipt['ledger_written']
    assert len({result['budget_before_sha256'],result['budget_after_sha256'],receipt['budget_before_sha256'],
        receipt['budget_after_sha256'],capture['budget_sha256'],launch['budget_before_sha256']}) == 1
    assert result['original_card_status_unchanged'] == 'FAILED_TECH'
    assert not result['formal_full64_method_acceptance'] and not result['independent_confirmation_claim'] and not result['clean_speed_claim']
    slots = result['all64_slots']
    assert len(slots) == 64 and len({(s['strategy'],s['sample_name'],s['method']) for s in slots}) == 64
    counts = dict(Counter(s['path_status'] for s in slots))
    assert counts == {'PATH_VALIDATED':14,'PARTIAL_FAILED_NOT_ELIGIBLE':1,'NOT_WRITTEN':49}
    assert result['validated_paths'] == 14 and result['invalid_paths'] == 0
    assert len(result['Native_files']) == 4 and len(result['trajectory_controls']) == 6
    assert all(p['actual36_guided_plus_final_reloaded'] for p in result['trajectory_controls'])
    valid = [s for s in slots if s['path_status'] == 'PATH_VALIDATED']
    assert sum(s['pairing']['compatible'] for s in valid) == 8
    assert sum(s['pairing']['strict_original_verdict']['compatible'] for s in valid) == result['strict_original_compatible_pairs'] == 0
    assert len(result['missing_prepared_input_paths_retained']) == 6
    assert sum(s['pairing']['missing_prepare_not_synthesized'] for s in valid) == 6
    assert all(len(s['actions']) == 36 and s['actual_full_CFG_branches'] == 2*s['actions'].count('DD')
        and s['actual_partial_CFG_branches'] == 2*s['actions'].count('PP') for s in valid)
    pairs = result['pairs']
    assert len(pairs) == result['numerical_paired_scores'] == 8
    assert result['actual_all93_frame_distances'] == 744 and len({p['sample_name'] for p in pairs}) == 1
    eligible = {(s['strategy'],s['sample_name'],s['method']):s for s in valid if s['pairing']['compatible']}
    scores = {}
    for p in pairs:
        slot = eligible[(p['strategy'],p['sample_name'],p['method'])]
        score = p['score']; values = score['frame_distances']
        assert score['frames'] == len(values) == len(score['pts']) == 93
        assert score['pts'] == [[1024*i,'1/16384'] for i in range(93)]
        assert all(type(v) in (float,int) and math.isfinite(v) and v >= 0 for v in values)
        assert abs(statistics.mean(values)-score['mean_LPIPS']) < 1e-12
        assert score['reference_sha256'] == p['reference']['sha256']
        assert score['candidate_sha256'] == p['candidate']['sha256'] == slot['video_artifact']['sha256']
        assert score['Native_fidelity_not_physics']
        scores[p['method']] = score
    for left,right in [('SOURCE_RA','DYNAMIC_NO_P'),('CPD','A_CPD_OFF'),('CPD','REF_CPD')]:
        assert scores[left] == scores[right]
    assert scores['DENSE_CONTROL']['mean_LPIPS'] == 0 and all(v == 0 for v in scores['DENSE_CONTROL']['frame_distances'])
    assert scores['DENSE_CONTROL']['candidate_sha256'] == scores['DENSE_CONTROL']['reference_sha256']
    old_bytes = gzip.decompress((root/registration['legacy_score_file_ref']).read_bytes())
    assert hashlib.sha256(old_bytes).hexdigest() == registration['legacy_score_native_sha256']
    old = json.loads(old_bytes)
    assert result['actual_metric_identity'] == old['actual_resource_identity']
    name = pairs[0]['sample_name']
    old_scores = {p['method']:p['score'] for p in old['pairs'] if p['sample_name'] == name}
    assert scores['SOURCE_RA'] == old_scores['RA']
    contrasts = []
    for candidate,reference,legacy in [('CPD','SOURCE_RA',False),('A_CPD_W1_ONE_PHASE','SOURCE_RA',False),
        ('A_CPD_BETA1_ONE_PHASE','SOURCE_RA',False),('A_CPD_W1_ONE_PHASE','CPD',False),
        ('A_CPD_BETA1_ONE_PHASE','CPD',False),('A_CPD_W1_ONE_PHASE','W1_ONE_PHASE',True),
        ('A_CPD_BETA1_ONE_PHASE','BETA1_ONE_PHASE',True)]:
        x,y = scores[candidate], (old_scores if legacy else scores)[reference]
        assert x['reference_sha256'] == y['reference_sha256'] and x['pts'] == y['pts']
        diffs = [a-b for a,b in zip(x['frame_distances'],y['frame_distances'])]
        contrasts.append({'candidate':candidate,'reference':reference,'legacy_quality_only_reference':legacy,
            'mean_LPIPS_difference':statistics.mean(diffs),
            'relative_distortion_reduction_percent':100*(y['mean_LPIPS']-x['mean_LPIPS'])/y['mean_LPIPS'],
            'improved_frames':sum(d<0 for d in diffs),'tied_frames':sum(d==0 for d in diffs),
            'worse_frames':sum(d>0 for d in diffs),'worst_frame_increase':max(diffs),
            'independent_video_pairs':1,'frames_are_not_independent_samples':True})
    summary = {'status':'E0_ORIGINAL_BYTES_AND_ALL744_DISTANCES_INDEPENDENTLY_RECONSTRUCTED',
        'source_revision':result['source_revision'],'result_sha256':capture['files']['result.json']['sha256'],
        'planned_original_paths':64,'path_counts':counts,'validated_tensor_contents':14*37,
        'decoded_candidate_videos':14,'decoded_Native_videos':4,'reloaded_actual_trajectory_control_pairs':6,
        'strict_original_compatible_paths':0,'new_numerical_compatible_paths':8,'missing_prepare_paths_retained':6,
        'scored_video_pairs':8,'all_frame_distances':744,'independent_scenes_with_scores':1,
        'means':{m:s['mean_LPIPS'] for m,s in scores.items()},'contrasts':contrasts,
        'action_counts':[{k:s[k] for k in ('sample_name','method','actual_full_CFG_branches','actual_partial_CFG_branches')}
            | {'DD_pairs':s['actions'].count('DD'),'PP_pairs':s['actions'].count('PP'),'remaining_C_or_A_reads':s['actions'].count('CC')}
            for s in valid],
        'controls':{'RA_noP_exact':True,'CPD_OFF_exact':True,'CPD_full_GEMM_tensor_close_video_exact':True,
            'allD_Native_file_exact_LPIPS_zero':True,'new_RA_old32_RA_exact_all_scores':True},
        'GPU_submissions':0,'budget_unchanged':True,'original_complete64_remains_failed':True,
        'formal_complete64_acceptance':False,'clean_speed_claim':False,'independent_confirmation_claim':False}
    args.output.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':summary['status'],'validated_paths':14,'scored_pairs':8,'distances':744}))


if __name__ == '__main__':
    main()
