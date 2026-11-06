"""Independent terminal capture and actual CPU tensor reload; no resampling."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    code=r'''import os,json,hashlib,base64,gzip,time
from pathlib import Path
os.environ['CUDA_VISIBLE_DEVICES']=''
project=Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=project/'.sync/wc-e5-early-head-cpu-r2-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((stage/'receipt.json').read_text());assert receipt['exit_code']==receipt['child_exit_code']==0
assert not any(Path('/proc/'+str(i)).exists() for i in (receipt['pid'],receipt['child_pid']))
registration=json.loads((stage/'registration.json').read_text());files=dict(registration['inherited_payload_sha256'],**registration['new_payload_sha256'])
assert {n:sha(stage/n) for n in files}==files==receipt['payload_after_sha256']
result=stage/'CPU-artifacts/result.json';assert sha(result)==receipt['result_sha256'];r=json.loads(result.read_text())
assert r['status']=='E5_CPU_FULL36_NATIVE_HEAD_EQUIVALENCE_PASS_NOT_REAL_GPU_ACCEPTANCE'
assert len(r['paths'])==12 and len(r['paired_comparisons'])==6 and len(r['unsupported_head_refusals'])==7 and len(r['actual_paired_branch_failures'])==4
assert r['own_version_full_physical_and_owned_restores']==24 and r['direct_tensor_equalities']==222
assert r['GPU_submissions']==0 and not r['CUDA_initialized'] and r['no_real_video_or_latency_claim']
import torch
torch.set_num_threads(2)
def forbidden(*a,**k):raise RuntimeError('E5 independent capture forbids CUDA/download')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
loaded={};file_records=[];tensor_count=0
for row in r['paths']+r['actual_paired_branch_failures']:
 path=Path(row['path']).resolve();assert path.is_relative_to((stage/'CPU-artifacts').resolve())
 assert sha(path)==row['sha256'];size=path.stat().st_size
 value=torch.load(path,map_location='cpu',weights_only=True);assert set(value)=={'guided','final_latent'}
 count=7 if 'fault' in row else 36;assert len(value['guided'])==count
 for t in value['guided']+[value['final_latent']]:
  assert t.dtype==torch.float32 and t.shape==(1,8,2,16,16) and t.device.type=='cpu' and torch.isfinite(t).all()
  tensor_count+=1
 assert sha(path)==row['sha256'] and path.stat().st_size==size
 loaded[path.name]=value;file_records.append({'path':str(path),'sha256':row['sha256'],'bytes':size,'tensors':count+1})
actual_pairs=[];equalities=0;raw_changes=0
for flow in (False,True):
 for method in ('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE'):
  rows=[next(x for x in r['paths'] if x['flow']==flow and x['method']==method and x['fast']==fast) for fast in (False,True)]
  a,b=[loaded[Path(x['path']).name] for x in rows]
  assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
  equalities+=37
  for x,y in zip(rows[0]['states'],rows[1]['states']):
   assert {k:v for k,v in x.items() if k not in ('fields','raw_projection')}=={k:v for k,v in y.items() if k not in ('fields','raw_projection')}
   assert {k:v for k,v in x['fields'].items() if k!='previous_output'}=={k:v for k,v in y['fields'].items() if k!='previous_output'}
   raw_changes+=x['raw_projection']!=y['raw_projection']
  h=rows[1]['summary']['A_readout']['history'];assert len(h)==36
  savings=rows[0]['actual_native_head_calls']-rows[1]['actual_native_head_calls']
  assert savings==sum(sum(x['original_head_elided']) for x in h)
  assert all(not any(x['original_head_elided']) for x in h if x['action']!='CC' or x['step']>=25)
  assert rows[1]['actual_native_head_calls']==sum(x['total_head_calls'] for x in h)
  actual_pairs.append({'flow':flow,'method':method,'legacy_native_head_calls':rows[0]['actual_native_head_calls'],
       'new_native_head_calls':rows[1]['actual_native_head_calls'],'saved_native_head_calls':savings,'actual_direct_equalities':37})
assert equalities==222 and tensor_count==476 and len(file_records)==16 and not torch.cuda.is_initialized()
packed={n:{'sha256':sha(stage/n),'gzip_base64':base64.b64encode(gzip.compress((stage/n).read_bytes(),mtime=0)).decode()} for n in ('registration.json','receipt.json','launch.json','CPU.log','CPU-artifacts/result.json')}
print(json.dumps({'status':'E5_CPU_R2_INDEPENDENT_WRITTEN_TENSOR_EQUIVALENCE_PASS_NOT_GPU_ACCEPTANCE',
 'source_revision':receipt['source_revision'],'supervisor_and_child_absent':True,'CPU_wall_seconds':receipt['CPU_wall_seconds'],
 'actual_payload_files_unchanged':len(files),'actual_loaded_files':file_records,'actual_loaded_tensors':tensor_count,
 'actual_direct_equalities':equalities,'actual_head_call_comparisons':actual_pairs,
 'driver_recorded_own_version_full_restores':24,'driver_recorded_head_refusals':r['unsupported_head_refusals'],
 'driver_recorded_actual_paired_failures':r['actual_paired_branch_failures'],
 'changed_bookkeeping_previous_output_steps':r['changed_previous_output_steps'],
 'raw_installation_projection_hash_changes':raw_changes,'cross_installation_parameter_versions_compared_by_native_names':True,
 'budget_before_sha256':receipt['budget_before_sha256'],'budget_after_sha256':receipt['budget_after_sha256'],
 'budget_live_sha256':sha(project/'reports/budget.json'),'original_files':packed,
 'CUDA_initialized':False,'GPU_submissions':0,'ledger_written':False,'no_real_video_or_clean_latency_claim':True,'observed_unix':time.time()}))
'''
    c=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if c.returncode:raise RuntimeError(c.stderr[-4000:])
    value=json.loads(c.stdout);originals=value.pop('original_files');refs={}
    for name,row in originals.items():
        zipped=base64.b64decode(row.pop('gzip_base64'));raw=gzip.decompress(zipped)
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        path=root/'reports'/('wc_e5_early_head_cpu_r2_terminal_20261011_'+name.replace('/','_')+'.native.gz')
        assert not path.exists();path.write_bytes(zipped);row['local_ref']=str(path.relative_to(root));refs[name]=row
    value['original_files']=refs
    path=root/'reports/wc_e5_early_head_cpu_r2_terminal_20261011_capture.json';assert not path.exists()
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k not in ('original_files','actual_loaded_files','driver_recorded_actual_paired_failures','driver_recorded_head_refusals')}))


if __name__=='__main__':main()
