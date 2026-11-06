"""Only the declared Native request bounds change in the Q5 bridge."""
import ast
from pathlib import Path
import unittest

from wcomr.cara_q5_native50_r1 import native50_ast, full50_ast

ROOT = Path(__file__).resolve().parents[1]


def execute_source(name):
    module=ast.parse((ROOT/name).read_text())
    fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
    return ast.unparse(fn)


class Q5SourceTests(unittest.TestCase):
    def test_native_guard_inverse_preserves_complete_function(self):
        source=execute_source('src/wcomr/policy_generator_r1/p2_native_sampling.py')
        tree=native50_ast(source)
        for node in ast.walk(tree):
            if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],ast.NotIn):
                self.assertEqual(ast.unparse(node.comparators[0]),'(50,)')
                node.comparators[0]=ast.parse('range(18,36)',mode='eval').body
            if isinstance(node,ast.Constant) and node.value=='Registered Native50 grid required':
                node.value='Registered Native 18..35 step grid required'
        self.assertEqual(ast.dump(tree),ast.dump(ast.parse(source)))

    def test_complete_request_inverse_preserves_all_other_operations(self):
        source=execute_source('src/wcomr/clean_speed20_r1.py')
        changed=full50_ast(source)
        for node in ast.walk(changed):
            if isinstance(node,ast.Constant):
                if type(node.value)is int and node.value in (50,51):node.value={50:35,51:36}[node.value]
                elif node.value=='Exact complete method/50-step guarded request required':node.value='Exact complete method/35-step guarded request required'
                elif node.value=='Complete guarded requested50/51-update output missing':node.value='Complete guarded full36 output missing'
        self.assertEqual(ast.dump(changed),ast.dump(ast.parse(source)))

    def test_changed_parent_sites_refused(self):
        native=execute_source('src/wcomr/policy_generator_r1/p2_native_sampling.py')
        with self.assertRaisesRegex(ValueError,'range guard'):native50_ast(native.replace('range(18, 36)','range(18, 37)'))
        full=execute_source('src/wcomr/clean_speed20_r1.py')
        with self.assertRaisesRegex(ValueError,'bounds changed'):full50_ast(full.replace('sample.num_steps != 35','sample.num_steps != 34'))


if __name__=='__main__':unittest.main()
