#!/usr/bin/env python3
"""Provision this explicitly authorized run's private capacity. Never launches GPU."""
import argparse
from wc_four_card_policy_assets_r1 import ssh,write
from wc_four_card_price_refresh_gpu_r1 import saved_secret
from pathlib import Path
REMOTE=r'''
import pathlib,json,sys,os,subprocess,time,shutil
p=json.load(sys.stdin);password=p.pop('sudo_password');assert not p
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');run='cara-shared-cal66-ada-r2'
base=root/'.sync/storage-reservations/cal66-r2';image=base/'output.ext4';out=root/'outputs'/run
journal=pathlib.Path('/data1/gaokuangda_cara_control/cal66-r2/control.journal')
assert not base.exists() and not out.exists() and not journal.parent.exists(),'Existing storage: inspect original; never overwrite'
assert shutil.disk_usage(root).free>64*2**30 and shutil.disk_usage(journal.parent.parent).free>2**30
sys.path.insert(0,str(root/'.sync/cara-shared66-combination-CPU-r3-20261025/src'))
from wcomr.history104_storage_r2 import FixedJournal,StorageGuard
base.mkdir(mode=0o700);out.mkdir(mode=0o700);journal.parent.mkdir(mode=0o700)
fd=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
finally:os.close(fd)
subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard','-m','0',str(image)],check=True,capture_output=True,timeout=60)
def sudo(args):
 r=subprocess.run(['sudo','-S','-p','']+args,input=password+'\n',text=True,capture_output=True,timeout=45)
 if r.returncode:raise RuntimeError('Selected private storage operation failed: '+args[0])
sudo(['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(out)])
sudo(['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(out)])
# Fresh filesystem's empty metadata directory only; never remove experiment files.
sudo(['/usr/bin/rmdir',str(out/'lost+found')]);password=None
FixedJournal(journal).create()
c=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=run,output_mount=str(out),output_device=out.stat().st_dev,image_path=str(image),image_inode=image.stat().st_ino,image_bytes=32*2**30,journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=4*2**30,minimum_free_inodes=1024,minimum_host_free_bytes=128*2**20,shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
v=dict(status='CAL66_PRIVATE_STORAGE_PROVISIONED_NO_GPU',observed_unix=time.time(),storage_contract=c,check=StorageGuard(c).check(),findmnt=subprocess.check_output(['findmnt','-J',str(out)],text=True),GPU_submissions=0,ledger_reservation_created=False)
(base/'provision.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 v=ssh(REMOTE,dict(sudo_password=saved_secret()));write(a.output,v);print(v['status'])
if __name__=='__main__':main()
