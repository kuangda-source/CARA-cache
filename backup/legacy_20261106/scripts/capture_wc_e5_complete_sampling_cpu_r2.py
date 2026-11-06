"""Reload all written E5 full-sampler vectors, never run the sampler again."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    code=r'''import os,json,hashlib,base64,gzip,time,sys
from pathlib import Path
os.environ['CUDA_VISIBLE_DEVICES']=''
project=Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=project/'.sync/wc-e5-complete-sampling-cpu-r2-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((stage/'receipt.json').read_text())
assert not any(Path('/proc/'+str(i)).exists() for i in (receipt['pid'],receipt['child_pid']))
registration=json.loads((stage/'registration.json').read_text())
files=dict(registration['inherited_payload_sha256'],**registration['new_payload_sha256'])
assert {n:sha(stage/n) for n in files}==files==receipt['payload_after_sha256'] and len(files)==416
native_names=['receipt.json','registration.json','launch.json','CPU.log','supervisor.log']
proof={'source_revision':receipt['source_revision'],'original_PIDs_absent':[receipt['pid'],receipt['child_pid']],
 'exit_code':receipt['exit_code'],'CPU_wall_seconds':receipt['CPU_wall_seconds'],
 'payload_files_unchanged':len(files),'GPU_submissions':0,'ledger_written':False,
 'budget_before_sha256':receipt['budget_before_sha256'],'budget_after_sha256':receipt['budget_after_sha256'],
 'budget_live_sha256':sha(project/'reports/budget.json'),'observed_unix':time.time()}
if receipt['exit_code']:
 proof.update(status='E5_COMPLETE_SAMPLER_CPU_R2_FAILURE_RETAINED_NOT_ACCEPTED',
  partial_or_complete_written_files=[str(p) for p in (stage/'CPU-artifacts').rglob('*.pt')])
else:
 assert receipt['child_exit_code']==0
 result=stage/'CPU-artifacts/result.json';assert sha(result)==receipt['result_sha256']
 value=json.loads(result.read_text());native_names.append('CPU-artifacts/result.json')
 assert value['status']=='E5_FULL_UNIPC_NATIVE_HEAD_CPU_PASS_NOT_GPU_ACCEPTANCE'
 assert value['complete_paths']==24 and value['updates']==864 and value['CFG_calls']==1728
 assert value['direct_equalities']==444 and value['full_physical_and_owned_restores']==96
 assert value['written_files']==24 and value['written_tensors']==888
 assert len(value['checks'])==4 and not value['CUDA_initialized'] and value['GPU_submissions']==0
 meta=value['actual_native_meta_head']
 assert meta['parameter_count']==2059174912 and meta['AdaLN_LoRA'] and meta['Wan_FP32']
 assert meta['unpatchify']=='PINNED_NATIVE_UNPATCHIFY' and meta['native_child_config_mutation_refused']
 assert meta['checkpoint_wrapper_contract']=='PINNED_NATIVE_NON_REENTRANT_SELECTIVE'
 assert len(set(meta['wrapper_mutation_refusals']))==7 and meta['meta_weights_not_real_forward']
 import torch
 torch.set_num_threads(2)
 def forbidden(*a,**k):raise RuntimeError('E5 actual capture forbids CUDA/download')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
 sys.path.insert(0,str(stage/'src'))
 from wcomr.mid_coverage import tree_digest
 seen=set();records=[];pairs=[];tensors=equalities=restores=0
 for check in value['checks']:
  state=check['receipt'];assert state['initial_state_restored']
  rows=state['requests'][0]['paths'];assert len(rows)==6
  loaded={}
  for row in rows:
   assert row['status']=='COMPLETE_PARENT_PATH' and len(row['guided_sha256'])==36
   assert len(row['solver_returns'])==36 and len(row['P0_roundtrips'])==4
   assert all(x['physical_state_restored'] and x['complete_additional_state_restored'] and
       x['checkpoint_perturbation_executed'] for x in row['P0_roundtrips'])
   restores+=4
   art=row['vector_artifact'];p=Path(art['path']).resolve()
   assert p.is_relative_to((stage/'CPU-artifacts').resolve()) and p not in seen
   seen.add(p);assert sha(p)==art['sha256'];size=p.stat().st_size
   x=torch.load(p,map_location='cpu',weights_only=True)
   assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
   assert {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
   for t in x['guided']+[x['final_latent']]:
    assert t.device.type=='cpu' and t.dtype==torch.float32 and t.shape==(1,2048,2,8,8)
    assert torch.isfinite(t).all();tensors+=1
   assert sha(p)==art['sha256'] and p.stat().st_size==size
   loaded[row['collect']]=x;records.append({'path':str(p),'sha256':art['sha256'],'bytes':size,'tensors':37})
  for mode in ('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE'):
   left,right=[next(x for x in rows if x['collect']==v+'_'+mode) for v in ('LEGACY','FAST')]
   a,b=[loaded[v+'_'+mode] for v in ('LEGACY','FAST')]
   assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
   equalities+=37
   for key in ('actions','solver_returns','condition_fields_before','condition_fields_after',
       'actual_raw_solver_configuration','rng_after','final_latent_sha256'):
    assert left[key]==right[key],key
   l,r=[row['collection_complete']['deployment'] for row in (left,right)]
   for x,y in zip(l['history'],r['history']):
    for k in ('true_D_before','true_D_after','working_source_ages','working_sources','actual_projection_records'):
     assert x[k]==y[k],k
    if check['family']=='CURRENT_BIRTH':assert x['source_policy']==y['source_policy']
   heads=[len(row['collection_complete']['actual_original_plus_candidate_heads']) for row in (left,right)]
   history=r['A_readout']['history'];assert len(history)==36
   saved=sum(sum(h['original_head_elided']) for h in history)
   assert heads[0]-heads[1]==saved
   assert heads[1]==r['A_readout']['total_head_calls']==sum(h['total_head_calls'] for h in history)
   assert all(not any(h['original_head_elided']) for h in history if h['action']!='CC' or h['step']>=25)
   counted=next(x for x in check['head_call_changes'] if x['method']==mode)
   assert (counted['actual_legacy_heads'],counted['actual_new_heads'],counted['saved_native_heads'])==(*heads,saved)
   assert mode!='OFF' or saved==0
   pairs.append({'flow':check['flow'],'family':check['family'],'mode':mode,
       'legacy_actual_native_heads':heads[0],'new_actual_native_heads':heads[1],
       'saved_actual_native_heads':saved,'actual_tensor_equalities':37})
 assert seen=={p.resolve() for p in (stage/'CPU-artifacts').rglob('*.pt')}
 assert len(seen)==24 and tensors==888 and equalities==444 and restores==96 and len(pairs)==12
 assert not torch.cuda.is_initialized()
 proof.update(status='E5_COMPLETE_SAMPLER_R2_INDEPENDENT_FULL_WRITTEN_EQUIVALENCE_PASS_NOT_GPU',
   actual_loaded_files=records,actual_loaded_tensors=tensors,actual_direct_equalities=equalities,
   actual_native_head_comparisons=pairs,driver_recorded_complete_physical_owned_restores=restores,
   native_Meta_guard_evidence=meta,CUDA_initialized=False,no_real_video_or_clean_latency_claim=True)
 proof['explicit_Toy_limits']=value['explicit_Toy_boundaries']
originals={n:{'sha256':sha(stage/n),'gzip_base64':base64.b64encode(gzip.compress((stage/n).read_bytes(),mtime=0)).decode()}
 for n in native_names}
print(json.dumps({'capture':proof,'original_files':originals}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    result=json.loads(call.stdout);proof=result['capture'];refs={}
    for name,row in result['original_files'].items():
        zipped=base64.b64decode(row.pop('gzip_base64'));raw=gzip.decompress(zipped)
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        p=root/'reports'/('wc_e5_complete_sampling_cpu_r2_terminal_20261011_'+name.replace('/','_')+'.native.gz')
        assert not p.exists();p.write_bytes(zipped);row['local_ref']=str(p.relative_to(root));refs[name]=row
    proof['original_files']=refs
    path=root/'reports/wc_e5_complete_sampling_cpu_r2_terminal_20261011_capture.json'
    assert not path.exists();path.write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('original_files','actual_loaded_files','explicit_Toy_limits')}))


if __name__=='__main__':main()
