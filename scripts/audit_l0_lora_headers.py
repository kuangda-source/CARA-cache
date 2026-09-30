"""CPU-only replayable structural audit of pinned adapter/base headers."""
import argparse,json
from pathlib import Path
from wcomr.lora_header_audit import validate_tensor_table,audit_adapter
from wcomr.development_vqa_run import load_bound
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();lock=json.loads(a.manifest.read_text())
base={};index=load_bound(a.project/lock['base_index']['path'],lock['base_index']['sha256'])['weight_map']
for row in lock['base_headers']:
 h=load_bound(a.project/row['path'],row['sha256']);entries=validate_tensor_table(h,row['file_bytes']-row['header_bytes']-8)
 if set(base)&set(entries):raise ValueError('Duplicate base keys across shards')
 for k in entries:
  if index[k]!=row['filename']:raise ValueError('Base index/shard differs')
 base.update(entries)
if set(base)!=set(index):raise ValueError('Base shard index coverage differs')
result={'status':'L0_STRUCTURE_AUDIT_COMPLETE_NOT_GPU_READY','base_tensors':len(base),'adapters':[],'gpu_workload_started':False}
for row in lock['adapters']:
 h=load_bound(a.project/row['header_path'],row['header_sha256']);c=load_bound(a.project/row['config_path'],row['config_sha256'])
 if c['base_model_name_or_path']!='Wan-AI/Wan2.2-TI2V-5B':raise ValueError('Adapter base family differs')
 out=audit_adapter(h,row['header_bytes'],row['file_bytes'],c,base,row['requested_weight']);out.update(repo=row['repo'],revision=row['revision']);result['adapters'].append(out)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'base_tensors':len(base),'adapters':[{k:r[k] for k in ['repo','revision','tensor_count','paired_target_count','rank','alpha']} for r in result['adapters']]},indent=2))
