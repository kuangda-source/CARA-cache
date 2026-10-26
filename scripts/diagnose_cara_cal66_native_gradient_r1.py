"""Accepted old CAL only; fixed light-blur explanation control, no fitted kernel."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
CAP='reports/cara_CAL66_A6000_terminal_20261026_0930.json'
ACC='reports/cara_CAL66_A6000_terminal_accepted_20261026_0930.json'
PROTOCOL=dict(luminance='BT709 on decoded sRGB/255; no gamma linearization',
    blur='one separable [1,2,1]/4 spatial convolution, reflect pad, FP64, no quantization or fitted strength',
    crop='one-pixel common interior after blur; native432x768, no resize',
    gradient='forward H/W differences, valid edges, element-count pooled squared error in FP64',
    energy_ratio_epsilon=1e-12,decode_frames=93,independent_unit='prompt',
    blurred_C_MUSIQ_recomputed=False,causal_blur_claim=False)


def light_blur(y):
    p=np.pad(y,((1,1),(0,0)),mode='reflect');z=(p[:-2]+2*p[1:-1]+p[2:])/4
    p=np.pad(z,((0,0),(1,1)),mode='reflect');return (p[:,:-2]+2*p[:,1:-1]+p[:,2:])/4


def metrics(y,n):
    y=y[1:-1,1:-1];n=n[1:-1,1:-1]
    dy=(np.diff(y,axis=0),np.diff(y,axis=1));dn=(np.diff(n,axis=0),np.diff(n,axis=1))
    count=sum(x.size for x in dy)
    error=sum(np.square(x-z).sum() for x,z in zip(dy,dn))/count
    ey=sum(np.square(x).sum() for x in dy)/count;en=sum(np.square(x).sum() for x in dn)/count
    return dict(gradient_residual_MSE=float(error),gradient_energy_ratio=float(ey/(en+1e-12)),
                teacher_gradient_energy=float(en),pixel_MSE=float(np.square(y-n).mean()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--video-root',type=Path,required=True)
    p.add_argument('--av-deps',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    sys.path.insert(0,str(a.av_deps));import av
    started=time.monotonic();cpu=time.process_time()
    cap=json.loads((ROOT/CAP).read_text());accepted=json.loads((ROOT/ACC).read_text())
    assert accepted['full_protocol_accepted']
    batch=json.loads(cap['files']['runner']['raw_utf8'])['batch']
    roles=('S25_C','S25_A_PHASE','NATIVE35')
    rows=[r for r in batch['rows'] if r['slot']['section']=='QUALITY' and r['slot']['role'] in roles]
    assert len(rows)==12
    artifacts=[]
    for r in rows:
        f=a.video_root/(r['slot']['id']+'.mp4');h=hashlib.sha256(f.read_bytes()).hexdigest()
        assert h==r['result']['video_artifact']['sha256']
        artifacts.append(dict(slot=r['slot']['id'],path=str(f),sha256=h,bytes=f.stat().st_size))
    results=[]
    for member in dict.fromkeys(r['slot']['member'] for r in rows):
        selected=[next(r for r in rows if r['slot']['role']==role and r['slot']['member']==member) for role in roles]
        streams=[av.open(str(a.video_root/(r['slot']['id']+'.mp4'))) for r in selected]
        try:
            for stream in streams:stream.streams.video[0].thread_count=1
            decoders=[iter(s.decode(video=0)) for s in streams];frames=[]
            for i in range(93):
                f=[next(d) for d in decoders]
                assert len({(x.pts,str(x.time_base)) for x in f})==1
                yy=[]
                for x in f:
                    rgb=x.to_ndarray(format='rgb24');assert rgb.shape==(432,768,3)
                    yy.append(np.einsum('hwc,c->hw',rgb.astype(np.float64)/255,np.array([.2126,.7152,.0722])))
                c,a_,n=yy;blur=light_blur(c)
                frames.append(dict(frame=i,pts=f[0].pts,time_base=str(f[0].time_base),
                    C=metrics(c,n),A=metrics(a_,n),BLUR_C=metrics(blur,n)))
            assert all(next(d,None) is None for d in decoders)
        finally:
            for s in streams:s.close()
        means={role:{k:float(np.mean([f[role][k] for f in frames])) for k in frames[0][role]} for role in ('C','A','BLUR_C')}
        results.append(dict(member=member,means=means,frames=frames))
    out=dict(status='OLD_CAL66_FIXED_NATIVE_GRADIENT_EXPLANATION_NOT_QUALITY_GATE',observed_unix=time.time(),
        protocol=PROTOCOL,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sources={x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in (CAP,ACC)},
        artifacts=artifacts,prompts=results,independent_prompts=4,decoded_video_frames=1116,
        wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform=sys.platform,
        decoder_version=av.__version__,new_GPU_submissions=0,DEV128_read=False,thresholds_changed=False)
    with a.output.open('x') as f:json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps([dict(member=r['member'],means=r['means']) for r in results],indent=2))


if __name__=='__main__':main()
