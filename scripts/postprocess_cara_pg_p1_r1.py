#!/usr/bin/env python3
"""After GPU release, reproduce selection and raw endpoint identities on CPU."""
import argparse,os,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();assert os.environ['CUDA_VISIBLE_DEVICES']==''
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
 from wcomr.policy_generator_r1.production_stage import RUN,read
 from wcomr.policy_generator_r1.production_capture import collect
 from wcomr.policy_generator_r1.production_terminal import scientific
 from wcomr.gpu_budget_pool_v2 import atomic_json
 packet=collect(a.project,a.stage,read(a.stage/'pg-GPU-authorization.json'))
 result=scientific(packet)
 atomic_json(a.project/'outputs'/RUN/'post-results.json',dict(status='PG_P1_COMPLETE_CPU_POST_REPLAY_ACCEPTED',scientific=result,runner_sha256=packet['files']['runner']['sha256'],CPU_only_after_UUID_release=True))
if __name__=='__main__':main()
