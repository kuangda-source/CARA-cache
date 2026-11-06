import copy,json,tempfile,unittest
from pathlib import Path
from wcomr.wc_time_card_r1 import select_tau
from wcomr.wc_time_collection_r1 import collect_phase,freeze_selection
ROOT=Path(__file__).resolve().parents[1]
CARD=json.loads((ROOT/'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml').read_text())
class Lifecycle(unittest.TestCase):
 def rows(self):return [dict(scene=s,tau=t,status='COMPLETE',T_DD=100,CARA_T_DD=100,Alex=t) for s in CARD['selection']['CAL'] for t in (.04,.06)]
 def test_selection_complete_and_unmatched(self):
  r=self.rows();self.assertEqual(select_tau(r,CARD['selection']['CAL'])['selected_tau'],.04)
  for x in r:x['T_DD']=120 if x['tau']==.04 else 110
  self.assertEqual(select_tau(r,CARD['selection']['CAL'])['selected_tau'],.06)
  self.assertEqual(select_tau(r,CARD['selection']['CAL'])['time_match'],'UNMATCHED')
  for bad in [r[:-1],r+[r[0]],r[:3]+[r[0]]]:
   with self.assertRaises(ValueError):select_tau(bad,CARD['selection']['CAL'])
  for k,v in [('Alex',float('nan')),('T_DD',0),('status','TEXT_REJECTED')]:
   bad=copy.deepcopy(r);bad[0][k]=v
   with self.assertRaises(ValueError):select_tau(bad,CARD['selection']['CAL'])
 def test_failure_denominator_and_no_overwrite(self):
  class Adapter:
   card=CARD;inference=None
   def __call__(self,s,p):raise OSError('injected')
  state=[]
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(OSError):collect_phase(Adapter(),'A',Path(p)/'A',before_request=lambda s:None,save=lambda s:state.append(copy.deepcopy(s)),after_diagnostics=lambda s:dict(passed=True))
   self.assertEqual(len(state[-1]['rows']),26);self.assertEqual(state[-1]['rows'][0]['status'],'TECH_FAILED')
   self.assertEqual(sum(r['status']=='NOT_REACHED' for r in state[-1]['rows']),25)
   with self.assertRaises(FileExistsError):collect_phase(Adapter(),'A',Path(p)/'A',before_request=lambda s:None,save=lambda s:None,after_diagnostics=lambda s:dict(passed=True))
 def test_release_freeze_and_candidate_identity(self):
  phase=dict(phase='A',scope_sha256=CARD['scope_sha256'],status='TERMINAL',rows=[dict(slot=s,status='COMPLETE',result=dict(T_DD=100)) for s in CARD['physical_matrix'] if s['section'].startswith('A_')])
  release=dict(phase='A',scope_sha256=CARD['scope_sha256'],GPU_released=True,cost_settled=True,original_process_exited=True,numerical_GPU_equivalence_passed=True,CPU_SYNTHETIC_FIXTURE=True)
  scores=[]
  for s in CARD['physical_matrix']:
   if s['section']=='A_CALIBRATION':scores.append(dict(slot_id=s['id'],reference_slot_id=next(x['id'] for x in CARD['physical_matrix'] if x['section']=='A_ANCHOR' and x['role']=='NATIVE_U36' and x['scene']==s['scene']),status='SCORED',frames=93,Alex=s['tau']))
  with tempfile.TemporaryDirectory() as p:
   for field in ['GPU_released','cost_settled','original_process_exited','numerical_GPU_equivalence_passed']:
    with self.assertRaises(ValueError):freeze_selection(CARD,phase,{**release,field:False},scores,Path(p)/field)
   bad=copy.deepcopy(scores);bad[0]['reference_slot_id']='WRONG_NATIVE'
   with self.assertRaises(ValueError):freeze_selection(CARD,phase,release,bad,Path(p)/'wrong')
   f=Path(p)/'frozen.json';value=freeze_selection(CARD,phase,release,scores,f);self.assertEqual(value['selected_tau'],.04)
   with self.assertRaises(ValueError):freeze_selection(CARD,phase,release,scores,f)
 def test_exact_diagnostic_gate_and_input_mismatch(self):
  import hashlib,torch,numpy as np
  from contextlib import contextmanager
  from unittest.mock import patch
  from wcomr.wc_time_diagnostics_r1 import verify
  @contextmanager
  def decoded(path):yield iter((np.zeros((2,2,3),dtype=np.uint8),i,None) for i in range(93))
  with tempfile.TemporaryDirectory() as directory:
   f=Path(directory)/'tiny.pt';torch.save(dict(final_latent=torch.ones(2),guided=[torch.ones(2)]*36),f)
   a=dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
   rows=[dict(slot=x,status='COMPLETE',tensor_artifact=a,diagnostic_inputs=dict(entry_rng='same',exit_rng='same',first_CFG_inputs=['same','same']),result=dict(video_path='declared_CPU_mock',actions=['DD']*36)) for x in CARD['physical_matrix'] if x['section']=='A_DIAGNOSTIC']
   with patch('wcomr.wc_time_diagnostics_r1.decoded_video',decoded):
    self.assertTrue(verify(rows)['passed'])
    bad=copy.deepcopy(rows);bad[0]['diagnostic_inputs']['entry_rng']='different'
    with self.assertRaises(ValueError):verify(bad)
    bad=copy.deepcopy(rows);bad[2]['result']['actions'][5]='CC'
    with self.assertRaises(ValueError):verify(bad)
if __name__=='__main__':unittest.main()
