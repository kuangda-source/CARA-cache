#!/usr/bin/env python3
"""Bind scoring to the exact launched complete64 card, never manufacture a launch."""
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    launch_ref=Path('reports/wc_current_birth_full64_r1_GPU_launch_20261010.json')
    if not launch_ref.exists():
        print(json.dumps({'status':'WAIT_EXACT_FULL64_GPU_LAUNCH_NO_SCORE_CARD_WRITTEN','GPU_submissions':0}));return 2
    sys.path.insert(0,'src')
    from wcomr.current_birth_real_production_r1 import CARD,RUN,COUNTS
    from wcomr.current_birth_full64_scores_r1 import WITHIN_CONTRASTS,LEGACY_BASELINES,METHODS,STRATEGIES
    sha=lambda n:hashlib.sha256(Path(n).read_bytes()).hexdigest()
    gate_ref=Path('manifests/wc_current_birth_full64_score_pipeline_source_r1_preregistration_20261010.json')
    gate=json.loads(gate_ref.read_text());assert {n:sha(n) for n in gate['source_sha256']}==gate['source_sha256']
    launch=json.loads(launch_ref.read_text());cpath=Path('configs/wc_current_birth_full64_selected_r1_20261010.json')
    c=json.loads(cpath.read_text())
    assert launch['run_id']==RUN and launch['planned_scope']==COUNTS and launch['GPU_submissions_by_launch']==1
    assert c['preregistration']['card']==CARD and c['preregistration']['scope_counts']==COUNTS
    assert sha(cpath)==launch['config_sha256'] and c['GPU_execution_selected']
    cpu=json.loads(Path('reports/wc_current_birth_full64_scores_cpu_r1_results_20261010.json').read_text())
    assert cpu['status']=='CURRENT_BIRTH_FULL64_STATISTICS_CPU_PASS_NOT_REAL_VIDEOS_OR_LPIPS'
    assert cpu['synthetic_complete_score_slots']==64 and cpu['synthetic_all_frame_values']==5952
    assert (cpu['same_card_contrasts'],cpu['legacy_quality_only_contrasts'])==(24,48)
    proof_ref='reports/wc_ra_plus_a_score_cpu_r1_terminal_20261010_capture_and_independent_audit.json'
    proof=json.loads(Path(proof_ref).read_text());assert proof['independent_checks']['success']
    files={n for n in c['payload_sha256'] if n.startswith('src/wcomr/')}
    files.update(gate['source_sha256']);files.update([str(gate_ref),proof_ref,proof['files']['result']['local_path'],
        'reports/wc_current_birth_full64_scores_cpu_r1_results_20261010.json'])
    reg={'registered_unix':time.time(),'scope_counts':COUNTS,'original_launch':launch,
        'maximum_pairs':64,'frames_per_pair':93,'sample_names':[row['name'] for row in c['preregistration']['requests']],
        'legacy_score_proof_ref':proof_ref,'within_contrasts':[list(v) for v in WITHIN_CONTRASTS],
        'cross_strategy_methods':list(METHODS),'strategies':list(STRATEGIES),
        'legacy_quality_only_baselines':list(LEGACY_BASELINES),'clean_speed_claim':False,
        'incompatible_slots_retained':True,'new_generation':False,'GPU_submissions':0,'budget_written':False,
        'payload_sha256':{n:sha(n) for n in sorted(files)}}
    assert all(reg['payload_sha256'][n]==v for n,v in c['payload_sha256'].items() if n.startswith('src/wcomr/'))
    target=Path('manifests/wc_current_birth_full64_score_cpu_r1_preregistration_20261010.json');assert not target.exists()
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':'COMPLETE64_ALL93_CPU_SCORE_REGISTERED_NOT_DEPLOYED','payload_files':len(files),'GPU_submissions':0}));return 0


if __name__=='__main__':raise SystemExit(main())
