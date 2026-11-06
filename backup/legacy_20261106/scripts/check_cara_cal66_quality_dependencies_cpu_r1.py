#!/usr/bin/env python3
"""Import only the isolated quality environment; never download or use CUDA."""
import argparse,importlib,importlib.metadata,json,os,time,traceback
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and not a.output.exists()
 import torch
 torch.set_num_threads(1)
 def deny(*a,**k):raise RuntimeError('CPU dependency check forbids CUDA/downloads')
 torch.cuda._lazy_init=deny;torch.hub.download_url_to_file=deny
 rows=[]
 for name in ('torchvision','timm','pyiqa','clip','lmdb','easydict','omegaconf','decord','cv2','filterpy','tensorboard'):
  try:
   module=importlib.import_module(name);rows.append(dict(module=name,status='PASS',source=getattr(module,'__file__',None)))
  except Exception as e:rows.append(dict(module=name,status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()))
 assert not torch.cuda.is_initialized()
 passed=all(r['status']=='PASS' for r in rows)
 value=dict(status='QUALITY_DEPENDENCIES_IMPORT_PASS' if passed else 'QUALITY_DEPENDENCIES_IMPORT_FAILED',observed_unix=time.time(),rows=rows,versions={n:importlib.metadata.version(n) for n in ('pyiqa','timm','easydict','openai-clip')},base_environment_modified=False,CUDA_initialized=False,GPU_submissions=0)
 with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=value['status'],failed=[r['module'] for r in rows if r['status']=='FAIL'])))
 raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
