#!/usr/bin/env python3
"""New local range-acquisition task after both original downloads terminated."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STAGE = '.sync/wc-N10-viclip-local-ranges-r3-20261016'
WORKER = 'scripts/fetch_wc_N10_viclip_ranges_r1.py'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not (ROOT/STAGE).exists()
    sys.path.insert(0, str(ROOT/'scripts'))
    import fetch_wc_N10_viclip_ranges_r1 as worker
    # Both previous original processes were actually collected terminal.
    refs = ['reports/wc_paper_N10_ViCLIP_resource_R1_collection_20261016_1317.json',
            'reports/wc_paper_N10_ViCLIP_local_proxy_R2_collection_20261016_1400.json']
    old = [json.loads((ROOT/p).read_text()) for p in refs]
    assert all(v['original_process_alive'] is False and v['result']['exit_code'] == 1 for v in old)
    previous = Path(old[1]['launch']['stage'])/(worker.NAME+'.part')
    assert previous.stat().st_size == old[1]['partial_bytes'] == old[1]['result']['actual_bytes_received']
    assert sha(previous) == old[1]['result']['partial_sha256']
    probe_refs = ['reports/wc_paper_N10_same_pin_HTTP_range_probe_20261016.json',
                  'reports/wc_paper_N10_curl_nonzero_range_transport_probe_20261016.json']
    first, second = [json.loads((ROOT/p).read_text()) for p in probe_refs]
    assert first['exact_206_range_accepted'] and first['probe_equals_original_R2_prefix']
    assert second['exact_206_range_accepted'] and second['equals_original_R2_range']
    expected_etag = first['ETag']
    assert 'etag: '+expected_etag in second['selected_response_headers']
    curl = Path(shutil.which('curl')).resolve()
    disk = os.statvfs(ROOT); free = disk.f_bavail*disk.f_frsize
    assert free > 4*worker.SIZE
    source = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name in (WORKER,'scripts/launch_wc_N10_viclip_ranges_r1.py','scripts/capture_wc_N10_viclip_local_proxy_r2.py'):
        assert subprocess.check_output(['git','show',source+':'+name],cwd=ROOT) == (ROOT/name).read_bytes()
    stage = ROOT/STAGE; stage.mkdir()
    target = stage/Path(WORKER).name; target.write_bytes((ROOT/WORKER).read_bytes())
    registration = dict(purpose='N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU',source_revision=source,
        worker_sha256=sha(target), expected_weight=dict(url=worker.URL,sha256=worker.SHA,bytes=worker.SIZE,name=worker.NAME),
        chunk_bytes=worker.CHUNK,attempts_per_range=worker.ATTEMPTS,expected_range_ETag=expected_etag,
        curl_executable=str(curl),curl_version=subprocess.check_output([str(curl),'--version'],text=True).splitlines()[0],
        prior_original_failure_capture_sha256={p:sha(ROOT/p) for p in refs},
        prior_R2_partial_preserved_sha256=sha(previous),
        range_transport_probe_sha256={p:sha(ROOT/p) for p in probe_refs},
        no_old_bytes_reused_without_new_transfer=True,GPU_submissions=0,ledger_written=False,models_imported=False)
    reg = stage/'registration.json'; reg.write_text(json.dumps(registration,indent=2)+'\n')
    command = ['/usr/bin/nice','-n','10',str(ROOT/'.venv/bin/python'),str(target),'--stage',str(stage)]
    started = time.time()
    with (stage/'resource.log').open('xb') as log:
        child = subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
    identity = subprocess.check_output(['ps','-p',str(child.pid),'-o','pid=,lstart=,command='],text=True,timeout=10).strip()
    assert str(target) in identity
    value = dict(status='N10_FIXED_PINNED_LOCAL_RANGE_RESOURCE_SINGLE_DISPATCHED',source_revision=source,
        pid=child.pid,process_at_admission=identity,stage=str(stage),stage_ref=STAGE,
        worker_file=target.name,worker_sha256=sha(target),registration_sha256=sha(reg),
        expected_weight=registration['expected_weight'],chunk_bytes=worker.CHUNK,
        attempts_per_range=worker.ATTEMPTS,expected_range_count=(worker.SIZE+worker.CHUNK-1)//worker.CHUNK,
        started_unix=started,first_collection_not_before_unix=started+90*60,estimated_wall_minutes=[60,90],
        local_free_bytes_at_admission=free,command=command,
        previous_originals_retained=True,models_imported=False,weights_loaded=0,
        GPU_submissions=0,SSH_queries=0,ledger_written=False)
    with args.output.open('x') as handle: json.dump(value,handle,indent=2)
    print(json.dumps(value,allow_nan=False))


if __name__ == '__main__': main()
