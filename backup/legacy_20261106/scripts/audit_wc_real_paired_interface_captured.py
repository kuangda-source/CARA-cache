#!/usr/bin/env python3
"""Audit all retained native evidence with actual server path-alias resolution.

The original capture failure stays intact. No GPU dispatch or source mutation.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time


def main():
    prefix='reports/wc_real_paired_interface_r1_terminal_20261009_'
    original=Path(prefix+'capture_and_independent_audit.json')
    cap=json.loads(original.read_text());objects={};raws={}
    for key,item in cap['files'].items():
        compressed=Path(item['local_path']).read_bytes();raw=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==item['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==item['bytes']
        raws[key]=raw
        if item['path'].endswith('.json'):objects[key]=json.loads(raw)
    rows=objects['runner']['teacher']['parents'][1]['origin']['pairs']
    packets=[{'label':r['label'],**r['artifact']} for r in rows]
    assert len(packets)==16
    remote='P='+repr(packets)+'\n'+r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out=root/'outputs/wc-w3-real-paired-interface-r1/diagnostic';items={}
for a in P:
 path=pathlib.Path(a['path']);resolved=path.resolve()
 assert out.resolve() in resolved.parents and resolved.suffix=='.pt'
 raw=path.read_bytes();assert len(raw)==a['bytes'] and hashlib.sha256(raw).hexdigest()==a['sha256']
 items[a['label']]={'recorded_path':a['path'],'resolved_path':str(resolved),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
print(json.dumps({'actual_server_file_bindings':items,'observed_unix':time.time(),'GPU_submissions':0,'remote_source_or_ledger_writes':False}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=remote,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    aliases=json.loads(call.stdout)
    assert len(aliases['actual_server_file_bindings'])==16
    spec=importlib.util.spec_from_file_location('complete_native_check',Path(__file__).with_name('capture_wc_real_paired_interface_terminal.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    launch=json.loads(module.LAUNCH.read_text())
    checks=module.independent_native_check(launch,objects,aliases['actual_server_file_bindings'])
    assert checks['success']
    proof={'status':'COMPLETE_REAL_PAIRED_INTERFACE_NATIVE_AND_ALIAS_BINDING_AUDIT_PASS_NOT_POLICY',
        'captured_original_failure_ref':str(original),'captured_original_failure_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
        'original_independent_capture_failure_retained':cap['independent_check_failure'],
        'canonical_path_cause':'Runner records /home alias; released CPU resolves the same actual files under /media.',
        'complete_actual_server_path_bindings':aliases,'independent_checks':checks,
        'source_revision':cap['source_revision'],'whole_GPU_wall_seconds':cap['actual_GPU_wall_seconds'],
        'budget_settled':objects['budget'],'original_PIDs_absent':cap['original_PIDs_absent'],
        'all_native_sha256_verified':{k:v['sha256'] for k,v in cap['files'].items()},
        'GPU_submissions':0,'observed_unix':time.time(),'second_model_or_tensor_run':False}
    dest=Path('reports/wc_real_paired_interface_r1_complete_alias_independent_audit_20261009.json');assert not dest.exists()
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    Path('reports/budget.json').write_bytes(raws['budget'])
    print(json.dumps({k:v for k,v in proof.items() if k not in ('complete_actual_server_path_bindings','budget_settled','all_native_sha256_verified')}))


if __name__=='__main__':main()
