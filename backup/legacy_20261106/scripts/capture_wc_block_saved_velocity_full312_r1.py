"""One read-only observation of the immutable B full312 original handles.

Remote JSON is gzip-compressed in transit. Local .json.gz or .json receipts are
created exclusively; this tool never launches, retries, or writes on the server.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "988ace1834af14c4ed535ed7b025c9619fec948e"
PYTHON = "/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python"
HOST = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
        "-o", "ClearAllForwardings=yes", "gkd_minchen"]
DEFAULT_OUTPUT = "reports/wc_block_saved_velocity_full312_collection_20261014.json.gz"

CODE = r'''
import base64,fcntl,gzip,hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/'.sync/wc-block-velocity-production-r1-20261013'
source='988ace1834af14c4ed535ed7b025c9619fec948e'
uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
sha=lambda data:hashlib.sha256(data).hexdigest()
def read_json(path):
 data=path.read_bytes()
 return json.loads(data),sha(data)
reg,reg_sha=read_json(stage/'registration.json')
assert reg['source_revision']==source
assert len(reg['payload_sha256'])==730
cfg,cfg_sha=read_json(stage/'configs/wc_block_velocity_suffix3_full312_production_r1_20261013.json')
assert cfg['run_id']=='wc-block-saved-velocity-full312-r1'
assert cfg['scope_counts']['pairs']==312 and cfg['scope_counts']['videos']==16
output=root/'outputs'/cfg['run_id']
r=dict(observed_unix=time.time(),stage=str(stage),output=str(output),
 source_revision=source,registration_sha256=reg_sha,config_sha256=cfg_sha,
 payload_files=len(reg['payload_sha256']),scope_counts=cfg['scope_counts'],
 GPU_submissions_by_capture=0,server_mutations_by_capture=False)
r['payload_verified']={}
for name,digest in reg['payload_sha256'].items():
 path=(stage/name).resolve()
 assert path.is_relative_to(stage.resolve())
 r['payload_verified'][name]=path.is_file() and sha(path.read_bytes())==digest
for key,path in [('launch',stage/'GPU-launch.json'),
 ('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),
 ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),
 ('production_CPU',stage/'production-CPU-result.json')]:
 if path.exists():r[key],r[key+'_sha256']=read_json(path)
if r.get('launch'):assert r['launch']['source_revision']==source
ids={}
for key in ('supervisor_pid','post_watcher_pid'):
 if r.get('launch',{}).get(key):ids[key]=r['launch'][key]
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
r['original_processes']={}
for key,pid in ids.items():
 assert isinstance(pid,int) and pid>0
 proc=pathlib.Path('/proc',str(pid));value=dict(pid=pid,exists=proc.exists())
 if value['exists']:
  try:value['cmdline']=proc.joinpath('cmdline').read_bytes().replace(b'\x00',b' ').decode(errors='replace').strip()
  except FileNotFoundError:value['exists']=False
  except OSError as error:value['cmdline_error']=str(error)
 r['original_processes'][key]=value
r['ledger'],r['ledger_sha256']=read_json(root/'reports/budget.json')
try:
 r['GPU']=subprocess.check_output(['nvidia-smi','-i',uuid,
  '--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],
  text=True,timeout=10).strip()
 r['compute_apps']=subprocess.check_output(['nvidia-smi',
  '--query-compute-apps=gpu_uuid,pid,process_name','--format=csv,noheader,nounits'],
  text=True,timeout=10).strip()
except (OSError,subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
 r['GPU_telemetry_error']=dict(status='TELEMETRY_UNAVAILABLE',error=str(error))
lock_path=root/'.sync/f1.lock'
if lock_path.exists():
 with lock_path.open('r') as lock:
  try:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   r['kernel_lock_free']=True
   fcntl.flock(lock,fcntl.LOCK_UN)
  except BlockingIOError:r['kernel_lock_free']=False
else:r['kernel_lock_free']=None;r['kernel_lock_status']='MISSING_EXISTING_LOCK_NOT_CREATED'
def tail(path):
 with path.open('rb') as handle:
  handle.seek(0,2);end=handle.tell();handle.seek(max(0,end-65536))
  return '\n'.join(handle.read().decode(errors='replace').splitlines()[-8:])
for key,path in [('GPU_log_tail',output/'GPU.log'),
 ('GPU_supervisor_log_tail',stage/'GPU-supervisor.log'),
 ('post_log_tail',stage/'post-CPU.log'),('post_watcher_log_tail',stage/'post-watcher.log')]:
 if path.exists():r[key]=tail(path)
raw=json.dumps(r,allow_nan=False,separators=(',',':')).encode()
compressed=gzip.compress(raw,compresslevel=6,mtime=0)
print(json.dumps(dict(encoding='gzip-base64',uncompressed_sha256=sha(raw),
 compressed_sha256=sha(compressed),payload=base64.b64encode(compressed).decode())))
'''


def decode_capture(response):
    packet = json.loads(response)
    assert packet["encoding"] == "gzip-base64"
    compressed = base64.b64decode(packet["payload"], validate=True)
    assert hashlib.sha256(compressed).hexdigest() == packet["compressed_sha256"]
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == packet["uncompressed_sha256"]
    result = json.loads(raw)
    assert result["source_revision"] == SOURCE and result["payload_files"] == 730
    assert len(result["payload_verified"]) == 730
    assert result["GPU_submissions_by_capture"] == 0
    assert result["server_mutations_by_capture"] is False
    return result, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Fresh .json.gz (compressed) or .json receipt; never overwritten")
    args = parser.parse_args()
    path = ROOT / args.output
    assert str(path).endswith((".json", ".json.gz")), "Use a .json or .json.gz receipt"
    assert not path.exists(), "Preserve earlier observation; select a fresh receipt filename"
    assert path.parent.is_dir(), "Receipt parent directory must already exist"
    compile(CODE, "B-full312-readonly-original-handles", "exec")
    response = subprocess.check_output(HOST + [PYTHON + " -"], input=CODE,
                                       text=True, timeout=120)
    result, raw = decode_capture(response)
    stored = gzip.compress(raw, compresslevel=6, mtime=0) if str(path).endswith(".gz") else raw
    with path.open("xb") as handle:
        handle.write(stored)
    runs = result.get("runner", {}).get("runs", [])
    print(json.dumps(dict(source_revision=result["source_revision"],
        payload_files=result["payload_files"],
        payload_all_verified=all(result["payload_verified"].values()),
        original_processes=result["original_processes"],
        parent_runs_recorded=len(runs),
        parents_finished=sum(row.get("status") in ("COMPLETE", "VIDEO_REJECTED") for row in runs),
        planned_parents=4, planned_suffixes=12, planned_video_slots=16,
        final_outputs_recorded=len(result.get("final", {}).get("outputs", [])),
        scored_videos=result.get("final", {}).get("scored_videos"),
        runner_status=result.get("runner", {}).get("status"),
        final_status=result.get("final", {}).get("status"),
        post_exit=result.get("post_exit", {}).get("exit_code"),
        kernel_lock_free=result.get("kernel_lock_free"),
        GPU=result.get("GPU"), GPU_telemetry_error=result.get("GPU_telemetry_error"),
        receipt=str(path), receipt_sha256=hashlib.sha256(stored).hexdigest(),
        uncompressed_sha256=hashlib.sha256(raw).hexdigest(),
        stored_bytes=len(stored), uncompressed_bytes=len(raw))))


if __name__ == "__main__":
    main()
