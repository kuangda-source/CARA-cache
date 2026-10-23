#!/usr/bin/env python3
"""Independent complete new collector/entry CPU acceptance; GPU stays gated."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_interval_assets_r1 import read,sha
from wcomr.policy_price_refresh_contract_r1 import COUNTS,matrix,VERSION


def accept(v):
    L=v['launch'];reg=v['registration'];container=v['container'];f=v['files']
    if container['state']['Running'] or container['state']['ExitCode']!=0 or container['state']['OOMKilled']:
        raise ValueError('Complete original CPU container exit0 required')
    if (container['image']!='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
            or not container['readonly_root'] or container['pid_mode']!='host'
            or container['device_requests'] or container['devices']):
        raise ValueError('GPU-hidden pinned original CPU container required')
    if reg['namespace']!=VERSION or reg['source_revision']!=L['source_revision']:
        raise ValueError('Exact new registered CPU source required')
    if v['payload_actual_sha256']!=reg['payload_sha256'] or v['runtime_actual_sha256']!=reg['runtime_source_sha256']:
        raise ValueError('Registered source/runtime changed')
    if not all(f[k]['exists'] for k in ('production','numerical','bundle','config')):
        raise ValueError('Original whole CPU command outputs required')
    p,n,b,c=[f[k]['data'] for k in ('production','numerical','bundle','config')]
    if (b['exit_code']!=0 or len(b['commands'])!=3 or any(x['exit_code']!=0 for x in b['commands'])
            or b['production_sha256']!=f['production']['sha256'] or b['numerical_sha256']!=f['numerical']['sha256']
            or b['registration_sha256']!=L['registration_sha256']):
        raise ValueError('Original complete three-command bundle required')
    if (p['source_revision']!=L['source_revision'] or p['registration_sha256']!=L['registration_sha256']
            or p['config_sha256']!=f['config']['sha256'] or p['scope_counts']!=COUNTS or p['matrix']!=matrix()
            or p['actual_Cosmos_request_count']!=4 or p['guard_refusal_controls']!=8
            or p['model_weights_loaded'] or p['CUDA_initialized'] or p['GPU_submissions']):
        raise ValueError('Real price production boundary differs')
    transport=p['host_transport_CPU'];codec=p['actual_guardrail_and_codec']
    if not all(transport[k] for k in ('parent_and_namespace_match','original_fd_inode_match','independent_open_refused',
                                      'GPU_hidden','child_exited','fixture_lock_released')):
        raise ValueError('Actual inherited-FD/CPU visibility boundary failed')
    if not all(codec[k] for k in ('actual_NLTK_tokenization','ordinary_video_writer','ffprobe_exit0')) or codec['RGB_frames']!=93:
        raise ValueError('Actual tokenizer/video pipeline failed')
    if (n['actual_CPU_paths']!=48 or n['new_price_paths']!=20 or n['new_price_cells']!=4060
            or n['new_price_readout_trials']!=48720 or n['original_cells_reloaded']!=4060
            or n['original_readout_trials']!=26040 or n['CUDA_initialized'] or n['GPU_submissions']):
        raise ValueError('Complete two-flow source/price denominator required')
    checks=n['checks']
    if len(checks)!=2 or {x['flow'] for x in checks}!={False,True}:raise ValueError('Both flow states required')
    for x in checks:
        if not all(x[k] for k in ('all36_original_Native_and_new_price_equal','full_final_and_CPU_RGB_equal',
                'old_source_mismatch_rejected_before_readout','no_new_interval_tensors','labels_unchanged_after_merge',
                'owners_released','ordinary_initial_state_restored')):
            raise ValueError('Real collector numerical or cleanup gate failed')
    return dict(status='PRICE_COLLECTOR_AND_REAL_ENTRY_CPU_ACCEPTED_LIFECYCLE_PENDING',
        source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],
        real_entry_CPU_accepted=True,full_price_collector_numerical_CPU_accepted=True,
        actual_CPU_paths=48,new_price_paths=20,new_price_cells=4060,new_price_readout_trials=48720,
        actual_tokenization_codec_and_FD_transport_accepted=True,
        full_GPU_lifecycle_CPU_accepted=False,production_CPU_accepted=False,GPU_dispatch_ready=False,
        remaining='Exact supervisor/host-guardian failure, settlement and restoration integration fixture; independent GPU terminal acceptor.',
        GPU_submissions=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();v=accept(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
    print(json.dumps(v))

if __name__=='__main__':main()
