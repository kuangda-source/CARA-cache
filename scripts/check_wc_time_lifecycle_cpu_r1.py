"""CPU-only control-plane tests, separate from numerical role evidence."""
import argparse,hashlib,json,os,sys,time,unittest,signal
from pathlib import Path
p=argparse.ArgumentParser()
for k in ('runtime','stage','output'):p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--host',required=True);a=p.parse_args();signal.alarm(60);start=time.time()
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and not a.output.exists()
sys.path[:0]=[str(a.stage/'src'),str(a.stage/'tests')]
reg=json.loads((a.stage/'registration.json').read_text())
assert all(hashlib.sha256((a.stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items())
import torch
assert not torch.cuda.is_initialized()
import test_wc_time_lifecycle_r1
x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_wc_time_lifecycle_r1));assert x.wasSuccessful()
a.output.write_text(json.dumps(dict(status='WC_TIME_LIFECYCLE_CPU_PASS',host=a.host,tests=x.testsRun,CPU_wall_seconds=time.time()-start,CUDA_initialized=False,GPU_submissions=0,payload_sha256=reg['payload_sha256']),indent=2)+'\n')
