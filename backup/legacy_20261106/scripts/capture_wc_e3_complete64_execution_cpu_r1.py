"""Original CPU handle/source receipts and independent real tensor re-read."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    ref='reports/wc_e3_complete64_execution_cpu_r1_launch_20261011.json';launch=json.loads((root/ref).read_text())
    code='L='+repr(launch)+'\n'+r'''import ast,base64,gzip,hashlib,json,os,pathlib,sys,time
os.environ['CUDA_VISIBLE_DEVICES']='';s=pathlib.Path(L['stage']);root=s.parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
 return h.hexdigest()
if pathlib.Path('/proc/'+str(L['supervisor_pid'])).exists():
 print(json.dumps({'capture':{'status':'ORIGINAL_E3_POST_SELECTION_CPU_LIVE','pid':L['supervisor_pid']},'native':{}}));raise SystemExit(0)
r=json.loads((s/'execution-CPU-receipt.json').read_text());assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
c=json.loads((s/'e3-complete64-config.json').read_text());p=json.loads((s/'e3-execution-protocol.json').read_text());reg=json.loads((s/'registration.json').read_text())
assert sha(s/'e3-complete64-config.json')==L['config_sha256'] and sha(s/'registration.json')==L['registration_sha256']
assert sha(s/'e3-execution-protocol.json')==L['protocol_sha256']==r['protocol_sha256']
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']==r['method_payload_after_sha256']
assert {n:sha(s/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']==r['execution_payload_after_sha256']
assert {n:sha(root/c['parent_stage']/n) for n in c['parent_import_source_sha256']}==c['parent_import_source_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(root/'reports/budget.json')
assert r['GPU_submissions']==0 and not r['ledger_written'] and not c['GPU_execution_selected']
independent=None
if r['exit_code']==0:
 assert r['status']=='E3_COMPLETE64_POST_SELECTION_ACTUAL_CPU_PASS_NOT_GPU' and not r['CUDA_initialized']
 a=r['affected_complete64_reporter_and_launch_wrapper_CPU_controls']
 assert a['inventory_slots']==a['score_routing_slots']==64 and a['stub93_scored']==60 and a['retained_gap_slots']==4
 assert a['not_actual_metric_or_GPU_results'] and len(a['authority_refusals'])==6
 assert len(r['file_reader_actual_refusals'])==7 and len(r['Native_pairing_refusals'])==5
 import torch,numpy as np
 from collections.abc import Mapping
 assert not torch.cuda.is_initialized();torch.set_num_threads(2)
 def forbidden(*a,**k):raise RuntimeError('Independent actual CPU re-read forbids CUDA/downloads')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
 # Pin and compile original tensor hash body only; no reporter function reused.
 source=root/c['parent_stage']/'src/wcomr/mid_coverage.py'
 assert sha(source)==c['parent_import_source_sha256']['src/wcomr/mid_coverage.py']
 node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='tree_digest')
 ns={'torch':torch,'np':np,'Mapping':Mapping,'hashlib':hashlib}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<original-hash-only>', 'exec'),ns);digest=ns['tree_digest']
 scope=json.loads((s/c['scope_ref']).read_text());rows=r['actual_reuse_reader']['per_path'];assert len(rows)==10
 total=0;files=[]
 for slot in scope['all64_slots']:
  if 'reuse_binding' not in slot:continue
  art=slot['reuse_binding']['vector_artifact'];path=pathlib.Path(art['path']).resolve()
  assert (root/'outputs').resolve() in path.parents and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
  data=torch.load(path,map_location='cpu',weights_only=True)
  assert set(data)=={'guided','final_latent'} and len(data['guided'])==36
  assert all(t.device.type=='cpu' and t.dtype==torch.float32 and list(t.shape)==[1,16,24,54,96]
   and bool(torch.isfinite(t).all()) for t in data['guided']+[data['final_latent']])
  assert {k:digest(v) for k,v in data.items()}==art['tensor_sha256']
  own=next(x for x in rows if x['slot']==slot['slot'])
  assert own['actual_vector_read']['file']==art and own['actual_vector_read']['actual_tensors_reloaded']==37
  assert own['decoded_video']['frames']==93 and own['pairing']['compatible']
  video=slot['reuse_binding']['video_artifact'];assert pathlib.Path(video['path']).stat().st_size==video['bytes'] and sha(pathlib.Path(video['path']))==video['sha256']
  files.append({'slot':slot['slot'],'actual_tensors_reloaded':37,'actual_file_sha256':art['sha256']});total+=37
  del data
 assert total==370 and not torch.cuda.is_initialized()
 assert r['actual_reuse_reader']['actual_decoded_frames']==930 and r['no_new_metric_values_generated']
 independent={'actual_original_files_reloaded':10,'actual_tensors_reloaded':total,'per_file':files,'CUDA_initialized':False}
capture={'status':'E3_ORIGINAL_POST_SELECTION_CPU_TERMINAL_NOT_GPU','source_revision':L['source_revision'],
 'original_PID_absent':r['pid'],'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'unchanged_method_files':len(c['payload_sha256']),'execution_files':len(p['execution_payload_sha256']),
 'independent_actual_reuse_reads':independent,'GPU_submissions':0,'ledger_written':False,'budget_sha256':r['budget_after_sha256'],
 'observed_unix':time.time()}
native={}
for n in ('execution-CPU-receipt.json','driver.log','launch.json','registration.json','e3-complete64-config.json','e3-execution-protocol.json'):
 raw=(s/n).read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(packed).hexdigest(),
  'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    prefix=root/'reports/wc_e3_complete64_execution_cpu_r1_terminal_20261011_'
    target=Path(str(prefix)+'capture.json');assert not target.exists();proof=value['capture'];proof['files']={};objects={}
    for name,info in value['native'].items():
        packed=base64.b64decode(info['base64'],validate=True);raw=gzip.decompress(packed)
        assert hashlib.sha256(raw).hexdigest()==info['sha256'] and len(raw)==info['bytes']
        assert hashlib.sha256(packed).hexdigest()==info['compressed_sha256']
        path=Path(str(prefix)+name+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][name]={k:v for k,v in info.items() if k!='base64'};proof['files'][name]['local_path']=str(path.relative_to(root))
        if name.endswith('.json'):objects[name]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json'];assert reg==json.loads((root/'manifests/wc_e3_complete64_execution_cpu_r1_preregistration_20261011.json').read_text())
    assert objects['e3-complete64-config.json']==json.loads((root/reg['config_ref']).read_text())
    assert objects['e3-execution-protocol.json']==json.loads((root/reg['protocol_ref']).read_text())
    for name,h in reg['execution_payload_sha256'].items():
        raw=subprocess.check_output(['git','show',launch['source_revision']+':'+name],cwd=root)
        assert hashlib.sha256(raw).hexdigest()==h,name
    proof['original_sources_complete64_post_selection_controls_and_actual_readers_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('files','independent_actual_reuse_reads')}));return 0


if __name__=='__main__':raise SystemExit(main())
