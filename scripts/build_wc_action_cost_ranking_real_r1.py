#!/usr/bin/env python3
"""Bind the independently captured full cost card to ranking-only inputs.

Reads metadata only. No unmeasured C/A completion, tensor loading, GPU or policy
installation. Missing live-card evidence is a wait, never an accepted subset.
"""
import dataclasses
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.action_cost_ranking import BOUNDARY,MODES,build_ranking
from wcomr.source_aware_action_cost_production_r1 import CARD,RUN,COUNTS


PROOF = Path('reports/wc_action_cost_real_r1_terminal_20261010_capture_and_independent_audit.json')
DEST = Path('reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json')


def read_native(proof,key):
    entry=proof['files'][key];path=Path(entry['local_path']).resolve()
    if not path.is_relative_to(Path('reports').resolve()) or path.suffix!='.gz':
        raise ValueError('Captured metadata must be within project reports')
    packed=path.read_bytes()
    if hashlib.sha256(packed).hexdigest()!=entry['compressed_sha256']:
        raise ValueError('Captured compressed metadata changed')
    raw=gzip.decompress(packed)
    if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:
        raise ValueError('Captured original metadata changed')
    return json.loads(raw)


def main():
    if not PROOF.exists():
        print(json.dumps({'status':'WAITING_FULL_REAL_COST_CAPTURE_NO_COSTS_INSTALLED',
                          'expected_proof':str(PROOF),'GPU_submissions':0,'ledger_written':False}))
        return 2
    proof=json.loads(PROOF.read_text())
    if (proof['GPU_exit_code']!=0 or proof['CPU_exit_code']!=0
            or not proof['independent_checks']['success'] or proof['run_id']!=RUN
            or proof['planned_scope']!=COUNTS
            or not proof['independent_checks']['complete_8_parent_8_origin_6_mode_reconstruction']
            or not proof['independent_checks']['actual_288_guided_8_latent_112_branch_reload_verified']):
        raise ValueError('Complete new real cost card independent proof required')
    config=read_native(proof,'config');table=read_native(proof,'calibration_table')
    result=read_native(proof,'CPU_result')
    if (config['preregistration']['card']!=CARD or config['preregistration']['scope_counts']!=COUNTS
            or table['status']!='REAL_COSMOS_ACTION_COST_GROUP_COST_AND_GUIDED_ERROR_NOT_VIDEO_RESULT'
            or table['cost_boundary']!=BOUNDARY
            or table['actual_same_state_teacher_and_post_RF_bundles_verified'] is not True
            or table['strictly_past_actual_D_only_history'] is not True
            or table['C_A_extra_heads_and_zero_deep_checked_by_complete_verifier'] is not True
            or table['teacher_updates_deployment_anchor'] is not False
            or table['all_group_cost_seconds']!=result['all_group_cost_seconds']
            or config['payload_sha256']!=proof['payload_after_sha256']):
        raise ValueError('Complete actual cost boundary, source or raw audit differs')
    context=json.loads(table['fingerprint_context'])
    if (hashlib.sha256(table['fingerprint_context'].encode()).hexdigest()!=table['context_sha256']
            or context['source_revision']!=proof['source_revision'] or context['run_id']!=RUN
            or context['config_sha256']!=proof['config_sha256']):
        raise ValueError('Actual model/card/context fingerprint differs')
    ranking=build_ranking(table['all_group_cost_seconds'],boundary=BOUNDARY,
        source_kind='INDEPENDENTLY_CAPTURED_REAL_FULL_ACTION_COST_CARD',
        source_sha256=proof['files']['calibration_table']['sha256'])
    value={'status':'REAL_COMPLETE_PAIRED_INCREMENTAL_COST_RANKING_READY_NOT_POLICY_OR_SPEED',
        'source_revision':proof['source_revision'],'source_proof_ref':str(PROOF),
        'source_proof_sha256':hashlib.sha256(PROOF.read_bytes()).hexdigest(),
        'source_table_sha256':proof['files']['calibration_table']['sha256'],
        'complete_scope':COUNTS,'registered_cost_rows':48,'timed_values':144,
        'ranking':dataclasses.asdict(ranking),
        'rank_inputs_by_selected_reuse_mode':{m:dataclasses.asdict(ranking.for_reuse_mode(m)) for m in MODES[:3]},
        'cost_role':'ACTION_ORDER_ONLY_NOT_TOTAL_PAIR_OR_END_TO_END_TIME',
        'common_probe_prefix_not_measured_or_installed':True,
        'per_step_descriptions_not_installed':True,'A_quality_or_future_P_drift_not_inferred':True,
        'real_clean_latency_or_new_policy_or_video_quality_claim':False,
        'GPU_submissions':0,'ledger_written':False}
    if DEST.exists():raise ValueError('Preserve first cost binding; register revisions separately')
    DEST.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','registered_cost_rows','timed_values','cost_role','GPU_submissions')}))
    return 0


if __name__=='__main__':raise SystemExit(main())
