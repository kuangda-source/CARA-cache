"""Explicit terminal -> central bill -> release -> scores -> freeze commands.

No command launches GPU or phase B. Score command construction also performs
no dispatch; an original released A32 and immutable pair manifest are required.
"""
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
    from wcomr.cara_fast_execution_r2 import RUN,require
    from wcomr.cara_fast_capture_r2 import file_sha
    manifest=json.loads(manifest_path.read_text())
    require(manifest['run_id']==RUN and manifest['GPU_released'] is True
            and manifest['CPU_bound']==dict(cpus=2,memory_GiB=8,wall_hours=2,max_pairs=12),
            'Original released and bounded calibration manifest required')
    require(stage.parent==project/'.sync' and result_directory==project/'outputs'/RUN/'A-score-CPU',
            'Exact original scoring result directory required')
    require(manifest_path.parent==result_directory and Path(manifest['manifest_path'])==manifest_path,
            'Manifest must be at its explicit original scoring path')
    environment=process_environment(project,result_directory/'caches')
    environment.update(TORCHINDUCTOR_COMPILE_THREADS='1',TORCH_HOME=manifest['torch_home'])
    command=container_command(project,stage,'cpu-worker',file_sha(manifest_path),
                              environment,os.getuid(),os.getgid())
    command[command.index('--name')+1]=stage.name+'-A-score-cpu'
    command[command.index('--memory')+1]='8g'
    index=command.index(str(stage)+':'+str(stage)+':rw')
    command[index]=str(stage)+':'+str(stage)+':ro'
    index=command.index('--entrypoint')
    output=project/'outputs'/RUN
    command[index:index]=['-v',str(output)+':'+str(output)+':ro',
                          '-v',str(result_directory)+':'+str(result_directory)+':rw']
    end=command.index('--entrypoint')+3
    return command[:end]+[str(stage/'scripts/score_cara_fast_fidelity_r1.py'),
        '--manifest',str(manifest_path),'--output',str(result_directory/'scores.json')]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['settle','release','manifest','score-command','accept-scores','freeze'])
    for key in ('capture','settlement','release','manifest','score-capture','accepted-scores','project','stage','output'):
        parser.add_argument('--'+key,type=Path)
    args=parser.parse_args()
    from wcomr.cara_fast_binding_r2 import load_card
    from wcomr.cara_fast_capture_r2 import file_sha
    from wcomr.cara_fast_execution_r2 import Pool,RUN,SPEC,require
    from wcomr.cara_fast_collection_r2 import freeze_selection
    from wcomr.cara_fast_post_r2 import calibration_manifest,accept_scores
    from wcomr.cara_fast_terminal_r2 import settle_original,released_terminal
    from wcomr.policy_price_terminal_r1 import record
    card=load_card(ROOT,SPEC)
    def read(path):
        require(path is not None, 'Missing explicit command input')
        return json.loads(path.read_text())
    def accepted_scores():
        observed=read(args.score_capture)
        require(observed['status']=='FAST_A32_SCORE_TERMINAL_CAPTURE', 'Observe the original stopped CPU scorer first')
        return accept_scores(read(args.capture),card,read(args.settlement),read(args.manifest),
            file_sha(args.manifest),record(observed,'scores'),observed['execution'])
    require(args.output is not None and not args.output.exists(), 'Fresh explicit output path required; never overwrite')
    if args.command=='settle':
        expected=json.loads((ROOT/'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json').read_text())['hostname']
        require(socket.gethostname()==expected and args.project==Path('/data20t/gaokuangda/worldcache_workspace'),
                'Settlement must run on the registered four-card central host; never mutate the two-card replica')
        capture=read(args.capture)
        require(file_sha(ROOT/'src/wcomr/cara_fast_terminal_r2.py')==capture['terminal_validator_sha256'],
                'Use the original admitted terminal validator')
        result=settle_original(Pool(args.project),capture,card)
    elif args.command=='release':
        capture=read(args.capture)
        require(file_sha(ROOT/'src/wcomr/cara_fast_terminal_r2.py')==capture['terminal_validator_sha256'],
                'Use the original admitted terminal validator')
        result=released_terminal(capture,card,read(args.settlement))
    elif args.command=='manifest':
        capture=read(args.capture)
        registration=record(capture,'registration')
        require(file_sha(ROOT/'src/wcomr/cara_fast_post_r2.py')==registration['payload_sha256']['src/wcomr/cara_fast_post_r2.py'],
                'Use the original prospective postprocessor')
        result=calibration_manifest(capture,card,read(args.settlement))
    elif args.command=='score-command':
        require(args.project is not None and args.stage is not None, 'Explicit original project/stage required')
        result=score_command(args.project,args.stage,args.manifest,args.project/'outputs'/RUN/'A-score-CPU')
    elif args.command=='accept-scores':
        result=accepted_scores()
    else:
        capture=read(args.capture)
        settlement=read(args.settlement)
        accepted=accepted_scores()
        require(accepted==read(args.accepted_scores), 'Accepted score file changed before freeze')
        release=released_terminal(capture,card,settlement)
        result=freeze_selection(card,record(capture,'collection'),release,accepted,args.output)
        print(json.dumps(dict(status='FROZEN_FIT_SELECTION_NO_B_AUTHORITY',output=str(args.output))))
        return
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status='EXPLICIT_POST_COMMAND_COMPLETE',command=args.command,output=str(args.output),GPU_submissions=0)))


if __name__=='__main__':
    main()
