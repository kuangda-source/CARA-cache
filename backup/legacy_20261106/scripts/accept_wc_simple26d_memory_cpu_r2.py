#!/usr/bin/env python3
"""Accept the saved once-only CPU collection without another SSH request."""
import argparse,gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.simple26d_memory_r2 import CPU_STATUS,PRODUCTION_CPU_STATUS,CONFIG,sha,COUNTS,matrix
from wcomr.gpu_budget_pool_v2 import BudgetPool

def accept(value):
 launch=value['launch'];b=value['bundle'];n=value['numeric'];p=value['production']
 assert all(value['payload_verified'].values()) and n['payload_sha256']==value['registration']['payload_sha256']
 assert b['status']=='SIMPLE26D_COMPLETE_CPU_ACCEPTED_NOT_GPU' and b['exit_code']==0
 assert b['source_revision']==launch['source_revision']==p['source_revision']==value['registration']['source_revision']
 assert n['status']==CPU_STATUS and n['actual_CPU_paths']==144 and n['legacy_complete_paths']==48 and n['repair_complete_paths']==96
 assert n['GPU_submissions']==0 and not n['CUDA_initialized'] and not b['GPU_submissions'] and not b['ledger_written']
 assert len(n['checks'])==2 and {x['flow'] for x in n['checks']}=={False,True}
 assert all(x['complete_CPU_paths']==72 and x['ordinary_initial_state_restored'] and x['all36_clean_outputs_actions_video_equal'] and len(x['checks'])==24 for x in n['checks'])
 assert p['status']==PRODUCTION_CPU_STATUS and p['exit_code']==0
 assert p['registration_sha256']==launch['registration_sha256'] and p['config_sha256']==sha(ROOT/CONFIG)
 assert p['sampling_CPU_sha256']==value['numeric_sha256'] and p['scope_counts']==COUNTS
 c=json.loads((ROOT/CONFIG).read_text());assert p['matrix']==matrix([r['name'] for r in c['requests']])
 assert not p['CUDA_initialized'] and p['GPU_submissions']==0 and not p['ledger_written']
 assert len(b['commands'])==5 and all(x['exit_code']==0 for x in b['commands'])
 assert value['process']['state'] in (None,'Z','X')
 totals=BudgetPool.accounting(value['pool']);assert all(value['pool'][k]==v for k,v in totals.items())
 return dict(status='SIMPLE26D_MEMORY_FULL144_ACTUAL_PRODUCTION_CPU_INDEPENDENT_ACCEPTED_NOT_GPU',
  source_revision=launch['source_revision'],CPU_paths=144,legacy_paths=48,repaired_paths=96,
  source_files=len(value['payload_verified']),CPU_seconds=b['wall_seconds'],numeric_CPU_seconds=n['CPU_wall_seconds'],
  original_process_terminal=True,real_GPU_memory_or_quality_claim=False,GPU_submissions=0,pool_at_CPU_collection=totals)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 result=accept(json.loads(gzip.decompress(a.capture.read_bytes())))
 result.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
 a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
