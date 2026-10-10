#!/usr/bin/env python3
"""Freeze all32 paths after the full CPU proof, without GPU selection."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    sys.path.insert(0, 'src')
    from wcomr import cfg_guided_w1_deployment_production as production
    design_ref = production.DESIGN
    design = json.loads(Path(design_ref).read_text())
    phase = json.loads(Path(production.PHASE).read_text())
    cpu_ref = 'manifests/wc_a_deployment_sampling_cpu_r3_preregistration_20261010.json'
    cpu = json.loads(Path(cpu_ref).read_text())
    audit_ref = 'reports/wc_a_deployment_sampling_cpu_r3_terminal_20261010_capture_reaudit.json'
    audit = json.loads(Path(audit_ref).read_text())
    assert audit['exit_code'] == 0 and audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert audit['original_native_bytes_unchanged']
    assert sha(audit['original_failed_capture_ref'])==audit['original_failed_capture_sha256']
    assert sha('scripts/capture_wc_a_deployment_sampling_cpu_r3.py')==audit['repair_current_capture_source_sha256']
    assert {n:sha(n) for n in cpu['payload_sha256']} == cpu['payload_sha256']
    assert [r['name'] for r in design['requests']] == production.NAMES
    cost_ref = design['whole_cost_ref']; cost = json.loads(Path(cost_ref).read_text())
    assert sha(cost_ref) == design['whole_cost_sha256']
    assert cost['forecast_complete_GPUh'] == design['forecast_complete_GPUh']
    score_controls_ref='reports/wc_ra_plus_a_score_summary_cpu_controls_20261010.json'
    score_controls=json.loads(Path(score_controls_ref).read_text())
    assert score_controls['complete_matrix_and_ten_contrasts_verified'] and score_controls['GPU_submissions']==0
    assert all(sha(n)==v for n,v in score_controls['source_sha256'].items())
    old = json.loads(Path('configs/wc_ra_comparison_production_r2_20261010.json').read_text())
    old_reg = old['preregistration']
    reg = {**old_reg, 'card':production.CARD, 'run_id':production.RUN,
        'registered_unix':time.time(), 'scope_counts':production.COUNTS,
        'requests':design['requests'], 'methods':production.METHODS,
        'complete_development_design_ref':design_ref,
        'complete_development_design_sha256':sha(design_ref),
        'A_phase_design_ref':production.PHASE, 'A_phase_design_sha256':sha(production.PHASE),
        'A_candidates':phase['prospective_candidates'], 'boundary_or_alpha_sweep':False,
        'teacher_calls':0, 'hypothesis':'Teacher-free guided A with fixed RA control improves endpoint fidelity; one prospective step25 strength revision limits late overcorrection; beta1 is a strong no-fit control.',
        'identity_selection':'Four already exposed CAL scenes, original seed0; real Common/Human seed3 prior transfer is development, not confirmation.',
        'forecast':cost, 'RA_threshold':production.THRESHOLD,
        'calibration_fingerprint':production.FINGERPRINT,
        'clean_latency_claim':False, 'independent_confirmation_claim':False,
        'does_not_accept_or_shrink_old_sixteen_path_card':True}
    reg_ref = 'manifests/wc_ra_plus_a_r1_preregistration_20261010.json'
    assert not Path(reg_ref).exists()
    Path(reg_ref).write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
    # Use a read-only live snapshot even when the separate original P0 owns the
    # GPU. Its reserved total remains distinguishable from settled spending.
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',
        'gkd_minchen','cat /home/gaokuangda/data/gkd/worldcache_omr/reports/budget.json'],
        capture_output=True,check=True,timeout=40)
    budget_raw=call.stdout;budget=json.loads(budget_raw)
    assert budget['cap_gpu_hours']==77.89524658965853 and budget['automatic_single_job_gpu_hours']==4
    generated={'profile-config.json':Path('.sync/ra-comparison-inputs-r2/profile-config.json').read_bytes(),
        'ra-plus-a-requests.jsonl':(''.join(json.dumps(r)+'\n' for r in reg['requests'])).encode(),
        'budget-at-preparation.json':budget_raw}
    files=set(cpu['payload_sha256'])|set(old['payload_sha256'])
    files.difference_update({'profile-config.json','ra-comparison-requests.jsonl','budget-at-preparation.json'})
    files.update({cpu_ref,audit_ref,reg_ref,design_ref,production.PHASE,cost_ref,
        audit['original_failed_capture_ref'],'scripts/capture_wc_a_deployment_sampling_cpu_r3.py',
        design['plan_ref'],'src/wcomr/cfg_guided_w1_deployment_production.py',
        'src/wcomr/cfg_ra_plus_a_scores.py',
        'tests/check_cfg_ra_plus_a_scores_cpu.py',score_controls_ref,
        'reports/wc_ra_plus_a_production_runner_source_map_20261010.json'})
    files.update(x['local_path'] for x in audit['files'].values())
    files.update(str(p) for p in Path('scripts').glob('*wc_ra_plus_a*.py'))
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    for name in files:
        if name.endswith('.py'):
            ast.parse(Path(name).read_bytes());compile(Path(name).read_bytes(),name,'exec')
    config={**old,'identity':'RA_PLUS_A_COMPLETE32_PREPARATION_NOT_SELECTED',
        'execution_run_id':production.RUN,'preregistration':reg,'preregistration_ref':reg_ref,
        'preregistration_sha256':sha(reg_ref),'payload_sha256':payload,
        'runtime_source_sha256':{**old['runtime_source_sha256'],**cpu['runtime_source_sha256']},
        'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
        'production_cpu_receipt_sha256':None,
        'production_cpu_stage':'.sync/wc-ra-plus-a-production-cpu-r1-20261010',
        'batch_cpu_registration_ref':cpu_ref,'batch_cpu_audit_ref':audit_ref,
        'complete32_scope_requires_specific_above4_confirmation':True}
    inputs=Path('.sync/ra-plus-a-inputs-r1');inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():(inputs/name).write_bytes(raw)
    for name in (design_ref,production.PHASE,production.RA_DESIGN):
        copied=inputs/name;copied.parent.mkdir(parents=True,exist_ok=True)
        copied.write_bytes(Path(name).read_bytes())
    target=inputs/reg_ref;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(Path(reg_ref).read_bytes())
    production.validate_contract(config,inputs)
    destination=Path('configs/wc_ra_plus_a_production_r1_20261010.json');assert not destination.exists()
    destination.write_text(json.dumps(config,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'FULL_RA_PLUS_A32_PREPARATION_NOT_GPU',
        'scope':reg['scope_counts'],'payload_files':len(payload),
        'forecast_complete_GPUh':cost['forecast_complete_GPUh'],'GPU_submissions':0,
        'specific_full_card_confirmation_required':cost['forecast_complete_GPUh']>4}))


if __name__=='__main__':main()
