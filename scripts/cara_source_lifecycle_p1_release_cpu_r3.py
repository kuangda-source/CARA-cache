"""New original media CPU after R2's explicit synthetic-ledger schema failure."""
from pathlib import Path

from cara_source_lifecycle_p1_release_cpu_r2 import OVERLAY as ORIGINAL,REMOTE,main,packaged_local_check as check

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-release-CPU-a6000-r3-20261102'
OVERLAY=ORIGINAL+('tests/test_cara_source_lifecycle_p1_release_fixture_r1.py',
                 'scripts/cara_source_lifecycle_p1_release_cpu_r3.py')
PREFLIGHT='reports/cara_v1_P1_release_packaged_local_CPU_r3_20261102.json'


def packaged_local_check():
    return check(overlay=OVERLAY,modules=('test_cara_source_lifecycle_p1_analysis_r1',
        'test_cara_source_lifecycle_p1_release_fixture_r1'),expected_tests=7)


if __name__=='__main__':
    main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,preflight=PREFLIGHT,
        inherited='reports/cara_v1_P1_release_Linux_CPU_capture_r4_20261102.json',
        transfer_label='cara-V1-P1-release-R3-CPU-transfer')
