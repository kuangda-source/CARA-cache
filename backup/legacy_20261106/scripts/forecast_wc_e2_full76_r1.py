#!/usr/bin/env python3
"""Charge the whole frozen E2 matrix; keep the prior conservative35% envelope."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    refs=['reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json',
          'reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json',
          'manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json']
    proof,costs,inputs=[json.loads(Path(n).read_text()) for n in refs]
    assert proof['independent_checks']['success']
    item=proof['files']['runner'];raw=gzip.decompress(Path(item['local_path']).read_bytes())
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    runner=json.loads(raw);native=runner['comparison']['references']
    assert len(native)==4 and all(r['outcome']=='ACCEPTED' and r['solver_steps']==36 and r['CFG_calls']==72 for r in native)
    assert inputs['complete_scope']['complete_paths']==72 and len(inputs['confirmation_slots'])==40 and len(inputs['timing_slots'])==32
    assert (costs['registered_cost_rows'],costs['timed_values'])==(48,144)
    means=dict(costs['ranking']['global_means'])
    dense=max(r['pipeline_wall_seconds'] for r in native)
    reuse=max(means['C'],means['A_W1_ONE_PHASE'],means['A_BETA1_ONE_PHASE'])
    # All76, even the known CAL timing and Native rows, are costed as slowest
    # complete Native, plus all36 extra reuse increments. This is conservative
    # double charging of mutually exclusive actions, not a performance model.
    full=76*dense;extra=76*36*reuse;loading=runner['load_seconds']
    subtotal=full+extra+loading;seconds=subtotal*1.35+120.
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    output={'status':'E2_FULL76_CONSERVATIVE_PLANNING_ENVELOPE_NOT_EXECUTABLE_CARD',
        'scientific_paths':72,'confirmation_paths':40,'balanced_timing_paths':32,'additional_parity_paths':4,
        'complete_actual_GPU_paths':76,'solver_updates':2736,'CFG_calls':5472,
        'native_all_four_pipeline_seconds':[r['pipeline_wall_seconds'] for r in native],
        'all76_slowest_Native_pipeline_seconds':full,'all36_extra_reuse_increment_seconds':extra,
        'observed_model_loading_seconds':loading,'unmargined_seconds':subtotal,
        'whole_scope_margin_multiplier':1.35,'shutdown_flush_reserve_seconds':120.,
        'forecast_complete_seconds':seconds,'forecast_complete_GPUh':seconds/3600.,
        'scope_shrunk_to_fit_permission':False,'current_window_autonomy_GPUh':8.,
        'requires_specific_confirmation_after_complete_CPU_and_production_preparation':seconds/3600.>8.,
        'forecast_is_not_runtime_guarantee_or_speed_result':True,
        'rationale':'Reuse preceding full64 35% complete-scope forecast rule with actual accepted Native and actual A action costs. Charge all76 as full Native plus every-step reuse even on Native and known CAL timing;35% covers current state/artifact/IO/hardware variation. No new timing or assumed removal saving used to lower forecast.',
        'source_sha256':{**{n:sha(n) for n in refs},item['local_path']:sha(item['local_path']),
            str(Path(__file__).resolve().relative_to(Path.cwd().resolve())):sha(__file__)},
        'GPU_execution_selected':False,'GPU_submissions':0,'budget_written':False,
        'CPU_validation_and_source_asset_admission_pending':True}
    path=Path('reports/wc_e2_full76_whole_cost_r1_20261011.json');assert not path.exists()
    path.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:output[k] for k in ('status','complete_actual_GPU_paths','forecast_complete_GPUh','GPU_submissions')}))


if __name__=='__main__':main()
