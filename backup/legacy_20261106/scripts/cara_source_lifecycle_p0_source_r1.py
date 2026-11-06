"""Prepare the distinct point20 source; no authority, GPU or central access."""
from cara_read_write_source_r1 import main


if __name__ == '__main__':
    main(run_id='cara-source-lifecycle-P0-point20-full14-r1-20261101',
         proof_ref='reports/cara_v1_P0_point20_whole_CPU_accepted_r1_20261101.json',
         accepted_ref='reports/cara_v1_P0_point20_entry_Linux_CPU_accepted_r1_20261101.json',
         quote_ref='plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_WHOLE_QUOTE_R1.json',
         storage_ref='reports/cara_v1_P0_point20_storage_accepted_r1_20261101.json')
