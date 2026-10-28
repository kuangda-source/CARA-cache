"""Explicit B terminal, central bill and32-position scoring; no GPU dispatch."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]


def score_command(project,stage,manifest_path,result_directory):
    from four_card_bank24_execution_tools_r1 import process_environment
    from four_card_policy_assets_port_r1 import container_command
    from wcomr.cara_fast_b36_execution_r1 import RUN,require
    from wcomr.cara_fast_capture_r2 import file_sha
    manifest=json.loads(manifest_path.read_text())
    require(manifest['run_id']==RUN and manifest['GPU_released'] is True
            and manifest['CPU_bound']==dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=32)
            and len(manifest['reused_A_metric_pairs'])==6, 'Exact released B scoring manifest required')
    require(stage.parent==project/'.sync' and result_directory==project/'outputs'/RUN/'B-score-CPU'
            and manifest_path.parent==result_directory and Path(manifest['manifest_path'])==manifest_path,
            'Original B scoring paths required')
    environment=process_environment(project,result_directory/'caches')
    environment.update(TORCHINDUCTOR_COMPILE_THREADS='1',TORCH_HOME=manifest['torch_home'])
    command=container_command(project,stage,'cpu-worker',file_sha(manifest_path),environment,os.getuid(),os.getgid())
    command[command.index('--name')+1]=stage.name+'-B-score-cpu'
    command[command.index('--memory')+1]='8g'
    index=command.index(str(stage)+':'+str(stage)+':rw')
    command[index]=str(stage)+':'+str(stage)+':ro'
    additions=['--memory-swap','8g','--cpuset-cpus','26,27']
    for path,mode in [(Path(manifest['A_output_root']),'ro'),(project/'outputs'/RUN,'ro'),(result_directory,'rw')]:
        additions.extend(['-v',str(path)+':'+str(path)+':'+mode])
    index=command.index('--entrypoint')
    command[index:index]=additions
    end=command.index('--entrypoint')+3
    return command[:end]+[str(stage/'scripts/score_cara_fast_b36_fidelity_r1.py'),
        '--manifest',str(manifest_path),'--output',str(result_directory/'scores.json')]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['settle','release','manifest','score-command','accept-scores'])
    for key in ('capture','settlement','manifest','score-capture','project','stage','output'):
        parser.add_argument('--'+key,type=Path)
    args=parser.parse_args()
    from wcomr.cara_fast_binding_r2 import load_card
    from wcomr.cara_fast_capture_r2 import file_sha
    from wcomr.cara_fast_b36_execution_r1 import Pool,RUN,SPEC,require,read
    from wcomr.cara_fast_b36_post_r1 import formal_manifest,accept_scores
    from wcomr.cara_fast_b36_terminal_r1 import settle_original,released_terminal,record
    card=load_card(ROOT,SPEC)
    require(args.output is not None and not args.output.exists(), 'Fresh explicit output; preserve originals')
    if args.command=='score-command':
        result=score_command(args.project,args.stage,args.manifest,args.project/'outputs'/RUN/'B-score-CPU')
    else:
        capture=read(args.capture)
        require(file_sha(ROOT/'src/wcomr/cara_fast_b36_terminal_r1.py')==capture['terminal_validator_sha256'],
                'Use original admitted B terminal validator')
        if args.command=='settle':
            expected=read(ROOT/'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json')['hostname']
            require(socket.gethostname()==expected and args.project==Path('/data20t/gaokuangda/worldcache_workspace'),
                    'Only the registered four-card central ledger can settle B')
            result=settle_original(Pool(args.project),capture,card)
        elif args.command=='release':
            result=released_terminal(capture,card,read(args.settlement))
        else:
            require(file_sha(ROOT/'src/wcomr/cara_fast_b36_post_r1.py')
                    ==record(capture,'registration')['payload_sha256']['src/wcomr/cara_fast_b36_post_r1.py'],
                    'Use original admitted B postprocessor')
            if args.command=='manifest':
                result=formal_manifest(capture,card,read(args.settlement))
            else:
                observed=read(args.score_capture)
                require(observed['status']=='FAST_B36_SCORE_TERMINAL_CAPTURE', 'Original stopped CPU scorer required')
                result=accept_scores(capture,card,read(args.settlement),read(args.manifest),file_sha(args.manifest),
                    record(observed,'scores'),observed['execution'],
                    new_manifest=observed['files']['new_manifest'],new_scores=observed['files']['new_scores'])
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status='EXPLICIT_B36_POST_COMPLETE',command=args.command,output=str(args.output),GPU_submissions=0)))


if __name__=='__main__':
    main()
