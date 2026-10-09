#!/usr/bin/env python3
"""H-T52 candidate exposure: standard-library read-only inventory, no CUDA."""
import hashlib
import json
from pathlib import Path
import subprocess


SOURCE = Path('configs/cal_w1d8.jsonl')
SOURCE_SHA = '7b99d44d9ec5aced6983dccbf1eb930344a84f053f185f423cecd12d94354d84'
BASE_NAME = 'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191'
OUTPUT = Path('reports/wc_other_scene_cfg_seed3_exposure_cpu_20261009.json')


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    matches = [json.loads(x) for x in raw.decode().splitlines() if x.strip()
               and json.loads(x).get('name') == BASE_NAME]
    assert len(matches) == 1
    original = matches[0]
    candidate = dict(original, name=BASE_NAME+'_seed3', seed=3)
    assert not OUTPUT.exists()
    remote = 'SOURCE_SHA='+repr(SOURCE_SHA)+'\nCANDIDATE='+repr(candidate)+'\n' + r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
assert hashlib.sha256((root/'configs/cal_w1d8.jsonl').read_bytes()).hexdigest()==SOURCE_SHA
paths=list((root/'outputs').rglob('*'+CANDIDATE['name']+'*'))
scanned=[];hits=[];errors=[]
for path in sorted((root/'outputs').rglob('receipt.json')):
 try:
  raw=path.read_bytes();value=json.loads(raw)
  scanned.append({'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  def walk(x,at='$'):
   if isinstance(x,dict):
    if x.get('name')==CANDIDATE['name'] or (x.get('seed')==CANDIDATE['seed'] and x.get('prompt')==CANDIDATE['prompt']):
     hits.append({'receipt':str(path),'location':at,'name':x.get('name'),'seed':x.get('seed')})
    for k,v in x.items():
     if isinstance(v,(dict,list)):walk(v,at+'.'+str(k))
   elif isinstance(x,list):
    for i,v in enumerate(x):
     if isinstance(v,(dict,list)):walk(v,at+'['+str(i)+']')
  walk(value)
 except Exception as error:errors.append({'path':str(path),'error':str(error)})
budget_raw=(root/'reports/budget.json').read_bytes()
print(json.dumps({'identity':'H_T52_OTHER_SCENE_CURRENT_WORLDCACHE_EXPOSURE_READONLY_CPU',
 'observed_unix':time.time(),'candidate':{'name':CANDIDATE['name'],'seed':CANDIDATE['seed'],
 'prompt_sha256':hashlib.sha256(CANDIDATE['prompt'].encode()).hexdigest()},
 'original_source_sha256':SOURCE_SHA,'matching_output_paths':[str(p) for p in paths],
 'request_identity_hits':hits,'read_errors':errors,'receipts':scanned,
 'budget_sha256':hashlib.sha256(budget_raw).hexdigest(),'budget':json.loads(budget_raw),
 'GPU_submissions':0,'scope':'All current WorldCache outputs/receipt.json; not external projects or unpublished runs',
 'prior_CPU_Toy_is_not_GPU_exposure':True,'GPU_execution_selected':False}))
'''
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                       input=remote, capture_output=True, text=True, timeout=55)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])
    proof = json.loads(p.stdout)
    proof['candidate_exposure_clear'] = not (proof['matching_output_paths'] or proof['request_identity_hits'] or proof['read_errors'])
    # Preserve hits and read failures too; they disqualify this candidate rather
    # than silently selecting a different seed or dropping a receipt.
    OUTPUT.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'status': 'CANDIDATE_EXPOSURE_CLEAR_WITHIN_CURRENT_INVENTORY' if proof['candidate_exposure_clear'] else 'CANDIDATE_NOT_CLEAR_REQUIRES_NEW_REGISTRATION',
        'candidate': proof['candidate'], 'receipts_scanned': len(proof['receipts']),
        'matching_paths': len(proof['matching_output_paths']), 'request_hits': len(proof['request_identity_hits']),
        'read_errors': len(proof['read_errors']), 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
