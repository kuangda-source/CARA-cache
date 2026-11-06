"""Measure full-size RGB artifact CPU/IO cost, with no model or GPU access."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for name in ('stage','runtime','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True);args=parser.parse_args()
    signal.alarm(180);started=time.time();sys.path.insert(0,str(args.stage/'src'))
    import numpy as np
    from wcomr.cara_budget_rgb_objective_r1 import save_endpoint,read_endpoint,full_rgb_mse,file_sha
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.cara_fast_binding_r2 import load_card
    reg=read_record(args.stage/'registration.json')
    assert not args.output.exists() and reg['host']==args.host
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(file_sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    card=load_card(args.stage,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    sample=next(r for r in card['inputs'] if r['name']==card['FIT'][0])
    shape=[3,sample['num_output_frames'],*map(int,sample['resolution'].split(','))]
    directory=args.stage/'CPU-full-RGB';directory.mkdir()
    native=dict(CPU_fixture_only=True,member='SYNTHETIC_FULL_GEOMETRY',RGB_shape=shape,kind='NATIVE')
    candidate=dict(native,kind='CANDIDATE');rgb=np.full(shape,.5,dtype=np.float32)
    t=time.monotonic();a=save_endpoint(directory/'native',native,rgb);native_save=time.monotonic()-t
    rgb[2,92,-1,-1]=.75
    t=time.monotonic();b=save_endpoint(directory/'candidate',candidate,rgb);candidate_save=time.monotonic()-t
    del rgb
    t=time.monotonic();ref,_=read_endpoint(directory/'native',native);value,_=read_endpoint(directory/'candidate',candidate);read_seconds=time.monotonic()-t
    t=time.monotonic();mse=full_rgb_mse(value,ref);mse_seconds=time.monotonic()-t
    assert mse==.25**2/int(np.prod(shape)) and 'torch' not in sys.modules
    proof=dict(status='FULL_RESOLUTION_RGB_CPU_IO_COST_COMPONENT_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),registration_sha256=file_sha(args.stage/'registration.json'),
        source_sha256=reg['payload_sha256'],RGB_shape=shape,retained_NPY_bytes=a['bytes']+b['bytes'],
        synthetic_RGB_MSE=mse,native_save_fsync_and_hash_seconds=native_save,
        candidate_save_fsync_and_hash_seconds=candidate_save,read_hash_validate_two_arrays_seconds=read_seconds,
        full_MSE_validate_and_compute_seconds=mse_seconds,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        original_artifacts={'native':a,'candidate':b},cache_state='NOT_CONTROLLED_NO_CACHE_EVICTION',
        cold_disk_bound_established=False,GPU_to_CPU_copy_measured=False,real_model_output=False,
        whole_GPU_quote_accepted=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
    signal.alarm(30);print(json.dumps({k:proof[k] for k in ['status','retained_NPY_bytes','peak_RSS_bytes']}),flush=True)


if __name__=='__main__':main()
