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
 # Re-run the actual entry and all18 sampler controls against this source closure.
 entry_path=a.stage/'PG-production-CPU.json';args=sys.argv
 try:
  sys.argv=['entry','--project',str(a.project),'--stage',str(a.stage),'--output',str(entry_path)]
  load(a.stage/'scripts/check_cara_pg_p1_production_cpu_r1.py','pg_actual_entry').main()
 finally:sys.argv=args;torch.load=original_load
 torch.set_num_threads(1)
 from wcomr.policy_generator_r1.production_evidence import sha,artifact,score_videos,validate_score
 # Load only accepted CPU LPIPS weights, no Cosmos weights or CUDA initialization.
 from bank24_fourcard_lifecycle_r1 import lpips_identity
 import lpips,importlib.metadata
 identity=lpips_identity(a.project,a.stage);assert importlib.metadata.version('lpips')=='0.1.4'
 torch.hub.set_dir(str(a.project/'cache/torch'))
 metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 out=a.stage/'CPU-full-video-score';out.mkdir()
 video=out/'declared-CPU-solid93.mp4'
 subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
 ref=artifact(video,out);t=time.monotonic();score=score_videos(ref,ref,metric,root=out,metric_identity=identity)
 assert validate_score(score,ref,ref,identity)==0. and score['frames']==93
 (out/'all93-score.json').write_text(json.dumps(score,indent=2)+'\n')
 metric_result=dict(actual_accepted_LPIPS_CPU=True,all93_original432x768=True,identity_zero=score['mean_LPIPS'],metric_identity=identity,
  score_sha256=sha(out/'all93-score.json'),video_sha256=ref['sha256'],seconds=time.monotonic()-t,Cosmos_generated_video=False)
 del metric
 life=load(a.stage/'tests/check_cara_pg_p1_lifecycle_cpu_r1.py','pg_actual_lifecycle').run(a.stage,a.stage/'CPU-lifecycle')
 # Actual supervisor/guardian fixture runs own real children; never real nvidia/sudo.
 import unittest
 module=load(a.stage/'tests/test_cara_pg_p1_combination_r1.py','pg_complete_acceptance_tests')
 t=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
 assert result.wasSuccessful()
 assert not torch.cuda.is_initialized()
 reg=json.loads((a.stage/'registration.json').read_text())
 value=dict(status='PG_P1_FULL_ENTRY_SUPERVISION_SCORE_TERMINAL_COMBINATION_CPU_PASS',source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),
  started_unix=started,ended_unix=time.time(),entry_proof_sha256=sha(entry_path),entry=json.loads(entry_path.read_text()),lifecycle=life,full_video_metric=metric_result,
  terminal_combination=dict(tests_run=result.testsRun,passed=True,seconds=time.monotonic()-t,synthetic_prices_and_endpoints=True,complete64_denominator=True),
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,actual_hardware_exclusivity_tested=False,clean_prices_accepted=False,
  CUDA_initialized=False,Cosmos_weights_loaded=0,GPU_submissions=0,authoritative_ledger_written=False,current_price_stage_modified=False)
 with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=value['status'],CPU_wall_seconds=time.time()-started)))
if __name__=='__main__':main()
