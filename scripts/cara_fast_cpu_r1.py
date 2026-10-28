"""Reuse the accepted CPU container lifecycle; only payload and worker differ."""
import argparse
import ast
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cara_two_card_transport_r1 import ssh,four_ssh
from wc_dual_host_time_card_cpu_r1 import REMOTE as EXISTING_CPU_TRANSPORT

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','capture'])
    p.add_argument('--host',choices=['four_card','two_card'],required=True);p.add_argument('--revision',type=int,default=1)
    p.add_argument('--shutdown-repair',action='store_true')
    p.add_argument('--exit-diagnostic',choices=['default','single'])
    p.add_argument('--binding-r2',action='store_true')
    p.add_argument('--score-cli-control',action='store_true')
    p.add_argument('--orchestration-r2',action='store_true')
    p.add_argument('--post-r2',action='store_true')
    p.add_argument('--b36-r1',action='store_true')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    label='ada' if a.host=='four_card' else 'a6000'
    stage_name='cara-fast-CPU-'+label+'-r'+str(a.revision)+'-20261028'
    payload=dict(action=a.action,host=a.host,stage_name=stage_name)
    # Exact accepted launch/capture code, unchanged CPU/network/memory safeguards.
    assert sum(bool(v) for v in (a.shutdown_repair,a.exit_diagnostic,a.binding_r2,a.score_cli_control,a.orchestration_r2,a.post_r2,a.b36_r1))<=1
    worker=('check_cara_fast_b36_cpu_r1.py' if a.b36_r1 else
            'check_cara_fast_post_cpu_r2.py' if a.post_r2 else
            'check_cara_fast_orchestration_cpu_r2.py' if a.orchestration_r2 else
            'check_cara_fast_scoring_cli_cpu_r2.py' if a.score_cli_control else
            'check_cara_fast_binding_cpu_r2.py' if a.binding_r2 else
            'diagnose_cara_fast_exit_r1.py' if a.exit_diagnostic else
            'check_cara_fast_shutdown_cpu_r1.py' if a.shutdown_repair else 'check_cara_fast_cpu_r1.py')
    remote=EXISTING_CPU_TRANSPORT.replace('check_wc_time_card_cpu_r1.py',worker)
    assert remote.count(worker)==1
    if a.b36_r1:
        before=" end=cmd.index('--entrypoint')+3"
        assert remote.count(before)==1
        remote=remote.replace(before,""" for option,value in [('--cpuset-cpus','26'),('--memory-swap','4g')]:
  if option in cmd:cmd[cmd.index(option)+1]=value
  else:cmd[cmd.index('--entrypoint'):cmd.index('--entrypoint')]=[option,value]
 end=cmd.index('--entrypoint')+3""")
        before="('NanoCpus','Memory','DeviceRequests','NetworkMode','ReadonlyRootfs')"
        assert remote.count(before)==1
        remote=remote.replace(before,"('NanoCpus','Memory','MemorySwap','CpusetCpus','DeviceRequests','NetworkMode','ReadonlyRootfs')")
    if a.action=='prepare':
        prior={'four_card':'cara_DEV128_full_four_card_CPU_complete2_r3_20261026.json',
               'two_card':'cara_DEV128_full_two_card_CPU_complete_r3_20261026.json'}[a.host]
        launch=json.loads((ROOT/'reports'/prior).read_text())['launch']
        paths=subprocess.check_output(['git','ls-files','src','tests'],cwd=ROOT,text=True).splitlines()
        paths=[s for s in paths if s.endswith('.py')]
        paths += ['src/wcomr/cara_fast_spec_r1.py','src/wcomr/cara_fast_requests_r1.py',
                  'src/wcomr/cara_fast_fidelity_r1.py','tests/test_cara_fast_spec_r1.py',
                  'tests/check_cara_fast_production_cpu_r1.py','scripts/check_cara_fast_cpu_r1.py',
                  'manifests/cara_DEV128_scope_r1_20261026.json','configs/cara_DEV128_requests_r1_20261026.json',
                  'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml',
                  'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json',
                  'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
                  'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json']
        files={n:(ROOT/n).read_bytes() for n in sorted(set(paths))}
        if a.shutdown_repair:
            for n in ['scripts/check_cara_fast_shutdown_cpu_r1.py','reports/cara_fast_four_card_CPU_terminal_r1_20261028.json']:
                files[n]=(ROOT/n).read_bytes()
        if a.exit_diagnostic:
            # Import/exit owns no numerical implementation; copy only its worker
            # and mode, while inheriting the same pinned runtime and CPU sandbox.
            files={'scripts/diagnose_cara_fast_exit_r1.py':(ROOT/'scripts/diagnose_cara_fast_exit_r1.py').read_bytes(),
                   'exit-mode.json':(json.dumps(dict(mode=a.exit_diagnostic))+'\n').encode()}
        if a.binding_r2:
            for name in ['src/wcomr/cara_fast_binding_r2.py','src/wcomr/cara_fast_requests_r2.py',
                         'tests/test_cara_fast_binding_r2.py','tests/check_cara_fast_binding_routes_r2.py',
                         'scripts/check_cara_fast_binding_cpu_r2.py',
                         'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
                         'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json']:
                files[name]=(ROOT/name).read_bytes()
        if a.score_cli_control:
            names=['src/wcomr/__init__.py','src/wcomr/cara_fast_spec_r1.py',
                   'src/wcomr/policy_generator_r1/__init__.py','src/wcomr/policy_generator_r1/interval_grammar.py',
                   'src/wcomr/cara_fast_fidelity_r1.py','src/wcomr/cara_fast_scoring_manifest_r2.py',
                   'scripts/score_cara_fast_fidelity_r1.py','scripts/check_cara_fast_scoring_cli_cpu_r2.py',
                   'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json']
            files={name:(ROOT/name).read_bytes() for name in names}
        if a.orchestration_r2:
            names=['src/wcomr/cara_fast_binding_r2.py','src/wcomr/cara_fast_requests_r2.py',
                   'src/wcomr/cara_fast_collection_r2.py','src/wcomr/cara_fast_execution_r2.py',
                   'tests/test_cara_fast_freeze_r2.py','tests/test_cara_fast_execution_r2.py',
                   'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
                   'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json',
                   'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
                   'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json']
            pending=['check_cara_fast_orchestration_cpu_r2','cara_fast_worker_r2',
                     'cara_fast_host_guardian_r2','run_cara_fast_r2']
            seen=set()
            while pending:
                name=pending.pop()
                if name in seen:
                    continue
                seen.add(name)
                path=ROOT/'scripts'/(name+'.py')
                names.append(str(path.relative_to(ROOT)))
                for node in ast.walk(ast.parse(path.read_bytes())):
                    modules=([node.module] if isinstance(node,ast.ImportFrom) and node.module else
                             [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
                    pending.extend(m for m in modules if (ROOT/'scripts'/(m+'.py')).exists())
            files.update({name:(ROOT/name).read_bytes() for name in names})
            profile=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json').read_text())
            payload['additional_runtime_sha256']=profile['precision']['runtime_source_sha256']
            before="assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())"
            assert remote.count(before)==1
            remote=remote.replace(before,before+"\n assert all(sha(root/'runtime'/n)==h for n,h in p['additional_runtime_sha256'].items())")
            before="runtime_source_sha256=reg['runtime_source_sha256'],parent_git_revision="
            assert remote.count(before)==1
            remote=remote.replace(before,"runtime_source_sha256={**reg['runtime_source_sha256'],**p['additional_runtime_sha256']},parent_git_revision=")
        if a.post_r2:
            names=['src/wcomr/cara_fast_binding_r2.py','src/wcomr/cara_fast_collection_r2.py',
                   'src/wcomr/cara_fast_execution_r2.py','src/wcomr/cara_fast_terminal_r2.py',
                   'src/wcomr/cara_fast_capture_r2.py','src/wcomr/cara_fast_post_r2.py',
                   'src/wcomr/cara_fast_scoring_manifest_r2.py',
                   'tests/test_cara_fast_post_r2.py','tests/test_cara_fast_execution_r2.py',
                   'tests/test_cara_fast_freeze_r2.py',
                   'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
                   'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json',
                   'reports/cara_fast_score_cli_two_card_raw_receipts_r2_20261028.json',
                   'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json']
            pending=['check_cara_fast_post_cpu_r2','postprocess_cara_fast_r2',
                     'capture_cara_fast_terminal_r2','score_cara_fast_fidelity_r1']
            seen=set()
            while pending:
                name=pending.pop()
                if name in seen:
                    continue
                seen.add(name)
                path=ROOT/'scripts'/(name+'.py')
                names.append(str(path.relative_to(ROOT)))
                for node in ast.walk(ast.parse(path.read_bytes())):
                    modules=([node.module] if isinstance(node,ast.ImportFrom) and node.module else
                             [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
                    pending.extend(module for module in modules if (ROOT/'scripts'/(module+'.py')).exists())
            files.update({name:(ROOT/name).read_bytes() for name in names})
        if a.b36_r1:
            names=['src/wcomr/cara_fast_b36_r1.py','tests/test_cara_fast_b36_r1.py',
                   'tests/check_cara_fast_b36_routes_r1.py','scripts/check_cara_fast_b36_cpu_r1.py',
                   'scripts/score_cara_fast_fidelity_r1.py',
                   'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
                   'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json',
                   'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
                   'reports/cara_fast_score_cli_two_card_raw_receipts_r2_20261028.json']
            files.update({name:(ROOT/name).read_bytes() for name in names})
            profile=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/EXECUTION_PROFILE.json').read_text())
            payload['additional_runtime_sha256']=profile['precision']['runtime_source_sha256']
            before="assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())"
            assert remote.count(before)==1
            remote=remote.replace(before,before+"\n assert all(sha(root/'runtime'/n)==h for n,h in p['additional_runtime_sha256'].items())")
            before="runtime_source_sha256=reg['runtime_source_sha256'],parent_git_revision="
            assert remote.count(before)==1
            remote=remote.replace(before,"runtime_source_sha256={**reg['runtime_source_sha256'],**p['additional_runtime_sha256']},parent_git_revision=")
        payload.update(base_stage=launch['stage'],base_registration_sha256=launch['registration_sha256'],
                       parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                       files={n:base64.b64encode(b).decode() for n,b in files.items()},
                       hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
    result=ssh(remote,payload,docker_group=True,timeout=90) if a.host=='two_card' else four_ssh(remote,payload,timeout=90)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result.get(k) for k in ('status','host','stage','container_state','log_tail')}))


if __name__=='__main__':main()
