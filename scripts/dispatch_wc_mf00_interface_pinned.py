#!/usr/bin/env python3
"""Use the same pinned interpreter as CPU proof at two dispatch-only sites.

Frozen scope, staged payload, selected CPU proof and old launcher are retained.
Only the remote admission interpreter and GPU-supervisor interpreter change;
the model runner already uses this exact environment. No new GPU payload is
created. Failed pre-admission never consumed the run identity or its budget.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import time

PINNED='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
ORIGINAL='scripts/launch_wc_mf00_interface.py'


def main():
    launch=json.loads(Path('reports/wc_mf00_interface_selected_cpu_r1_launch_20261010.json').read_text())
    original=Path(ORIGINAL).read_text()
    assert original.encode()==subprocess.check_output(['git','show',launch['source_revision']+':'+ORIGINAL])
    sites=[("'gkd_minchen','python3 -'", "'gkd_minchen',"+repr(PINNED+' -')),
           ("command=['python3',str(stage/'scripts/supervise_wc_mf00_interface.py')",
            "command=["+repr(PINNED)+",str(stage/'scripts/supervise_wc_mf00_interface.py')")]
    modified=original
    for before,after in sites:
        assert modified.count(before)==1,(before,modified.count(before))
        modified=modified.replace(before,after)
    restored=modified
    for before,after in reversed(sites):restored=restored.replace(after,before)
    assert restored==original
    ast.parse(modified)
    proof={'status':'MF00_DISPATCH_INTERPRETER_ONLY_TWO_SITE_INVERSE_SOURCE_PASS',
        'frozen_launcher_ref':ORIGINAL,'frozen_source_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'effective_dispatch_source_sha256':hashlib.sha256(modified.encode()).hexdigest(),
        'pinned_interpreter':PINNED,'registered_dispatch_sites':2,
        'inverse_source_equal':True,'source_revision':launch['source_revision'],
        'dispatcher_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'scope_or_runtime_payload_changed':False,'recorded_unix':time.time()}
    receipt=Path('reports/wc_mf00_interface_pinned_dispatch_source_20261010.json')
    assert not receipt.exists()
    receipt.write_text(json.dumps(proof,indent=2)+'\n')
    namespace={'__name__':'mf00_pinned_dispatch','__file__':str(Path(ORIGINAL).resolve())}
    exec(compile(modified,ORIGINAL+'#pinned-dispatch-only', 'exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
