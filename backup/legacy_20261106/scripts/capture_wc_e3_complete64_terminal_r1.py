"""Read the original E3 terminal chain; never rerun its GPU or CPU readers.

The frozen post reader owns tensor decoding and LPIPS. This independent capture
binds originals, rehashes artifacts and reconstructs all reported frame contrasts.
A live original handle yields WAIT and creates no local terminal evidence.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''import base64,gzip,hashlib,json,math,pathlib,time
from statistics import mean
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=project/'.sync/wc-e3-complete64-selected-r1-20261011'
root=project/'outputs/wc-e3-current-birth-complete64-reuse10-fresh54-r1'
source='2e39cd31b593540130c08a394b92d9f5b5b5db42'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
def read(path):return json.loads(path.read_text())
sup=read(root/'supervisor.json');launch=read(stage/'GPU-launch.json')
assert sup['pid']==launch['gpu_supervisor_pid']==4163981
assert sup['source_revision']==launch['source_revision']==source
post_path=stage/'post-CPU-receipt.json'
post=read(post_path) if post_path.exists() else None
ids=[sup['pid'],launch['post_CPU_pid']]+[b['pid'] for b in sup['blocks'] if 'pid' in b]
assert launch['post_CPU_pid']==4163982
if post is not None:
 assert post['pid']==4163982 and post['original_supervisor_pid']==4163981 and post['source_revision']==source
 if 'child_pid' in post:ids.append(post['child_pid'])
live=[pid for pid in ids if pathlib.Path('/proc/'+str(pid)).exists()]
if live:
 print(json.dumps({'status':'WAIT_ORIGINAL_E3_GPU_OR_POST_CPU','original_live_pids':live,
  'GPU_status':sup['status'],'post_CPU_status':None if post is None else post['status'],
  'registered_positions':64,'new_GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}))
 raise SystemExit(0)
assert sup['status']=='E3_COMPLETE64_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
assert post is not None and post['exit_code'] in (0,1)
c=read(stage/'e3-complete64-config.json');p=read(stage/'e3-execution-protocol.json')
selection=read(stage/'selection.json')
assert sha(stage/'e3-complete64-config.json')==sup['config_sha256']==selection['selected_config_sha256']==B['selected_config_sha256']
assert sha(stage/'e3-execution-protocol.json')==B['protocol_sha256']
assert len(c['payload_sha256'])==449 and len(p['execution_payload_sha256'])==16
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
assert {n:sha(stage/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']
assert sha(stage/'production-CPU-receipt.json')==sup['production_CPU_receipt_sha256']
authority_path=stage/'manifests/wc_e3_complete64_direct_authorization_20261011.json'
assert sha(authority_path)==B['direct_authorization_sha256']
selected_cpu=read(stage/'selected-CPU-receipt.json')
assert sha(stage/'selected-CPU-receipt.json')==selection['selected_CPU_receipt_sha256']
assert selected_cpu['source_revision']==source and selected_cpu['exit_code']==selected_cpu['child_exit_code']==0
assert selected_cpu['GPU_submissions']==0 and selected_cpu['ledger_written'] is False
assert selected_cpu['budget_before_sha256']==selected_cpu['budget_after_sha256']
scope=read(stage/c['scope_ref'])
assert sha(stage/c['scope_ref'])==c['scope_sha256']
assert c['scope_counts']==sup['planned_scope']==B['planned_scope']
assert len(scope['all64_slots'])==64 and len(scope['blocks'])==len(sup['blocks'])==20
assert sum(len(b['paths']) for b in scope['blocks'])==54
before,after=sup['budget_before'],sup['budget_after']
assert not any('inflight' in k for k in after)
billed=sup['wall_seconds']/3600
assert math.isfinite(billed) and 0<=billed<=sup['authorized_billed_GPUh_limit']
assert math.isclose(after['used_gpu_hours'],before['used_gpu_hours']+billed,rel_tol=0,abs_tol=1e-10)
assert after['gpu_jobs_launched']==before['gpu_jobs_launched']+1==80
assert after['cap_gpu_hours']==before['cap_gpu_hours']==77.89524658965853
assert after['used_gpu_hours']<=after['cap_gpu_hours']
assert not sup['legacy_seconds_deadline_active']
originals={'GPU_supervisor':root/'supervisor.json','post_CPU_supervisor':post_path,
 'GPU_launch':stage/'GPU-launch.json','selected_config':stage/'e3-complete64-config.json',
 'execution_protocol':stage/'e3-execution-protocol.json','scope':stage/c['scope_ref'],
 'selection':stage/'selection.json','direct_authorization':authority_path,
 'selected_CPU_receipt':stage/'selected-CPU-receipt.json'}
fresh={}
for declared,lifecycle in zip(scope['blocks'],sup['blocks']):
 assert declared['id']==lifecycle['id'] and lifecycle['planned_paths']==len(declared['paths'])
 path=root/declared['id']/'receipt.json'
 if not path.exists():
  assert 'receipt_sha256' not in lifecycle
  continue
 assert sha(path)==lifecycle['receipt_sha256']
 receipt=read(path)
 assert receipt['source_revision']==source and receipt['pid']==lifecycle['pid']
 assert receipt['block']==declared and receipt['config_sha256']==sup['config_sha256']
 originals[declared['id']+'_receipt']=path
 allowed={(x['sample_name'],x['method']):x['slot'] for x in declared['paths']}
 for q in receipt.get('batch',{}).get('requests',[]):
  for row in q.get('paths',[]):
   key=(q['sample_name'],row['collect']);assert key in allowed
   slot=allowed[key];assert slot not in fresh
   fresh[slot]=(row,{'path':str(path),'sha256':sha(path)})
reused={}
reuse_sources={}
for name,bound in p['reuse_receipts'].items():
 path=project/bound['path'];assert sha(path)==bound['sha256']
 original=read(path);assert original['source_revision']==bound['source_revision']
 reuse_sources[name]=original;originals[name+'_reuse_receipt']=path
for slot in scope['all64_slots']:
 if slot['disposition']!='REUSE_QUALIFIED_DEV_OUTPUT':continue
 name='ORIGINAL64' if slot['reuse_binding']['origin']=='ORIGINAL_FAILED64_VALID_E0_PATH' else 'E1_CPU_PREFIX'
 original=reuse_sources[name]
 batch=original['batches'][slot['strategy']] if name=='ORIGINAL64' else original['batch']
 matches=[row for q in batch['requests'] if q['sample_name']==slot['sample_name']
  for row in q['paths'] if row['collect']==slot['method']]
 assert len(matches)==1;reused[slot['slot']]=matches[0]
raw_path=stage/'raw-audit.json';score_path=stage/'score-result.json'
raw=read(raw_path) if raw_path.exists() else None
score=read(score_path) if score_path.exists() else None
if raw is not None:originals['raw_audit']=raw_path
if score is not None:originals['score_result']=score_path
accepted=post['exit_code']==0
artifacts={};scored={};contrasts=[];raw_valid=0;tensors=0
def verify_artifact(art,artifact_root=None):
 path=pathlib.Path(art['path']).resolve()
 if artifact_root is not None:assert pathlib.Path(artifact_root).resolve() in path.parents
 else:assert (project/'outputs').resolve() in path.parents
 key=str(path)
 if key not in artifacts:
  assert path.is_file() and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
  artifacts[key]={'path':key,'bytes':art['bytes'],'sha256':art['sha256']}
 else:assert artifacts[key]['bytes']==art['bytes'] and artifacts[key]['sha256']==art['sha256']
if raw is not None:
 assert len(raw['slots_all64'])==64 and raw['GPU_supervisor']==sup
 assert raw['supervisor_sha256']==sha(root/'supervisor.json')
 assert raw['GPU_submissions']==0 and raw['ledger_written'] is False and raw['CUDA_initialized'] is False
 for declared,item in zip(scope['all64_slots'],raw['slots_all64']):
  assert all(declared[k]==item[k] for k in ('slot','strategy','sample_name','method','disposition'))
  assert item['missing_filled_with_zero'] is False
  if declared['disposition']=='REUSE_QUALIFIED_DEV_OUTPUT':
   assert item['source_kind']=='QUALIFIED_REUSED_DEV'
   for kind in ('vector_artifact','video_artifact'):
    assert reused[item['slot']][kind]==declared['reuse_binding'][kind]
    verify_artifact(declared['reuse_binding'][kind],item['artifact_root'])
  elif item['slot'] in fresh:
   row,receipt=fresh[item['slot']];assert item['source_kind']=='FRESH_E3_BLOCK' and item['source_receipt']==receipt
   if 'actual_vector_read' in item:assert item['actual_vector_read']['file']==row['vector_artifact']
  if item['status'].startswith('RAW_VALID'):
   v=item['actual_vector_read'];assert v['actual_tensors_reloaded']==37 and v['final_and_all_guided_hashes_verified']
   row=reused[item['slot']] if item['slot'] in reused else fresh[item['slot']][0]
   assert v['file']==row['vector_artifact'] and item['candidate']==row['video_artifact']
   assert item['decoded_video']['frames']==93
   verify_artifact(v['file'],item['artifact_root']);verify_artifact(item['candidate'],item['artifact_root'])
   assert item['pairing']['compatible']==item['compatible']
   actions=row['actions'];complete=row['collection_complete']
   deployment=complete.get('deployment');correction=deployment.get('A_readout') if deployment is not None else None
   extra=correction['extra_candidate_heads'] if correction else 0
   assert len(actions)==complete['complete_pairs']==36 and all(x in ('CC','PP','DD') for x in actions)
   assert len(complete['actual_original_plus_candidate_heads'])==72+extra
   cost={'actions':actions,'complete_branch_calls':2*actions.count('DD'),
    'partial_branch_calls':2*actions.count('PP'),'reuse_branch_calls':2*actions.count('CC'),
    'extra_candidate_heads':extra,'instrumented_pipeline_wall_seconds':row['instrumented_parent_pipeline_wall_seconds'],
    'source_kind':item['source_kind'],'source_revision':item['source_revision'],
    'source_receipt':item['source_receipt'],'block_id':item.get('block_id'),
    'clean_speed_claim':False,'cross_batch_or_load_order_isolation':False}
   assert cost==item['recorded_cost']
   raw_valid+=1;tensors+=37
if score is not None:
 assert raw is not None and score['raw_audit_sha256']==sha(raw_path)
 assert score['execution_protocol_sha256']==sha(stage/'e3-execution-protocol.json')
 assert len(score['slots_all64'])==64 and not score['GPU_submissions'] and not score['ledger_written'] and not score['CUDA_initialized']
 for original,item in zip(raw['slots_all64'],score['slots_all64']):
  assert all(original[k]==item[k] for k in ('slot','strategy','sample_name','method','disposition'))
  if not item['scored']:
   assert item['score'] is None
   continue
  assert original['status']=='RAW_VALID_COMPATIBLE_READY_TO_SCORE' and item['status']=='SCORED_FULL93' and item['compatible']
  value=item['score'];frames=value['frame_distances'];pts=value['pts']
  assert value['frames']==len(frames)==len(pts)==93 and len({tuple(x) for x in pts})==93
  assert all(math.isfinite(x) for x in frames) and math.isclose(mean(frames),value['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
  assert value['reference_sha256']==item['reference']['sha256'] and value['candidate_sha256']==item['candidate']['sha256']
  verify_artifact(item['reference']);verify_artifact(item['candidate'],item['artifact_root'])
  key=(item['strategy'],item['sample_name'],item['method']);assert key not in scored;scored[key]=item
 if score.get('summary') is not None:
  summary=score['summary']
  assert summary['registered_positions']==64 and summary['qualified_reuse_positions']==10 and summary['fresh_generation_positions']==54
  assert summary['scored_pairs']==len(scored) and summary['actual_frame_distances']==93*len(scored)
  assert summary['gaps_retained']==64-len(scored) and not summary['missing_scores_filled_with_zero']
  assert not summary['clean_speed_claim'] and not summary['frames_are_independent_samples']
  assert summary['fidelity_not_semantic_or_physics_quality'] and summary['development_not_independent_confirmation']
  assert len(summary['per_slot'])==64
  for item,presented in zip(score['slots_all64'],summary['per_slot']):
   assert all(item.get(k)==v for k,v in presented.items())
  within=[('DYNAMIC_NO_P','SOURCE_RA'),('CPD','DYNAMIC_NO_P'),('REF_CPD','CPD'),('A_CPD_OFF','CPD'),
   ('A_CPD_W1_ONE_PHASE','CPD'),('A_CPD_BETA1_ONE_PHASE','CPD'),('A_CPD_W1_ONE_PHASE','A_CPD_BETA1_ONE_PHASE'),
   ('DENSE_CONTROL','SOURCE_RA')]
  expected=[([s,a],[s,b]) for s in scope['strategies'] for a,b in within]
  expected += [([scope['strategies'][1],m],[scope['strategies'][0],m]) for m in scope['methods']]
  assert [(x['candidate'],x['baseline']) for x in summary['contrasts']]==expected and len(expected)==24
  for entry in summary['contrasts']:
   matched=[];gaps=[];cs,cm=entry['candidate'];bs,bm=entry['baseline']
   for name in scope['sample_names']:
    candidate=scored.get((cs,name,cm));baseline=scored.get((bs,name,bm))
    if candidate is None or baseline is None:
     gaps.append({'sample_name':name,'candidate_available':candidate is not None,'baseline_available':baseline is not None});continue
    a,b=candidate['score'],baseline['score']
    assert candidate['reference']==baseline['reference'] and a['pts']==b['pts']
    delta=[y-x for x,y in zip(a['frame_distances'],b['frame_distances'])]
    matched.append({'sample_name':name,'candidate_LPIPS':a['mean_LPIPS'],'baseline_LPIPS':b['mean_LPIPS'],
     'baseline_minus_candidate_LPIPS':mean(delta),
     'relative_LPIPS_improvement_percent':100*mean(delta)/b['mean_LPIPS'] if b['mean_LPIPS']>0 else None,
     'improved_frames':sum(x>0 for x in delta),'degraded_frames':sum(x<0 for x in delta),'tied_frames':sum(x==0 for x in delta),
     'contiguous31_frame_mean_differences':[mean(delta[i:i+31]) for i in (0,31,62)],
     'candidate_recorded_cost':candidate.get('recorded_cost'),'baseline_recorded_cost':baseline.get('recorded_cost'),
     'same_card_clean_timing_comparison':False})
   reconstructed={'candidate':entry['candidate'],'baseline':entry['baseline'],'registered_scenes':4,
    'matched_scenes':len(matched),'gaps':gaps,'per_scene':matched,
    'scene_equal_mean_LPIPS_difference':mean(x['baseline_minus_candidate_LPIPS'] for x in matched) if matched else None,
    'improved_scenes':sum(x['baseline_minus_candidate_LPIPS']>0 for x in matched),
    'degraded_scenes':sum(x['baseline_minus_candidate_LPIPS']<0 for x in matched)}
   assert reconstructed==entry
   contrasts.append(reconstructed)
if accepted:
 assert post['child_exit_code']==0 and post['status']=='E3_COMPLETE_SCOPE_CPU_EXIT0_ALL_AVAILABLE93_NOT_METHOD_ACCEPTANCE'
 assert raw['status']=='E3_COMPLETE64_RAW_CPU_TERMINAL_ALL_SLOTS_RETAINED'
 assert score['status']=='E3_COMPLETE64_ALL_AVAILABLE93_CPU_TERMINAL_NOT_AUTOMATIC_METHOD_ACCEPTANCE'
 assert post['raw_sha256']==sha(raw_path) and post['score_sha256']==sha(score_path)
 assert post['budget_before_sha256']==post['budget_after_sha256']==score['budget_after_sha256']==raw['budget_before_sha256']
 assert len(contrasts)==24 and score['whole64_all_scored']==(len(scored)==64)
 assert score['whole64_all_scored']==post['whole64_all_scored']
 assert score['actual_score_failures']==post['actual_score_failures']==sum(x['status']=='SCORE_FAILED_RETAINED' for x in score['slots_all64'])
 assert raw['valid_complete_paths']==raw_valid
 assert post['GPU_submissions']==0 and post['ledger_written'] is False
current_ledger=read(project/'reports/budget.json')
blobs={}
for name,path in originals.items():
 raw_bytes=path.read_bytes();h=hashlib.sha256(raw_bytes).hexdigest()
 blobs[name]={'remote_path':str(path),'bytes':len(raw_bytes),'sha256':h,
  'gzip_base64':base64.b64encode(gzip.compress(raw_bytes,mtime=0)).decode()}
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in ids)
assert sha(root/'supervisor.json')==blobs['GPU_supervisor']['sha256']
print(json.dumps({'status':'E3_ORIGINAL_COMPLETE_SCOPE_TERMINAL_INDEPENDENTLY_CAPTURED',
 'source_revision':source,'original_PIDs_absent':ids,'registered_positions':64,'qualified_reuses':10,
 'fresh_registered_paths':54,'all20_original_processes_attempted':sup['all20_original_processes_attempted'],
 'post_CPU_exit_code':post['exit_code'],'complete_scope_post_chain_verified':accepted,
 'whole64_all_scored':len(scored)==64,'raw_valid_paths':raw_valid,'actual_original_reader_tensors':tensors,
 'scored_pairs':len(scored),'actual_frame_distances':93*len(scored),'all24_contrasts_independently_reconstructed':len(contrasts)==24,
 'frozen_method_files_unchanged':449,'frozen_execution_files_unchanged':16,
 'artifact_hashes_independently_verified':list(artifacts.values()),'contrasts':contrasts,
 'billed_GPUh':billed,'settled_ledger':after,'remaining_GPUh_at_settlement':after['cap_gpu_hours']-after['used_gpu_hours'],
 'current_ledger_observation':current_ledger,'new_GPU_submissions':0,'ledger_written':False,
 'original_CPU_reader_rerun':False,'method_acceptance_or_clean_speed_claim':False,'observed_unix':time.time(),'originals':blobs}))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = args.output if args.output.is_absolute() else root / args.output
    assert target.parent.resolve() == (root / 'reports').resolve()
    assert not target.exists()
    startup = json.loads((root / 'reports/wc_e3_complete64_real_gpu_start_r1_20261011.json').read_text())
    assert startup['source_revision'] == '2e39cd31b593540130c08a394b92d9f5b5b5db42'
    binding = {k: startup[k] for k in ('planned_scope',)}
    # These values also bind the historical startup originals, not current HEAD.
    binding.update(selected_config_sha256='4ae93359ff2e0ec51fdcb3aa957ecdfcca4b6724119146354883ee3e367b57ba',
                   protocol_sha256='3ca6e941c45684e5853be9ad418dedc2194c48bb5e0ce69f000d6c7526291d72',
                   direct_authorization_sha256='a3119dd46f1005a56abbd371880189622487f914b0fe9080250ca4ddf9f4c843')
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input='B='+repr(binding)+'\n'+REMOTE, text=True, capture_output=True)
    if call.returncode:
        raise RuntimeError(call.stderr[-3500:])
    value = json.loads(call.stdout)
    if value['status'].startswith('WAIT_'):
        print(json.dumps(value)); return
    folder = target.with_suffix('')
    assert not folder.exists()
    folder.mkdir()
    for name, entry in value['originals'].items():
        packed = base64.b64decode(entry.pop('gzip_base64'), validate=True)
        raw = gzip.decompress(packed)
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
        local = folder / (name+'.json.gz')
        local.write_bytes(packed)
        entry.update(local_ref=str(local.relative_to(root)), local_gzip_sha256=hashlib.sha256(packed).hexdigest())
    target.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','complete_scope_post_chain_verified',
        'whole64_all_scored','scored_pairs','actual_frame_distances','billed_GPUh')}))


if __name__ == '__main__':
    main()
