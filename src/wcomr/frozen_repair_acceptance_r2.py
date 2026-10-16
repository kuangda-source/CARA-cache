"""Original full180 terminal audit, with exact repair run/CPU entry bindings."""
from functools import lru_cache
import ast
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent


@lru_cache(maxsize=1)
def derived_acceptor():
    from . import frozen_shared_acceptance_r1 as old
    from . import frozen_repair180_r2 as repair
    name=Path(old.__file__)
    if hashlib.sha256(name.read_bytes()).hexdigest()!='b93600daff82f236ec99a377f6eb762a0d4df297266785f1f486ae87a4f63997':
        raise ValueError('Original independent full180 acceptance changed')
    source=dedent(inspect.getsource(old.accept));changed=source
    edits=[('from .frozen_shared_cpu_acceptance_r1 import validate_bundle',
        'from .frozen_repair_cpu_acceptance_r2 import validate_bundle'),
        ('scripts/run_wc_paper_N07_frozen_shared180_r1.py','scripts/run_wc_paper_N07_refusal_repair180_r2.py')]
    for before,after in edits:
        if changed.count(before)!=1:raise ValueError('Exact repair CPU acceptance binding required')
        changed=changed.replace(before,after)
    restored=changed
    for before,after in reversed(edits):restored=restored.replace(after,before)
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('Numerical/statistical acceptance cannot be weakened')
    namespace={**vars(old),'__package__':'wcomr','RUN':repair.RUN,
        'validate_contract':repair.validate_contract,'validate_launch_authority':repair.validate_launch_authority}
    exec(compile(changed,str(name)+'#independent-repair-bindings-r2','exec'),namespace)
    return namespace['accept'],dict(original_acceptor_sha256=hashlib.sha256(name.read_bytes()).hexdigest(),
        inverse_bytes_and_AST_equal=True,full180_and_93frame_and_grouped_statistics_preserved=True,
        original_source_written=False)


def accept(value,launch,*,bootstrap_repetitions=4096):
    function,proof=derived_acceptor()
    result=function(value,launch,bootstrap_repetitions=bootstrap_repetitions)
    return dict(result,repair_run_id=launch['run_id'],repair_terminal_acceptor_derivation=proof)
