#!/usr/bin/env python3
"""One fresh complete direct-resource task after accepted bounded transfer evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
STAGE='.sync/wc-N10-viclip-direct-r4-20261017'
WORKER='scripts/fetch_wc_N10_viclip_direct_r2.py'
ORIGINAL='scripts/fetch_wc_N10_viclip_ranges_r1.py'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validated_direct_probe(probe,expected_weight,expected_etag):
    row=next((r for r in probe.get('requests',[]) if r.get('name')=='failed_offset_direct'),{})
    if (probe.get('canonical_public_url')!=expected_weight['url']
            or probe.get('expected_ETag')!=expected_etag or row.get('route')!='DIRECT'
            or row.get('accepted') is not True or row.get('curl_exit')!=0 or row.get('response_status')!=206
            or row.get('requested_range')!=[117440512,118489087] or row.get('body_bytes')!=1048576
            or row.get('response_headers',{}).get('etag')!=expected_etag
            or row.get('response_headers',{}).get('content-range')!='bytes 117440512-118489087/1710545812'):
        raise ValueError('A complete exact direct transfer at the original failed offset is required')
    stage=Path(probe['local_stage']).resolve();body=stage/'failed_offset_direct.bin'
    if body.stat().st_size!=row['body_bytes'] or sha(body)!=row['body_sha256']:
        raise ValueError('The original accepted probe bytes changed')
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('probe','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or (ROOT/STAGE).exists():raise FileExistsError('Never redispatch an existing resource stage')
    sys.path.insert(0,str(ROOT/'scripts'))
    import fetch_wc_N10_viclip_ranges_r1 as original
    import fetch_wc_N10_viclip_direct_r2 as worker
    oldref=ROOT/'reports/wc_paper_N10_ViCLIP_local_ranges_R3_collection_20261016_1550.json'
    old=json.loads(oldref.read_text())
    if old['original_process_alive'] is not False or old['result']['exit_code']!=1:
        raise ValueError('Keep the original R3 terminal failure before selecting a fresh task')
    oldreg=Path(old['launch']['stage'])/'registration.json'
    if sha(oldreg)!=old['launch']['registration_sha256']:raise ValueError('Original failed registration changed')
    expected=dict(url=original.URL,sha256=original.SHA,bytes=original.SIZE,name=original.NAME)
    if old['launch']['expected_weight']!=expected:raise ValueError('The pinned full checkpoint cannot change')
    etag=json.loads(oldreg.read_text())['expected_range_ETag'];probe=json.loads(args.probe.read_text())
    validated_direct_probe(probe,expected,etag)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names=(WORKER,ORIGINAL,'scripts/launch_wc_N10_viclip_direct_r2.py',
           'scripts/capture_wc_N10_viclip_local_proxy_r2.py')
    for name in names:
        if subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)!=(ROOT/name).read_bytes():
            raise ValueError('Commit every current direct-resource tool before staging: '+name)
    free=os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize
    if free<4*original.SIZE:raise ValueError('Preserve old files and reserve the full target plus range artifacts')
    stage=ROOT/STAGE;stage.mkdir()
    for name in (WORKER,ORIGINAL):(stage/Path(name).name).write_bytes((ROOT/name).read_bytes())
    _,derivation=worker.derive(stage)
    reg=dict(purpose='N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU',source_revision=revision,
        worker_sha256=sha(stage/Path(WORKER).name),original_range_worker_sha256=worker.ORIGINAL_SHA,
        transport_policy=worker.POLICY,transport_derivation=derivation,expected_weight=expected,
        chunk_bytes=original.CHUNK,attempts_per_range=original.ATTEMPTS,expected_range_ETag=etag,
        curl_executable='/usr/bin/curl',prior_R3_terminal_capture_ref=str(oldref),prior_R3_terminal_capture_sha256=sha(oldref),
        range_transport_probe_ref=str(args.probe),range_transport_probe_sha256=sha(args.probe),
        no_old_bytes_reused_without_new_transfer=True,GPU_submissions=0,ledger_written=False,models_imported=False)
    registration=stage/'registration.json';registration.write_text(json.dumps(reg,indent=2)+'\n')
    command=['/usr/bin/nice','-n','10',str(ROOT/'.venv/bin/python'),str(stage/Path(WORKER).name),'--stage',str(stage)]
    started=time.time()
    with (stage/'resource.log').open('xb') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
    identity=subprocess.check_output(['ps','-p',str(child.pid),'-o','pid=,lstart=,command='],text=True,timeout=10).strip()
    if str(stage/Path(WORKER).name) not in identity:raise RuntimeError('Retain stage and investigate original process; never dispatch again')
    value=dict(status='N10_FIXED_PINNED_DIRECT_RANGE_RESOURCE_SINGLE_DISPATCHED',source_revision=revision,
        pid=child.pid,process_at_admission=identity,stage=str(stage),stage_ref=STAGE,
        worker_file=Path(WORKER).name,worker_sha256=reg['worker_sha256'],registration_sha256=sha(registration),
        original_range_worker_sha256=worker.ORIGINAL_SHA,transport_policy=worker.POLICY,expected_weight=expected,
        chunk_bytes=original.CHUNK,attempts_per_range=original.ATTEMPTS,
        expected_range_count=(original.SIZE+original.CHUNK-1)//original.CHUNK,
        started_unix=started,midpoint_health_not_before_unix=started+45*60,
        first_collection_not_before_unix=started+90*60,estimated_wall_minutes=[60,90],local_free_bytes_at_admission=free,
        command=command,previous_originals_retained=True,models_imported=False,weights_loaded=0,
        GPU_submissions=0,SSH_queries=0,ledger_written=False)
    with args.output.open('x') as h:json.dump(value,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(value,allow_nan=False))


if __name__=='__main__':main()
