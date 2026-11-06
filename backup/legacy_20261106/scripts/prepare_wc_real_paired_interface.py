#!/usr/bin/env python3
"""Build the registered Common identity from immutable complete prior evidence.

Writes only local preparation files. Server access is read-only; deployment and
GPU selection are separate explicit operations with fresh original handles.
"""
import ast
import base64
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    old=json.loads(gzip.decompress(Path('reports/wc_other_scene_cfg_confirmation_r1_terminal_20261009_config_native.gz').read_bytes()))
    ref='manifests/wc_real_paired_interface_r1_preregistration_20261009.json'
    reg=json.loads(Path(ref).read_text());c=copy.deepcopy(old)
    # Only already completed, unchanged assets/configs are borrowed. No prior
    # Human output is a Common reference and its production contract is unused.
    generated={name:Path('.sync/other-scene-cfg-confirmation-inputs-r1',name).read_bytes() for name in ('profile-config.json','onset-config.json')}
    assert all(sha(raw)==old['payload_sha256'][name] for name,raw in generated.items())
    remote="import base64,pathlib;print(base64.b64encode(pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/reports/budget.json').read_bytes()).decode())"
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -c '+repr(remote)],text=True,capture_output=True,timeout=45)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    budget=base64.b64decode(call.stdout.strip(),validate=True)
    b=json.loads(budget);assert b['cap_gpu_hours']==50 and not any('inflight' in k for k in b)
    assert budget==Path('reports/budget.json').read_bytes()
    generated.update({'original-request.jsonl':(json.dumps(reg['original_request'])+'\n').encode(),
                      'teacher-request.jsonl':(json.dumps(reg['confirmation_request'])+'\n').encode(),
                      'budget-at-preparation.json':budget})
    files=set(old['payload_sha256'])|{ref,'plans/WORLD_CACHE_REAL_PAIRED_INTERFACE_20261009.md',
                                    'src/wcomr/cfg_real_paired_interface_production.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_real_paired_interface*.py'))
    files.update(reg['input_sha256'])
    paired_reg='manifests/wc_cfg_paired_interface_sampling_cpu_r1_preregistration_20261009.json'
    paired=json.loads(Path(paired_reg).read_text())
    files.update(paired['payload_sha256']);files.add(paired_reg)
    prefix='reports/wc_cfg_paired_interface_sampling_cpu_r1_terminal_20261009_'
    paired_refs={'paired_cpu_registration_ref':paired_reg,'paired_cpu_receipt_ref':prefix+'receipt.json.native.gz',
        'paired_cpu_result_ref':prefix+'result.json.native.gz','paired_cpu_audit_ref':prefix+'capture_and_independent_audit.json'}
    files.update(paired_refs.values())
    paired_receipt=json.loads(gzip.decompress(Path(paired_refs['paired_cpu_receipt_ref']).read_bytes()))
    assert paired_receipt['exit_code']==0
    c.update(paired_refs,paired_cpu_source_revision=paired_receipt['source_revision'],paired_prefix_reserve_bytes=4*(1<<30))
    payload={}
    for name in sorted(files):
        raw=generated.get(name,Path(name).read_bytes() if Path(name).is_file() else None)
        if raw is None:raise ValueError('Missing complete bound payload '+name)
        payload[name]=sha(raw)
        if name.endswith('.py'):ast.parse(raw);compile(raw,name,'exec')
    core=json.loads(Path(old['core_registration_ref']).read_text())
    assert all(payload[name]==value for name,value in core['payload_sha256'].items())
    assert all(sha(Path(name).read_bytes())==value for name,value in reg['input_sha256'].items())
    c.update(identity='REAL_PAIRED_INTERFACE_PRODUCTION_PREPARATION_NOT_SELECTED',execution_run_id=reg['run_id'],
             preregistration=reg,preregistration_ref=ref,preregistration_sha256=sha(Path(ref).read_bytes()),
             payload_sha256=payload,GPU_execution_selected=False,gpu_uuid=None,single_job_exception_authority=None,
             production_cpu_stage='.sync/wc-real-paired-interface-production-cpu-r1-20261009',production_cpu_receipt_sha256=None)
    inputs=Path('.sync/real-paired-interface-inputs-r1');inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():(inputs/name).write_bytes(raw)
    for name in (ref,):
        p=inputs/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path(name).read_bytes())
    spec=importlib.util.spec_from_file_location('new_common_contract',Path('src/wcomr/cfg_real_paired_interface_production.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_contract(c,inputs)
    dest=Path('configs/wc_real_paired_interface_production_r1_20261009.json');assert not dest.exists()
    dest.write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps({'status':'REAL_PAIRED_INTERFACE_LOCAL_CONTRACT_COMPILE_PASS_NOT_PRODUCTION_CPU',
          'payload_files':len(payload),'scope':reg['scope_counts'],'forecast_GPUh':reg['forecast']['forecast_complete_GPUh'],
          'budget_GPUh':b['used_gpu_hours'],'GPU_selected':False,'GPU_submissions':0}))


if __name__=='__main__':main()
