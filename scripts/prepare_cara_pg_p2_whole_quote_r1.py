#!/usr/bin/env python3
"""Reproduce the full P2 envelope from accepted historical planning clocks."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.p2_production_contract import complete_quote

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 refs=['reports/wc_four_card_BANK24_retry2_recovered_terminal_20261022.json','reports/wc_paper_N10_full960_terminal_independent_acceptance_20261018.json']
 raw=[(ROOT/r).read_bytes() for r in refs];value=complete_quote(*map(json.loads,raw))
 value['planning_sources']=[dict(ref=r,sha256=hashlib.sha256(b).hexdigest()) for r,b in zip(refs,raw)]
 with a.output.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({k:value[k] for k in ('status','forecast_complete_GPUh','billed_limit_GPUh','auxiliary90_included_not_separate_authorization')}))
if __name__=='__main__':main()
