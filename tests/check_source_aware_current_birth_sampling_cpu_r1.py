"""Both full128 scopes with current P birth and preserved C-after-P drift."""
import ast
from pathlib import Path


def run(runtime, tensor_loader, artifact_root):
    path = Path(__file__).with_name('check_source_aware_working_epoch_sampling_cpu_r1.py')
    original = path.read_text()
    changes = [('source_aware_working_epoch_sampling_r1 as working',
        'source_aware_current_birth_sampling_r1 as working'),
        ('    assert len(results)==8 and early>0 and late>0 and P_queries>0',
         "    for check in results:\n"
         "        if check['status'] != 'PASS': continue\n"
         "        import copy\n"
         "        check['current_birth_mutation_refusals'] = []\n"
         "        for fault in ('foreign_current_birth_rule', 'old_P_drift_added_again', 'C_drops_retained_P_floor'):\n"
         "            bad = copy.deepcopy(check['receipt'])\n"
         "            d = bad['requests'][-1]['paths'][2]['collection_complete']['deployment']\n"
         "            if fault == 'foreign_current_birth_rule': d['current_P_birth_rule'] = 'FOREIGN'\n"
         "            elif fault == 'old_P_drift_added_again':\n"
         "                entry = next(h for h in d['history'] if h['action'] == 'PP')\n"
         "                entry['source_policy']['decision']['added_risk'] += .001\n"
         "            else:\n"
         "                entry = next(h for h in d['history'] if h['action'] == 'CC' and h['source_policy']['decision']['state_before'][1] == 'P')\n"
         "                entry['source_policy']['decision']['added_risk'] -= .001\n"
         "            try: working.verify_batch(bad)\n"
         "            except ValueError: check['current_birth_mutation_refusals'].append(fault)\n"
         "            else: raise AssertionError('Wrong current P or later C objective accepted')\n"
         "    assert len(results)==8 and early>0 and late>0 and P_queries>0"),
        ("        'complete_executed_paths':256,'same_synthetic_creation_phase_inputs':True}",
         "        'complete_executed_paths':256,'same_synthetic_creation_phase_inputs':True,\n"
         "        'current_birth_rule': working.CURRENT_BIRTH_RULE,\n"
         "        'additional_current_birth_mutation_refusals': 12}")]
    changed = original
    for before, after in changes:
        if changed.count(before) != 1: raise ValueError('Pinned full256 fixture changed')
        changed = changed.replace(before, after)
    inverse = changed
    for before, after in reversed(changes): inverse = inverse.replace(after, before)
    if inverse != original or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(original)):
        raise ValueError('Original full256 fixture changed outside current-birth controls')
    namespace = {'__name__': 'current_birth_complete_fixture', '__file__': str(path.resolve())}
    exec(compile(changed, __file__+'#complete-current-birth-fixture', 'exec'), namespace)
    return namespace['run'](runtime, tensor_loader, artifact_root)
