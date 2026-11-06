#!/usr/bin/env python3
"""Real entry +112 serialization/release/score composition; CUDA forbidden."""
import argparse,copy,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();started=time.time();os.environ['CUDA_VISIBLE_DEVICES']='';sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import torch
 original_load=torch.load;argv=sys.argv
 try:
  sys.argv=['entry','--project',str(a.project),'--stage',str(a.stage),'--output',str(a.stage/'PG-production-CPU.json')]
  load(a.stage/'scripts/check_cara_pg_p1_production_cpu_r1.py','entry').main()
 finally:sys.argv=argv;torch.load=original_load
 torch.set_num_threads(1)
 from wcomr.policy_generator_r1.cost112_card import MANIFEST,read
 from wcomr.policy_generator_r1.cost112_collection import collect,gather,score_after_release
 from wcomr.policy_generator_r1.production_evidence import sha,metric_resource_identity,score_videos,validate_score
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from test_cara_cost112_combination_r1 import result_fixture,METRIC
 from unittest.mock import patch
 reg=read(a.stage/'registration.json');old=read(a.stage/'reports/cara_history_bridge_production_CPU_terminal_r5_20261024.json')
 from audit_cara_historical_bridge_cpu_r1 import accept as history_accept
 history=history_accept(old)
 unchanged={n:h for n,h in old['registration']['payload_sha256'].items() if n.startswith(('src/','scripts/','tests/')) and n in reg['payload_sha256']}
 assert unchanged and all(reg['payload_sha256'][n]==h for n,h in unchanged.items())
 out=a.stage/'CPU-complete112';out.mkdir();video=out/'fixture93.mp4'
 subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
 card=read(a.stage/MANIFEST)
 def execute(slot,policy,directory):
  directory.mkdir();shutil.copyfile(video,directory/'video.mp4');r=result_fixture(slot,policy);r.update(video_path=str(directory/'video.mp4'),final_latent=torch.zeros(1))
  if slot['section']=='DIAGNOSTIC':r['guided']=[torch.zeros(1) for _ in range(36)]
  return r
 state=collect(card,out,execute,lambda s:atomic_json(out/'batch.json',s));packet=gather(card,state,out);assert len(packet['controls'])==23
 # Full112 cannot replay an existing request, even with complete old artifacts.
 try:collect(card,out,execute,lambda s:None)
 except ValueError:pass
 else:raise AssertionError('GPU request replay accepted')
 release=dict(GPU_released=True,ledger_settled=True,lock_free=True,CUDA_hidden=True)
 try:score_after_release(card,state,out,None,METRIC,dict(release,GPU_released=False),lambda s:None)
 except ValueError:pass
 else:raise AssertionError('Scoring admitted before release')
 def fake_score(reference,candidate,metric,**kw):
  return dict(reference_sha256=reference['sha256'],candidate_sha256=candidate['sha256'],frames=93,pts=[[i,'1/16'] for i in range(93)],frame_distances=[0.]*93,mean_LPIPS=0.,metric_identity=METRIC,geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
 calls=[]
 def failure(reference,candidate,*args,**kw):
  calls.append(1)
  if len(calls)==3:raise RuntimeError('DECLARED_CPU_SCORE_FAILURE')
  return fake_score(reference,candidate,*args,**kw)
 with patch('wcomr.policy_generator_r1.cost112_collection.score_videos',failure):
  try:score_after_release(card,state,out,None,METRIC,release,lambda s:atomic_json(out/'scores.json',s))
  except RuntimeError:pass
  else:raise AssertionError('Score failure suppressed')
 assert read(out/'scores.json')['completed_pairs']==2 and len(list(out.glob('*/request.json')))==112
 with patch('wcomr.policy_generator_r1.cost112_collection.score_videos',fake_score):
  score=score_after_release(card,state,out,None,METRIC,release,lambda s:atomic_json(out/'scores.json',s))
 assert score['completed_pairs']==72 and len(list(out.glob('*/request.json')))==112
 # One complete real fixed metric call, separate from synthetic72 scheduling controls.
 import lpips
 identity=metric_resource_identity(a.project);torch.hub.set_dir(str(a.project/'cache/torch/hub'));metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 r=state['rows'][0]['result'];s=state['rows'][1]['result'];actual=score_videos(r['video_artifact'],s['video_artifact'],metric,root=out,metric_identity=identity)
 assert validate_score(actual,r['video_artifact'],s['video_artifact'],identity)==0 and actual['frames']==93
 atomic_json(out/'real-LPIPS93.json',actual);del metric
 life=load(a.stage/'tests/check_cara_cost112_lifecycle_cpu_r1.py','life').run(a.stage,a.stage/'CPU-cost112-lifecycle')
 storage_life=load(a.stage/'tests/check_cost112_storage_cpu_r1.py','storage_life').run(a.stage,a.stage/'CPU-storage112-lifecycle')
 import unittest
 tests=load(a.stage/'tests/test_cara_cost112_combination_r1.py','terminal_tests');result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));assert result.wasSuccessful()
 model_tests=load(a.stage/'tests/test_cara_cost112_model_r1.py','model_tests');model_result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(model_tests));assert model_result.wasSuccessful()
 assert not torch.cuda.is_initialized()
 proof=dict(status='COST112_FULL_COLLECTION_RELEASE_SCORE_TERMINAL_CPU_PASS',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
  entry=read(a.stage/'PG-production-CPU.json'),entry_proof_sha256=sha(a.stage/'PG-production-CPU.json'),historical148_accepted=history,unchanged_historical_execution_SHA=unchanged,
  collection=dict(paths=112,controls=23,requests_serialized=112,diagnostic_guided_artifacts=4,complete72_score_schedule=True,score_failure_raw_retained=True,score_resume_no_GPU_replay=True,pre_release_score_refused=True,same_slot_replay_refused=True,synthetic_endpoints_and_72_scores=True),
  full_video_metric=dict(real_LPIPS93=True,identity_zero=0.,metric_identity=identity,score_sha256=sha(out/'real-LPIPS93.json'),Cosmos_generated_video=False),lifecycle=life,storage_lifecycle=storage_life,terminal_tests=result.testsRun,model_tests=model_result.testsRun,
  CUDA_initialized=False,Cosmos_weights_loaded=0,GPU_submissions=0,authoritative_ledger_written=False)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)))
if __name__=='__main__':main()
