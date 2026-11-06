"""Accept only the completed no-hardware Linux allocation component controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_allocation_cpu_r1 import FILES,SCOPE,SCOPE_R2

ROOT=Path(__file__).resolve().parents[1]


def accept(capture,scope,revision,host,attempt='r2'):
    state,launch,result=capture['container_state'],capture['launch'],capture['result']
    stage='cara-sq-allocation-cpu-'+host.replace('_','-')+'-'+attempt+'-20261029'
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Error']
        and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead')),
        'Original allocation CPU container is not cleanly terminal')
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and launch['stage'].endswith('/'+stage)
        and launch['container']==stage+'-cpu' and launch['source_revision']==revision
        and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],'Original CPU source/handle differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
            Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Registered allocation CPU runtime/resource boundary differs')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256']
        and result['status']=='SQ_FULL_ALLOCATION_CPU_PASS_STUB_HARDWARE_NOT_GPU_READY'
        and result['scope']==scope and result['profile']==host,'Original bound full CPU result differs')
    require(result['unit_controls']['tests']==12 and result['unit_controls']['skipped']==0
        and result['actual_platform']['system']=='Linux' and result['actual_Linux_CPU_children_started']==scope['actual_CPU_children']
        and result['all_CPU_children_exited'] is True
        and len(result['CPU_child_exit_codes'])==scope['actual_CPU_children'] and all(v is not None for v in result['CPU_child_exit_codes']),
        'Twelve complete Linux controls and all admitted original CPU children required')
    require(result['hardware_modes_and_container_observations']=='EXPLICIT_SYNTHETIC_CPU_STUBS'
        and result['all_bill_times_in_tests_are_synthetic'] is True
        and result['original_Q1_f3_launch_readiness_withdrawn'] is True
        and all(result[k] is False for k in ('Torch_imported','real_hardware_calls',
            'Q1_correction_integrated','S_GPU_entry_integrated'))
        and all(result[k]==0 for k in ('GPU_submissions','new_GPUh','ledger_writes')),
        'CPU component was misrepresented as real hardware or a complete Q1/S correction')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<result['CPU_wall_seconds']<=wall<=1810 and 0<result['peak_RSS_KiB']*1024<8*2**30,
        'Allocation CPU worker/container resource interval differs')
    return dict(passed=True,status='FULL_HOST_ALLOCATION_COMPONENT_CPU_ACCEPTED_NOT_INTEGRATED_GPU_CARD',
        host=host,source_revision=revision,unit_controls=12,actual_CPU_children=scope['actual_CPU_children'],
        all_CPU_children_exited=True,real_hardware_calls=False,Q1_correction_integrated=False,S_GPU_entry_integrated=False,
        GPU_submissions=0,ledger_writes=0,resources=dict(container_wall_seconds=wall,
            worker_wall_seconds=result['CPU_wall_seconds'],parent_CPU_seconds=result['CPU_seconds'],
            reaped_child_CPU_seconds=result['reaped_child_CPU_seconds'],parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,
            allocated_vCPU_seconds_upper_bound=2*wall,transport_staging_git_CPU_unmetered=True))


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r1','r2'),default='r2')
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original allocation component acceptance')
    scope_name=SCOPE_R2 if args.attempt=='r2' else SCOPE
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/scope_name).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    result=accept(capture,scope,revision,args.host,args.attempt)
    cases=dict(running_body=lambda c:c['container_state'].update(Running=True),
        stale_source=lambda c:c.update(source_hashes_equal=False),
        GPU_exposure=lambda c:c['host_config'].update(DeviceRequests=[{}]),
        skipped_control=lambda c:c['result']['unit_controls'].update(skipped=1),
        live_child=lambda c:c['result'].update(all_CPU_children_exited=False),
        hardware_call=lambda c:c['result'].update(real_hardware_calls=True),
        premature_Q1_ready=lambda c:c['result'].update(Q1_correction_integrated=True),
        simulated_bill_is_not_real=lambda c:c['result'].update(all_bill_times_in_tests_are_synthetic=False))
    rejected={}
    for name,mutate in cases.items():
        altered=copy.deepcopy(capture);mutate(altered);altered['result_sha256']=result_sha(altered['result'])
        try:accept(altered,scope,revision,args.host,args.attempt)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged allocation component receipt accepted: '+name)
    result.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        rejection_controls=rejected,critical_source_sha256={name:hashlib.sha256(subprocess.check_output(
            ['git','show',revision+':'+name],cwd=ROOT)).hexdigest() for name in FILES+((SCOPE_R2,) if args.attempt=='r2' else ())})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','host','unit_controls','actual_CPU_children','resources')}))


if __name__=='__main__':main()
