#!/usr/bin/env python3
"""Freeze complete placement-swap science scope and reprice all controls, CPU only."""
import argparse, hashlib, json, sys
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config-output',type=Path,required=True)
    args=parser.parse_args();root=args.project
    if args.output.exists() or args.config_output.exists():raise ValueError('Preserve prior proposal identity')
    sys.path.insert(0,str(root/'src'))
    from wcomr.rv0_placement_scope import scope_from_parents, validate_scope, cost_proposal
    sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
    old=json.loads((root/'reports/wc_w3_small_window_cpu_preparation_20261004.json').read_text())
    for name,digest in old['input_receipt_sha256'].items():
        if sha(name)!=digest:raise ValueError('Parent source or original ledger changed: '+name)
    candidates=old['selected_parent_mask_swaps'];scope=scope_from_parents(candidates);validation=validate_scope(scope,candidates)
    cost=old['cost']['components_seconds'];native=old['cost']['stress_suffix_seconds_each']-25
    budget=json.loads((root/'reports/budget.json').read_text());remaining=(budget['cap_gpu_hours']-budget['used_gpu_hours'])*3600
    pricing=cost_proposal(cost['loading'],cost['two_diagnostic_parent_only']/2,
                         cost['twelve_unchanged_suffix_proxies']/12,native,remaining)
    a=json.loads((root/'configs/wc_w3_small_cd_production_r1_draft.json').read_text())
    c={'scope':scope,'references':a['references'],'historical_wc_settings':a['historical_wc_settings'],
        'cal_config_sha256':a['cal_config_sha256'],'f1_setup_sha256':a['f1_setup_sha256'],
        'upstream_source_sha256':a['upstream_source_sha256'],'historical_reference_bindings':a['historical_reference_bindings'],
        'CPU_interface_stage':'.sync/wc-w3-fixed-mask-cpu-r1-20261004',
        'CPU_interface_original_sha256':'a8da6bfac7f7940ec41b6d621f04bcad8fad51611640e5a7869dc2be3e2a8df6',
        'scientific_choice_status':'PREREGISTERED_COMPLETE_SCOPE_ONLY_NOT_EXECUTION_CONFIGURATION',
        'cost':pricing,'source_receipt_sha256':{name:sha(name) for name in [
         'reports/wc_w3_small_window_cpu_preparation_20261004.json',
         'reports/wc_w3_fixed_mask_cpu_r1_audit_20261004.json','configs/wc_w3_small_cd_production_r1_draft.json',
         'src/wcomr/rv0_fixed_plan.py','src/wcomr/rv0_fixed_mask.py','src/wcomr/rv0_placement_scope.py',
         'scripts/prepare_wc_w3_placement_scope_cpu.py','reports/budget.json']}}
    args.config_output.write_text(json.dumps(c,indent=2)+'\n')
    r={'status':'PLACEMENT_FULL_FOUR_PAIR_SCOPE_AND_COST_CPU_PREPARATION_NOT_GPU','scope_check':validation,
       'swaps':[{k:row[k] for k in ['scene','parent_mask_sha256','parent_full_counts_per_CFG','swaps']} for row in scope['scenes']],
       'cost':pricing,'config_sha256':hashlib.sha256(args.config_output.read_bytes()).hexdigest(),
       'source_receipt_sha256':c['source_receipt_sha256'],'GPU_submissions':0,'ledger_written':False,
       'scientific_results':0,'full_C_D_and_fixed_mask_GPU_core_altered':False,
       'limits':'Static parent-mask/preregistered full-scope and conditional proxy cost only; no real own-state swap feasibility, video quality or launch authority.'}
    args.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'status':r['status'],'nominal_seconds':pricing['nominal_complete_seconds'],
        'stress_proxy_seconds':pricing['stress_proxy_complete_seconds'],
        'nominal_B_shortfall_after_A_full_cap':pricing['nominal_B_shortfall_after_A_full_cap']}))


if __name__=='__main__':main()
