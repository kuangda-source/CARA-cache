#!/usr/bin/env python3
"""Bind complete <=4h card to its actual production CPU proof without dispatch."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    proof=json.loads(Path('reports/wc_action_cost_real_production_cpu_r1_terminal_20261010_capture.json').read_text())
    assert proof['exit_code']==0 and proof['local_native_bytes_binding_scope_and_request_verified']
    c=json.loads(Path('configs/wc_action_cost_real_production_r1_20261010.json').read_text())
    spec=importlib.util.spec_from_file_location('mf00_contract','src/wcomr/source_aware_action_cost_production_r1.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert proof['config_binding_sha256']==m.binding(c)
    raw=gzip.decompress(Path(proof['files']['receipt.json']['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==proof['files']['receipt.json']['sha256']
    assert 0<c['preregistration']['forecast']['forecast_complete_GPUh']<=4
    c.update(GPU_execution_selected=True,gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        production_cpu_receipt_sha256=hashlib.sha256(raw).hexdigest())
    assert c['single_job_exception_authority'] is None
    assert m.binding(c)==proof['config_binding_sha256']
    m.validate_contract(c,Path('.sync/action-cost-real-inputs-r1'))
    target=Path('configs/wc_action_cost_real_selected_r1_20261010.json');assert not target.exists()
    target.write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps({'status':'ACTION_COST_COMPLETE_CARD_SELECTED_NOT_GPU',
        'scope':c['preregistration']['scope_counts'],
        'forecast_complete_GPUh':c['preregistration']['forecast']['forecast_complete_GPUh'],
        'automatic_single_job_GPUh':4,'GPU_submissions':0}))


if __name__=='__main__':main()
