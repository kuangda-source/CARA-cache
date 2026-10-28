"""Reuse the accepted CPU container lifecycle; only payload and worker differ."""
import argparse
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
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    label='ada' if a.host=='four_card' else 'a6000'
    stage_name='cara-fast-CPU-'+label+'-r'+str(a.revision)+'-20261028'
    payload=dict(action=a.action,host=a.host,stage_name=stage_name)
    # Exact accepted launch/capture code, unchanged CPU/network/memory safeguards.
    worker='check_cara_fast_shutdown_cpu_r1.py' if a.shutdown_repair else 'check_cara_fast_cpu_r1.py'
    remote=EXISTING_CPU_TRANSPORT.replace('check_wc_time_card_cpu_r1.py',worker)
    assert remote.count(worker)==1
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
        payload.update(base_stage=launch['stage'],base_registration_sha256=launch['registration_sha256'],
                       parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                       files={n:base64.b64encode(b).decode() for n,b in files.items()},
                       hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
    result=ssh(remote,payload,docker_group=True,timeout=90) if a.host=='two_card' else four_ssh(remote,payload,timeout=90)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result.get(k) for k in ('status','host','stage','container_state','log_tail')}))


if __name__=='__main__':main()
