#!/usr/bin/env python3
"""Read-only original66 handle collection and independent acceptance. No launch."""
import argparse,json,sys
from pathlib import Path
import wc_four_card_cara_cost112_gpu_r1 as transport
from wc_four_card_policy_assets_r1 import read,write,sha,REPO
sys.path.insert(0,str(REPO/'src'))
from wcomr.policy_generator_r1.shared66_terminal import accept

CAPTURE=transport.CAPTURE.replace('cost112','shared66').replace('COST112','SHARED66')
CAPTURE=CAPTURE.replace("pid_mode=c['HostConfig']['PidMode'],", "nano_cpus=c['HostConfig']['NanoCpus'],memory_bytes=c['HostConfig']['Memory'],pid_mode=c['HostConfig']['PidMode'],")
# The independent control journal lives outside the project bind mount.
CAPTURE=CAPTURE.replace(" for env in original['Config']['Env']:", " storage_config=read(stage/'history104-storage.json')\n command+=['-v',storage_config['journal_path']+':'+storage_config['journal_path']+':ro']\n for env in original['Config']['Env']:")
transport.CAPTURE=CAPTURE

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['capture','accept'])
 p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path)
 p.add_argument('--mode',choices=['admission','halfway','terminal'],default='terminal');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Preserve original receipt')
 if a.command=='capture':
  if a.launch_ref is None:raise ValueError('Existing exact launch required; this tool cannot launch')
  v=transport.capture(a)
 else:
  v=accept(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture));write(a.output,v)
 print(json.dumps({k:v.get(k) for k in ('status','full_protocol_accepted','health','terminal_collection_error')}))
if __name__=='__main__':main()
