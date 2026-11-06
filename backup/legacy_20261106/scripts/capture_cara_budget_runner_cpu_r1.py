"""Read the original R2 CPU handle with compressed transport; never dispatch."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import time
import zlib

from cara_budget_calibration_cpu_hosts_r2 import DELTA_REMOTE,ROOT,STAGES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ssh-config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.ssh_config.stat().st_mode&0o077:
        raise ValueError('Fresh receipt and private transport configuration required')
    launch=json.loads((ROOT/'reports/cara_budget_runner_four_card_CPU_launch_r1_20261030.json').read_text())
    if Path(launch['stage']).name!=STAGES['four_card'] or launch['host']!='four_card':
        raise ValueError('Original registered CPU launch required')
    code='import io,contextlib,zlib,base64\nbuffer=io.StringIO()\nwith contextlib.redirect_stdout(buffer):\n exec('+repr(DELTA_REMOTE)+')\nprint(base64.b64encode(zlib.compress(buffer.getvalue().encode(),6)).decode())\n'
    payload=json.dumps(dict(action='capture',host='four_card',stage_name=STAGES['four_card']))
    result=subprocess.run(['/usr/bin/ssh','-F',str(args.ssh_config),'-o','BatchMode=yes',
        '-o','ConnectTimeout=90','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
        'four_card','python3 -c '+shlex.quote(code)],input=payload.encode(),capture_output=True,timeout=180)
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace')[-1600:])
    raw=zlib.decompress(base64.b64decode(result.stdout.strip(),validate=True))
    capture=json.loads(raw)
    if capture['launch']!=launch or capture['registration_sha256']!=launch['registration_sha256']:
        raise ValueError('Recovered CPU handle differs')
    capture['readonly_compressed_transport']=dict(observer_source_sha256=hashlib.sha256(DELTA_REMOTE.encode()).hexdigest(),
        transport_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        uncompressed_bytes=len(raw),wire_bytes=len(result.stdout),observed_unix=time.time(),
        original_worker_modified=False,new_CPU_or_GPU_submissions=0)
    with args.output.open('x') as stream:json.dump(capture,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(state=capture['container_state'],CPU_proof_present=capture['CPU_proof'] is not None,
        transport=capture['readonly_compressed_transport'])))


if __name__=='__main__':main()
