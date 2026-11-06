import copy,hashlib,json,tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_cara_cal_select_exposure_r1 import accepted_p1_unused_select
REF='reports/cara_PG_P1_original_terminal_codec_recovered_20261024_0035.json'
class Exposure(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'reports').mkdir()
  rows=[dict(id=f'x{i}',split='CAL_SELECT' if i<10 else 'CAL_FIT',status='UNUSED_REGISTERED_UPPER_BOUND') for i in range(64)]
  self.data=dict(launch={'launch_id':'old'},files={'runner':{'raw_utf8':json.dumps(dict(batch=dict(rows=rows,status='BUDGET_NOT_VERIFIED',selection_frozen=None)))}},requests={},scores={},artifact_checks={})
  self.save()
 def save(self):
  raw=json.dumps(self.data).encode();(self.root/REF).write_bytes(raw)
  self.acc=dict(capture_ref=REF,capture_sha256=hashlib.sha256(raw).hexdigest(),full_protocol_accepted=True,launch_id='old',scientific={'selected_policy':None})
  (self.root/'reports/cara_PG_P1_original_terminal_accepted_20261024_0037.json').write_text(json.dumps(self.acc))
 def tearDown(self):self.tmp.cleanup()
 def test_exact_unused_original(self):self.assertTrue(accepted_p1_unused_select(REF,self.data,self.root))
 def test_added_request_blocks_even_with_hash_binding(self):
  self.data['requests']['x0']={};self.save();self.assertFalse(accepted_p1_unused_select(REF,self.data,self.root))
 def test_changed_original_blocked(self):
  other=copy.deepcopy(self.data);other['artifact_checks']['x0']={};self.assertFalse(accepted_p1_unused_select(REF,other,self.root))
 def test_executed_select_blocks(self):
  d=json.loads(self.data['files']['runner']['raw_utf8']);d['batch']['rows'][0]['status']='COMPLETE';self.data['files']['runner']['raw_utf8']=json.dumps(d);self.save();self.assertFalse(accepted_p1_unused_select(REF,self.data,self.root))
if __name__=='__main__':unittest.main()
