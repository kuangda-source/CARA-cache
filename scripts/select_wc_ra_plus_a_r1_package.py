#!/usr/bin/env python3
"""Bind the complete32 card to CPU evidence and exact direct authorization."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--authority',type=Path)
    args=parser.parse_args()
    proof=json.loads(Path('reports/wc_ra_plus_a_production_cpu_r1_terminal_20261010_capture.json').read_text())
    assert proof['exit_code']==0 and proof['local_native_bytes_binding_scope_and_request_verified']
    c=json.loads(Path('configs/wc_ra_plus_a_production_r1_20261010.json').read_text())
    sys.path.insert(0,'src')
    from wcomr import cfg_guided_w1_deployment_production as m
    assert proof['config_binding_sha256']==m.binding(c)
    raw=gzip.decompress(Path(proof['files']['receipt.json']['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==proof['files']['receipt.json']['sha256']
    forecast=c['preregistration']['forecast']['forecast_complete_GPUh']
    if forecast>4:
        if args.authority is None:
            raise ValueError('Exact direct authorization of the complete32 above4 card is pending')
        authorized=json.loads(args.authority.read_text())
        assert authorized['direct_user_authorization'] and authorized['card']==m.CARD and authorized['run_id']==m.RUN
        assert authorized['scope_counts']==m.COUNTS and authorized['forecast_complete_GPUh']==forecast
        assert authorized['preregistration_sha256']==c['preregistration_sha256']
        c['single_job_exception_authority']={'ref':str(args.authority),
            'sha256':hashlib.sha256(args.authority.read_bytes()).hexdigest()}
    else:
        assert args.authority is None and c['single_job_exception_authority'] is None
    c.update(GPU_execution_selected=True,gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        production_cpu_receipt_sha256=hashlib.sha256(raw).hexdigest())
    assert m.binding(c)==proof['config_binding_sha256']
    m.validate_contract(c,Path('.sync/ra-plus-a-inputs-r1'))
    target=Path('configs/wc_ra_plus_a_selected_r1_20261010.json');assert not target.exists()
    target.write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps({'status':'RA_PLUS_A_COMPLETE32_SELECTED_NOT_GPU',
        'scope':c['preregistration']['scope_counts'],'forecast_complete_GPUh':forecast,
        'automatic_single_job_GPUh':4,'GPU_submissions':0}))


if __name__=='__main__':main()
