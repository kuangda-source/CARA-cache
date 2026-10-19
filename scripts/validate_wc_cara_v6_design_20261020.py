#!/usr/bin/env python3
"""Verify scope/provenance and preservation, not experimental efficacy."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'plans/cara_v6_20261020'


def load(p):return json.loads(p.read_text())
def digest(p):
    b=p.read_bytes();return dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))


def validate():
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(dict(name=name,passed=True))
    archive=ROOT/'plans/reviews/cara_v5_20261019'
    package=load(archive/'PACKAGE_MANIFEST.json')
    check('all_supplied_review_files_exact',all(digest(archive/e['name'])==
        {k:e[k] for k in ('sha256','bytes')} for e in package['files']))
    rec=load(ROOT/'reports/wc_cara_v6_revision_package_and_current_evidence_reconciliation_20261020.json')
    a=rec['BANK24_automation_binding']
    check('original_BANK24_automation_bytes_unchanged',digest(Path(a['path']))=={k:a[k] for k in ('sha256','bytes')})
    check('new_turn_has_no_remote_dispatch_or_results',rec['SSH_calls']==rec['new_server_CPU_jobs']==rec['new_GPU_submissions']==0
        and rec['new_scientific_results'] is None)
    ctl=load(ROOT/'reports/wc_cara_v6_interval_compiler_local_CPU_controls_20261020.json')
    check('all19_local_structural_controls_not_production_CPU',ctl['number_of_checks']==19
        and all(c['passed'] for c in ctl['checks']) and not ctl['actual_production_CPU_accepted'])
    check('local_control_code_exactly_bound',all(digest(ROOT/p)==v for p,v in ctl['source_bindings'].items()))
    card=load(BASE/'FIRST_DEV_UNION32_DRAFT.json');rows=card['positions']
    formal=[r for r in rows if r['section']=='FORMAL'];warm=[r for r in rows if r['section']!='FORMAL']
    check('complete32_denominator_and_unique_position_identity',len(rows)==len({r['id'] for r in rows})==32
        and len(formal)==20 and len(warm)==12)
    names={r['name'] for r in card['requests']};methods={r['method'] for r in formal}
    check('exact4CAL_cross5_newmethods',len(names)==4 and len(methods)==5
        and {(r['scene'],r['method']) for r in formal}=={(s,m) for s in names for m in methods})
    check('all_new_methods_full_two_warms_plus_two_old_bridges',all(sum(r['method']==m for r in warm)==2 for m in methods)
        and sum(r['section']=='COMPATIBILITY_WARMUP' for r in warm)==2
        and all(r['trace_all36'] for r in warm))
    source=ROOT/card['source_request_config']
    check('exact_original_CAL_request_payload_reused',digest(source)==card['source_request_binding']
        and card['requests']==load(source)['requests'])
    check('whole_card_pair_CFG_load_Native_teacher_scope',card['scope_counts']['ordinary_pairs']==1152
        and card['scope_counts']['ordinary_CFG_calls']==2304 and card['scope_counts']['loads']==1
        and card['scope_counts']['new_Native_formal']==card['scope_counts']['online_teacher_pairs']==0)
    q=card['quote']
    check('complete_engineering_quote_recomputed_not_GPU_permission',math.isclose(q['forecast_complete_GPUh'],
        sum(q['terms_seconds'].values())*q['margin']/3600,abs_tol=1e-12)
        and q['forecast_complete_GPUh']<q['proposed_billed_limit_GPUh']==6.25<12
        and not card['GPU_dispatch_ready'] and not card['actual_production_CPU_accepted'])
    dev=load(BASE/'DEVELOPMENT_UNION_V6.json')
    accepted=load(ROOT/dev['quality_pool_ref'])
    for candidate,old_method in dev['accepted_equivalent_candidates'].items():
        found=[x for x in accepted['per_scene_methods'] if x['method']==old_method]
        check('reuse_'+candidate+'_matches_actual4_endpoint_masks',len(found)==4
            and all(x['plan']==dev['candidates'][candidate]['actions'] for x in found))
    check('at_most3_candidates_per_count_family_no_fake_time_budgets',all(len(v)==3 for v in dev['count_families'].values())
        and dev['time_budgets_B1_B2_seconds'] is None and dev['R3_union_new_formal_count'] is None
        and not dev['clean_timing_reusable'] and not dev['first32_completes_budget_calibration'])
    test=load(BASE/'TEST_V6_RESERVATION_PROTOCOL.json')
    check('new_TEST_design168_plus_conditional72_not_frozen_or_launched',test['primary_R4A']['formal_paths']==168
        and test['conditional_R4B']['maximum_additional_formal_paths']==72
        and test['primary_R4A']['identities'] is None and not test['conditional_R4B']['enabled']
        and test['complete_GPUh_quote'] is None and test['new_GPU_submissions']==0)
    check('old_N07_CAL_and_BANK_DEV_excluded_from_future_TEST',test['exclude_all_N07']
        and test['exclude_all_CAL_and_EXPL_DEV'] and test['exclude_BANK24_DEV6']
        and len(test['local_declared_exposure_inventory'])>=18)
    check('YAML1_2_and_JSON_registries_identical',all((BASE/(s+'.json')).read_bytes()==
        (BASE/(s+'.yaml')).read_bytes() for s in ('TASK_REGISTRY_V6','paper_variant_map')))
    reg=load(BASE/'TASK_REGISTRY_V6.json')
    check('exact11_revision_tasks_future_results_empty',len(reg['tasks'])==11
        and all(t['quality_results'] is None and t['speed_results'] is None
                and not t['GPU_dispatch_ready'] for t in reg['tasks']))
    master=load(ROOT/'paper/experiment_master_table.json')
    check('inventory48_unique_rows_and_exact_status_count',len(master['rows'])==len({r['id'] for r in master['rows']})==48
        and sum(master['status_counts'].values())==48)
    previous=json.loads(subprocess.check_output(['git','show','HEAD:paper/experiment_master_table.json'],cwd=ROOT))
    check('all37_legacy_scientific_rows_preserved',master['rows'][:37]==previous['rows'][:37])
    mapping=load(ROOT/'paper/internal_to_paper_mapping.json')
    changed=list(BASE.iterdir())+[ROOT/'paper/EXPERIMENT_MASTER_TABLE.md',ROOT/'paper/INTERNAL_TO_PAPER_MAPPING.md',
        ROOT/'reports/wc_cara_v6_interval_compiler_local_CPU_controls_20261020.json']
    check('updated_plan_and_mapping_file_bindings_current',all(mapping['file_bindings'].get(str(p.relative_to(ROOT)))==digest(p)
        for p in changed if p.is_file()))
    check('master_points_to_current_mapping_SHA',master['latest_mapping_sha256']==digest(ROOT/'paper/internal_to_paper_mapping.json')['sha256'])
    missing=[]
    for p in list(BASE.glob('*.md'))+[ROOT/'research/610_WC_CARA_V6_REVIEW_CLOSURE_PLAN_INTERVAL_SPEC_AND_FIRST_DEV_SCOPE_20261020.md']:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' not in link and not link.startswith('#') and not (p.parent/link.split('#')[0]).exists():
                missing.append((str(p),link))
    check('all_new_local_document_links_resolve',not missing)
    return dict(status='CARA_V6_DESIGN_SCOPE_AND_PROVENANCE_INDEPENDENT_LOCAL_ACCEPTANCE',
        design_integrity_accepted=True,checks=checks,number_of_checks=len(checks),
        actual_production_CPU_accepted=False,GPU_dispatch_ready=False,
        new_scientific_results=None,SSH_calls=0,new_GPU_submissions=0,
        first_dev_formal_paths=20,first_dev_complete_paths=32,
        source_bindings={str(p.relative_to(ROOT)):digest(p) for p in list(BASE.iterdir()) if p.is_file()})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    value=validate();out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:value[k] for k in ('status','number_of_checks','actual_production_CPU_accepted','new_GPU_submissions')}))
