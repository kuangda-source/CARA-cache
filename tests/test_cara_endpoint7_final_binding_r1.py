"""Selected46 actual frozen command construction and refusal gates; no GPU calls."""
import copy,json,unittest
from pathlib import Path
import test_cara_s_endpoint_gpu_dispatch_r1 as original
from wcomr import cara_s_endpoint_gpu_dispatch_r1 as dispatch
from wcomr.gpu_budget_pool_v2 import sha

class FinalBinding(unittest.TestCase):
 endpoint7=True
 setUp=original.DispatchTests.setUp
 write=original.DispatchTests.write
 write_all=original.DispatchTests.write_all
 refresh=original.DispatchTests.refresh
 invoke_dispatch=original.DispatchTests.invoke_dispatch
 publish=original.DispatchTests.publish
 test_original_guardian=original.DispatchTests.test_original_guardian_publication_binds_frozen_commands_and_runner_context
 test_recovery_without_spawn=original.DispatchTests.test_second_call_recovers_before_admission_or_spawn_even_with_dead_or_unknown_guardian
 test_no_approval=original.DispatchTests.test_missing_approval_refused_before_intent
 test_source_CPU_quote=original.DispatchTests.test_changed_source_incomplete_CPU_and_partial_quote_refused
 test_stale_central=original.DispatchTests.test_stale_or_changed_central_original_refused
 test_admission_failure=original.DispatchTests.test_admission_failure_does_not_write_intent
 def test_exact46_container_and_storage(self):
  command=dispatch.frozen_commands(self.project,self.stage,self.reg,self.auth,self.f.profile,self.storage)['container_cli']
  self.assertIn(str(self.stage/'scripts/cara_s_endpoint_supervisor_worker_r1.py'),command)
  self.assertEqual(self.f.profile['physical_paths'],46);self.assertEqual(self.f.profile['new_scoring_pairs'],16)
  self.assertEqual(self.f.profile['storage']['minimum_host_free_before_provision_bytes'],80*2**30)
  self.storage.config['minimum_output_free_bytes']=4*2**30
  with self.assertRaisesRegex(ValueError,'private output'):dispatch.frozen_commands(self.project,self.stage,self.reg,self.auth,self.f.profile,self.storage)
 def test_seven_flag_and_host_floor_required(self):
  profile=copy.deepcopy(self.f.profile);profile['endpoint7']=False
  with self.assertRaisesRegex(ValueError,'whole container'):dispatch.frozen_commands(self.project,self.stage,self.reg,self.auth,profile,self.storage)
  profile=copy.deepcopy(self.f.profile);profile['storage']['minimum_host_free_bytes']=128*2**20
  with self.assertRaisesRegex(ValueError,'storage floors'):dispatch.frozen_commands(self.project,self.stage,self.reg,self.auth,profile,self.storage)
if __name__=='__main__':unittest.main()
