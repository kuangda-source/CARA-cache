#!/usr/bin/env python3
"""Offline fixed ridge1/window4 T0/T1/T2 on two preregistered data cohorts."""
import argparse,gzip,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
sys.path.insert(0,str(ROOT/'src'))
from wcomr.w3_grouped_action_eval_r1 import accept_dataset,evaluate,COHORTS,sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--original-capture',type=Path,required=True);p.add_argument('--repair-capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 started=time.perf_counter();data,accepted=accept_dataset(ROOT,json.loads(gzip.decompress(a.original_capture.read_bytes())),json.loads(gzip.decompress(a.repair_capture.read_bytes())))
 result=dict(status='W3_RAW_COHORTS_ACCEPTED_AND_FIXED_GROUPED_T0_T1_T2_CPU_EVALUATION',preregistration='research/454_WC_W3_FULL864_TERMINAL_CAPTURE_VIDEO_AUDIT_FAILURE_AND_READONLY_REPAIR_20261016.md',acceptance=accepted,cohorts=[evaluate(data,n) for n in COHORTS],
  original_capture_ref=str(a.original_capture),original_capture_sha256=sha(a.original_capture),repair_capture_ref=str(a.repair_capture),repair_capture_sha256=sha(a.repair_capture),GPU_submissions=0,new_teacher_computations=0,ledger_written=False)
 result.update(CPU_wall_seconds=time.perf_counter()-started,source_sha256={n:sha(ROOT/n) for n in ['src/wcomr/w3_grouped_action_eval_r1.py','src/wcomr/w3_causal_trend_r1.py',str(Path(__file__).relative_to(ROOT))]})
 a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps(dict(status=result['status'],CPU_seconds=result['CPU_wall_seconds'],cohorts=[dict(cohort=c['cohort'],groups=c['prompt_groups'],points=c['points'],models=[{k:m[k] for k in ['model','prompt_equal_mean_regret','regret_change_percent_vs_T0_CAD','prompt_equal_oracle_error_rate','actions_changed_vs_T0_CAD','prompt_regret_wins_vs_T0_CAD','action_counts','prompt_equal_repair_rate']} for m in c['models']]) for c in result['cohorts']]),allow_nan=False))
if __name__=='__main__':main()
