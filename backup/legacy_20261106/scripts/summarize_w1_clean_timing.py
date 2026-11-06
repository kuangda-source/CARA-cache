"""Recompute full repeated CAL timing; never complete a partial receipt."""
import argparse
import json
from pathlib import Path
from wcomr.clean_timing import summarize
from wcomr.development_vqa_run import load_bound
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=json.loads(a.receipt.read_text());p=r['protocol'];f=load_bound(a.project/p['frozen_replay_protocol'],p['frozen_replay_sha256'])
reference=load_bound(a.project/f['reference_receipt'],f['reference_receipt_sha256']);prior=load_bound(a.project/p['prior_candidate_receipt'],p['prior_candidate_sha256'])
result=summarize(r,f,reference,prior);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
