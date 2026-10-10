#!/usr/bin/env python3
"""Full frozen audit, observed asynchronously with cheaper receipt compression.

Only audit threads, the observation deadline and lossless gzip level change.
No original experiment process, native artifact, scope or GPU ledger changes.
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
    replacements=[('\n import torch\n','\n import torch\n torch.set_num_threads(2)\n'),
        ('timeout=55)','timeout=600)'),
        ('gzip.compress(raw,mtime=0)','gzip.compress(raw,compresslevel=1,mtime=0)')]
    changed=source
    for old,new in replacements:
        assert changed.count(old)==1
        changed=changed.replace(old,new,1)
    inverse=changed
    for old,new in reversed(replacements):
        assert inverse.count(new)==1
        inverse=inverse.replace(new,old,1)
    assert inverse==source
    assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(source),include_attributes=False)
    destination=Path('reports/wc_p0_deployment_sampling_cpu_r1_terminal_20261010_capture.json')
    assert not destination.exists()
    namespace={'__name__':'independent_readonly_capture_R3','__file__':str(original)}
    exec(compile(changed,str(original)+'#read-only-observer-R3','exec'),namespace)
    code=namespace['main']()
    if code!=0:return code
    proof=json.loads(destination.read_text())
    proof['independent_readonly_audit_adapter']={
        'source_helper':str(original),'frozen_source_revision':launch['source_revision'],
        'frozen_source_sha256':hashlib.sha256(frozen).hexdigest(),
        'adapter_helper':str(Path(__file__)),
        'adapter_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'explicit_remote_Torch_threads':2,'lossless_gzip_level':1,
        'inverse_source_and_AST_equal':True,'observation_timeout_seconds':600,
        'caller_nonblocking_exec_and_bounded_polling_required':True,
        'original_generation_not_repeated':True,'remote_artifacts_not_mutated':True,
        'original_observation_failures_preserved':[
            'reports/wc_p0_deployment_sampling_cpu_r1_original_capture_timeout_20261010.json',
            'reports/wc_p0_deployment_sampling_cpu_r1_thread2_capture_timeout_20261010.json']}
    destination.write_text(json.dumps(proof,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
