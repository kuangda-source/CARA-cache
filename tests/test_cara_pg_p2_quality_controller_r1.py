"""CPU controller fault guards only; no SSH, Docker, model or GPU calls."""
import base64,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('quality_controller',ROOT/'scripts/wc_four_card_cara_pg_p2_quality_cpu_r1.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Guards(unittest.TestCase):
 def setUp(self):
  reg={'CPU_FIXTURE_ONLY':True};raw=b'{"CPU_FIXTURE_ONLY":true}'
  self.v=dict(registration=reg,launch={'registration_sha256':hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()},
    container=dict(state=dict(Running=False,ExitCode=0),readonly_root=True,devices=[],device_requests=[],network='none',nano_cpus=10**9,memory=8*2**30),
    files={'synthetic.json':dict(exists=True,raw_base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest(),data={'CPU_FIXTURE_ONLY':True})})
 def accept(self):
  with patch('accept_wc_N10_models_cpu_r1.accept',return_value={'DECLARED_CPU_FIXTURE':True}):return m.accept(self.v)
 def test_transport_code_compiles(self):
  for code in (m.PREFLIGHT,m.DEPLOY,m.CAPTURE):compile(code,'declared_remote_body','exec')
 def test_synthetic_complete_guard(self):self.assertTrue(self.accept()['DECLARED_CPU_FIXTURE'])
 def test_container_isolation(self):
  for k,v in [('readonly_root',False),('devices',[{}]),('device_requests',[{}]),('network','default'),('nano_cpus',2*10**9),('memory',16*2**30)]:
   old=copy.deepcopy(self.v);self.v['container'][k]=v
   with self.assertRaises(ValueError):self.accept()
   self.v=old
 def test_live_or_failed_container(self):
  for field,value in [('Running',True),('ExitCode',1)]:
   old=copy.deepcopy(self.v);self.v['container']['state'][field]=value
   with self.assertRaises(ValueError):self.accept()
   self.v=old
 def test_original_raw_bytes(self):
  self.v['files']['synthetic.json']['data']['CPU_FIXTURE_ONLY']=False
  with self.assertRaises(ValueError):self.accept()
 def test_registration_changed(self):
  self.v['registration']['CPU_FIXTURE_ONLY']=False
  with self.assertRaises(ValueError):self.accept()
if __name__=='__main__':unittest.main()
