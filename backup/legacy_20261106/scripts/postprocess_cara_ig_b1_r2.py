"""CPU-only local B1 receipt audit after the exact GPU lease is released."""
import argparse,json,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();sys.path[:0]=[str(a.stage/'src')]
 from wcomr.innovation_gain_b1_card_r2 import validate,read,sha,RUN,COUNTS,PhaseBudgetPool
 from wcomr.gpu_budget_pool_v2 import atomic_json
 validate(a.project,a.stage);out=a.project/'outputs'/RUN
 result=read(out/'B1-results.json');bill=read(out/'billing.json');release=read(out/'exclusive-monitor-final.json')
 assert release['accepted'] and not release['final_snapshot']['compute_apps']
 assert result['status']=='B1_LOCAL_READOUT_COMPLETE_PENDING_VIDEO_VALIDATION'
 assert len(result['rows'])==4 and all(r['status']=='COMPLETE' for r in result['rows'])
 assert len(result['replays'])==72 and len(result['controls'])==2
 assert {k:result[k] for k in ('complete_parent_paths','states','original_readout_positions','additional_guided_replays','additional_head_pairs')}==dict(complete_parent_paths=4,states=12,original_readout_positions=72,additional_guided_replays=108,additional_head_pairs=216)
 job=PhaseBudgetPool(a.project,a.stage).read()['jobs'][RUN]
 assert job['status']=='SETTLED' and job['actual_GPUh']==bill['actual_GPUh'] and job['billing_sha256']==sha(out/'billing.json')
 atomic_json(out/'post-results.json',dict(status='B1_LOCAL_READOUT_ACCEPTED_PENDING_CENTRAL_SETTLEMENT_AND_VIDEO',
  scope_counts=COUNTS,result_sha256=sha(out/'B1-results.json'),billing_sha256=sha(out/'billing.json'),
  actual_GPUh=bill['actual_GPUh'],mainline_admitted=False,independent_video_quality_measured=False,
  summary=result['summary'],deployment_coefficients=result['deployment_coefficients']))
if __name__=='__main__':main()
