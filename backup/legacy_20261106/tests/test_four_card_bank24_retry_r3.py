import ast
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import four_card_bank24_gpu_port_r1 as port
import four_card_bank24_execution_tools_r1 as tools
import wc_four_card_bank24_execution_r2 as transport
import wc_four_card_bank24_execution_cpu_r3 as cpu


class RetryBindingTests(unittest.TestCase):
    def test_physical_attempt_is_distinct_from_frozen_scientific_identity(self):
        config = json.loads(Path('configs/wc_scout_bank24_production_entry_r1_20261018.json').read_text())
        self.assertEqual(config['run_id'], port.SCIENTIFIC_RUN)
        self.assertNotEqual(port.SCIENCE_RUN, port.SCIENTIFIC_RUN)
        self.assertTrue(tools.TARGET_STAGE.endswith('-r3-20261022'))
        self.assertEqual(config['scope_counts']['total_paths'], 24)

    def test_runner_and_post_share_new_output_without_mutating_original_run_mapping(self):
        original = {'BANK24': port.SCIENTIFIC_RUN, 'CAL12': 'cal-original'}
        namespace = {'RUNS': original, 'SCIENCE_RUN': port.SCIENCE_RUN}
        nodes = [n for n in ast.parse(port.contract_source()).body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in ('RUN', 'RUNS') for t in n.targets)]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<attempt-output-binding>', 'exec'), namespace)
        self.assertEqual(namespace['RUN'], port.SCIENCE_RUN)
        self.assertEqual(namespace['RUNS']['BANK24'], port.SCIENCE_RUN)
        self.assertEqual(original['BANK24'], port.SCIENTIFIC_RUN)
        self.assertEqual(namespace['RUNS']['CAL12'], 'cal-original')

    def test_production_cpu_validates_the_actual_retry_transport(self):
        self.assertIn('wc_four_card_bank24_execution_r2.py', tools.PRODUCTION_SCRIPTS)
        self.assertIn('wc_four_card_bank24_execution_r2.py', cpu.PAYLOADS)
        self.assertNotIn('wc-bank24-fourcard-full-execution-r1-20261022', transport.REMOTE_LAUNCH)
        ast.parse(transport.REMOTE_LAUNCH)
        ast.parse(cpu.SETUP)
        ast.parse("L={};MODE='terminal'\n" + cpu.CAPTURE)


if __name__ == '__main__':
    unittest.main()
