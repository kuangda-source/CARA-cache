#!/usr/bin/env python3
"""Read-only inventory of the candidate's WorldCache output/receipt exposure."""
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
candidate={'name':'human_199_seed3','seed':3}; paths=list((root/'outputs').rglob('*human_199_seed3*'))
scanned=[];hits=[];errors=[]
for path in sorted((root/'outputs').rglob('receipt.json')):
 try:
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();value=json.loads(raw)
  scanned.append({'path':str(path),'bytes':len(raw),'sha256':digest})
  def walk(x,at='$'):
   if isinstance(x,dict):
    if x.get('name')==candidate['name'] or (x.get('seed')==3 and 'tennis court at the University of Barcelona' in str(x.get('prompt',''))):
     hits.append({'receipt':str(path),'location':at,'name':x.get('name'),'seed':x.get('seed')})
    for k,v in x.items():
     if isinstance(v,(dict,list)):walk(v,at+'.'+str(k))
   elif isinstance(x,list):
    for i,v in enumerate(x):
     if isinstance(v,(dict,list)):walk(v,at+'['+str(i)+']')
  walk(value)
 except Exception as error:errors.append({'path':str(path),'error':str(error)})
budget=root/'reports/budget.json'
print(json.dumps({'identity':'H_T48_CURRENT_WORLDCACHE_RECEIPT_EXPOSURE_READONLY_CPU',
 'observed_unix':time.time(),'candidate':candidate,'matching_output_paths':[str(p) for p in paths],
 'request_identity_hits':hits,'read_errors':errors,'receipts':scanned,
 'budget_sha256':hashlib.sha256(budget.read_bytes()).hexdigest(),'GPU_submissions':0,
 'scope':'WorldCache outputs and all receipt.json files, not external projects or unpublished runs',
 'prior_CPU_toy_seed_is_not_GPU_exposure':True}))
'''


if __name__ == '__main__':
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                            input=REMOTE, text=True, capture_output=True, timeout=55)
    if result.returncode: raise RuntimeError(result.stderr[-4000:])
    proof = json.loads(result.stdout)
    assert not proof['matching_output_paths'] and not proof['request_identity_hits'] and not proof['read_errors']
    path = Path('reports/wc_cfg_confirmation_seed3_exposure_cpu_20261009.json'); assert not path.exists()
    path.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'candidate':proof['candidate'],'receipts_scanned':len(proof['receipts']),
                      'receipt_bytes_scanned':sum(x['bytes'] for x in proof['receipts']),
                      'matching_paths':0,'request_hits':0,'read_errors':0,'GPU_submissions':0}))
