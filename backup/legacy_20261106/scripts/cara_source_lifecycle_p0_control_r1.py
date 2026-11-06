"""Original point20 control only; never inherit M1 authority or central access."""
from cara_read_write_control_r1 import main


if __name__ == '__main__':
    main(authorization_ref='plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_AUTHORIZATION_R1.json',
         proof_ref='reports/cara_v1_P0_point20_whole_CPU_accepted_r1_20261101.json',
         source_ref='reports/cara_v1_P0_point20_source_preparation_r1_20261101.json')
