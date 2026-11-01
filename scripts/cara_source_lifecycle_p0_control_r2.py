"""Transport-only P0 recovery: unchanged RPC bytes and original GPU source.

The jump host has a30-second connection timeout. Allow60seconds for the full
target handshake instead of expiring its banner at25seconds; disable QoS in the
task's separate private config. No model, protocol, authority or budget change.
"""
from pathlib import Path
from cara_read_write_control_r1 import main

ROOT=Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    main(authorization_ref='plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_AUTHORIZATION_R1.json',
         proof_ref='reports/cara_v1_P0_point20_whole_CPU_accepted_r1_20261101.json',
         source_ref='reports/cara_v1_P0_point20_source_preparation_r1_20261101.json',
         ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
         connect_timeout=60)
