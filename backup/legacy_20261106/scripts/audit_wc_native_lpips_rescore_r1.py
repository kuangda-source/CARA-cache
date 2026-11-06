"""Read-only old-video CPU re-score: original Alex and official PIQ VGG metric.

No generation, GPU, configuration edits, fit or change to old acceptance.
One-frame execution and a cached frozen PIQ instance bound memory; official
compute_metrics function is executed unchanged on each frame.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse,ast,hashlib,json,time,traceback,sys
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args();s=a.stage
 cfg=json.loads((s/'scope.json').read_text());os.environ['TORCH_HOME']=str(s/'torch')
 os.sched_setaffinity(0,set(cfg['CPU_affinity']))
 sys.path[:0]=[str(s/'site'),cfg['original_lpips_site']]
 import torch,numpy as np,av,mediapy,piq,lpips
 torch.set_num_threads(len(cfg['CPU_affinity']));torch.set_num_interop_threads(1)
 assert not torch.cuda.is_initialized()
 start=time.time();r=dict(status='RUNNING',started_unix=start,rows=[],GPU_submissions=0,new_generation=0,scope_sha256=sha(s/'scope.json'),worker_sha256=sha(__file__),official_script_sha256=sha(s/'official_evaluate.py'),packages=dict(torch=torch.__version__,piq=piq.__version__,lpips='0.1.4',av=av.__version__),CPU_affinity=sorted(os.sched_getaffinity(0)),adaptation='official function unchanged, cache metric object, frame batch 1, mean of all93; no resize or trim triggered')
 def save():
  q=s/'result.tmp';q.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');q.replace(s/'result.json')
 save()
 try:
  alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).eval().cpu()
  vgg=piq.LPIPS().eval().cpu()
  import types
  proxy=types.SimpleNamespace(LPIPS=lambda:vgg,psnr=piq.psnr,ssim=piq.ssim)
  tree=ast.parse((s/'official_evaluate.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compute_metrics')
  from typing import Dict
  ns=dict(torch=torch,piq=proxy,Dict=Dict);exec(compile(ast.Module(body=[fn],type_ignores=[]),'official_evaluate.py','exec'),ns)
  r['weight_sha256']={str(p):sha(p) for p in (s/'torch/hub/checkpoints').iterdir() if p.is_file()}
  for pair in cfg['pairs']:
   paths=[pair[k]['path'] for k in ['candidate','reference']]
   for k in ['candidate','reference']:assert sha(pair[k]['path'])==pair[k]['sha256']
   # mediapy is the official reader. Verify its entire decoded RGB stream
   # against historical PyAV and verify both original PTS sequences.
   videos=[mediapy.read_video(p) for p in paths];streams=[]
   for path,v in zip(paths,videos):
    assert v.shape==(93,432,768,3) and v.dtype==np.uint8
    with av.open(path) as con:
     frames=list(con.decode(video=0));assert len(frames)==93
     assert all(np.array_equal(fr.to_ndarray(format='rgb24'),v[i]) for i,fr in enumerate(frames))
     streams.append([(fr.pts,str(fr.time_base)) for fr in frames])
   assert streams[0]==streams[1]
   row=dict(scene=pair['scene'],variant=pair['variant'],reference=pair['reference'],candidate=pair['candidate'],frames=93,PTS_equal=True,all_RGB_reader_equal=True,alex=[],piq_vgg=[],PSNR=[],SSIM=[])
   for i,(pred,gt) in enumerate(zip(*videos)):
    x=torch.from_numpy(pred.copy()).permute(2,0,1).unsqueeze(0);y=torch.from_numpy(gt.copy()).permute(2,0,1).unsqueeze(0)
    with torch.inference_mode():
     aa=float(alex(x.float()/127.5-1,y.float()/127.5-1).item());vv=ns['compute_metrics'](x,y)
     if i==0 and not r.get('controls'):
      assert float(alex(x.float()/127.5-1,x.float()/127.5-1))==0
      assert float(vgg(x.float()/255,x.float()/255))==0
      # Same input/repeat and batch grouping controls under published PIQ defaults.
      bx=torch.cat([x,y]).float()/255;by=torch.cat([y,x]).float()/255
      assert abs(float(vgg(bx,by))-vv['lpips'])<1e-6
      r['controls']=dict(Alex_self_zero=True,PIQ_self_zero=True,PIQ_two_frame_batch_mean_parity=True)
    assert np.isfinite([aa,vv['lpips'],vv['psnr'],vv['ssim']]).all()
    row['alex'].append(aa);row['piq_vgg'].append(vv['lpips']);row['PSNR'].append(vv['psnr']);row['SSIM'].append(vv['ssim'])
   row.update(alex_mean=float(np.mean(row['alex'])),piq_vgg_mean=float(np.mean(row['piq_vgg'])),historical_alex_mean=pair['historical_alex_mean'])
   row['max_frame_abs_diff_from_historical']=float(np.max(np.abs(np.array(row['alex'])-pair['historical_frame_distances'])))
   assert row['max_frame_abs_diff_from_historical']<1e-6
   for k in ['candidate','reference']:assert sha(pair[k]['path'])==pair[k]['sha256']
   r['rows'].append(row);save();print(pair['scene'],pair['variant'],row['alex_mean'],row['piq_vgg_mean'],flush=True)
  r.update(status='COMPLETE_ORIGINAL_ALEX_REPRODUCED_AND_OFFICIAL_PIQ_RESCORED',CUDA_initialized=torch.cuda.is_initialized(),exit_code=0)
  assert len(r['rows'])==len(cfg['pairs']) and not r['CUDA_initialized']
 except BaseException as e:
  r.update(status='FAILED_DENOMINATOR_PRESERVED',error=repr(e),exit_code=1);traceback.print_exc();raise
 finally:r.update(ended_unix=time.time(),CPU_wall_seconds=time.time()-start);save()
if __name__=='__main__':main()
