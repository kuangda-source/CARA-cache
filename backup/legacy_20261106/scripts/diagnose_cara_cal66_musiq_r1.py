"""Read accepted old CAL66 frame scores only; descriptive, no new inference."""
import argparse,json,hashlib,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAP='reports/cara_CAL66_A6000_terminal_20261026_0930.json'
ACC='reports/cara_CAL66_A6000_terminal_accepted_20261026_0930.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 cap=json.loads((ROOT/CAP).read_text());acc=json.loads((ROOT/ACC).read_text())
 assert acc['full_protocol_accepted']
 card=json.loads(cap['files']['card']['raw_utf8']);slots={s['id']:s for s in card['matrix']}
 scores={}
 for rec in cap['quality_scores'].values():
  raw=rec['raw_utf8'];assert hashlib.sha256(raw.encode()).hexdigest()==rec['sha256']
  s=json.loads(raw)
  if s['dimension']=='MUSIQ_LONGER512':
   slot=slots[s['method']];assert slot['section']=='QUALITY' and len(s['frame_scores'])==93
   scores[(slot['member'],slot['role'])]=s
 comparisons=[]
 pairs=[('S24_C','S24_A_PHASE'),('S25_C','S25_A_PHASE'),('SHARED24_C','SHARED24_A_PHASE_ALL'),('SHARED25_C','SHARED25_A_PHASE_ALL'),('SHARED24_A_PHASE_ALL','SHARED24_A_PHASE_AGE3'),('SHARED25_A_PHASE_ALL','SHARED25_A_PHASE_AGE3')]
 for left,right in pairs:
  rows=[]
  for member in card['CAL_FIT_members']:
   c=scores[member,left];s=scores[member,right];assert c['pts']==s['pts']
   d=[y-x for x,y in zip(c['frame_scores'],s['frame_scores'])]
   rows.append(dict(member=member,mean_difference=statistics.mean(d),negative_frame_count=sum(x<0 for x in d),frame_differences=d,thirds_mean=[statistics.mean(d[i:i+31]) for i in (0,31,62)],left_video_sha256=c['video_sha256'],right_video_sha256=s['video_sha256']))
  comparisons.append(dict(left=left,right=right,mean_difference=statistics.mean(r['mean_difference'] for r in rows),negative_prompt_count=sum(r['mean_difference']<0 for r in rows),rows=rows))
 out=dict(status='ACCEPTED_CAL66_FRAME_MUSIQ_DESCRIPTIVE_DIAGNOSIS',observed_unix=time.time(),capture_ref=CAP,capture_sha256=sha(ROOT/CAP),acceptance_ref=ACC,acceptance_sha256=sha(ROOT/ACC),comparisons=comparisons,
  independent_prompts=4,frames_not_independent_samples=True,sharpness_or_blur_measured=False,causal_blur_claim=False,new_DEV_inspected=False,GPU_submissions=0,thresholds_or_policies_changed=False)
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ('left','right','mean_difference','negative_prompt_count')} for r in comparisons],indent=2))
if __name__=='__main__':main()
