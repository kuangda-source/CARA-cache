#!/usr/bin/env python3
"""One post-halfway relay health snapshot; never hashes or loads weights."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--launch-ref', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    launch = json.loads(a.launch_ref.read_text())
    if time.time() < launch['started_unix'] + 900:
        raise SystemExit('Before the original relay halfway time; no process or SSH query')
    stage = Path(launch['stage'])
    assert sha(stage / 'registration.json') == launch['registration_sha256']
    worker = stage / 'relay_wc_N10_viclip_resource_r1.py'
    assert sha(worker) == launch['worker_sha256']
    spec = importlib.util.spec_from_file_location('original_relay_health_helpers', worker)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = json.loads((stage / 'registration.json').read_text())
    assert metadata['source_revision'] == launch['source_revision']
    assert metadata['remote_stage'] == launch['remote_stage']
    alive, same, process = module.original_local_process(launch)
    out = dict(status='N10_ORIGINAL_RELAY_ONCE_HALFWAY_TECHNICAL_SNAPSHOT_NOT_RESOURCE_ACCEPTANCE',
        launch=launch, observed_unix=time.time(), original_process_alive=alive,
        same_original_process_identity=same, actual_local_process=process,
        server=None, server_observation_error=None, local_technical_result=None,
        full_weight_hash_performed=False, models_imported=False, weights_loaded=0,
        GPU_submissions=0, ledger_written=False, original_worker_or_resource_written=False)
    result_path = stage / 'relay-result.json'
    if result_path.exists():
        result = json.loads(result_path.read_text())
        assert result['source_revision'] == launch['source_revision']
        out['local_technical_result'] = {k: result.get(k) for k in ('status', 'exit_code', 'error_type', 'error', 'ended_unix')}
    # The transfer worker creates server-prepared only after its sole stage setup.
    # Reading file sizes here does not duplicate that operation or accept weights.
    if (stage / 'server-prepared.json').exists():
        code = 'META=' + repr(metadata) + '\n' + r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(META['remote_stage'])
assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2
assert relative.parts[0]=='.sync' and relative.parts[1].startswith('wc-N10-viclip-relay-')
stage=root/relative;reg=stage/'registration.json'
assert hashlib.sha256(reg.read_bytes()).hexdigest()==META['remote_registration_sha256']
name=META['expected_weight']['name'];sizes={}
for suffix in ('','.part'):
 p=stage/(name+suffix);sizes[name+suffix]=dict(exists=p.is_file(),bytes=p.stat().st_size if p.is_file() else None)
v=dict(observed_unix=time.time(),registration_sha256=META['remote_registration_sha256'],file_sizes=sizes,full_hash_performed=False,server_files_written=False)
result=stage/'resource-result.json'
if result.is_file():
 d=json.loads(result.read_text());v['technical_result']={k:d.get(k) for k in ('status','exit_code','source_revision','ended_unix')}
print(json.dumps(v,allow_nan=False))
'''
        try:
            out['server'] = module.remote(code, timeout=30)
        except Exception as e:
            out['server_observation_error'] = type(e).__name__ + ': ' + str(e)
    with a.output.open('x') as f:
        json.dump(out, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: out[k] for k in ('status', 'original_process_alive', 'same_original_process_identity',
                                         'local_technical_result', 'server_observation_error')}))


if __name__ == '__main__':
    main()
