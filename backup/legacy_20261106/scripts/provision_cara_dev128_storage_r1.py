"""Provision only the directly authorized DEV128 private volume; no GPU call."""
import argparse
from pathlib import Path
from cara_two_card_transport_r1 import ssh,password
from provision_cara_cal66_storage_r2 import REMOTE
from wc_four_card_resource_cpu_r4 import write

def code():
 return (REMOTE.replace("run='cara-shared-cal66-ada-r2'","run='cara-shared25-dev128-r1'")
 .replace('.sync/storage-reservations/cal66-r2','.sync/storage-reservations/dev128-a6000-r1')
 .replace('/data1/gaokuangda_cara_control/cal66-r2/control.journal','/home/gaokuangda/cara_control/dev128-a6000-r1/control.journal')
 .replace('.sync/cara-shared66-combination-CPU-r3-20261025/src','.sync/cara-dev128-fullCPU-a6000-r2-20261026/src')
 .replace("status='CAL66_PRIVATE_STORAGE_PROVISIONED_NO_GPU'","status='DEV128_PRIVATE_STORAGE_PROVISIONED_NO_GPU'"))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 v=ssh(code(),dict(sudo_password=password()));write(a.output,v);print(v['status'])
