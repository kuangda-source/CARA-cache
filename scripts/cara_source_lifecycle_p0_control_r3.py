"""Transport-only original P0 recovery using Tailscale's installed nc command.

Keep the original peer, host keys, TWO/CENTRAL RPC and source3263bdfe. The task
private SSH config routes only the Windows SSH stream through tailscaled's nc;
no server, global SSH, Clash, model or budget configuration is changed.
"""
from pathlib import Path
from cara_read_write_control_r1 import main

ROOT=Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    main(authorization_ref='plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_AUTHORIZATION_R1.json',
         proof_ref='reports/cara_v1_P0_point20_whole_CPU_accepted_r1_20261101.json',
         source_ref='reports/cara_v1_P0_point20_source_preparation_r1_20261101.json',
         ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_tailscale_nc.private',
         connect_timeout=60)
