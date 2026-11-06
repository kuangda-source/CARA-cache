#!/usr/bin/env python3
"""Offline scope/financial terminal acceptance; original CPU failure stays failed."""
import argparse,gzip,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool
from wcomr.w3_label64_post_r1 import full_matrix

def accept(value):
 assert value['transport_exit_code']==0
 c=value['capture'];assert c['source_revision']=='047dcf181a3ab706002b2965e74b626e4648deea' and c['verified_payload_files']==1627
 read=lambda name:next(x for n,x in c['receipts'].items() if n.endswith(name))
 sup=read('/supervisor.json')['data'];runner=read('/runner.json')['data'];post=read('/post-CPU-exit.json')['data'];final=read('/CPU-final-results.json')['data']
 assert sup['source_revision']==runner['source_revision']==c['source_revision'] and sup['child_exit_code']==0
 assert sup['runner_sha256']==read('/runner.json')['sha256'] and c['original_launch']['supervisor_pid']==sup['pid']==876730
 assert all(p['state'] in (None,'Z','X') for p in c['processes']) and c['lock_free']
 assert sup['release']['uuid']=='GPU-cebf7119-cf03-23b9-e192-cd196332b704' and not sup['release']['pids']
 assert c['compute_apps']['exit_code']==0 and sup['release']['uuid'] not in c['compute_apps']['stdout']
 requests=[json.loads(x) for x in (ROOT/'configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl').read_text().splitlines()]
 plan=full_matrix(requests);assert len(runner['runs'])==len(plan)==18
 for row,want in zip(runner['runs'],plan):
  assert all(row[k]==want[k] for k in ('id','scene','section','kind'))
  assert row['status'] in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED')
  if row['status']=='COMPLETE':assert row['solver_steps']==row['guided_pairs']==36 and len(row['guided_sha256'])==36
  if row['status']=='TEXT_REJECTED':assert row['actual_pair_computations']==0 and not row.get('diagnostic_points')
 pairs=sum(row['actual_pair_computations'] for row in runner['runs']);assert pairs==runner['actual_pairs']==768
 assert sum(r['status']=='COMPLETE' for r in runner['runs'])==16 and sum(r['status']=='TEXT_REJECTED' for r in runner['runs'])==2
 pool=read('reports/gpu-budget-v2.json')['data'];totals=BudgetPool.accounting(pool);assert all(pool[k]==v for k,v in totals.items())
 bill=read('/legacy-W3-billing.json');job=pool['jobs'][pool['legacy_job_id']]
 actual=sup['wall_seconds']/3600
 assert job['status']=='SETTLED' and job['actual_GPUh']==bill['data']['actual_GPUh']==actual
 assert job['billing_sha256']==bill['sha256'] and bill['data']['wall_seconds']==sup['wall_seconds']
 assert post['exit_code']==1 and final['status']=='W3_FULL_RAW_CPU_TECH_FAILURE_ALL_DENOMINATORS_RETAINED'
 assert final['error_type']=='CalledProcessError' and '9_FORMAL_DIAGNOSTIC' in final['error']
 return dict(status='W3_ORIGINAL_GPU_SCOPE_AND_FINANCE_TERMINAL_ACCEPTED_RAW_SCIENCE_PENDING',
  original_parent_denominator=18,original_formal_label_denominator=64,original_warmup_label_denominator=8,
  completed_parent_records=16,text_rejected_parent_records=2,actual_pairs=pairs,actual_CFG_calls=pairs*2,
  teacher_record_count_unverified=sum(len(r.get('diagnostic_points',[])) for r in runner['runs']),
  raw_teacher_science_accepted=False,original_CPU_post_accepted=False,
  post_failure_type=final['error_type'],corrupt_video_parent_id='9_FORMAL_DIAGNOSTIC',
  actual_GPUh=actual,original_GPU_and_lock_released=True,other_UUID_app_does_not_invalidate_release=True,
  pool_totals=totals,GPU_submissions=0,ledger_written=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 result=accept(json.loads(gzip.decompress(a.capture.read_bytes())));result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
