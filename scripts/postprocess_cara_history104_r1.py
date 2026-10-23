#!/usr/bin/env python3
"""Score original104 only after settled GPU release; never replays inference."""
import argparse,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert os.environ['CUDA_VISIBLE_DEVICES']==''
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
 from wcomr.policy_generator_r1.historical_card import validate,RUN,read
 from wcomr.policy_generator_r1.production_evidence import metric_resource_identity,sha
 from wcomr.policy_generator_r1.historical_collection import score_after_release
 from wcomr.policy_generator_r1.historical_capture import collect
 from wcomr.policy_generator_r1.historical_terminal import scientific
 from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,process_identity,atomic_json
 c,reg,card=validate(a.project,a.stage);out=a.project/'outputs'/RUN
 sup=read(out/'supervisor.json');bill=read(out/'billing.json');pool=BudgetPool(a.project).read()
 ident=process_identity(sup['child_identity']['pid']);assert ident['start_ticks']!=sup['child_identity']['start_ticks'] or ident['state'] in (None,'Z','X')
 assert sup['exclusive_monitor_accepted'] and not sup.get('release_error') and pool['jobs'][RUN]['status']=='SETTLED' and pool['jobs'][RUN]['billing_sha256']==sha(out/'billing.json')
 with DeviceLease(a.project,sup['gpu_uuid']):pass
 import torch,lpips
 torch.set_num_threads(2);assert not torch.cuda.is_initialized();identity=metric_resource_identity(a.project)
 torch.hub.set_dir(str(a.project/'cache/torch/hub'));metric=lpips.LPIPS(net='alex',version='0.1',spatial=False,verbose=False).cpu().eval()
 for v in metric.parameters():v.requires_grad_(False)
 release=dict(GPU_released=True,ledger_settled=True,lock_free=True,CUDA_hidden=True,billing_sha256=sha(out/'billing.json'),observed_unix=time.time(),GPU_ended_unix=bill['ended_unix'])
 runner=read(out/'runner.json')
 score_after_release(card,runner['batch'],out,metric,identity,release,lambda v:atomic_json(out/'score-progress.json',v))
 assert not torch.cuda.is_initialized()
 packet=collect(a.project,a.stage,read(a.stage/'pg-GPU-authorization.json'))
 result=scientific(packet)
 atomic_json(out/'post-results.json',dict(status='HISTORY104_COMPLETE_CPU_POST_ACCEPTED',scientific=result,runner_sha256=packet['files']['runner']['sha256'],CPU_only_after_UUID_release=True,metric_identity=identity))
if __name__=='__main__':main()
