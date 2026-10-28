"""Accept complete original CPU synthetic timings without upgrading GPU prices."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_s_host_cost_cpu_r1 import FILES,SCOPE

ROOT=Path(__file__).resolve().parents[1]


def accept(capture,scope,revision,host):
    s,L,r=capture['container_state'],capture['launch'],capture['result']
    name='cara-sq-s-host-cost-cpu-'+host.replace('_','-')+'-r1-20261029'
    require(s['Status']=='exited' and s['ExitCode']==0 and not s['Error']
        and not any(s[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
        and capture['original_CLI_live'] is False,'Original CPU cost handles must be terminal')
    require(L['source_revision']==revision and L['stage'].endswith('/'+name) and L['container']==name+'-cpu'
        and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],'Original CPU cost source differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,Memory=8*2**30,
            MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),'Original CPU sandbox differs')
    cpu_mounts(capture,host)
    require(r is not None and result_sha(r)==capture['result_sha256'] and r['profile']==host and r['scope']==scope
        and r['status']=='S_FIXED_SYNTHETIC_HOST_CPU_COSTS_COMPLETE_NOT_GPU_OR_SSD_PRICE','Original synthetic result differs')
    require(r['synthetic_input']==dict(shape=[1,24,27,48,2048],dtype='torch.bfloat16',bytes=127401984,
        deterministic_zero_fixture=True,checkpoint_or_real_state=False),'Fixed synthetic denominator differs')
    require(r['formal_operation_calls']==12 and r['warmup_operation_calls']==4
        and r['separate_setup_digest_calls']==1 and r['copy_value_checks_outside_operation_clock']==8
        and r['source_input_version_unchanged'] is True and list(r['operations'])==scope['operations'],
        'All fixed warmups/formal calls/value checks required')
    elapsed=r['explicit_setup_digest_seconds'];rates={}
    require(math.isfinite(elapsed) and elapsed>0,'Explicit setup digest cost required')
    for name,row in r['operations'].items():
        times=row['ordered_repeat_seconds'];warmup=row['warmup_seconds'];sizes=row['output_bytes']
        require(len(times)==3 and len(warmup)==1 and len(sizes)==3
            and all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in times+warmup)
            and row['repeats_dropped']==0 and row['input_tensor_bytes_per_call']==127401984
            and row['maximum_observed_seconds']==max(times)
            and row['minimum_observed_input_bytes_per_second']==127401984/max(times),
            'Every actual ordered CPU timing and conservative observed rate required')
        expected=64 if 'tree_digest' in name else 127401984
        require(all((expected<size<expected+65536) if 'BytesIO' in name else size==expected for size in sizes),
            'Actual CPU output byte denominator differs')
        elapsed+=sum(times)+sum(warmup);rates[name]=row['minimum_observed_input_bytes_per_second']
    require(all(r[k] is False for k in ('actual_CUDA','real_state_or_weights_loaded','real_generated_video',
        'actual_GPU_transfer_price_measured','actual_GPU_forward_price_measured','actual_SSD_IO_price_measured','whole_S_quote_frozen'))
        and all(r[k]==0 for k in ('S_real_labels','GPU_submissions','new_GPUh','ledger_writes')),
        'Synthetic CPU rates cannot be GPU/SSD/scientific acceptance')
    require(r['actual_platform']['system']=='Linux' and r['torch_version']=='2.7.1+cu128','Pinned Linux Torch required')
    wall=(instant(s['FinishedAt'])-instant(s['StartedAt'])).total_seconds()
    require(0<elapsed<r['CPU_wall_seconds']<=wall<=1810 and 0<r['peak_RSS_KiB']<8*2**20,
        'Actual original CPU wall/resource accounting differs')
    return dict(status='S_FIXED_SYNTHETIC_CPU_COSTS_ACCEPTED_NOT_GPU_OR_SSD_PRICE',passed=True,host=host,
        source_revision=revision,formal_operation_calls=12,warmup_operation_calls=4,explicit_setup_digest_calls=1,
        conservative_observed_CPU_rates_bytes_per_second=rates,
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=r['CPU_wall_seconds'],worker_CPU_seconds=r['CPU_seconds'],
            parent_peak_RSS_GiB=r['peak_RSS_KiB']/2**20,allocated_vCPU_seconds_upper_bound=2*wall,
            interpreter_wrapper_and_staging_CPU_unmetered=True),
        actual_GPU_transfer_or_forward_or_SSD_price_measured=False,whole_S_quote_frozen=False,
        real_S_labels=0,GPU_submissions=0,ledger_writes=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Retain original synthetic cost acceptance')
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    scope=json.loads(subprocess.check_output(['git','show',revision+':'+SCOPE],cwd=ROOT));c=json.loads(args.capture.read_text())
    result=accept(c,scope,revision,args.host)
    cases=dict(live_container=lambda c:c['container_state'].update(Running=True),live_CLI=lambda c:c.update(original_CLI_live=True),
        GPU_exposure=lambda c:c['host_config'].update(DeviceRequests=[{}]),stale_source=lambda c:c.update(source_hashes_equal=False),
        missing_operation=lambda c:c['result']['operations'].pop(scope['operations'][0]),
        missing_repeat=lambda c:c['result']['operations'][scope['operations'][0]]['ordered_repeat_seconds'].pop(),
        dropped_repeat=lambda c:c['result']['operations'][scope['operations'][0]].update(repeats_dropped=1),
        GPU_price_claim=lambda c:c['result'].update(actual_GPU_transfer_price_measured=True))
    refused={}
    for name,mutate in cases.items():
        forged=copy.deepcopy(c);mutate(forged);forged['result_sha256']=result_sha(forged['result'])
        try:accept(forged,scope,revision,args.host)
        except ValueError:refused[name]=True
        else:raise ValueError('Forged CPU cost receipt accepted: '+name)
    result.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        rejection_controls=refused,auditor_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        critical_source_sha256={n:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in FILES})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','host','conservative_observed_CPU_rates_bytes_per_second','resources')}))


if __name__=='__main__':main()
