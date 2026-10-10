"""Use the original full24 import-only adapter for the new six action arms."""
import ast
from pathlib import Path


def main():
    source=(Path(__file__).resolve().parents[1]/'scripts/check_wc_p0_group_sampling_cpu_r3.py').read_text()
    changes=[('tests/check_partial_mlp_sampling_cpu.py','tests/check_source_aware_action_cost_sampling_cpu_r2.py'),
        ('P0_FULL_GROUP_PIPELINE_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_MODEL','ACTION_COST_FULL_GROUP_SAMPLING_CPU_PASS_NOT_REAL_MODEL'),
        ("        assert bad[0]['complete_scope_retained'] and bad[0]['initial_full_state_restored']",
         "        assert all(len(v['new_action_cost_mutation_refusals'])==6 for v in good)\n"
         "        assert bad[0]['complete_scope_retained'] and bad[0]['initial_full_state_restored']"),
        ('mutation_refusals=10,last_parent_writer_failure_controls=1',
         'mutation_refusals=10,new_action_cost_mutation_refusals=12,last_parent_writer_failure_controls=1')]
    changed=source
    for before,after in changes:
        assert changed.count(before)==1;changed=changed.replace(before,after)
    inverse=changed
    for before,after in reversed(changes):inverse=inverse.replace(after,before)
    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))
    ns={'__name__':'action_cost_full_CPU','__file__':__file__}
    exec(compile(changed,__file__+'#explicit-cost-fixture-rebinding','exec'),ns)
    ns['main']()


if __name__=='__main__':main()
