"""Recover original P0 acceptance over its verified original SSH route."""
from pathlib import Path
import subprocess

from cara_read_write_accept_transport_r1 import main

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    probe = subprocess.run(
        ['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
         '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
        capture_output=True, text=True, timeout=12)
    print('Original peer probe:', probe.returncode, probe.stdout.strip(), flush=True)
    main(start_ref='reports/cara_v1_P0_point20_actual_start_accepted_r1_20261101.json',
         terminal_ref='reports/cara_v1_P0_point20_final_original_r1_20261101.json',
         settlement_ref='reports/cara_v1_P0_point20_final_settlement_r1_20261101.json',
         ssh_config=ROOT / '.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
         connect_timeout=60)
