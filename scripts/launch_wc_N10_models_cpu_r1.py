#!/usr/bin/env python3
"""Stage the pinned code/resources and run the complete five-model CPU bundle."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
GIT_FILES=('scripts/evaluate_wc_N10_metric_model_cpu_r1.py','scripts/evaluate_wc_N10_models_cpu_bundle_r1.py',
 'scripts/launch_wc_N10_models_cpu_r1.py','scripts/capture_wc_N10_models_cpu_r1.py',
 'scripts/accept_wc_N10_models_cpu_r1.py','src/wcomr/__init__.py','src/wcomr/imaging_quality.py',
 'src/wcomr/automatic_quality_models_r1.py','src/wcomr/automatic_quality_metric_r1.py',
 'src/wcomr/automatic_quality_r1.py','src/wcomr/rv0_video_reader.py',
 'src/wcomr/frozen_shared_statistics_r1.py')
BOOT=r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
meta=json.loads(sys.stdin.buffer.readline());archive=sys.stdin.buffer.read()
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(meta['stage'])
assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2
assert relative.parts[0]=='.sync' and relative.parts[1].startswith('wc-N10-models-cpu-')
stage=root/meta['stage'];assert not stage.exists()
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
active=[name for name,job in pool['jobs'].items() if job['status']=='RESERVED_OR_RUNNING']
if active:
 print(json.dumps(dict(status='N10_HEAVY_MODEL_CPU_DEFERRED_REGISTERED_GPU_MAINLINE_ACTIVE',
  active_GPU_job_ids=active,stage_created=False,GPU_submissions=0,ledger_written=False)));sys.exit(0)
files={}
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as stream:
 for member in stream:
  name=pathlib.PurePosixPath(member.name)
  assert member.isfile() and not name.is_absolute() and '..' not in name.parts
  assert member.name in meta['payload_sha256'] and member.name not in files
  raw=stream.extractfile(member).read();assert hashlib.sha256(raw).hexdigest()==meta['payload_sha256'][member.name]
  files[member.name]=raw
assert set(files)==set(meta['payload_sha256'])
stage.mkdir()
for name,raw in files.items():
 path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
dino_root=pathlib.Path(meta['DINO_source_root']).resolve();all_sha=dict(meta['payload_sha256'])
for record in meta['DINO_source_records']:
 relative=pathlib.PurePosixPath(record['relative']);assert not relative.is_absolute() and '..' not in relative.parts
 source=dino_root/relative;assert source.resolve().is_relative_to(dino_root)
 raw=source.read_bytes();assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
 name='external/dino/'+str(relative);path=stage/name;assert not path.exists()
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);all_sha[name]=record['sha256']
registration=dict(purpose='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING',roles=meta['roles'],
 source_revision=meta['source_revision'],stage=str(stage),payload_sha256=all_sha,
 official_VBench_commit=meta['official_VBench_commit'],resource_capture_sha256=meta['resource_capture_sha256'],
 GPU_submissions=0,original_generation_stages_written=False,ledger_written=False)
with (stage/'registration.json').open('x') as handle:json.dump(registration,handle,indent=2)
command=[sys.executable,str(stage/'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py'),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),
 OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
os.nice(10)
with (stage/'CPU-model-bundle.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
  env=env,start_new_session=True)
fields=(pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split();now=time.time()
launch=dict(status='N10_FULL_FIVE_METRIC_MODEL_CPU_SINGLE_DISPATCHED',pid=child.pid,start_ticks=int(fields[19]),
 process_state=fields[0],command=command,stage=str(stage),source_revision=meta['source_revision'],roles=meta['roles'],
 registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 payload_files=len(all_sha),started_unix=now,first_collection_not_before_unix=now+900,
 GPU_submissions=0,ledger_written=False,paper_quality_scores_generated=False)
with (stage/'CPU-model-launch.json').open('x') as handle:json.dump(launch,handle,indent=2)
print(json.dumps(launch,allow_nan=False))
'''


def packet(resource_capture,stage):
    sys.path.insert(0,str(ROOT/'scripts'))
    from evaluate_wc_N10_metric_model_cpu_r1 import ROLES,WEIGHTS,BPE_SHA
    captured=json.loads(resource_capture.read_text());launch=captured['launch'];result=captured['result']
    if (captured['status']!='N10_ORIGINAL_RESOURCE_ONCE_CAPTURE' or captured['original_process_alive']
            or captured['observed_unix']<launch['first_collection_not_before_unix']
            or not captured['target_exists'] or result is None or result['exit_code']!=0
            or result['source_revision']!=launch['source_revision']
            or result['status']!='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME'
            or (captured['independent_target_bytes'],captured['independent_target_sha256'])!=WEIGHTS['ViCLIP']
            or (result['actual_bytes'],result['actual_sha256'])!=WEIGHTS['ViCLIP']):
        raise ValueError('Receive and independently accept the original whole ViCLIP bytes before model CPU')
    if result['target']!=str(Path(launch['stage'])/launch['expected_weight']['name']):
        raise ValueError('Use the original independently read resource file')
    files={};revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name in GIT_FILES:
        raw=(ROOT/name).read_bytes()
        if subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)!=raw:
            raise ValueError('Commit every CPU source before immutable staging: '+name)
        files[name]=raw
    pack=json.loads((ROOT/'reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json').read_text())
    if (pack['official_commit']!='fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
            or pack['verified_files']!=216 or len(pack['records'])!=216):
        raise ValueError('Use the already frozen full code pack')
    for row in pack['records']:
        name=Path(row['path'])
        if name.is_absolute() or '..' in name.parts:raise ValueError('Pinned source path escaped')
        raw=(ROOT/pack['source_root']/name).read_bytes()
        if (len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']
                or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['expected_git_blob_sha1']):
            raise ValueError('Pinned upstream source bytes changed: '+str(name))
        files['upstream/'+str(name)]=raw
    bpe=(ROOT/'.sync/wc-N10-official-tokenizer-pinned-r1-20261016/bpe_simple_vocab_16e6.txt.gz').read_bytes()
    assert len(bpe)==1356917 and hashlib.sha256(bpe).hexdigest()==BPE_SHA
    files['cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz']=bpe
    audit=json.loads((ROOT/'reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json').read_text())['observation']
    resources={}
    for row in audit['resources']:
        if (row['bytes'],row['sha256'])!=WEIGHTS[row['role']]:raise ValueError('Existing resource identity changed')
        resources[row['role']]={k:row[k] for k in ('path','bytes','sha256')}
    resources['ViCLIP']=dict(path=result['target'],bytes=WEIGHTS['ViCLIP'][0],sha256=WEIGHTS['ViCLIP'][1])
    assert set(resources)==set(ROLES)
    files['model-resources.json']=(json.dumps(dict(resources=resources),indent=2)+'\n').encode()
    for name in ('reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json',
                 'manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'):
        files['references/'+Path(name).name]=(ROOT/name).read_bytes()
    metadata=dict(stage=stage,source_revision=revision,roles=list(ROLES),
        official_VBench_commit=pack['official_commit'],resource_capture_sha256=hashlib.sha256(resource_capture.read_bytes()).hexdigest(),
        payload_sha256={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},
        DINO_source_root=audit['DINO_cached_source_root'],
        DINO_source_records=[{k:r[k] for k in ('relative','bytes','sha256')} for r in audit['DINO_cached_python_sources']])
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name,raw in sorted(files.items()):
            info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;archive.addfile(info,io.BytesIO(raw))
    return metadata,stream.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource-capture',type=Path,required=True)
    parser.add_argument('--stage',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    relative=Path(args.stage)
    assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2
    assert relative.parts[0]=='.sync' and relative.parts[1].startswith('wc-N10-models-cpu-')
    meta,archive=packet(args.resource_capture,args.stage)
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(BOOT)],
            input=json.dumps(meta).encode()+b'\n'+archive,capture_output=True,timeout=120)
    except (subprocess.TimeoutExpired,OSError) as error:
        args.output.write_text(json.dumps(dict(status='N10_MODEL_CPU_DISPATCH_TRANSPORT_UNKNOWN_NO_RETRY',
            stage=args.stage,source_revision=meta['source_revision'],error_type=type(error).__name__,error=str(error),
            original_launch_ref='CPU-model-launch.json',GPU_submissions=0,ledger_written=False),indent=2)+'\n')
        raise
    value=dict(transport_exit_code=call.returncode,stderr=call.stderr.decode(),
               source_revision=meta['source_revision'],overlay_metadata=meta)
    try:value['launch']=json.loads(call.stdout)
    except json.JSONDecodeError:value['stdout']=call.stdout.decode()
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='overlay_metadata'},allow_nan=False));raise SystemExit(call.returncode)


if __name__=='__main__':main()
