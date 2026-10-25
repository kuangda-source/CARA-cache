"""New A6000 run's private volume and cross-disk journal; no GPU dispatch."""
import argparse
from pathlib import Path
from cara_two_card_transport_r1 import ssh,password
from wc_four_card_resource_cpu_r4 import write
from provision_cara_cal66_storage_r2 import REMOTE as TEMPLATE


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    code=TEMPLATE.replace("run='cara-shared-cal66-ada-r2'", "run='cara-shared-cal66-a6000-r1'")
    code=code.replace('.sync/storage-reservations/cal66-r2', '.sync/storage-reservations/cal66-a6000-r1')
    code=code.replace('/data1/gaokuangda_cara_control/cal66-r2/control.journal', '/home/gaokuangda/cara_control/cal66-a6000-r1/control.journal')
    code=code.replace('.sync/cara-shared66-combination-CPU-r3-20261025/src', '.sync/cara-shared66-full-ada-r2-20261025/src')
    value=ssh(code,dict(sudo_password=password()));write(a.output,value)
    print(value['status'])


if __name__=='__main__':main()
