"""CPU-only official-reader LPIPS, immutable A freeze; B's 28x4 original metrics."""
import argparse,json,os,sys,time,math,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
 from wcomr.wc73_execution_r1 import validate,read,sha,RUN,PLAN,Pool
 from wcomr.gpu_budget_pool_v2 import atomic_json,DeviceLease
 from wcomr.wc_time_collection_r1 import freeze_selection
 c,reg,auth=validate(a.project,a.stage);phase=auth['phase'];out=a.project/'outputs'/RUN;state=read(out/(phase+'-collection.json'));release=read(out/(phase+'-release.json'))
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and release['GPU_released'] and release['cost_settled'] and release['original_process_exited'] and state['status']=='TERMINAL'
 assert read(a.stage/'pg-host-guardian.json')['mode_restoration']['restored']
 ledger=Pool(a.project).read();job=ledger['jobs'][RUN+('-A-settled' if phase=='A' else '')]
 assert job['status']=='SETTLED' and job['billing_sha256']==release['billing_sha256']
 with DeviceLease(a.project,auth['gpu_uuid']):pass
 overlay=Path(read(a.stage/PLAN)['host_profiles'][auth['host']]['score_overlay']);sys.path.insert(0,str(overlay/'site'));os.environ['TORCH_HOME']=str(overlay/'torch')
 import torch,numpy as np,av,mediapy,lpips
 torch.set_num_threads(4);torch.set_num_interop_threads(1);assert not torch.cuda.is_initialized()
 def no_download(*a,**k):raise RuntimeError('Offline scoring only')
 torch.hub.download_url_to_file=no_download
 alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
 if phase=='B':
  import piq
  vgg=piq.LPIPS().cpu().eval()
 rows=state['rows'];targets=[r for r in rows if r['slot']['section']==('A_CALIBRATION' if phase=='A' else 'B_QUALITY') and r['slot']['role']!='NATIVE_U36']
 assert len(targets)==(4 if phase=='A' else 24)
 scored=[];start=time.time()
 def decoded(path):
  video=mediapy.read_video(path);assert video.shape==(93,432,768,3) and video.dtype==np.uint8
  with av.open(path) as stream:
   frames=list(stream.decode(video=0));assert len(frames)==93
   assert all(np.array_equal(f.to_ndarray(format='rgb24'),video[i]) for i,f in enumerate(frames))
   pts=[(f.pts,str(f.time_base)) for f in frames]
  return video,pts
 for row in targets:
  slot=row['slot'];native=next(r for r in rows if r['slot']['section']==('A_ANCHOR' if phase=='A' else 'B_QUALITY') and r['slot']['role']=='NATIVE_U36' and r['slot']['scene']==slot['scene'])
  paths=[row['result']['video_path'],native['result']['video_path']];hashes=[sha(p) for p in paths]
  x,px=decoded(paths[0]);y,py=decoded(paths[1]);assert px==py
  aa=[];vv=[]
  with torch.inference_mode():
   for xx,yy in zip(x,y):
    xx=torch.from_numpy(xx.copy()).permute(2,0,1).unsqueeze(0).float();yy=torch.from_numpy(yy.copy()).permute(2,0,1).unsqueeze(0).float()
    aa.append(float(alex(xx/127.5-1,yy/127.5-1)))
    if phase=='B':vv.append(float(vgg(xx/255,yy/255)))
  assert all(math.isfinite(v) for v in aa+vv) and hashes==[sha(p) for p in paths]
  s=dict(slot_id=slot['id'],reference_slot_id=native['slot']['id'],status='SCORED',frames=93,Alex=sum(aa)/93,Alex_frames=aa,video_sha256=hashes,PTS_equal=True,official_reader_RGB_equal=True)
  if vv:s.update(PIQ_VGG=sum(vv)/93,PIQ_VGG_frames=vv)
  scored.append(s);atomic_json(out/(phase+'-LPIPS-progress.json'),dict(rows=scored,expected=len(targets)))
 del alex
 if phase=='B':del vgg
 atomic_json(out/(phase+'-LPIPS.json'),dict(status='COMPLETE',rows=scored,wall_seconds=time.time()-start,CUDA_initialized=False))
 if phase=='A':freeze_selection(c,state,release,scored,out/'frozen-selection.json')
 else:
  # Use a separate process so every metric module is imported from its accepted original stage.
  cmd=[sys.executable,str(a.stage/'scripts/score_cara_wc73_quality_r1.py'),'--stage',str(a.stage),'--output',str(out)]
  subprocess.run(cmd,check=True)
 assert not torch.cuda.is_initialized()
if __name__=='__main__':main()
