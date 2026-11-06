"""Old accepted S25 C/A videos only. Descriptive sharpness, never a quality gate.
Fixed full93-frame, native-resolution luminance Laplacian and Hann-window FFT.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--video-root',type=Path,required=True);p.add_argument('--av-deps',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--preview',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and not a.preview.exists();sys.path.insert(0,str(a.av_deps));import av
 capref='reports/cara_CAL66_A6000_terminal_20261026_0930.json';cap=json.loads((ROOT/capref).read_text());batch=json.loads(cap['files']['runner']['raw_utf8'])['batch'];old=json.loads((ROOT/'reports/cara_CAL66_MUSIQ_frame_diagnosis_20261026.json').read_text());musiq=next(c for c in old['comparisons'] if c['left']=='S25_C')
 rows=[r for r in batch['rows'] if r['slot']['section']=='QUALITY' and r['slot']['role'] in ['S25_C','S25_A_PHASE']];results=[];images={}
 for r in rows:
  slot=r['slot'];art=r['result']['video_artifact'];f=a.video_root/(slot['id']+'.mp4');assert hashlib.sha256(f.read_bytes()).hexdigest()==art['sha256'];vals=[]
  with av.open(str(f)) as stream:
   for i,frame in enumerate(stream.decode(video=0)):
    rgb=frame.to_ndarray(format='rgb24');assert rgb.shape==(432,768,3)
    if i in (0,46,92):images[slot['member'],slot['role'],i]=Image.fromarray(rgb)
    zrgb=rgb.astype(np.float64)
    y=(.2126*zrgb[:,:,0]+.7152*zrgb[:,:,1]+.0722*zrgb[:,:,2])/255
    assert np.isfinite(y).all() and 0<=y.min()<=y.max()<=1
    lap=y[:-2,1:-1]+y[2:,1:-1]+y[1:-1,:-2]+y[1:-1,2:]-4*y[1:-1,1:-1]
    window=np.hanning(432)[:,None]*np.hanning(768)[None,:];z=(y-y.mean())*window
    power=np.abs(np.fft.fft2(z))**2;power[0,0]=0
    fy=np.fft.fftfreq(432)[:,None];fx=np.fft.fftfreq(768)[None,:];mask=np.hypot(fy,fx)>=.25
    vals.append(dict(frame=i,pts=frame.pts,time_base=str(frame.time_base),laplacian_variance=float(lap.var()),high_frequency_fraction=float(power[mask].sum()/power.sum()),luminance_mean=float(y.mean()),luminance_std=float(y.std())))
  assert len(vals)==93
  results.append(dict(slot=slot,video_sha256=art['sha256'],frames=vals,means={k:float(np.mean([v[k] for v in vals])) for k in vals[0] if k not in ('frame','pts','time_base')}))
 pairs=[]
 for m in [r['member'] for r in musiq['rows']]:
  c=next(x for x in results if x['slot']['member']==m and x['slot']['role']=='S25_C');b=next(x for x in results if x['slot']['member']==m and x['slot']['role']=='S25_A_PHASE');assert [(x['pts'],x['time_base']) for x in c['frames']]==[(x['pts'],x['time_base']) for x in b['frames']]
  pairs.append(dict(member=m,MUSIQ_A_minus_C=next(x['mean_difference'] for x in musiq['rows'] if x['member']==m),A_over_C={k:b['means'][k]/c['means'][k] for k in ('laplacian_variance','high_frequency_fraction')},mean_C=c['means'],mean_A=b['means']))
 canvas=Image.new('RGB',(1536,4*188+40),'white');d=ImageDraw.Draw(canvas);d.text((8,5),'CAL66 accepted S25-C (left in each pair) / S25-A-phase (right); frames 0,46,92',fill='black')
 for j,pa in enumerate(pairs):
  for col,(fr,role) in enumerate((f,r) for f in (0,46,92) for r in ('S25_C','S25_A_PHASE')):
   im=images[pa['member'],role,fr].resize((256,144));x=col*256;y=40+j*188;canvas.paste(im,(x,y));d.text((x+4,y+146),f"{pa['member'][:18]} {role} f{fr}",fill='black')
 canvas.save(a.preview)
 out=dict(status='CAL66_OLD_VIDEO_LOCAL_SHARPNESS_DESCRIPTIVE',observed_unix=time.time(),source_capture=capref,source_capture_sha256=hashlib.sha256((ROOT/capref).read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),decoder=dict(PyAV=av.__version__,libraries={k:list(v) for k,v in av.library_versions.items()}),geometry=[432,768],source_frames=93,independent_prompts=4,
  protocol=dict(luminance='BT709 coefficients on decoded sRGB values, no gamma linearization',laplacian='4-neighbor interior variance, no resize',spectrum='subtract frame mean; 2D Hann; FFT power excluding DC; radial >=0.25 cycles/pixel fraction'),pairs=pairs,raw_frames=results,preview=str(a.preview),new_DEV_used=False,GPU_submissions=0,causal_blur_established=False,quality_gate_changed=False)
 a.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps(pairs,indent=2))
if __name__=='__main__':main()
