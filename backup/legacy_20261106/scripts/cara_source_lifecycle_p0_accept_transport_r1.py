"""Resume only the new point20 postrelease reader and eight-pair scorer."""
from cara_read_write_accept_transport_r1 import main


if __name__ == '__main__':
    main(start_ref='reports/cara_v1_P0_point20_actual_start_accepted_r1_20261101.json',
         terminal_ref='reports/cara_v1_P0_point20_final_original_r1_20261101.json',
         settlement_ref='reports/cara_v1_P0_point20_final_settlement_r1_20261101.json')
