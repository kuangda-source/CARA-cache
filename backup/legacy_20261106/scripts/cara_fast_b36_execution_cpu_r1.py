"""Reuse the accepted CPU transport, changing only new B payload/worker and core27."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from cara_two_card_transport_r1 import ssh, four_ssh
from wc_dual_host_time_card_cpu_r1 import REMOTE

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','capture'])
    parser.add_argument('--host',choices=['four_card','two_card'],required=True)
    parser.add_argument('--revision',type=int,default=17)
    parser.add_argument('--post',action='store_true')
    parser.add_argument('--startup',action='store_true')
    parser.add_argument('--dispatch',action='store_true')
    parser.add_argument('--assets',action='store_true')
    parser.add_argument('--analysis',action='store_true')
    parser.add_argument('--figures',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    label={'four_card':'ada','two_card':'a6000'}[args.host]
    assert sum(map(bool,(args.post,args.startup,args.dispatch,args.assets,args.analysis,args.figures)))<=1
    phase=('figures' if args.figures else 'analysis' if args.analysis else 'assets' if args.assets else 'dispatch' if args.dispatch
           else 'startup' if args.startup else 'post' if args.post else 'outer')
    payload=dict(action=args.action,host=args.host,stage_name='cara-fast-B36-'+phase+'-CPU-'+label+'-r'+str(args.revision)+'-20261029')
    worker=('check_cara_fast_b36_figures_cpu_r1.py' if args.figures else
            'check_cara_fast_b36_analysis_cpu_r1.py' if args.analysis else
            'check_cara_fast_b36_assets_cpu_r2.py' if args.assets else
            'check_cara_fast_b36_dispatch_cpu_r2.py' if args.dispatch else
            'check_cara_fast_b36_startup_cpu_r2.py' if args.startup else
            'check_cara_fast_b36_post_cpu_r1.py' if args.post else 'check_cara_fast_b36_execution_cpu_r1.py')
    remote=REMOTE.replace('check_wc_time_card_cpu_r1.py',worker)
    before=" end=cmd.index('--entrypoint')+3"
    assert remote.count(before)==1
    remote=remote.replace(before,""" for option,value in [('--cpuset-cpus','27'),('--memory-swap','4g')]:
  if option in cmd:cmd[cmd.index(option)+1]=value
  else:cmd[cmd.index('--entrypoint'):cmd.index('--entrypoint')]=[option,value]
 end=cmd.index('--entrypoint')+3""")
    if args.assets:
        assert args.host=='two_card'
        remote=remote.replace("('--cpuset-cpus','27')","('--cpuset-cpus','26')")
    before="('NanoCpus','Memory','DeviceRequests','NetworkMode','ReadonlyRootfs')"
    assert remote.count(before)==1
    remote=remote.replace(before,"('NanoCpus','Memory','MemorySwap','CpusetCpus','DeviceRequests','NetworkMode','ReadonlyRootfs')")
    if args.figures:
        before="CPU_proof_sha256=sha(proof) if proof.exists() else None,"
        assert remote.count(before)==1
        remote=remote.replace(before,before+"figure_layout=dict(proof_sha256=sha(stage/'figure-layout-preview/CPU-layout-proof.json'),files={q.name:sha(q) for q in (stage/'figure-layout-preview').iterdir() if q.is_file() and q.name!='CPU-layout-proof.json'}) if (stage/'figure-layout-preview/CPU-layout-proof.json').exists() else None,")
    if args.action=='prepare':
        prior={'four_card':'cara_DEV128_full_four_card_CPU_complete2_r3_20261026.json',
               'two_card':'cara_DEV128_full_two_card_CPU_complete_r3_20261026.json'}[args.host]
        launch=json.loads((ROOT/'reports'/prior).read_text())['launch']
        names=set(subprocess.check_output(['git','ls-files','src'],cwd=ROOT,text=True).splitlines())
        names={name for name in names if name.endswith('.py')}
        names.update(['src/wcomr/cara_fast_b36_execution_r1.py','tests/test_cara_fast_b36_execution_r1.py',
            'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
            'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
            'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
            'plans/cara_next_stage_20261028/mainline/r2/B36_EXECUTION_PROFILE_R1.json',
            'reports/cara_fast_A6000_central_settlement_20261029_0052.json'])
        profile=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/B36_EXECUTION_PROFILE_R1.json').read_text())
        names.update(row['path'] for row in profile['A32_handoff_files'].values())
        pending=['check_cara_fast_b36_execution_cpu_r1','cara_fast_b36_worker_r1',
                 'cara_fast_b36_host_guardian_r1','run_cara_fast_b36_r1']
        if args.post or args.startup or args.dispatch or args.analysis or args.figures:
            names.update(['src/wcomr/cara_fast_b36_terminal_r1.py','src/wcomr/cara_fast_b36_capture_r1.py',
                'src/wcomr/cara_fast_b36_post_r1.py','tests/test_cara_fast_b36_post_r1.py',
                'reports/cara_fast_score_cli_two_card_raw_receipts_r2_20261028.json',
                'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json'])
            pending.extend(['check_cara_fast_b36_post_cpu_r1','postprocess_cara_fast_b36_r1',
                'capture_cara_fast_b36_terminal_r1','score_cara_fast_b36_fidelity_r1','score_cara_fast_fidelity_r1'])
        if args.analysis or args.figures:
            names.update(['src/wcomr/cara_fast_b36_analysis_r1.py','tests/test_cara_fast_b36_analysis_r1.py'])
            pending.extend(['check_cara_fast_b36_analysis_cpu_r1','analyze_cara_fast_b36_complete_r1',
                            'dispatch_cara_fast_b36_score_cpu_r2'])
        if args.figures:
            names.update(['src/wcomr/cara_fast_b36_figures_r1.py','tests/test_cara_fast_b36_figures_r1.py',
                'reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json',
                'plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST.json'])
            pending.extend(['check_cara_fast_b36_figures_cpu_r1','render_cara_fast_b36_figures_r1','analyze_cara_fast_r1'])
        if args.startup or args.dispatch:
            names.add('tests/test_cara_fast_b36_startup_r2.py')
            pending.append('check_cara_fast_b36_startup_cpu_r2')
        if args.dispatch:
            core=json.loads((ROOT/'reports/cara_fast_B36_CPU_acceptance_r1_20261029.json').read_text())
            names.update(core['critical_source_sha256'])
            names.add('reports/cara_fast_B36_CPU_acceptance_r1_20261029.json')
            names.update(['tests/test_cara_fast_b36_dispatch_r2.py','src/wcomr/cara_fast_b36_dispatch_r2.py',
                'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'])
            pending.extend(['check_cara_fast_b36_dispatch_cpu_r2','cara_fast_b36_dispatch_r2','dispatch_cara_fast_b36_score_cpu_r2'])
        if args.assets:
            names.update(['src/wcomr/cara_fast_b36_dispatch_r2.py',
                'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'])
            pending.append('check_cara_fast_b36_assets_cpu_r2')
        seen=set()
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name)
            path=ROOT/'scripts'/(name+'.py')
            names.add(str(path.relative_to(ROOT)))
            for node in ast.walk(ast.parse(path.read_bytes())):
                modules=([node.module] if isinstance(node,ast.ImportFrom) and node.module else
                         [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
                pending.extend(module for module in modules if (ROOT/'scripts'/(module+'.py')).exists())
        payload['additional_runtime_sha256']=profile['precision']['runtime_source_sha256']
        before="assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())"
        assert remote.count(before)==1
        remote=remote.replace(before,before+"\n assert all(sha(root/'runtime'/n)==h for n,h in p['additional_runtime_sha256'].items())")
        before="runtime_source_sha256=reg['runtime_source_sha256'],parent_git_revision="
        assert remote.count(before)==1
        remote=remote.replace(before,"runtime_source_sha256={**reg['runtime_source_sha256'],**p['additional_runtime_sha256']},parent_git_revision=")
        files={name:(ROOT/name).read_bytes() for name in sorted(names)}
        payload.update(base_stage=launch['stage'],base_registration_sha256=launch['registration_sha256'],
            parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    result=ssh(remote,payload,docker_group=True,timeout=90) if args.host=='two_card' else four_ssh(remote,payload,timeout=90)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({key:result.get(key) for key in ('status','host','stage','container_state','log_tail')}))


if __name__=='__main__':
    main()
