"""Reject changed upstream bytes and retain the controller's candidate denominator."""
import ast
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budcache_audit', ROOT/'scripts/audit_cara_budcache_source_r1.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SourceAuditTests(unittest.TestCase):
    def test_changed_upstream_bytes_are_rejected_before_execution(self):
        with TemporaryDirectory() as directory:
            Path(directory, 'LICENSE').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Pinned upstream bytes differ: LICENSE'):
                audit.audit(Path(directory))

    def test_missing_original_controller_functions_are_rejected(self):
        config = dict(task='CPU_FIXTURE')
        with self.assertRaisesRegex(ValueError, 'Expected original search functions missing'):
            audit.controller_probe(ast.parse('def main(): pass'), config, 0)

    def test_quota_violation_in_controller_is_rejected(self):
        source = '''
def mutate_schedule(schedule): return schedule
def get_swap_neighbors(schedule): return []
def main():
    cfg = load_config('fixture')
    pipe = src.wan.WanT2V()
    pipe.model.enable_budcache = True
    pipe.model.cache_schedule = [1, 0, 0, 0]
    get_latents(pipe, cfg)
'''
        with self.assertRaisesRegex(ValueError, 'Original controller changed quota'):
            audit.controller_probe(ast.parse(source), dict(task='CPU_FIXTURE', steps=4, nfe=2), 0)


if __name__ == '__main__':
    unittest.main()
