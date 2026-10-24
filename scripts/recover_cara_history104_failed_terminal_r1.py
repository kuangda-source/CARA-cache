#!/usr/bin/env python3
"""Capture failed104 without codecs, success assertions, analysis or dispatch."""
import argparse,json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from wc_four_card_policy_assets_r1 import base_ssh,write,read
from wcomr.history104_failure_recovery_r1 import REMOTE_CAPTURE,classify,reconstruction

def main():
 p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 v=base_ssh(REMOTE_CAPTURE,read(a.launch_ref),timeout=90)
 if 'container_state' in v:
  v['status']=classify(v['container_state'],v['live_handles'])
  v['full_protocol_accepted']=False
  if v['status']=='FAILED_ORIGINAL_TERMINAL':
   try:v['reconstruction']=reconstruction(v)
   except (ValueError,TypeError,KeyError) as e:v['accounting_reconstruction_not_applicable']=str(e)
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','available_bytes','monitor_summary','reconstruction')}))
if __name__=='__main__':main()
