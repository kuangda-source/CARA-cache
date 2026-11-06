#!/usr/bin/env python3
"""Register all28 available all93 scores against the actual complete32 launch."""
import ast
import hashlib
import json
from pathlib import Path
import time


def main():
    launch=json.loads(Path('reports/wc_ra_plus_a_r1_GPU_launch_20261010.json').read_text())
    assert launch['run_id']=='wc-ra-plus-a-full-video-r1'
    assert launch['planned_scope']['complete_paths']==32 and launch['planned_scope']['maximum_fidelity_pairs']==28
    old=json.loads(Path('manifests/wc_ra_comparison_score_cpu_r2_preregistration_20261010.json').read_text())
    controls_ref='reports/wc_ra_plus_a_score_summary_cpu_controls_20261010.json'
    controls=json.loads(Path(controls_ref).read_text())
    assert controls['complete_matrix_and_ten_contrasts_verified'] and controls['GPU_submissions']==0
    payload_names=[
        'scripts/score_wc_ra_plus_a_cpu_r1.py',
        'scripts/supervise_wc_ra_plus_a_score_cpu_r1.py',
        'scripts/deploy_wc_ra_plus_a_score_cpu_r1.py',
        'src/wcomr/__init__.py','src/wcomr/cfg_ra_plus_a_scores.py',
        'src/wcomr/lpips_resource_identity.py','src/wcomr/rv0_lpips.py',
        'src/wcomr/rv0_video_reader.py','tests/check_cfg_ra_plus_a_scores_cpu.py',controls_ref]
    payload={}
    for name in payload_names:
        raw=Path(name).read_bytes();payload[name]=hashlib.sha256(raw).hexdigest()
        if name.endswith('.py'):ast.parse(raw)
        if name in old['payload_sha256']:assert payload[name]==old['payload_sha256'][name]
    for name,digest in controls['source_sha256'].items():assert payload[name]==digest
    r={**old,'identity':'WC_RA_PLUS_A_COMPLETE32_ALL93_CPU_SCORE_R1_20261010',
        'registered_unix':time.time(),'original_launch':launch,
        'sample_names':controls['sample_names'],'methods':controls['methods'],
        'maximum_pairs':28,'payload_sha256':payload,
        'scope_counts':{'original_method_paths':28,'original_reference_slots':4,
            'maximum_pairs':28,'frames_per_pair':93,'maximum_actual_frame_distances':2604,
            'planned_scene_method_summaries':28,'registered_contrasts':10,'actual_cost_slots':32,
            'new_generation':0,'GPU_submissions':0},
        'reference_rejections':'Retain four original slots and all28 method paths; score all exact available Native pairs without replacement or zero fill.',
        'cost_summary':'All32 source-bound actual instrumented pipeline walls/full calls, all A paid extra heads and teacher/deep=0. No matched-time or clean-speed claim.',
        'prior_summary_CPU_controls_ref':controls_ref,
        'independent_capture_source_ref':'scripts/capture_wc_ra_plus_a_score_cpu_r1.py',
        'independent_capture_source_sha256':hashlib.sha256(Path('scripts/capture_wc_ra_plus_a_score_cpu_r1.py').read_bytes()).hexdigest()}
    target=Path('manifests/wc_ra_plus_a_score_cpu_r1_preregistration_20261010.json');assert not target.exists()
    target.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'FULL32_ALL93_CPU_SCORE_REGISTERED_NOT_DISPATCHED',
        'scope':r['scope_counts'],'payload_files':len(payload),'GPU_submissions':0}))


if __name__=='__main__':main()
