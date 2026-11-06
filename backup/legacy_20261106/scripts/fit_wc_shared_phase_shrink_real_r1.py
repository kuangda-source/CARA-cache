#!/usr/bin/env python3
"""Fit a frozen offline shared shrink after full real cost source acceptance."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.cfg_shared_phase_shrink import MODES,fit_shared_shrink
from wcomr.source_aware_action_cost_production_r1 import CARD,RUN,COUNTS
from build_wc_action_cost_ranking_real_r1 import PROOF,DEST,read_native

OUTPUT=Path('reports/wc_shared_phase_shrink_real_r1_calibration_20261010.json')
REG=Path('manifests/wc_shared_phase_shrink_r1_preregistration_20261010.json')


def main():
    registration=json.loads(REG.read_text())
    for name,digest in registration['source_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Preregistered shared fit source changed')
    if not PROOF.exists() or not DEST.exists():
        print(json.dumps({'status':'WAITING_FULL_REAL_COST_AND_BOUND_INPUT_NO_FIT_OR_INSTALL',
            'GPU_submissions':0,'ledger_written':False}));return 2
    proof=json.loads(PROOF.read_text());bound=json.loads(DEST.read_text())
    if (not proof['independent_checks']['success'] or proof['GPU_exit_code']!=0
            or proof['CPU_exit_code']!=0
            or proof['run_id']!=RUN or proof['planned_scope']!=COUNTS
            or bound['complete_scope']!=COUNTS
            or bound['status']!='REAL_COMPLETE_PAIRED_INCREMENTAL_COST_RANKING_READY_NOT_POLICY_OR_SPEED'
            or bound['source_proof_sha256']!=hashlib.sha256(PROOF.read_bytes()).hexdigest()
            or bound['registered_cost_rows']!=48 or bound['timed_values']!=144):
        raise ValueError('Complete independently captured new real source required')
    config=read_native(proof,'config')
    if config['preregistration']['card']!=CARD:
        raise ValueError('Registered complete new cost card required')
    table=read_native(proof,'calibration_table');audit=read_native(proof,'CPU_result')
    if (table['all_modes_direct_guided_moments']!=audit['all_modes_direct_guided_moments']
            or not table['actual_same_state_teacher_and_post_RF_bundles_verified']
            or table['teacher_updates_deployment_anchor'] is not False
            or bound['source_table_sha256']!=proof['files']['calibration_table']['sha256']):
        raise ValueError('Actual combined moments or source binding differs')
    fits={mode:fit_shared_shrink(table['all_modes_direct_guided_moments'][mode],
        mode=mode,source_sha256=proof['files']['calibration_table']['sha256']) for mode in MODES}
    result={'status':'FULL_REAL_CAL_SHARED_PHASE_SHRINK_FITTED_NOT_DEPLOYED_OR_CONFIRMED',
        'registration_ref':str(REG),'registration_sha256':hashlib.sha256(REG.read_bytes()).hexdigest(),
        'source_proof_sha256':bound['source_proof_sha256'],
        'source_table_sha256':bound['source_table_sha256'],'all_eight_CAL_origins_retained':True,
        'fits':fits,'fixed_phase_and_beta1_controls_preserved':True,
        'supplied_moments_teacher_proven_by_complete_independent_source':True,
        'GPU_submissions':0,'ledger_written':False,'model_or_controller_installed':False,
        'same_state_CAL_fit_not_endpoint_video_or_generalization':True}
    if OUTPUT.exists():raise ValueError('Preserve first fit; preregister revisions separately')
    OUTPUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'shared_shrink_by_mode':{
        m:v['shared_shrink'] for m,v in fits.items()},'GPU_submissions':0}));return 0


if __name__=='__main__':raise SystemExit(main())
