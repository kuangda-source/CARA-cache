"""Execute actual durable dispatch body on CPU; no SSH/sudo/CUDA or child launch."""
import hashlib,io,json,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wc_four_card_cara_pg_gpu_r1 as c


class Entry(unittest.TestCase):
 def exercise(self,recovery=False,existing_output=False):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);stage=root/'stage';stage.mkdir();runtime=root/'runtime';runtime.mkdir()
   sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
   meta=dict(job=str(runtime),status='NATIVE_CONTROL_PYTHON_CPU_PASS',exit_code=0)
   for n,k in [('bin/python3','wrapper_sha256'),('usr-local/bin/python3.10','python_sha256'),('lib/ld-linux-x86-64.so.2','loader_sha256'),('manifest.json','manifest_sha256')]:
    f=runtime/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('CPU FIXTURE');meta[k]=sha(f)
   (runtime/'result.json').write_text('{"status":"NATIVE_CONTROL_PYTHON_CPU_PASS"}')
   for n in ('config','proof','pg-independent-CPU-acceptance.json'):(stage/n).write_text('{}')
   counts={'CPU_FIXTURE':True};L=dict(stage=str(stage),registration_sha256='reg')
   auth=dict(source_revision='src',registration_sha256='reg',config_sha256=sha(stage/'config'),production_CPU_sha256=sha(stage/'proof'),scope_counts=counts,billed_limit_GPUh=10.5,independent_CPU_acceptance_sha256=sha(stage/'pg-independent-CPU-acceptance.json'),launch_id='original',gpu_uuid='GPU-fixture',forecast_GPUh=8.,controller_source_revision='src')
   p=dict(stage_ref=L,auth=auth,control_runtime=meta,sudo_password='CPU_FIXTURE',recovery_controller_revision='fixed')
   if recovery:
    (stage/'pg-GPU-authorization.json').write_text(json.dumps(auth));p['authorization_sha256']=sha(stage/'pg-GPU-authorization.json')
   before=(stage/'pg-GPU-authorization.json').read_bytes() if recovery else None
   if existing_output:(root/'outputs'/'fixture-run').mkdir(parents=True)
   child=MagicMock();child.pid=123;child.stdin=MagicMock()
   namespace=dict(root=root,L=L,reg={'source_revision':'src'},sha=sha,read=lambda p:json.loads(p.read_text()),RUN='fixture-run',CONFIG='config',CPU_PROOF='proof',COUNTS=counts,value={'admissible':True},c={'forecast_complete_GPUh':8.,'billed_limit_GPUh':10.5},pool={'jobs':{}},time=time,hashlib=hashlib,subprocess=types.SimpleNamespace(Popen=MagicMock(return_value=child),PIPE=-1,STDOUT=-2))
   source=c.LAUNCH_PREFIX+(c.authorization_continuation() if recovery else c.LAUNCH_SUFFIX)
   try:
    with patch.object(sys,'stdin',io.StringIO(json.dumps(p))),patch.object(sys,'stdout',io.StringIO()),patch('wcomr.gpu_budget_pool_v2.process_identity',return_value={'pid':123,'start_ticks':456}):
     if existing_output:
      with self.assertRaises(AssertionError):exec(source,namespace)
      namespace['subprocess'].Popen.assert_not_called();return
     exec(source,namespace)
    self.assertEqual(json.loads((stage/'pg-GPU-launch.json').read_text())['launch_id'],'original')
    self.assertEqual(namespace['subprocess'].Popen.call_count,1)
    self.assertTrue((stage/'pg-GPU-intent.json').exists())
    if recovery:self.assertEqual(before,(stage/'pg-GPU-authorization.json').read_bytes())
   finally:
    if 'lock' in namespace:namespace['lock'].close()
 def test_actual_initial_body_fsync_and_environment(self):self.exercise()
 def test_actual_recovery_body_keeps_original_authorization(self):self.exercise(recovery=True)
 def test_recovery_rejects_existing_output_before_child(self):self.exercise(recovery=True,existing_output=True)

if __name__=='__main__':unittest.main()
