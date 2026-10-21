"""The new host predicates must not weaken science, accounting or admission."""
import ast
import copy
import importlib.util
import json
import io
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import four_card_bank24_execution_adapter_r1 as adapter
from check_wc_four_card_bank24_execution_adapter_r1 import exercise_controls
from wc_four_card_bank24_execution_adapter_cpu_r1 import SETUP,CAPTURE


class ExecutionAdapterTest(unittest.TestCase):
    def setUp(self):
        self.original=subprocess.check_output(['git','show',adapter.LIFECYCLE_SOURCE+':src/wcomr/gpu_budget_pool_v2.py'],cwd=ROOT,text=True)
        sys.path.insert(0,str(ROOT/'src'))

    def test_reversible_patch_refuses_foreign_source(self):
        with self.assertRaises(ValueError):adapter.adapt_runner('print("foreign")')

    def test_host_runner_keeps_actual_guards_and_algorithm(self):
        original=subprocess.check_output(['git','show',adapter.LIFECYCLE_SOURCE+':scripts/run_wc_drop1_full18_r1.py'],cwd=ROOT,text=True)
        code,binding=adapter.adapt_runner(original)
        self.assertIn('torch.cuda.get_device_capability()==(8,9)',code)
        self.assertIn('len(net.blocks)==28',code)
        self.assertIn("lease_path=(a.project/'.sync/gpu-locks'",code)
        self.assertIn("life['observed_owners']==(0 if planned['method']=='NATIVE35' else 1)",code)
        self.assertIn('SCOUT_TECHNICAL_STOP_COMPLETE_SCOPE_RETAINED',code)
        self.assertFalse(binding['sampling_or_guardrails_or_readout_changed'])

    def test_only_gpu_predicate_changes_accounting_AST(self):
        port=adapter.adapt_budget_pool(self.original)
        def methods(code):
            cls=next(n for n in ast.parse(code).body if isinstance(n,ast.ClassDef) and n.name=='BudgetPool')
            return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
        old,new=methods(self.original),methods(port)
        self.assertEqual(set(old),set(new))
        self.assertEqual([n for n in old if old[n]!=new[n]],['reserve'])
        self.assertEqual(port.replace("'RTX 6000 Ada' not in gpu['name']","'A6000' not in gpu['name']").replace("gpu['compute_cap'] != '8.9'","gpu['compute_cap'] != '8.6'"),self.original)

    def test_actual_reserve_settle_code21_controls_in_memory(self):
        result=exercise_controls(self.original,adapter.adapt_budget_pool(self.original))
        self.assertEqual(len(result['checks']),21)
        self.assertTrue(all(result['checks'].values()))
        self.assertFalse(result['actual_GPU_ledger_opened'])

    def test_cpu_receipt_cannot_grant_GPU(self):
        with self.assertRaises(ValueError):adapter.require_gpu_prerequisites(dict(execution_adapter_CPU_accepted=True,host_boundary_CPU_accepted=True))

    def test_original_files_not_overridden_by_metadata(self):
        m=json.loads((ROOT/'manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json').read_text())
        self.assertEqual(len(m['original_payload_sha256']),1789)
        self.assertEqual(len(m['additional_metadata_sha256']),29)
        archive=subprocess.check_output(['git','archive','--format=tar',adapter.LIFECYCLE_SOURCE,'--']+list(m['additional_metadata_sha256']),cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            actual={n.name:adapter.digest(source.extractfile(n).read()) for n in source.getmembers() if n.isfile()}
        self.assertEqual(actual,m['additional_metadata_sha256'])
        bad=copy.deepcopy(m['additional_metadata_sha256']);key=next(iter(m['original_payload_sha256']));bad[key]=m['original_payload_sha256'][key]
        with self.assertRaises(ValueError):adapter.verify_inputs(ROOT/'NEVER_READ',m['original_payload_sha256'],bad)

    def test_remote_once_only_templates_compile_and_hide_GPU(self):
        compile(SETUP,'<once-dispatch>','exec');compile(CAPTURE,'<once-collector>','exec')
        self.assertIn('EXISTING_STAGE_RESTORE_ONLY',SETUP)
        self.assertIn('fcntl.LOCK_EX|fcntl.LOCK_NB',SETUP)
        self.assertIn('independent_extra_metadata_sha256',CAPTURE)
        self.assertIn('independent_generated_sha256',CAPTURE)
        self.assertNotIn('nvidia-smi',SETUP+CAPTURE)
        self.assertNotIn('.is_relative_to(',SETUP)
        self.assertIn('PRIOR_STAGE_EXISTS_RESTORE_ONLY',SETUP)


if __name__=='__main__':unittest.main()
