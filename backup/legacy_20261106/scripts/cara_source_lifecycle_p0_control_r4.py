"""Original P0 RPC after a bounded probe of its original Tailscale peer.

The original two-layer SSH and original host keys remain in use. A single peer
probe precedes each serialized control call; no routing, service, model or budget
configuration changes. TWO/CENTRAL remain byte-identical to source3263bdfe.
"""
from pathlib import Path
import subprocess

from cara_read_write_control_r1 import main

ROOT=Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    probe=subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping',
        '--until-direct=false','--c','1','--timeout','5s','100.103.229.16'],
        capture_output=True,text=True,timeout=12)
    print('Original peer probe:',probe.returncode,probe.stdout.strip(),flush=True)
    main(authorization_ref='plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_AUTHORIZATION_R1.json',
         proof_ref='reports/cara_v1_P0_point20_whole_CPU_accepted_r1_20261101.json',
         source_ref='reports/cara_v1_P0_point20_source_preparation_r1_20261101.json',
         ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
         connect_timeout=60)
