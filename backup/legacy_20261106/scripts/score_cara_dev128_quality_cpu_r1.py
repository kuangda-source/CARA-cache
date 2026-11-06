#!/usr/bin/env python3
"""Score from the accepted model stage so imported metric sources stay bound.

The caller supplies an existing complete plan and settled GPU-release receipt.
This child inherits the postprocessor's CPU/memory/wall-time envelope.
"""
import argparse,json,os,sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]

def main():
 p=argparse.ArgumentParser();p.add_argument('--binding',type=Path,required=True)
 p.add_argument('--plan',type=Path);p.add_argument('--release',type=Path);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--declared-synthetic-CPU-probe',action='store_true');a=p.parse_args()
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 b=json.loads(a.binding.read_text());quality_root=Path(b['registration']['stage']);assert quality_root.is_dir()
 # Import metrics from their accepted original stage. Only new plan orchestration
 # is resolved from this DEV stage; do not rebind model source identities.
 sys.path[:0]=[str(quality_root/'src'),str(quality_root/'scripts')]
 import wcomr.policy_generator_r1 as package
 package.__path__.append(str(ROOT/'src/wcomr/policy_generator_r1'))
 import torch
 torch.set_num_threads(2);assert not torch.cuda.is_initialized()
 from wcomr.policy_generator_r1.p2_quality_entry import original_factory,validate_sources_and_decoder
 from wcomr.policy_generator_r1.dev128_quality import execute,DIMENSIONS,digest
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from wcomr.automatic_quality_batch_r1 import validate_result
 from wcomr.automatic_quality_r1 import sampling_spec,text_sha
 from wcomr.policy_generator_r1.production_evidence import sha
 factory=original_factory(stage=quality_root,resources=b['resources'],acceptance=b['acceptance'],registration=b['registration'],identity=b['identity'],torch=torch,device='cpu')
 if not a.declared_synthetic_CPU_probe:
  release=json.loads(a.release.read_text());plan=json.loads(a.plan.read_text())
  assert plan['evaluator_identity']==b['identity']
  execute(plan,factory,a.output/'quality',release,lambda v:atomic_json(a.output/'quality-progress.json',v))
 else:
  assert not a.output.exists();a.output.mkdir();video=a.output/'fixture93.mp4'
  subprocess.run(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-f','lavfi','-i','color=c=gray:s=768x432:r=16','-frames:v','93','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(video)],check=True,timeout=60)
  rows=[];total=time.monotonic()
  for dim in DIMENSIONS:
   row=dict(case_id='DECLARED_SYNTHETIC_CPU',method='CPU93',dimension=dim,seed=0,prompt='Synthetic gray CPU fixture',prompt_sha256=text_sha('Synthetic gray CPU fixture'),video_path=str(video),video_sha256=sha(video),scorer_fingerprint=digest(b['identity']),expected_sampling=sampling_spec(dim),input_status='READY_TO_SCORE')
   start=time.monotonic()
   with factory(dim) as scorer:
    loaded=time.monotonic();result=scorer.score(row);scored=time.monotonic()
    atomic_json(a.output/(dim+'.raw.json'),result)
    validate_result(row,result);validate_sources_and_decoder(b['identity'],result)
   rows.append(dict(dimension=dim,load_seconds=loaded-start,score_seconds=scored-loaded,total_seconds=time.monotonic()-start,result_sha256=sha(a.output/(dim+'.raw.json'))))
  atomic_json(a.output/'result.json',dict(status='DEV128_REAL_THREE_METRIC_93_FRAME_CPU_PROBE_PASS',rows=rows,wall_seconds=time.monotonic()-total,scientific_quality_result=False,synthetic_input=True,frames=93,geometry=[432,768],models_really_loaded=True,CUDA_initialized=False,GPU_submissions=0))
 assert not torch.cuda.is_initialized()
if __name__=='__main__':main()
