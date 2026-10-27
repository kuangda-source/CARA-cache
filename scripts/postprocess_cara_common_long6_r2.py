"""Scores only after original lease release and local actual-cost settlement."""
import argparse,os,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();sys.path.insert(0,str(a.stage/'src'))
 from wcomr.common_long_card_r2 import validate,read,sha,RUN,MANIFEST,require
 from wcomr.common_long_finance_r2 import HostBudgetPool
 from wcomr.gpu_budget_pool_v2 import DeviceLease,atomic_json
 from wcomr.common_long_collection_r1 import rescore
 c,reg,m=validate(a.project,a.stage);out=a.project/'outputs'/RUN
 bill=read(out/'billing.json');release=read(out/'exclusive-monitor-final.json')
 require(release['accepted'] and not release['final_snapshot']['compute_apps'],'GPU not released')
 require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU must hide GPU')
 import torch
 torch.set_num_threads(2);require(not torch.cuda.is_initialized(),'no CUDA')
 job=HostBudgetPool(a.project).read()['jobs'][RUN]
 require(job['status']=='SETTLED' and job['actual_GPUh']==bill['actual_GPUh'] and job['billing_sha256']==sha(out/'billing.json'),'original settlement')
 with DeviceLease(a.project,bill['gpu_uuid']):pass
 scored=rescore(read(out/'collection.json'),m)
 import resource,time
 scored['resource_limits']=dict(affinity_cpus=len(os.sched_getaffinity(0)),address_space_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],GPU_hidden=os.environ.get('CUDA_VISIBLE_DEVICES')=='',observed_unix=time.time())
 scored.update(collection_sha256=sha(out/'collection.json'),billing_sha256=sha(out/'billing.json'))
 atomic_json(out/'post-results.json',scored)
if __name__=='__main__':main()
