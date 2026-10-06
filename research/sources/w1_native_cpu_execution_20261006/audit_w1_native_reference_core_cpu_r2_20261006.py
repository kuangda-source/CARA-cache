import ast,hashlib,json,subprocess
from pathlib import Path
m=json.loads(Path('manifests/wc_w1_native_reference_core_cpu_r2_20261006.json').read_text());r=json.loads(Path('reports/wc_w1_native_reference_core_actual_cpu_r2_20261006.json').read_text());oldB=json.loads(Path('manifests/wc_w3_placement_production_cpu_r2_20261005.json').read_text())
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text());ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
expected={}
root='/home/gaokuangda/data/gkd/worldcache_omr';stage=root+'/'+m['stage'];base=root+'/'+m['base_stage']
for name,d in m['payload_sha256'].items():expected[stage+'/'+name]=d
for name,d in m['base_complete_payload_sha256'].items():expected[base+'/'+name]=d
expected[base+'/receipt.json']=m['base_original_receipt_sha256'];expected[stage+'/receipt.json']=r['server_receipt_sha256']
for name,d in oldB['payload_sha256'].items():expected[root+'/'+oldB['stage']+'/'+name]=d
expected[root+'/'+oldB['stage']+'/receipt.json']='f6d978561fe231da2b7aafe33f77cf4408ace7bb452120d8f3178e77b9f72aac'
expected[root+'/reports/budget.json']=m['budget_sha256']
remote='EXPECTED='+repr(expected)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(root)+'\n'+r'''
import hashlib,json,os,pathlib,time
root=pathlib.Path(ROOT);stage=pathlib.Path(STAGE)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert all(sha(p)==d for p,d in EXPECTED.items())
r=json.loads((stage/'receipt.json').read_text());assert r['exit_code']==0 and r['GPU_submissions']==0 and r['actual_new_videos']==0
checks={x['name']:x for x in r['checks']};assert all(x['exit_code']==0 for x in checks.values())
core=checks['two-complete-five-reference-torch-fixtures']['result'];assert core['CPU_mock_writer'] and not core['real_video_or_codec_verified'] and core['old_instance_patch_never_executed']
assert len(core['batches'])==2 and len(core['generation_refusals'])==8 and len(core['scope_refusals'])==16
verified=[]
for batch in core['batches']:
 assert batch['planned_references']==5 and batch['original_denominator']==[8,7,1] and len(batch['cases'])==5
 for c in batch['cases']:
  assert c['full_frame_decode_status']=='PENDING_CPU_AFTER_GPU_RELEASE'
  if c['outcome']=='TEXT_REJECTED':assert c['CFG_calls']==0 and c['artifact'] is None
  else:
   assert c['CFG_calls']==72 and c['solver_steps']==36 and c['prepare_calls']==1
   assert len(c['trace'])==72 and all(e['deep_executed'] for e in c['trace'])
   assert c['block_counts']=={'denoiser_calls':72,'full_calls':72,'skipped_deep_calls':0}
  if c['outcome']!='ACCEPTED':assert c['artifact'] is None
  else:
   path=pathlib.Path(c['artifact']['path']);assert path.is_file() and sha(path)==c['artifact']['sha256']
   EXPECTED[str(path)]=c['artifact']['sha256']
 verified.append({'accepted':batch['accepted_references'],'rejected':batch['rejected_references'],'CFG_calls':[c['CFG_calls'] for c in batch['cases']], 'mock_only':True})
real=checks['actual-native-class-original-arguments-import']['result'];assert real['parsed_original_requests']==8 and not real['CUDA_initialized'] and not real['weights_loaded'] and not real['model_instantiated']
handles=[]
for path in [stage/'CPU-start.json']+sorted(stage.glob('*-handle.json')):
 x=json.loads(path.read_text());pid=x['PID'];alive=pathlib.Path('/proc')/str(pid)
 assert not alive.exists(), 'CPU handle still live or reused: '+str(pid)
 handles.append({'path':str(path),'PID':pid,'exited':True});EXPECTED[str(path)]=sha(path)
for path in sorted(stage.glob('*.log'))+sorted(stage.glob('*.err'))+[stage/'manifest.json']:
 EXPECTED[str(path)]=sha(path)
print(json.dumps({'status':'FIVE_NATIVE_REFERENCE_CPU_NATIVE_SHA_AND_FULL_RAW_SCOPE_AUDIT_PASS','observed_unix':time.time(),
 'native_sha256':EXPECTED,'native_file_count':len(EXPECTED),'two_mock_batches':verified,'source_and_budget_unchanged':True,
 'old_B_and_R1_failed_stages_unchanged':True,'exited_CPU_handles':handles,'scope_refusals':16,'generation_refusals':8,
 'real_native_import_and_eight_original_arguments_pass':True,'B_authorization_exists':(root/'manifests/wc_w3_placement_gpu_authorization_20261005.json').exists(),
 'B_output_exists':(root/'outputs/wc-w3-placement-swap-r1').exists(),'W1_GPU_output_exists':(root/'outputs/wc-w1-native-reference-cal8-r1').exists(),
 'GPU_submissions':0,'actual_new_videos':0,'mock_artifacts_are_video_evidence':False,'audit_imports_new_sampling_code':False,'budget_sha256':sha(root/'reports/budget.json')}))
'''
p=subprocess.run(ssh+['python3 -'],input=remote,text=True,capture_output=True,timeout=55);assert p.returncode==0,p.stderr
value=json.loads(p.stdout);value['audit_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
out=Path('reports/wc_w1_native_reference_core_cpu_audit_r2_20261006.json');assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:value[k] for k in ['status','native_file_count','two_mock_batches','scope_refusals','generation_refusals','B_authorization_exists','B_output_exists','W1_GPU_output_exists','GPU_submissions']}))
