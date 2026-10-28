"""Fixed synthetic feature CPU costs; no tensors/assets from an experiment."""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    p=argparse.ArgumentParser()
    for key in ('assets','output'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('profile','scope','manifest-sha256'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original synthetic CPU cost receipt')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('CPU cost measurement must hide GPUs')
    started,cpu=time.monotonic(),time.process_time()
    scope=json.loads((ROOT/args.scope).read_text())
    import torch
    def forbidden(*a,**kw):raise RuntimeError('CPU cost measurement forbids CUDA, loads and downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    from wcomr.mid_coverage import tree_digest
    from wcomr.sq_s_collection_r1 import data_record
    value=torch.zeros(scope['synthetic_shape'],dtype=torch.bfloat16)
    nbytes=value.numel()*value.element_size();version=value._version
    if nbytes!=127401984 or value.is_cuda or value.requires_grad:raise ValueError('Fixed synthetic geometry differs')
    operations={}
    def measure(name,call,check):
        times=[];warmups=[];sizes=[]
        for i in range(scope['warmups_per_operation']+scope['formal_repeats_per_operation']):
            before=time.monotonic();result=call();elapsed=time.monotonic()-before
            size=check(result)
            if elapsed<=0 or value._version!=version:raise ValueError('Invalid cost clock or synthetic input changed')
            if i<scope['warmups_per_operation']:warmups.append(elapsed)
            else:times.append(elapsed);sizes.append(size)
            del result
        operations[name]=dict(warmup_seconds=warmups,ordered_repeat_seconds=times,
            input_tensor_bytes_per_call=nbytes,output_bytes=sizes,maximum_observed_seconds=max(times),
            minimum_observed_input_bytes_per_second=nbytes/max(times),repeats_dropped=0)
    def digest_check(result):
        if len(result)!=64 or result!=expected_digest:raise ValueError('Same synthetic bytes must retain their digest')
        return 64
    # This first digest is an explicit setup control, separately accounted.
    before=time.monotonic();expected_digest=tree_digest(value);setup_digest_seconds=time.monotonic()-before
    measure('source_exact_tree_digest_including_finite_scan',lambda:tree_digest(value),digest_check)
    def copied(result):
        if (result.shape!=value.shape or result.dtype!=value.dtype or result.device.type!='cpu'
                or result.untyped_storage()._cdata==value.untyped_storage()._cdata
                or not torch.equal(result,value)):raise ValueError('Synthetic independent copy differs')
        return result.numel()*result.element_size()
    measure('source_exact_data_record_CPU_clone',lambda:data_record(value),copied)
    measure('original_deepcopy_CPU_tensor',lambda:copy.deepcopy(value),copied)
    def serialize():
        output=io.BytesIO();torch.save(dict(synthetic_CPU_feature=value),output);return output
    def encoded(output):
        size=output.getbuffer().nbytes
        if not nbytes<size<nbytes+65536:raise ValueError('Original uncompressed tensor serialization size differs')
        return size
    measure('original_torch_save_CPU_to_BytesIO_no_disk',serialize,encoded)
    if torch.cuda.is_initialized() or len(operations)!=4:raise ValueError('Complete CPU-only denominator required')
    result=dict(status='S_FIXED_SYNTHETIC_HOST_CPU_COSTS_COMPLETE_NOT_GPU_OR_SSD_PRICE',scope=scope,
        profile=args.profile,operations=operations,explicit_setup_digest_seconds=setup_digest_seconds,
        synthetic_input=dict(shape=list(value.shape),dtype=str(value.dtype),bytes=nbytes,
            deterministic_zero_fixture=True,checkpoint_or_real_state=False),
        formal_operation_calls=12,warmup_operation_calls=4,separate_setup_digest_calls=1,
        copy_value_checks_outside_operation_clock=8,source_input_version_unchanged=True,
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        actual_CUDA=False,real_state_or_weights_loaded=False,real_generated_video=False,
        actual_GPU_transfer_price_measured=False,actual_GPU_forward_price_measured=False,
        actual_SSD_IO_price_measured=False,whole_S_quote_frozen=False,S_real_labels=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
