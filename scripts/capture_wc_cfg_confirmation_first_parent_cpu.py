#!/usr/bin/env python3
"""Read-only audit of a completed first parent; no scoring or scope acceptance."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch=json.loads(Path('reports/wc_cfg_mechanism_confirmation_r1_GPU_launch_20261009.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,math,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(L['stage']);run=root/'outputs'/L['run_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sup=json.loads((run/'supervisor.json').read_text());raw=(run/'diagnostic/receipt.json').read_bytes();r=json.loads(raw)
pids=[sup['pid'],sup['child_pid'],L['post_CPU_pid']];live=[p for p in pids if pathlib.Path('/proc/'+str(p)).exists()]
assert sup['pid']==L['supervisor_pid'] and sup['source_revision']==r['source_revision']==L['source_revision']
c=json.loads((stage/'teacher-config.json').read_text());assert sha(stage/'teacher-config.json')==L['config_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256'] and len(c['payload_sha256'])==77
parents=r['teacher']['parents'];assert parents and parents[0]['phase']=='OFF';p=parents[0]
if p['status']!='COMPLETE_PARENT':
 print(json.dumps({'proof':{'status':'ORIGINAL_FIRST_PARENT_NOT_COMPLETE_NO_PARTIAL_ACCEPTANCE','observed_unix':time.time(),'parent_status':p['status'],'original_live_PIDs':live,'GPU_submissions':0},'native':None}));raise SystemExit(0)
assert len(p['inputs'])==len(p['outputs'])==len(p['deep'])==len(p['banks'])==len(p['net_measurements'])==72
assert len(p['solver_outputs'])==len(p['solver_measurements'])==36 and len(p['final_components'])==1216
assert p['flags_before']==p['flags_after']
if 'actual_cfg_calls' in p['pipeline']:assert p['pipeline']['actual_cfg_calls']==72
contract='CFG_MEASUREMENT_SPACES_AND_ACTIVE_CONDITION_V1';empty=0;zero_mask=0;full_sha=set();active_sha=set();dtypes=set()
for signature,witness in zip(p['inputs'],p['net_measurements']):
 assert witness['contract']==contract and witness['space']=='ACTUAL_NET_INPUT_AFTER_DENOISE_CONDITIONING'
 assert witness['x_B_C_T_H_W']['tree_sha256']==signature['kwargs']['x_B_C_T_H_W']
 condition=witness['condition'];gt=condition['full_gt_frames'];mask=condition['condition_mask'];active=condition['active_values']
 assert gt['tree_sha256']==signature['kwargs']['gt_frames'] and mask['tree_sha256']==signature['kwargs']['condition_video_input_mask_B_C_T_H_W']
 assert condition['selection']=='BCTHW_CONTIGUOUS_FLAT_ORDER_WHERE_BROADCAST_MASK_IS_ONE'
 assert condition['zero_active_values']==(active['elements']==0) and not condition['full_condition_equality_inferred_from_active_values']
 for item in (witness['x_B_C_T_H_W'],gt,mask,active):
  assert item['elements']==math.prod(item['shape']) and len(item['tree_sha256'])==64
 if condition['zero_active_values']:
  assert active['shape']==[0] and active['dtype']==gt['dtype']
  assert hashlib.sha256(str((active['dtype'],active['shape'])).encode()).hexdigest()==active['tree_sha256'];empty+=1
  sizes={'torch.bfloat16':2,'torch.float16':2,'torch.float32':4,'torch.float64':8,'torch.bool':1,'torch.uint8':1}
  assert mask['dtype'] in sizes
  h=hashlib.sha256();h.update(str((mask['dtype'],mask['shape'])).encode());h.update(bytes(mask['elements']*sizes[mask['dtype']]))
  assert h.hexdigest()==mask['tree_sha256'];zero_mask+=1
 full_sha.add(gt['tree_sha256']);active_sha.add(active['tree_sha256']);dtypes.add(gt['dtype'])
for witness,original in zip(p['solver_measurements'],p['solver_outputs']):
 assert witness['contract']==contract and witness['space']=='RAW_SOLVER_RETURN_AND_EXTRACTED_NEXT_SAMPLER_LATENT'
 assert witness['raw_return_tree_sha256']==original and witness['raw_return_structure'] in ('tuple','list')
 assert witness['extraction']=='ORIGINAL_LOOP_VALUE_0_SQUEEZE_0'
 a,b=witness['raw_first_tensor'],witness['next_sampler_latent']
 expected=a['shape'][1:] if a['shape'] and a['shape'][0]==1 else a['shape']
 assert expected==b['shape'] and a['dtype']==b['dtype'] and a['elements']==b['elements']
item=p['artifact'];video=pathlib.Path(item['path']);assert (run/'diagnostic').resolve() in video.resolve().parents
assert video.stat().st_size==item['bytes'] and sha(video)==item['sha256']
budget=json.loads((root/'reports/budget.json').read_text());assert budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
gpu_live=any(pid in live for pid in (sup['pid'],sup['child_pid']))
if gpu_live:assert budget.get('wc_cfg_teacher_inflight',{}).get('supervisor_pid')==sup['pid']
proof={'status':'FIRST_COMPLETE_PARENT_METADATA_MEASUREMENT_AND_VIDEO_BYTES_READONLY_PASS_NOT_FULL_CARD',
 'observed_unix':time.time(),'source_revision':L['source_revision'],'original_live_PIDs':live,'original_config_and77_payload_unchanged':True,
 'complete_parents_verified':1,'planned_parents':2,'net_condition_witnesses_bound':72,'solver_space_witnesses_bound':36,
 'explicit_empty_active_value_hashes_reconstructed':empty,'zero_condition_mask_hashes_reconstructed':zero_mask,
 'distinct_full_gt_frames_hashes':len(full_sha),'distinct_active_values_hashes':len(active_sha),'actual_gt_dtypes':sorted(dtypes),
 'video_file_bytes_sha256_verified':True,'video_full93_decode_performed':False,
 'full_parent_parity_or_five_origin_scope_accepted':False,'old_condition_equality_imputed':False,
 'current_budget_is_inflight_reservation_not_final_spend':gpu_live,'GPU_submissions':0,'scientific_quality_or_fidelity_claim':False}
compressed=gzip.compress(raw,mtime=0)
print(json.dumps({'proof':proof,'native':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}}))
'''
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                           input=source,text=True,capture_output=True,timeout=55)
    if process.returncode:raise RuntimeError(process.stderr[-4000:])
    result=json.loads(process.stdout)
    if result['native'] is None:print(json.dumps(result['proof']));return 2
    item=result['native'];compressed=base64.b64decode(item['gzip_base64'],validate=True);raw=gzip.decompress(compressed)
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    assert hashlib.sha256(compressed).hexdigest()==item['compressed_sha256']
    prefix='reports/wc_cfg_mechanism_confirmation_r1_first_parent_20261009_'
    archive=Path(prefix+'receipt.native.gz');dest=Path(prefix+'readonly_audit.json');assert not archive.exists() and not dest.exists()
    archive.write_bytes(compressed);proof=result['proof']
    proof['original_partial_receipt']={k:v for k,v in item.items() if k!='gzip_base64'}
    proof['original_partial_receipt']['local_path']=str(archive)
    dest.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='original_partial_receipt'}));return 0


if __name__=='__main__':raise SystemExit(main())
