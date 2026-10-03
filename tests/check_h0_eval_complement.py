"""Run pinned shadow controls from default-mode toys through the actual adapter."""
import ast
from pathlib import Path

import torch

from wcomr.h0_mode import establish_shared_eval, verify_shared_eval


def run(source_path, old_test_path):
    receipts = []

    def adapt_eval(net):
        assert net.training and any(m.training for m in net.modules())
        receipt = establish_shared_eval(net)
        verify_shared_eval(net, receipt)
        receipts.append(receipt)
        return net

    class Startup(ast.NodeTransformer):
        replaced = 0

        def visit_Call(self, node):
            node = self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'eval':
                assert not node.args and not node.keywords
                self.replaced += 1
                return ast.copy_location(ast.Call(
                    func=ast.Name(id='adapt_eval', ctx=ast.Load()),
                    args=[node.func.value], keywords=[]), node)
            return node

    tree = ast.parse(Path(old_test_path).read_text())
    startup = Startup()
    tree = ast.fix_missing_locations(startup.visit(tree))
    assert startup.replaced == 3  # two paired arms and the failure arm
    namespace = {'adapt_eval': adapt_eval}
    exec(compile(tree, str(old_test_path), 'exec'), namespace)
    checks = namespace['run_cpu_controls'](source_path)
    assert len(receipts) == 5 and all(x['after']['training_modules'] == 0 for x in receipts)
    assert not torch.cuda.is_initialized()
    return {
        'default_mode_startups': len(receipts),
        'all_setup_before_shadow_and_strict_eval_guard_retained': True,
        'pinned_four_arm_and_nonfinite_failure_controls': checks,
        'interpretation': 'Synthetic kernels and CPU wiring, no native weights or GPU gain',
    }
