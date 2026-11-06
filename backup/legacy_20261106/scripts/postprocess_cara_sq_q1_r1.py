"""CPU-only Q1 selection after original context/mode release and settlement."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]


def container_arguments(project,stage,directory):
    from four_card_bank24_execution_tools_r1 import process_environment
    from four_card_policy_assets_port_r1 import container_command
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_q1_execution_r1 import read,require
    from wcomr.sq_q1_spec_r1 import PROFILE,RUN
    require(directory==project/'outputs'/RUN/'CPU-post','Original released Q1 CPU output required')
    host=read(stage/'registration.json')['host'];cpus=read(stage/PROFILE)['hosts'][host]['cpuset_cpus']
    command=container_command(project,stage,'cpu-worker',sha(stage/'registration.json'),
        process_environment(project,directory/'caches'),os.getuid(),os.getgid())
    command[command.index('--name')+1]=stage.name+'-post-cpu'
    command[command.index('--memory')+1]='8g'
    command[command.index(str(stage)+':'+str(stage)+':rw')]=str(stage)+':'+str(stage)+':ro'
    position=command.index('--entrypoint')
    command[position:position]=['--memory-swap','8g','--cpuset-cpus',cpus,
        '-v',str(directory)+':'+str(directory)+':rw','--ulimit','fsize=67108864:67108864']
    position=command.index('--entrypoint')+1;python=command[position]
    command[position]='/usr/bin/timeout'
    image_end=position+2
    return command[:image_end]+['--signal=TERM','--kill-after=10s','300',
        '/usr/bin/ionice','-c','3',python,str(stage/'scripts/postprocess_cara_sq_q1_r1.py'),
        '--capture',str(directory/'capture.json'),'--settlement',str(directory/'settlement.json'),
        '--output',str(directory/'analysis.json')]


def main():
    p=argparse.ArgumentParser()
    for name in ('capture','settlement','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original Q1 CPU analysis')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('Released Q1 analysis must hide all GPU devices')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    def forbidden(*args,**kwargs):raise RuntimeError('Q1 CPU analysis cannot initialize CUDA or download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_q1_spec_r1 import SCOPE
    from wcomr.sq_q1_execution_r1 import read,require
    from wcomr.sq_q1_terminal_r1 import analyse_released
    capture,settlement=read(args.capture),read(args.settlement)
    require(sha(ROOT/'src/wcomr/sq_q1_terminal_r1.py')==capture['terminal_validator_sha256'],
            'Use the original admitted Q1 terminal validator')
    result=analyse_released(capture,read(ROOT/SCOPE),settlement)
    require(not torch.cuda.is_initialized(),'Q1 CPU analysis initialized CUDA')
    result.update(capture_sha256=sha(args.capture),settlement_sha256=sha(args.settlement),
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        CUDA_initialized=False,GPU_submissions=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'])


if __name__=='__main__':main()
