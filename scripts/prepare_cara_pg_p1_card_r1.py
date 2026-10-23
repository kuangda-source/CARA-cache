#!/usr/bin/env python3
"""Bind accepted CPU components and the complete PG-P1 quote; no GPU dispatch."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from audit_cara_pg_p1_production_cpu_r1 import accept
from wcomr.policy_generator_r1.production_contract import complete_quote,COUNTS
from wcomr.policy_interval_assets_r1 import read,sha


def main():
 p=argparse.ArgumentParser()
 for n in ('cpu-capture','cpu-acceptance','quote','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();capture=read(a.cpu_capture);expected=accept(capture)
 expected.update(capture_ref=str(a.cpu_capture),capture_sha256=sha(a.cpu_capture))
 if read(a.cpu_acceptance)!=expected:raise ValueError('Independent CPU acceptance must reproduce exactly')
 quote=read(a.quote);bank=read(ROOT/quote['planning_source_ref'])
 recomputed=complete_quote(bank)
 if any(quote[k]!=v for k,v in recomputed.items()) or quote['planning_source_sha256']!=sha(ROOT/quote['planning_source_ref']):
  raise ValueError('Complete original quote differs')
 bank_accepted=read(ROOT/'reports/wc_four_card_BANK24_retry2_recovered_terminal_accepted_20261022.json')
 if not bank_accepted['full_protocol_accepted'] or bank_accepted['capture_sha256']!=quote['planning_source_sha256']:raise ValueError('Original planning source not accepted')
 files={n:h for n,h in capture['registration']['payload_sha256'].items() if n.startswith('src/wcomr/policy_generator_r1/')}
 for n,h in files.items():
  if sha(ROOT/n)!=h:raise ValueError('CPU-accepted generator source changed: '+n)
 v=dict(status='PG_P1_ENTRY_CPU_AND_COMPLETE_QUOTE_PREPARED_PRICE_PENDING',scope_counts=COUNTS,
  production_entry_CPU_accepted=True,CPU_acceptance_ref=str(a.cpu_acceptance),CPU_acceptance_sha256=sha(a.cpu_acceptance),
  CPU_capture_ref=str(a.cpu_capture),CPU_capture_sha256=sha(a.cpu_capture),CPU_source_revision=expected['source_revision'],
  accepted_generator_source_sha256=files,quote_ref=str(a.quote),quote_sha256=sha(a.quote),
  forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],
  recipe_ref='plans/cara_policy_generator_20261020/generator_recipe_r1.json',
  CAL_SELECT_ref='plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json',
  next_sequence=['Accept complete exclusive price originals and settle original job',
   'Bind accepted old labels and new price SHA; recheck scoped SELECT metadata',
   'Bind full PG-P1 GPU lifecycle/terminal acceptance to new source and stage; fresh UUID/ledger admission',
   'One whole card: Native warm2+FIT4 clean full-request clock, B=.80, first4+refinement4, frozen SELECT'],
  current_price_GPU_stage_modified=False,GPU_submissions=0,ledger_written=False,
  clean_prices_accepted=False,full_GPU_lifecycle_accepted=False,GPU_dispatch_ready=False)
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:v[k] for k in ('status','forecast_complete_GPUh','billed_limit_GPUh','GPU_dispatch_ready')}))
if __name__=='__main__':main()
