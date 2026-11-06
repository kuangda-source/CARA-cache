#!/usr/bin/env python3
"""Same full64 real-data wiring scope, with one current-P loss revision."""
import ast
from pathlib import Path


def main():
    path = Path('scripts/check_wc_real_working_epoch_parameters_cpu_r1.py')
    original = path.read_text()
    changes = [
        ('from wcomr.source_aware_working_epoch_control_r2 import WorkingEpochCPDController, STRATEGIES',
         'from wcomr.source_aware_working_epoch_control_r2 import STRATEGIES\n'
         'from wcomr.source_aware_current_birth_control_r1 import CurrentBirthCPDController as WorkingEpochCPDController, CURRENT_BIRTH_RULE', 1),
        ('wc_real_working_epoch_parameters_cpu_r1_preregistration_20261010.json',
         'wc_current_birth_real_parameters_cpu_r1_preregistration_20261010.json', 1),
        ('        bindings.append(evidence)',
         "        evidence['current_P_birth_rule'] = CURRENT_BIRTH_RULE\n"
         "        evidence['parameter_binding_fingerprint'] = hashlib.sha256(json.dumps(evidence, sort_keys=True, allow_nan=False).encode()).hexdigest()\n"
         '        bindings.append(evidence)', 1),
        ('REAL_PARAMETER_FULL64_SCRIPTED_CPU_PASS_NOT_COSMOS_ROLLOUT',
         'CURRENT_BIRTH_REAL_PARAMETER_FULL64_SCRIPTED_CPU_PASS_NOT_COSMOS_ROLLOUT', 1),
        ("    result = {'status':",
         "    old_ref = Path(reg['original_parameter_result_ref'])\n"
         "    old_result = json.loads(old_ref.read_text())\n"
         "    assert sha(old_ref) == reg['original_parameter_result_sha256']\n"
         "    assert old_result['complete_scripted_full36_paths'] == 64 and old_result['scripted_P_actions_not_real_P_calls'] == 0\n"
         "    assert P_pairs > 0\n"
         "    assert [(p['strategy'], p['scene'], p['method']) for p in paths] == [(p['strategy'], p['scene'], p['method']) for p in old_result['paths']]\n"
         "    result = {'current_P_birth_rule': CURRENT_BIRTH_RULE, 'original_full64_P_actions': 0, 'original_parameter_result_sha256': sha(old_ref), 'status':", 1)]
    changed = original
    for before, after, count in changes:
        if changed.count(before) != count:
            raise ValueError('Pinned complete real parameter driver site differs')
        changed = changed.replace(before, after)
    inverse = changed
    for before, after, count in reversed(changes):
        if inverse.count(after) != count:
            raise ValueError('Current-birth complete parameter driver inverse differs')
        inverse = inverse.replace(after, before)
    if inverse != original or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(original)):
        raise ValueError('Complete parameter driver changed outside registered sites')
    namespace = {'__name__': 'current_birth_full64_driver', '__file__': str(path.resolve())}
    exec(compile(changed, __file__+'#source-bound-full64-driver', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__': main()
