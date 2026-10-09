#!/usr/bin/env python3
"""Bind the actual R2 launch to unchanged full93 metric and summary protocols."""
import ast
import hashlib
import json
from pathlib import Path
import time


def main():
    launch=json.loads(Path('reports/wc_ra_comparison_r2_GPU_launch_20261010.json').read_text())
    assert launch['run_id']=='wc-ra-full-video-comparison-r2'
    assert launch['planned_scope']['complete_paths']==8 and launch['planned_scope']['maximum_fidelity_pairs']==6
    r=json.loads(Path('manifests/wc_ra_comparison_score_cpu_r1_preregistration_20261010.json').read_text())
    r.update(identity='WC_RA_COMPLETE_COMPARISON_ALL93_CPU_SCORE_R2_20261010',registered_unix=time.time(),original_launch=launch)
    # The metric entrypoint and numerical summary have no fixed card identity.
    # Reuse their exact original source and CPU controls; only dispatch/capture names differ.
    payload={}
    for name in r['payload_sha256']:
        n=name.replace('wc_ra_comparison_score_cpu_r1','wc_ra_comparison_score_cpu_r2')
        raw=Path(n).read_bytes();payload[n]=hashlib.sha256(raw).hexdigest()
        if n.endswith('.py'):ast.parse(raw)
        if n==name:assert payload[n]==r['payload_sha256'][name]
    assert len(payload)==10
    r['payload_sha256']=payload
    target=Path('manifests/wc_ra_comparison_score_cpu_r2_preregistration_20261010.json');assert not target.exists()
    target.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'COMPLETE_R2_ALL93_CPU_SCORE_REGISTERED_NOT_DISPATCHED','original_run_id':launch['run_id'],'scope':r['scope_counts'],'payload_files':len(payload),'GPU_submissions':0}))


if __name__=='__main__':main()
