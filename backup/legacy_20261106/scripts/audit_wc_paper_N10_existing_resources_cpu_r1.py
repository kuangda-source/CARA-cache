#!/usr/bin/env python3
"""Read and hash named metric resources; do not import models or write server files."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE = r'''
import hashlib,importlib.metadata as md,json,os,pathlib,sys,time
started=time.time();home=pathlib.Path('/home/gaokuangda');cache=home/'.cache'
project=(home/'data/gkd/worldcache_omr').resolve()
def digest(path):
 before=path.stat();value=hashlib.sha256()
 with path.open('rb') as handle:
  for block in iter(lambda:handle.read(8*1024*1024),b''):value.update(block)
 after=path.stat()
 assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
 return dict(path=str(path),resolved_path=str(path.resolve()),bytes=after.st_size,
  mtime_ns=after.st_mtime_ns,sha256=value.hexdigest(),stable_during_read=True)
targets=[('DINO',cache/'torch/hub/checkpoints/dino_vitbase16_pretrain.pth',343242485,None),
 ('AMT_S',cache/'vbench/amt_model/amt-s.pth',12038359,None),
 ('RAFT_THINGS',cache/'vbench/raft_model/models/raft-things.pth',21108000,None),
 ('MUSIQ_SPAQ',cache/'vbench/pyiqa_model/musiq_spaq_ckpt-358bb6af.pth',108610983,
  '358bb6af275e28ea56821d44fb55c6cb83645db11f394d3ad65b2d149965ab50')]
resources=[];errors=[]
for role,path,expected_bytes,expected_sha in targets:
 row=dict(role=role,path=str(path),exists=path.is_file(),previous_observed_bytes=expected_bytes,
  expected_sha256=expected_sha,canonical_author_bytes_proven_by_this_audit=expected_sha is not None)
 try:
  if row['exists']:
   row.update(digest(path));row['previous_size_matches']=row['bytes']==expected_bytes
   row['known_expected_SHA_matches']=row['sha256']==expected_sha if expected_sha else None
 except Exception as error:
  row.update(error_type=type(error).__name__,error=str(error));errors.append(dict(role=role,**row))
 resources.append(row)
dino=cache/'torch/hub/facebookresearch_dino_main';sources=[]
if dino.is_dir():
 for path in sorted(dino.rglob('*.py')):
  try:
   row=digest(path);row['relative']=str(path.relative_to(dino));sources.append(row)
   if path.name=='hubconf.py':row['source_text']=path.read_text()
  except Exception as error:errors.append(dict(path=str(path),error=str(error)))
packages={}
for name in ('torch','torchvision','pyiqa','vbench','decord','opencv-python','av','easydict',
 'omegaconf','einops','timm','ftfy','regex','scipy','yacs','open_clip_torch'):
 try:packages[name]=md.version(name)
 except md.PackageNotFoundError:packages[name]=None
pyiqa_arch=None
try:
 path=pathlib.Path(md.distribution('pyiqa').locate_file('pyiqa/archs/musiq_arch.py'))
 if path.is_file():pyiqa_arch=digest(path)
except md.PackageNotFoundError:pass
expected_viclip_sha='7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56'
names={'ViClip-InternVid-10M-FLT.pth',expected_viclip_sha}
roots=[cache/'vbench/ViCLIP',cache/'huggingface/hub/models--OpenGVLab--VBench_Used_Models',
 project/'hfhub/models--OpenGVLab--VBench_Used_Models',project/'models',home/'data/gkd/models']
if os.environ.get('VBENCH_CACHE_DIR'):
 roots.append(pathlib.Path(os.environ['VBENCH_CACHE_DIR'])/'ViCLIP')
searches=[];matches=[];seen_roots=set();seen_files=set()
for root in roots:
 label=str(root.resolve())
 if label in seen_roots:continue
 seen_roots.add(label);record=dict(root=str(root),exists=root.is_dir(),visited_entries=0,truncated=False)
 if root.is_dir():
  def walk_error(error):errors.append(dict(kind='SCOPED_VICLIP_WALK_ERROR',path=error.filename,error=str(error)))
  for directory,dirs,files in os.walk(root,followlinks=False,onerror=walk_error):
   dirs.sort()
   for filename in sorted(files):
    record['visited_entries']+=1
    if record['visited_entries']>20000:
     record['truncated']=True;break
    if filename not in names:continue
    path=pathlib.Path(directory)/filename
    if str(path.resolve()) in seen_files:continue
    seen_files.add(str(path.resolve()))
    try:
     row=digest(path);row['expected_SHA_matches']=row['sha256']==expected_viclip_sha;matches.append(row)
    except Exception as error:errors.append(dict(path=str(path),error=str(error)))
   if record['truncated']:break
 searches.append(record)
disk=[]
for path in (project,cache):
 info=os.statvfs(path);disk.append(dict(path=str(path),available_bytes=info.f_bavail*info.f_frsize))
assert 'torch' not in sys.modules and 'vbench' not in sys.modules
print(json.dumps(dict(status='N10_SCOPED_EXISTING_WEIGHT_HASH_AND_SOURCE_AUDIT_NOT_MODEL_RUNTIME',
 observed_unix=time.time(),wall_seconds=time.time()-started,interpreter=sys.executable,
 resources=resources,DINO_cached_source_root=str(dino),DINO_cached_python_sources=sources,
 package_versions=packages,pyiqa_MUSIQ_architecture=pyiqa_arch,
 ViCLIP_scoped_searches=searches,ViCLIP_exact_checkpoint_candidates=matches,errors=errors,disk=disk,
 implicit_downloads=0,weights_loaded=0,metric_models_imported=False,GPU_queries=0,GPU_submissions=0,
 server_files_written=False,server_ledger_written=False,final_test_video_or_scores_read=False,
 scoped_absence_is_not_machine_wide_absence=True),allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen', PYTHON+' -c '+shlex.quote(CODE)],
        capture_output=True, timeout=120)
    value = dict(transport_exit_code=result.returncode, stderr=result.stderr.decode(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_readonly_body_sha256=hashlib.sha256(CODE.encode()).hexdigest())
    if result.returncode == 0:
        value['observation'] = json.loads(result.stdout)
    else:
        value['stdout'] = result.stdout.decode()
    with args.output.open('x') as handle:json.dump(value,handle,indent=2,allow_nan=False)
    observed = value.get('observation', {})
    print(json.dumps(dict(receipt=str(args.output),transport_exit_code=result.returncode,
        named_weight_files_hashed=sum('sha256' in r for r in observed.get('resources',[])),
        DINO_source_files=len(observed.get('DINO_cached_python_sources',[])),
        ViCLIP_exact_candidates=len(observed.get('ViCLIP_exact_checkpoint_candidates',[])),
        errors=len(observed.get('errors',[])),GPU_submissions=0,server_files_written=False)))
    raise SystemExit(result.returncode)


if __name__ == '__main__':main()
