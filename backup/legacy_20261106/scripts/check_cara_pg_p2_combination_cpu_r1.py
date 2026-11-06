#!/usr/bin/env python3
"""GPU-hidden combined entry, lifecycle, complete-video metric and acceptance check."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();started=time.time();os.environ['CUDA_VISIBLE_DEVICES']=''
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import torch
 original_load=torch.load
 # Re-run the actual entry and all48 sampler controls against this source closure.
 entry_path=a.stage/'PG-P2-production-CPU.json';args=sys.argv
 try:
  sys.argv=['entry','--project',str(a.project),'--stage',str(a.stage),'--output',str(entry_path)]
  load(a.stage/'scripts/check_cara_pg_p2_production_cpu_r1.py','pg_actual_entry').main()
 finally:sys.argv=args;torch.load=original_load
 torch.set_num_threads(1)
 from wcomr.policy_generator_r1.production_evidence import sha,artifact,score_videos,validate_score
 # Load only accepted CPU LPIPS weights, no Cosmos weights or CUDA initialization.
 from wcomr.policy_generator_r1.production_evidence import metric_resource_identity
 import lpips,importlib.metadata
 identity=metric_resource_identity(a.project);assert importlib.metadata.version('lpips')=='0.1.4'
 torch.hub.set_dir(str(a.project/'cache/torch/hub'))
 metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 out=a.stage/'CPU-full-video-score';out.mkdir()
 video=out/'declared-CPU-solid93.mp4'
 subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
 from unittest.mock import patch
 from wcomr.policy_generator_r1.p2_combination import Scores
 from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
 import shutil
 # Requests owns sampler serialization (exercised in embedded 48-path entry).
 # Here synthetic video/latent bytes enter the real P2 score callback.
 def serialized_fixture(identifier):
  directory=out/identifier;directory.mkdir();shutil.copyfile(video,directory/'video.mp4')
  torch.save(dict(final_latent=torch.zeros(1)),directory/'final-latent.pt')
  value=dict(status='COMPLETE',video_artifact=artifact(directory/'video.mp4',out),final_latent_artifact=artifact(directory/'final-latent.pt',out))
  (directory/'request.json').write_text(json.dumps(dict(declared_CPU_fixture=True,result=value)))
  return value
 cb=Scores(out,metric,identity);reference=serialized_fixture('native_cpu')
 candidate_result=serialized_fixture('candidate_cpu');t=time.monotonic()
 candidate=cb(dict(id='candidate_cpu',lpips=True),candidate_result,reference)
 score=json.loads(Path(candidate['score_artifact']['path']).read_text())
 assert candidate['LPIPS']==0. and score['frames']==93
 failed_result=serialized_fixture('score_failure_cpu')
 with patch('wcomr.policy_generator_r1.p2_combination.score_videos',side_effect=RuntimeError('DECLARED_SCORE_FAILURE')):
  try:cb(dict(id='score_failure_cpu',lpips=True),failed_result,reference)
  except RuntimeError:pass
  else:raise AssertionError('Metric failure suppressed')
 assert (out/'score_failure_cpu/request.json').exists() and not (out/'score_failure_cpu/score.json').exists()
 try:cb(dict(id='candidate_cpu',lpips=True),candidate_result,reference)
 except ValueError:pass
 else:raise AssertionError('Original score overwritten')
 metric_result=dict(actual_accepted_LPIPS_CPU=True,all93_original432x768=True,identity_zero=score['mean_LPIPS'],metric_identity=identity,
  score_sha256=candidate['score_artifact']['sha256'],video_sha256=candidate_result['video_artifact']['sha256'],seconds=time.monotonic()-t,Cosmos_generated_video=False,
  actual_endpoint_callback_serialization=True,metric_failure_propagated_raw_retained=True,same_slot_replay_refused=True)
 del metric
 life=load(a.stage/'tests/check_cara_pg_p2_lifecycle_cpu_r1.py','pg_actual_lifecycle').run(a.stage,a.stage/'CPU-lifecycle')
 # Actual supervisor/guardian fixture runs own real children; never real nvidia/sudo.
 import unittest
 suite=unittest.TestSuite()
 for filename in ('test_cara_pg_p2_combination_r1.py','test_cara_pg_p2_terminal_r1.py'):
  module=load(a.stage/'tests'/filename,filename[:-3]);suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
 t=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert result.wasSuccessful()
 assert not torch.cuda.is_initialized()
 reg=json.loads((a.stage/'registration.json').read_text())
 value=dict(status='PG_P2_FULL_ENTRY_SUPERVISION_SCORE_TERMINAL_COMBINATION_CPU_PASS',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),
  started_unix=started,ended_unix=time.time(),entry_proof_sha256=sha(entry_path),entry=json.loads(entry_path.read_text()),lifecycle=life,full_video_metric=metric_result,
  terminal_combination=dict(tests_run=result.testsRun,passed=True,seconds=time.monotonic()-t,synthetic_prices_and_endpoints=True,complete518_denominator=True,quality1600_schema_controls=True,actual_five_quality_models_loaded=False),
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,actual_hardware_exclusivity_tested=False,clean_prices_accepted=False,
  CUDA_initialized=False,Cosmos_weights_loaded=0,GPU_submissions=0,authoritative_ledger_written=False,active_P1_stage_modified=False,final_budget_determined=False)
 with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=value['status'],CPU_wall_seconds=time.time()-started)))
if __name__=='__main__':main()
