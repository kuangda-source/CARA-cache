#!/usr/bin/env python3
"""Read the original P1 terminal in its original codec image, entirely read-only."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wc_four_card_cara_pg_gpu_r1 import CAPTURE
from wc_four_card_policy_assets_r1 import ssh,write

COLLECT=r'''
 import subprocess,os
 original=json.loads(subprocess.check_output(['docker','inspect',L['container']],text=True))[0]
 assert not original['State']['Running'] and original['State']['ExitCode']==0
 code="import pathlib,json,sys; p=json.load(sys.stdin); assert not list(pathlib.Path('/dev').glob('nvidia*')); sys.path.insert(0,p['stage']+'/src'); from wcomr.policy_generator_r1.production_capture import collect; print(json.dumps(collect(p['root'],p['stage'],p['launch']),allow_nan=False))"
 command=['docker','run','--rm','-i','--read-only','--network','none','--cpus','1','--memory','2g','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'-v',str(root)+':'+str(root)+':ro','-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void','-e','PYTHONDONTWRITEBYTECODE=1']
 for env in original['Config']['Env']:
  if env.startswith(('PATH=','LD_LIBRARY_PATH=')):command+=['-e',env]
 command += [original['Image'],str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python'),'-c',code]
 try:
  result=subprocess.run(command,input=json.dumps(dict(root=str(root),stage=str(stage),launch=L)),text=True,capture_output=True,timeout=140)
  assert result.returncode==0,result.stderr[-2000:]
  v.update(json.loads(result.stdout));v['terminal_codec_readonly_recovery']=dict(image=original['Image'],GPU_hidden=True,root_readonly=True,network='none',original_stage_modified=False,original_outputs_modified=False)
 except Exception as e:v['terminal_collection_error']=dict(error_type=type(e).__name__,error=str(e))
'''
OLD=" from wcomr.policy_generator_r1.production_capture import collect\n try:v.update(collect(root,stage,L))\n except Exception as e:v['terminal_collection_error']=dict(error_type=type(e).__name__,error=str(e))\n"
assert CAPTURE.count(OLD)==1
RECOVERY=CAPTURE.replace(OLD,COLLECT)
def main():
 p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=ssh(RECOVERY,dict(launch=json.loads(a.launch_ref.read_text()),terminal=True));write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','health','terminal_collection_error','terminal_codec_readonly_recovery')}))
if __name__=='__main__':main()
