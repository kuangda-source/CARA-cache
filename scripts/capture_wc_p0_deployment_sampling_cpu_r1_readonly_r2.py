#!/usr/bin/env python3
"""Repeat independent read-only capture with bounded Torch CPU threads.

The original generation and capture helper stay frozen. This changes one
remote audit-thread setting, with inverse source/AST equality, never a test
scope, artifact, experiment process, CUDA operation or ledger.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    original=Path('scripts/capture_wc_p0_deployment_sampling_cpu_r1.py')
    source=original.read_text()
    launch=json.loads(Path('reports/wc_p0_deployment_sampling_cpu_r1_launch_20261010.json').read_text())
    frozen=subprocess.check_output(['git','show',launch['source_revision']+':'+str(original)])
    assert source.encode()==frozen
    old='\n import torch\n'
    new=old+' torch.set_num_threads(2)\n'
    assert source.count(old)==1
    changed=source.replace(old,new,1)
    assert changed.replace(new,old,1)==source
    assert ast.dump(ast.parse(changed.replace(new,old,1)),include_attributes=False)==ast.dump(ast.parse(source),include_attributes=False)
    destination=Path('reports/wc_p0_deployment_sampling_cpu_r1_terminal_20261010_capture.json')
    assert not destination.exists()
    namespace={'__name__':'independent_readonly_capture_thread2','__file__':str(original)}
    exec(compile(changed,str(original)+'#read-only-thread2','exec'),namespace)
    code=namespace['main']()
    if code!=0:
        return code
    proof=json.loads(destination.read_text())
    proof['independent_readonly_audit_thread_adapter']={
        'source_helper':str(original), 'frozen_source_revision':launch['source_revision'],
        'frozen_source_sha256':hashlib.sha256(frozen).hexdigest(),
        'adapter_helper':str(Path(__file__)),
        'adapter_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'explicit_remote_Torch_threads':2,'inverse_source_and_AST_equal':True,
        'observation_timeout_seconds_unchanged':55,
        'original_generation_not_repeated':True,'remote_artifacts_not_mutated':True,
        'original_observation_failure_ref':'reports/wc_p0_deployment_sampling_cpu_r1_original_capture_timeout_20261010.json'}
    destination.write_text(json.dumps(proof,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
