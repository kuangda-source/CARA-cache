#!/usr/bin/env python3
"""Freeze an unselected complete five-reference production card, never approval."""
import hashlib
import json
from pathlib import Path
import argparse


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',choices=['r1','r2'],default='r2')
    revision=parser.parse_args().revision
    project=Path(__file__).resolve().parents[1]
    read=lambda n:json.loads((project/n).read_text())
    sha=lambda n:hashlib.sha256((project/n).read_bytes()).hexdigest()
    base=read('manifests/wc_w1_native_reference_core_cpu_r2_20261006.json')
    core=read('configs/wc_w1_native_reference_core_r2_draft_20261006.json')
    proof=read('reports/wc_w1_native_reference_core_actual_cpu_r2_20261006.json')
    files=['src/wcomr/w1_native_reference_execution.py','src/wcomr/w1_native_reference_evaluation.py',
        'scripts/run_w1_native_references.py','scripts/supervise_w1_native_references.py',
        'scripts/audit_w1_native_references_terminal.py','scripts/score_w1_native_references_cpu.py',
        'tests/check_w1_native_reference_production_cpu.py','scripts/build_w1_native_reference_production_draft.py',
        'reports/wc_w1_native_reference_core_actual_cpu_r2_20261006.json','reports/wc_w1_native_reference_cost_proxy_r1_20261006.json']
    payload=dict(base['payload_sha256']);payload.update({n:sha(n) for n in files})
    resource='reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json'
    audit=read(resource)
    config={'card':'WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A','run_id':'wc-w1-native-reference-cal8-r1',
        'role':'UNSELECTED_COMPLETE_FIVE_REFERENCE_PRODUCTION_DRAFT_NOT_GPU_AUTHORIZATION',
        'expected_project_root':'/home/gaokuangda/data/gkd/worldcache_omr',
        'sample_indices':[0,3,4,5,7],'sample_names':[read('manifests/wc_w1_native_reference_cal8_r1_draft_20261006.json')['rows'][i]['scene'] for i in [0,3,4,5,7]],
        'original_denominator':[8,7,1],'new_reference_phases':5,'production_entry_ready':True,
        'all_seven_must_improve':False,'new_training_or_human_review':False,
        'execution_limits':{'timeout_seconds':3600,'child_timeout_seconds':3570,'kill_grace_seconds':5,
            'admission_allowance_seconds':30,'minimum_disk_free_bytes':4*1024**3},
        'payload_sha256':payload,'core_cpu_payload_sha256':base['payload_sha256'],
        'upstream_source_sha256':base['upstream_sha256'],'project_input_sha256':core['project_input_sha256'],
        'budget_snapshot':core['budget_snapshot'],'core_cpu_stage':base['stage'],
        'core_cpu_receipt_sha256':proof['server_receipt_sha256'],'draft_sha256':core['draft_sha256'],
        'lpips_resource_stage':'.sync/wc-rv0-lpips-resource-v2','lpips_resource_receipt_sha256':audit['server_receipt_sha256'],
        'lpips_resource_audit':{'path':resource,'sha256':sha(resource)},
        'cost_report_ref':'reports/wc_w1_native_reference_cost_proxy_r1_20261006.json',
        'cost_report_sha256':sha('reports/wc_w1_native_reference_cost_proxy_r1_20261006.json'),
        'GPU_execution_selected':False,'gpu_uuid':None,'execution_scope_authority':None}
    name='configs/wc_w1_native_reference_production_'+revision+'_draft_20261006.json'
    if (project/name).exists():raise ValueError('Preserve frozen production config; use a new revision')
    data=(json.dumps(config,indent=2)+'\n').encode();(project/name).write_bytes(data)
    payload=dict(payload,**{'native-prod-config.json':hashlib.sha256(data).hexdigest()})
    sources={n:n for n in files};sources['native-prod-config.json']=name
    manifest={'identity':'WC_W1_COMPLETE_FIVE_REFERENCE_PRODUCTION_CPU_R1_NOT_GPU',
        'stage':'.sync/wc-w1-native-reference-production-cpu-'+revision+'-20261006','base_stage':base['stage'],
        'base_payload_sha256':base['payload_sha256'],'base_original_receipt_sha256':proof['server_receipt_sha256'],
        'payload_sha256':payload,'source_path_by_stage_path':sources,'upstream_sha256':base['upstream_sha256'],
        'budget_sha256':core['project_input_sha256']['reports/budget.json'],'CPU_only':True,'GPU_submissions':0,
        'new_GPU_authorization':False,'reference_phases':5,'original_denominator':[8,7,1]}
    (project/('manifests/wc_w1_native_reference_production_cpu_'+revision+'_20261006.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':'FIVE_REFERENCE_PRODUCTION_DRAFT_FROZEN_NOT_AUTHORITY','payload_files':len(payload)}))


if __name__=='__main__':main()
