import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paper_timing_acceptance',ROOT/'scripts/audit_cara_paper_timing_cpu_r1.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class AcceptanceTests(unittest.TestCase):
 def test_both_originals(self):
  for h in ('four_card','two_card'):
   c=json.loads((ROOT/f'reports/cara_paper_timing_{h}_CPU_terminal_r2_20261027.json').read_text())
   self.assertEqual(audit.accept(c)['complete_CPU_paths'],18)
 def test_false_acceptance_mutations(self):
  original=json.loads((ROOT/'reports/cara_paper_timing_four_card_CPU_terminal_r2_20261027.json').read_text())
  mutations={
   'still_running':lambda c:c['container_state'].update(Running=True),
   'nonzero_exit':lambda c:c['container_state'].update(ExitCode=1),
   'GPU_exposed':lambda c:c['host_config'].update(DeviceRequests=[{'Count':1}]),
   'CPU_limit':lambda c:c['host_config'].update(NanoCpus=8_000_000_000),
   'runtime_changed':lambda c:c.update(runtime_intact=False),
   'source_changed':lambda c:c.update(payload_intact=False),
   'wrong_host':lambda c:c['CPU_proof'].update(host='two_card'),
   'whole_card_claim':lambda c:c['CPU_proof'].update(whole_method_card_accepted=True),
   'CUDA_initialized':lambda c:c['CPU_proof'].update(CUDA_initialized=True),
   'missing_flow':lambda c:c['CPU_proof']['numeric']['checks'].pop(),
   'missing_role':lambda c:c['CPU_proof']['numeric']['checks'][0]['roles'].pop(),
   'wrong_steps':lambda c:c['CPU_proof']['numeric']['checks'][0]['roles'][1].update(updates=36),
   'changed_alpha':lambda c:c['CPU_proof']['numeric']['checks'][0]['roles'][2].update(original_alpha_history_equal=False),
   'prepare_inside_clock':lambda c:c['CPU_proof']['numeric']['checks'][0].update(event_order=['loop_start','prepare','loop_end','decode','timed_end']),
  }
  for name,change in mutations.items():
   c=copy.deepcopy(original);change(c)
   c['CPU_proof_sha256']=hashlib.sha256((json.dumps(c['CPU_proof'],indent=2,allow_nan=False)+'\n').encode()).hexdigest()
   with self.subTest(name=name),self.assertRaises(AssertionError):audit.accept(c)
