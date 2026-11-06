#!/usr/bin/env python3
"""Actual new128 orchestration with declared synthetic endpoints; no CUDA."""
import argparse,copy,importlib.util,json,os,shutil,subprocess,sys,time,unittest
from pathlib import Path

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();started=time.time();os.environ['CUDA_VISIBLE_DEVICES']='';sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import torch
 torch.set_num_threads(1);assert not torch.cuda.is_initialized()
 from wcomr.policy_generator_r1.dev128_card import MANIFEST,read
 from wcomr.policy_generator_r1.dev128_collection import collect,gather,score_after_release
 from wcomr.policy_generator_r1.dev128_quality import plan,execute as quality_execute,audit as quality_audit,DIMENSIONS,digest
 from wcomr.policy_generator_r1.production_evidence import sha,metric_resource_identity,score_videos,validate_score
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from test_cara_shared66_combination_r1 import result_fixture,METRIC
 from unittest.mock import patch
 reg=read(a.stage/'registration.json');card=read(a.stage/MANIFEST)
 from wcomr.policy_generator_r1.dev128_card import check_card
 check_card(card)
 out=Path('/fixture')/'CPU-complete128';assert os.path.ismount(out.parent);out.mkdir();video=out/'fixture93.mp4'
 subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
 def request(slot,policy,directory):
  directory.mkdir();shutil.copyfile(video,directory/'video.mp4');r=result_fixture(slot,policy);r.update(video_path=str(directory/'video.mp4'),final_latent=torch.zeros(1))
  if slot['section']=='DIAGNOSTIC':r['guided']=[torch.zeros(1) for _ in range(36)]
  return r
 state=collect(card,out,request,lambda s:atomic_json(out/'batch.json',s));packet=gather(card,state,out);assert len(packet['controls'])==26
 try:collect(card,out,request,lambda s:None)
 except ValueError:pass
 else:raise AssertionError('Request replay accepted')
 release=dict(GPU_released=True,ledger_settled=True,lock_free=True,CUDA_hidden=True,observed_unix=time.time())
 try:score_after_release(card,state,out,None,METRIC,dict(release,GPU_released=False),lambda s:None)
 except ValueError:pass
 else:raise AssertionError('Pre-release scores accepted')
 def synthetic_score(reference,candidate,*args,**kw):
  return dict(reference_sha256=reference['sha256'],candidate_sha256=candidate['sha256'],frames=93,pts=[[i,'1/16'] for i in range(93)],frame_distances=[0.]*93,mean_LPIPS=0.,metric_identity=METRIC,geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
 calls=[]
 def fail(reference,candidate,*args,**kw):
  calls.append(1)
  if len(calls)==3:raise RuntimeError('DECLARED_SCORE_FAILURE')
  return synthetic_score(reference,candidate,*args,**kw)
 with patch('wcomr.policy_generator_r1.dev128_collection.score_videos',fail):
  try:score_after_release(card,state,out,None,METRIC,release,lambda s:atomic_json(out/'scores.json',s))
  except RuntimeError:pass
  else:raise AssertionError('Score failure hidden')
 assert read(out/'scores.json')['completed_pairs']==2
 with patch('wcomr.policy_generator_r1.dev128_collection.score_videos',synthetic_score):
  scores=score_after_release(card,state,out,None,METRIC,release,lambda s:atomic_json(out/'scores.json',s))
 assert len(list((out/'score-failures').glob('*.json')))==1
 assert scores['completed_pairs']==80 and len(list(out.glob('*/request.json')))==128
 from test_cara_pg_p2_quality_binding_r1 import plan_and_scores
 from contextlib import contextmanager
 from types import SimpleNamespace
 oldplan,templates=plan_and_scores();identity=oldplan['evaluator_identity']
 from wcomr.automatic_quality_r1 import text_sha
 members={m:dict(prompt='Declared CPU fixture '+m,prompt_sha256=text_sha('Declared CPU fixture '+m)) for m in card['DEV_members']}
 qp=plan(card,state,members,identity,out);qdir=out/'quality';count=[]
 @contextmanager
 def factory(dim):
  def score(p):
   count.append(1)
   if len(count)==3:raise RuntimeError('DECLARED_QUALITY_FAILURE')
   return dict(next(t for t in templates if t['dimension']==dim),**{k:p[k] for k in ('case_id','method','video_sha256','prompt_sha256','scorer_fingerprint')})
  yield SimpleNamespace(dimension=dim,scorer_fingerprint=digest(identity),score=score)
 try:quality_execute(qp,factory,qdir,release,lambda s:atomic_json(out/'quality-progress.json',s))
 except RuntimeError:pass
 else:raise AssertionError('Quality failure hidden')
 assert read(out/'quality-progress.json')['status']=='QUALITY_FAILED_ORIGINALS_RETAINED'
 qs=quality_execute(qp,factory,qdir,release,lambda s:atomic_json(out/'quality-progress.json',s));quality=quality_audit(qp,qs)
 assert len(list((qdir/'failures').glob('*.json')))==1
 assert quality['positions']==288 and len(list(out.glob('*/request.json')))==128
 shutil.copytree(out/'score-failures',a.stage/'CPU-score-failures')
 shutil.copytree(qdir/'failures',a.stage/'CPU-quality-failures')
 atomic_json(a.stage/'CPU-fixture-summary.json',dict(batch=state,controls=packet['controls'],LPIPS=scores,quality=qs,declared_synthetic=True))
 import lpips
 identity=metric_resource_identity(a.project);torch.hub.set_dir(str(a.project/'cache/torch/hub'));metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 r=state['rows'][0]['result'];s=state['rows'][1]['result'];actual=score_videos(r['video_artifact'],s['video_artifact'],metric,root=out,metric_identity=identity)
 assert validate_score(actual,r['video_artifact'],s['video_artifact'],identity)==0 and actual['frames']==93
 atomic_json(a.stage/'real-LPIPS93.json',actual);del metric
 assert not torch.cuda.is_initialized()
 proof=dict(status='DEV128_COLLECTION_AND_RELEASE_SCORE_CPU_PASS',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
  collection=dict(paths=128,controls=26,requests_serialized=128,score_pairs=80,score_frames=7440,quality_videos=96,quality_positions=288,synthetic_endpoints_and_scores=True,score_resume_without_GPU_replay=True,quality_resume_without_GPU_replay=True,pre_release_score_refused=True,same_slot_replay_refused=True),
  fixture_summary_sha256=sha(a.stage/'CPU-fixture-summary.json'),full_video_metric=dict(real_LPIPS93=True,metric_identity=identity,score_sha256=sha(a.stage/'real-LPIPS93.json'),Cosmos_generated_video=False),
  CUDA_initialized=False,Cosmos_weights_loaded=0,GPU_submissions=0,authoritative_ledger_written=False)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)))
if __name__=='__main__':main()
