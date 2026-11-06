import json,subprocess,hashlib,time,resource,signal
from pathlib import Path
from fractions import Fraction
signal.alarm(900)
start=time.time();o=Path('/data20t/gaokuangda/worldcache_workspace/outputs/cara-wc73-r1-20261027');d=json.loads((o/'A-runner.json').read_text());out=[]
for r in d['batch']['rows']:
 if r['status']!='COMPLETE':continue
 p=r['result']['video_path'];print(json.dumps({'step':'start','slot':r['slot']['id']}),flush=True)
 raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,time_base:frame=width,height,best_effort_timestamp','-of','json',p],timeout=120);meta=json.loads(raw);st=meta['streams'][0];fr=meta['frames'];assert len(fr)==93 and (st['width'],st['height'])==(768,432);assert Fraction(st['r_frame_rate'])==16 and Fraction(st['avg_frame_rate'])==16
 pts=[x['best_effort_timestamp'] for x in fr];assert all((b-a)*Fraction(st['time_base'])==Fraction(1,16) for a,b in zip(pts,pts[1:]));assert all((x['width'],x['height'])==(768,432) for x in fr)
 cmd=['ffmpeg','-v','error','-threads','1','-filter_threads','1','-i',p,'-map','0:v:0','-an','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'];c=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);h=hashlib.sha256();n=0
 while True:
  b=c.stdout.read(1024*1024)
  if not b:break
  h.update(b);n+=len(b)
 err=c.stderr.read();assert c.wait(timeout=30)==0 and not err and n==93*768*432*3
 row={'slot':r['slot'],'RGB_SHA256':h.hexdigest(),'frames':93,'PTS':pts,'time_base':st['time_base'],'bytes':n};out.append(row);print(json.dumps({'step':'complete_video','result':row}),flush=True)
print(json.dumps({'status':'COMPLETE','videos':out,'wall_seconds':time.time()-start,'CPU_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'child_CPU_seconds':resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,'GPUh':0}),flush=True)
