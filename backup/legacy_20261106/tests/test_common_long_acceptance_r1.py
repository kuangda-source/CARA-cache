import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_cara_common_long_cpu_r1 import accept
class AcceptanceTests(unittest.TestCase):
 def test_dual_originals(self):
  for host in ('four_card','two_card'):
   p=ROOT/f'reports/cara_common_long_{host}_CPU_terminal_r2_20261027.json'
   self.assertEqual(accept(json.loads(p.read_text()))['host'],host)
 def test_semantic_and_resource_faults(self):
  original=json.loads((ROOT/'reports/cara_common_long_four_card_CPU_terminal_r2_20261027.json').read_text())
  for fault in ('exit','oom','gpu','memory','source','states','positions','short','teacher','free','fault_missing','timing'):
   cap=copy.deepcopy(original);p=cap['CPU_proof'];n=p['numeric']
   if fault=='exit':cap['container_state']['ExitCode']=1
   elif fault=='oom':cap['container_state']['OOMKilled']=True
   elif fault=='gpu':cap['host_config']['DeviceRequests']=[{'Count':1}]
   elif fault=='memory':cap['host_config']['Memory']=8*2**30
   elif fault=='source':cap['payload_intact']=False
   elif fault=='states':n['selected_states']=23
   elif fault=='positions':n['readout_positions']=144
   elif fault=='short':n['short_A_exact']=False
   elif fault=='teacher':n['teacher_free_candidate']=False
   elif fault=='free':n['candidate_free_running']=True
   elif fault=='fault_missing':n['checks'][0]['failed_boundary_attempts'].pop()
   elif fault=='timing':n['dual_clocks']=False
   cap['CPU_proof_sha256']=hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
   with self.subTest(fault=fault),self.assertRaises(AssertionError):accept(cap)
if __name__=='__main__':unittest.main()
