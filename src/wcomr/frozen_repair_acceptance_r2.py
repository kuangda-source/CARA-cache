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


def accept_after_human_wait_override(value, launch, authority, *, bootstrap_repetitions=4096):
    """The specific human instruction changes waiting time, never scientific gates."""
    if (authority.get('human_quote') != 'gpu 生成完了那就直接验收呗'
            or authority.get('scope') != 'ORIGINAL_R2_READONLY_TERMINAL_COLLECTION_ONLY'
            or authority.get('launch') != launch
            or launch.get('source_revision') != '6e10aa31197b4c137705b9117090c3a4e538e863'
            or launch.get('run_id') != 'wc-paper-n07-refusal-repair180-r2'
            or authority.get('launch_sha256') != '56f4dca57f4e9f124d8fe69b36ae28a60f85bc39dc8286b0f5ba05ff174ebb7b'
            or authority.get('CPU_acceptance_sha256') != 'b233c3a5c5f8e88ee2c866b3ec858a00dccdb1a214db361c92e2c033a0ea35ac'
            or authority.get('GPU_done_health_sha256') != '0020bbf4f59c43c77c6e84cf1d00f1d6dd17f440bc873c0b14b419eedbd3282d'
            or authority.get('new_GPU_submissions') != 0
            or authority.get('server_or_budget_mutation') is not False
            or not isinstance(authority.get('authorized_at_unix'), (int, float))
            or not launch['started_unix'] < authority['authorized_at_unix'] <= value['observed_unix']):
        raise ValueError('Exact source-bound human waiting override required')
    from . import frozen_shared_acceptance_r1 as old
    function, proof = derived_acceptor()
    source = dedent(inspect.getsource(old.accept))
    edits = [
        ('from .frozen_shared_cpu_acceptance_r1 import validate_bundle',
         'from .frozen_repair_cpu_acceptance_r2 import validate_bundle'),
        ('scripts/run_wc_paper_N07_frozen_shared180_r1.py',
         'scripts/run_wc_paper_N07_refusal_repair180_r2.py'),
        ("if value['observed_unix'] < launch['next_check_not_before_unix']:",
         "if value['observed_unix'] < launch['next_check_not_before_unix'] and not human_wait_override:")]
    changed = source
    for before, after in edits:
        if changed.count(before) != 1:
            raise ValueError('Original independent acceptance guard changed')
        changed = changed.replace(before, after)
    restored = changed
    for before, after in reversed(edits):
        restored = restored.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('Only the explicit local ETA guard may change')
    namespace = {**function.__globals__, 'human_wait_override': True}
    exec(compile(changed, str(Path(old.__file__)) + '#explicit-human-wait-override', 'exec'), namespace)
    result = namespace['accept'](value, launch, bootstrap_repetitions=bootstrap_repetitions)
    return dict(result, repair_run_id=launch['run_id'], repair_terminal_acceptor_derivation=proof,
        direct_human_waiting_override=authority,
        waiting_override_derivation=dict(inverse_bytes_and_AST_equal=True,
            original_scheduled_ETA_preserved=launch['next_check_not_before_unix'],
            numerical_scope_statistics_and_cost_gates_unchanged=True))
