#!/usr/bin/env python3
"""Actual Cosmos entry + repair102 adaptive serialization + complete LPIPS CPU."""
import argparse,copy,importlib.util,json,os,shutil,subprocess,sys,time,unittest
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
 from wcomr.policy_generator_r1.production_evidence import sha,metric_resource_identity,score_videos,validate_score
 from wcomr.policy_generator_r1.p1_repair_callbacks import Callbacks
 from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from test_cara_pg_p1_repair102_r1 import exercise,inputs
 from unittest.mock import patch
 out=a.stage/'CPU-repair102';out.mkdir();video=out/'fixture93.mp4'
 subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
 import lpips
 identity=metric_resource_identity(a.project);torch.hub.set_dir(str(a.project/'cache/torch/hub'));metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 def execute(slot,policy,directory):
  directory.mkdir();shutil.copyfile(video,directory/'video.mp4')
  seconds=300. if policy is None else 300.+5.759309912605651*(policy['counts']['D']-36)+.12491496618716978*policy['counts']['A']
  return dict(status='COMPLETE',video_path=str(directory/'video.mp4'),final_latent=torch.zeros(1),solver_steps=36,guided_pairs=36,
   timing_boundary=TIME_BOUNDARY,full_request_seconds=seconds,core_seconds=seconds-5.,declared_CPU_endpoint_fixture=True)
 card,data,accepted=inputs()
 with patch('wcomr.policy_generator_r1.p1_repair_callbacks.accepted_assets',return_value=(b'{}',json.dumps({'profile_identity':data['profile']['identity']}).encode(),{},{})):
  cb=Callbacks(project=a.project,stage=a.stage,out=out,execute_request=execute,metric=metric,metric_identity=identity,fit_members=data['CAL_FIT_members'],select_members=['cpu_select_0','cpu_select_1'],launch={},runner={})
 def synthetic(reference,candidate,metric,**kw):
  return dict(reference_sha256=reference['sha256'],candidate_sha256=candidate['sha256'],frames=93,pts=[[i,'1/16'] for i in range(93)],frame_distances=[.05]*93,mean_LPIPS=sum([.05]*93)/93,metric_identity=identity,geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
 with patch('wcomr.policy_generator_r1.p1_repair_callbacks.score_videos',synthetic):
  batch,events,saved=exercise(external_endpoint=cb.endpoint,external_score=cb.score)
 atomic_json(out/'declared-CPU-batch.json',batch)
 # The whole scheduler used synthetic scores; separately execute its actual
 # scoring callback over every frame, and prove failed/replayed requests stop.
 reference=next(r for r in batch['rows'] if r['id']=='native_fit_0')
 slot=dict(reference,id='real_metric_cpu',kind='QUERY',status='RUNNING');slot.pop('request_artifact',None)
 result=cb.endpoint(slot,card['policies']['PG_ALL_D']);row=dict(slot,**result)
 t=time.monotonic();real=cb.score(row,reference);elapsed=time.monotonic()-t;assert real['LPIPS']==0.
 try:cb.endpoint(slot,card['policies']['PG_ALL_D'])
 except ValueError:pass
 else:raise AssertionError('Existing original request replayed')
 from wcomr.policy_generator_r1.p1_repair_replay import replay
 request_ids=[e[1] for e in events if e[0]=='request'];score_ids=[e[1] for e in events if e[0]=='score']
 requests={i:json.loads((out/i/'request.json').read_text()) for i in request_ids}
 by={x['id']:x for x in batch['rows']}
 # Callback returns request_artifact after persisting its own request bytes.
 for i,v in requests.items():v['result']['request_artifact']=by[i]['request_artifact']
 scores={i:dict(data=json.loads((out/i/'score.json').read_text()),artifact=by[i]['score_artifact']) for i in score_ids}
 replay_args=dict(card=card,accepted=accepted,consumer=data,native_clock=batch['native_clock'],fit=data['CAL_FIT_members'],select=['cpu_select_0','cpu_select_1'],requests=requests,scores=scores,metric_identity=identity,exposure=batch['SELECT_exposure_recheck'],reported=batch,cap=14.)
 independent=replay(**replay_args)
 tampered=copy.deepcopy(batch);tampered['query_attempts']+=1
 try:replay(**dict(replay_args,reported=tampered))
 except ValueError:pass
 else:raise AssertionError('Tampered decision accepted')
 tests=load(a.stage/'tests/test_cara_pg_p1_repair102_r1.py','repair_tests');res=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));assert res.wasSuccessful()
 assert not torch.cuda.is_initialized();reg=json.loads((a.stage/'registration.json').read_text())
 value=dict(status='P1_REPAIR102_ENTRY_ADAPTIVE_SCORE_REPLAY_CPU_PASS',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
  entry=json.loads((a.stage/'PG-production-CPU.json').read_text()),entry_proof_sha256=sha(a.stage/'PG-production-CPU.json'),
  adaptive=dict(registered_positions=102,executed_CPU_paths=len(request_ids),score_pairs=len(score_ids),tests=res.testsRun,independent_replay=independent,decision_tamper_rejected=True,original_request_replay_rejected=True,synthetic_endpoints=True,synthetic_COST112_gate=True),
  real_metric=dict(all93frames=True,LPIPS=real['LPIPS'],seconds=elapsed,score_sha256=real['score_artifact']['sha256'],identity=identity,synthetic_video=True),
  CUDA_initialized=False,GPU_submissions=0,ledger_written=False,current112_modified=False,actual_COST112_accepted=False,full_GPU_lifecycle_CPU_accepted=False,GPU_dispatch_ready=False)
 with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=value['status'],wall_seconds=time.time()-started)))
if __name__=='__main__':main()
