"""One new isolated Linux entry/scorer CPU card, preserving all old CPU terminals."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_endpoint7_final_cpu_r2 import OVERLAY as ENDPOINT_CLOSURE
from cara_read_write_collection_linux_cpu_r1 import OVERLAY as READ_WRITE, REMOTE
from wcomr.cara_read_write_runner_binding_r1 import REQUIRED as RUNNER
from wcomr.cara_read_write_dispatch_r1 import REQUIRED as DISPATCH

STAGE = 'cara-read-write-entry-CPU-a6000-r1-20261101'
OVERLAY = tuple(dict.fromkeys(ENDPOINT_CLOSURE+READ_WRITE+RUNNER+DISPATCH+(
    'tests/check_cara_read_write_loaded_cpu_r1.py', 'tests/check_cara_read_write_packet_fixture_r1.py',
    'tests/test_cara_read_write_entry_r1.py', 'tests/test_cara_read_write_central_r1.py',
    'tests/test_cara_read_write_postrelease_r1.py', 'tests/test_cara_read_write_score_capture_r1.py',
    'tests/test_cara_read_write_score_dispatch_r1.py', 'tests/check_cara_read_write_score_cli_r1.py',
    'scripts/check_cara_read_write_entry_linux_cpu_r1.py',
    'plans/cara_next_stage_20261101/read_write/M1_FULL14_WHOLE_QUOTE_DRAFT_R2.json',
)))
REMOTE = REMOTE.replace('check_cara_read_write_collection_linux_cpu_r1.py', 'check_cara_read_write_entry_linux_cpu_r1.py')

if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
