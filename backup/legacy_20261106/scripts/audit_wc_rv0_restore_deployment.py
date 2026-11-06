#!/usr/bin/env python3
"""Read-only independent deployment audit before the single restoration GPU card."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def audit(root,stage,expected_source):
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    r=json.loads((stage/'deploy-r1.json').read_text());c=json.loads((stage/'mid-config.json').read_text())
    assert r['source_revision']==expected_source
    assert r['status']=='ACTUAL_RESTORE_CPU_SOURCE_ASSET_IMPORT_FROZEN_CONDITION_PASS_NO_GPU'
    assert r['budget_unchanged'] is True and r['global_lock_free'] is True
    assert r['validation']['config_sha256']==sha(stage/'mid-config.json')
    assert r['payload_sha256']=={**c['payload_sha256'],'mid-config.json':sha(stage/'mid-config.json')}
    for name,digest in r['payload_sha256'].items():assert sha(stage/name)==digest,name
    for name,digest in c['upstream_source_sha256'].items():assert sha(root/'runtime'/name)==digest,name
    binding=c['cpu_control_binding'];raw=root/binding['server_stage']/'receipt.json'
    assert sha(raw)==binding['receipt_sha256']
    prior=json.loads(raw.read_text());assert prior['exit_code']==0 and prior['controls']['cuda_initialized'] is False
    assert prior['payload_sha256']==binding['payload_sha256']
    for name,digest in binding['payload_sha256'].items():assert sha(stage/name)==digest,name
    cpu=r['cpu_checks'];assert cpu['cuda_initialized'] is False and cpu['torch']=='2.7.1+cu128'
    assert cpu['scope_control']['checks']==22 and cpu['audit_control']['checks']==18
    native=cpu['native_mode'];assert native['cuda_initialized'] is False and native['weights_loaded'] is False
    assert native['mode']['before']['training_modules']==1173 and native['mode']['after']['training_modules']==0
    imports=r['origins'];assert imports[0]['status']=='CPU_ACTUAL_COSMOS_IMPORT_ORIGINS_PASS_NO_MODEL_OR_CUDA'
    assert imports[0]['cuda_initialized'] is False and imports[-1]['cuda_initialized'] is False
    assert imports[-1]['status']=='RESTORE_ACTUAL_IMPORT_FROZEN_CLASSES_PASS_NO_CUDA' and all(imports[-1]['classes'].values())
    metadata=cpu['sample_metadata'];assert metadata['cuda_initialized'] is False
    assert [v['sample'] for v in metadata['samples']]==c['sample_names']
    assert all(v['requested_steps']==35 and v['seed']==0 for v in metadata['samples'])
    assert [v['sample_context_sha256'] for v in metadata['samples']]==['3f7f757246c121fc1da737dfbb4dfbd24de751a2fb11cb8735135826ab6f0c7e','762b295ec6a4d74f8ba16034abf34d64956614733eb909fbd7dbae4abebeefc4']
    for sample,item in c['historical_WC_artifacts'].items():
        path=Path(item['path']);assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']==c['expected_parent_video_sha256'][sample]
    budget=json.loads((root/'reports/budget.json').read_text())
    assert budget==prior['budget_before'] and budget['cap_gpu_hours']==12 and not any(k.endswith('_inflight') for k in budget)
    assert c['gpu_execution_selected'] is True and c['GPU_submitted'] is False and c['budget_reserved_seconds']==0
    assert (12-budget['used_gpu_hours'])*3600>=c['timeout_seconds']+15
    logs={name:sha(stage/name) for name in ['cpu-controls.log','native-mode.log','asset-validate.log','cpu-import.log','sample-metadata.log']}
    return {'status':'RESTORE_ACTUAL_DEPLOYMENT_ORIGINALS_CPU_SOURCE_ASSET_IMPORT_AUDIT_PASS_NO_GPU',
            'source_revision':expected_source,'observed_unix':time.time(),'deployment_receipt_sha256':sha(stage/'deploy-r1.json'),
            'config_sha256':sha(stage/'mid-config.json'),'payload_sha256':r['payload_sha256'],'CPU_original_sha256':binding['receipt_sha256'],
            'CPU_source_bound_files':len(binding['payload_sha256']),'log_sha256':logs,'budget':budget,
            'GPU_submissions':0,'RV_labels':0,'full_RV0_acceptance':False,'no_Torch_import':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-source',required=True);a=p.parse_args()
    print(json.dumps(audit(a.project,a.stage,a.expected_source)))
