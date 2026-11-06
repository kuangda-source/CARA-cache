#!/usr/bin/env python3
"""CPU read-only source proof for decoder versus guarded-writer intervals."""
import hashlib,json,subprocess
from pathlib import Path

CODE=r'''import ast,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-pi0-suffix8-production-r1-20261013'
reg=json.loads((stage/'registration.json').read_text())
names=['cosmos_predict2/inference.py','cosmos_predict2/_src/predict2/inference/video2world.py']
out={'source_revision':reg['source_revision'],'runtime':{},'observed_unix':time.time()}
def calls(body):
 result=[]
 for n in ast.walk(ast.Module(body=body,type_ignores=[])):
  if isinstance(n,ast.Call):
   f=n.func;name=f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else ''
   if name in ('run_video_guardrail','save_img_or_video'):result.append({'name':name,'lineno':n.lineno})
 return result
for name in names:
 p=root/'runtime'/name;raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==reg['runtime_source_sha256'][name]
 tree=ast.parse(raw);out['runtime'][name]={'sha256':h}
 if name.endswith('inference.py'):
  function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_generate_sample')
  body=function.body[-2:];out['guarded_writer_calls']=calls(body)
 else:
  function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='generate_vid2world')
  starts=[i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sample' for t in n.targets)]
  assert len(starts)==1;out['decoder_guarded_writer_calls']=calls(function.body[starts[0]+1:])
assert {r['name'] for r in out['guarded_writer_calls']}=={'run_video_guardrail','save_img_or_video'}
assert not out['decoder_guarded_writer_calls']
n='scripts/run_wc_pi0_suffix8_r1.py';out['runner_sha256']=hashlib.sha256((stage/n).read_bytes()).hexdigest();assert out['runner_sha256']==reg['payload_sha256'][n]
out.update(status='PI0_SUFFIX8_DECODER_GUARDED_WRITER_SOURCE_BOUNDARY_CPU_VERIFIED',
 original_field_actual_intervals={'VAE_and_video_guardrail_seconds':'source-derived decoder tail only; video guardrail is not included',
 'video_write_seconds':'entire source-derived guarded writer, including frame conversions, video guardrail, encoding/save'},
 registered_sampling_VAE_guardrail_without_encoding_save_time_identifiable=False,
 available_intervals=['instrumented sampling + decoder tail','instrumented sampling + decoder tail + entire guarded writer'],
 GPU_submissions=0,ledger_written=False,staged_source_modified=False)
print(json.dumps(out))
'''


if __name__=='__main__':
    compile(CODE,'<timing-source-proof>','exec')
    result=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=CODE,text=True)
    r=json.loads(result);p=Path(__file__).resolve().parents[1]/'reports/wc_pi0_suffix8_timing_source_boundary_cpu_20261013.json'
    assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('status','source_revision','registered_sampling_VAE_guardrail_without_encoding_save_time_identifiable','GPU_submissions')}))
