"""Freeze exact prior evidence and a separate unselected three-scene CPU card."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--revision',default='r1',choices=['r1','r2','r3']);a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    read=lambda n:json.loads((root/n).read_text());sha=lambda n:hashlib.sha256((root/n).read_bytes()).hexdigest()
    from sys import path
    path.insert(0,str(root/'src'))
    from wcomr.own_state_execution import CARD,RUN,INDICES,NAMES,CALLS,LIMITS,validate_config
    old=read('reports/w1_replay_r1_runner.json');cal=read('reports/w1d_cal8_r1_runner.json')
    own_core=read('manifests/wc_w1_own_state_core_cpu_r2_20261006.json')
    proof=read('reports/wc_w1_own_state_core_actual_cpu_r2_20261006.json')
    base=read('manifests/wc_w1_native_reference_production_cpu_r2_20261006.json')
    baseproof=read('reports/wc_w1_native_reference_production_actual_cpu_r2_20261006.json')
    prev=read('configs/wc_w1_native_reference_production_r2_draft_20261006.json')
    prereg=read('manifests/wc_post_reference_hypotheses_r1_20261006.json')
    assert prereg['future_measurement']['scenes']==NAMES and prereg['future_measurement']['fixed_CFG_calls']==CALLS
    costref='reports/wc_w1_own_state_cost_proxy_r1_20261006.json'
    if not (root/costref).exists():
        off=[c['scalar_off']['seconds_with_hashing_and_diagnostics'] for c in old['cases']]
        all_phases=off+[old['official_gate']['seconds_with_hashing_and_diagnostics'],old['cases'][0]['scalar_on']['seconds_with_hashing_and_diagnostics']]
        unallocated=old['process_wall_seconds']-sum(all_phases)
        diagnostics=[r['diagnostic_seconds'] for c in cal['cases'] for r in c['on']['shadow_records']]
        expected_off=sum(off[i] for i in INDICES);extra=sum(diagnostics)/len(diagnostics)*12
        native=read('reports/wc_w1_native_reference_runner_20261006.json')
        native_unallocated=native['process_wall_seconds']-sum(c['pipeline_wall_seconds'] for c in native['cases'])
        # Conservative reuse proxy: ALL original unallocated time, plus complete new-Native overhead,
        # despite their partial overlap. The shared teacher/mask diagnostic is not a measured bound.
        nominal=expected_off+max(0,unallocated)+max(0,native_unallocated)+extra
        cost={'identity':'WC_W1_OWN_STATE_FULL_COST_PROXY_R1_20261006','source_files':{n:sha(n) for n in
            ['reports/w1_replay_r1_runner.json','reports/w1d_cal8_r1_runner.json','reports/wc_w1_native_reference_runner_20261006.json']},
            'original_three_OFF_pipeline_seconds':expected_off,'all_original_replay_unallocated_seconds':unallocated,
            'all_recent_native_unallocated_seconds':native_unallocated,'original_diagnostic_observations':len(diagnostics),
            'old_diagnostic_total_seconds':sum(diagnostics),'twelve_teacher_proxy_seconds':extra,
            'nominal_proxy_seconds':nominal,'stress_multiplier':1.5,'stress_proxy_seconds':nominal*1.5,
            'proposed_inclusive_cap_seconds':1800,'proposed_child_timeout_seconds':1770,
            'stress_margin_to_child_seconds':1770-nominal*1.5,'hard_upper_bound':False,'GPU_authorization':False,
            'limitations':'Cross-run conditional arithmetic, hashing/RGB/flush may vary. No fresh OFF runs; old OFF is a mandatory identity bridge, not a clean speed comparison. All loading, diagnostics, failures, flush/release charged.'}
        (root/costref).write_text(json.dumps(cost,indent=2)+'\n')
    cost=read(costref);assert cost['stress_proxy_seconds']<1770
    files=['src/wcomr/own_state_sampling.py','src/wcomr/own_state_execution.py','src/wcomr/own_state_summary.py',
        'scripts/run_w1_own_state.py','scripts/supervise_w1_own_state.py','scripts/audit_w1_own_state_terminal.py',
        'scripts/summarize_w1_own_state.py','scripts/build_w1_own_state_production_draft.py',
        'tests/check_w1_own_state_production_cpu.py','reports/wc_w1_own_state_core_actual_cpu_r2_20261006.json',costref]
    payload={n:d for n,d in base['payload_sha256'].items() if n!='native-prod-config.json'}
    payload.update(own_core['payload_sha256']);payload.update({n:sha(n) for n in files})
    c={'card':CARD,'run_id':RUN,'expected_project_root':'/home/gaokuangda/data/gkd/worldcache_omr',
        'sample_indices':INDICES,'sample_names':NAMES,'fixed_CFG_calls':CALLS,'seed':0,
        'planned_scenes':3,'planned_observations':12,'historical_OFF_bridge_required':True,
        'independent_confirmation':False,'new_training_or_human_review':False,'teacher_written_to_deployment':False,
        'all_scenes_must_improve':False,'execution_limits':LIMITS,'payload_sha256':payload,
        'core_cpu_payload_sha256':own_core['payload_sha256'],'core_cpu_stage':own_core['stage'],
        'core_cpu_receipt_sha256':proof['original_receipt_sha256'],
        'upstream_source_sha256':base['upstream_sha256'],'project_input_sha256':prev['project_input_sha256'],
        'prereg_ref':'manifests/wc_post_reference_hypotheses_r1_20261006.json',
        'prereg_sha256':sha('manifests/wc_post_reference_hypotheses_r1_20261006.json'),
        'old_replay_sha256':sha('reports/w1_replay_r1_runner.json'),'cost_report_ref':costref,'cost_report_sha256':sha(costref),
        'budget_snapshot':read('reports/budget.json'),'GPU_execution_selected':False,'gpu_uuid':None,'execution_scope_authority':None}
    validate_config(c)
    target='configs/wc_w1_own_state_production_'+a.revision+'_draft_20261006.json'
    if (root/target).exists():raise ValueError('Preserve old stage and config; use fresh revision')
    raw=(json.dumps(c,indent=2)+'\n').encode();(root/target).write_bytes(raw)
    payload=dict(payload,**{'own-state-config.json':hashlib.sha256(raw).hexdigest()})
    m={'identity':'WC_W1_OWN_STATE_PRODUCTION_ACTUAL_CPU_'+a.revision.upper()+'_20261006',
        'stage':'.sync/wc-w1-own-state-production-cpu-'+a.revision+'-20261006','base_stage':base['stage'],
        'base_original_receipt_sha256':baseproof['server_receipt_sha256'],'base_payload_sha256':base['payload_sha256'],
        'payload_sha256':payload,'source_path_by_stage_path':{**{n:n for n in files},'own-state-config.json':target},
        'own_core_stage':own_core['stage'],'own_core_payload_sha256':own_core['payload_sha256'],
        'own_core_original_receipt_sha256':proof['original_receipt_sha256'],'budget_sha256':sha('reports/budget.json'),
        'CPU_only':True,'GPU_submissions':0,'scientific_labels':0,'passed_core_not_rerun':True}
    (root/('manifests/wc_w1_own_state_production_cpu_'+a.revision+'_20261006.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps({'status':'OWN_STATE_PRODUCTION_CARD_FROZEN_NOT_GPU','payload_files':len(payload),
        'nominal_proxy_seconds':cost['nominal_proxy_seconds'],'stress_proxy_seconds':cost['stress_proxy_seconds']}))


if __name__=='__main__':main()
