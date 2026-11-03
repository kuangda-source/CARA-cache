"""Bind the accepted private-volume provisioner to this card's 256 GiB volume."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

if __name__=='__main__':
    original=ROOT/'scripts/provision_cara_f19_speed190_storage_r1.py'
    source=original.read_text()
    source=source.replace('os.posix_fallocate(fd, 0, 16*2**30)',
                          'os.posix_fallocate(fd, 0, 256*2**30)')
    source=source.replace('PRIVATE16','PRIVATE256')
    source=source.replace('image_bytes=16*2**30','image_bytes=256*2**30')
    source=source.replace('free >= 32*2**30','free >= 272*2**30')
    scope=dict(__name__='sensitivity_private_storage',__file__=str(original))
    exec(compile(source,str(original)+'#sensitivity256','exec'),scope)
    project=ROOT.parents[1]
    base=project/'.sync/storage-reservations/native-sensitivity8-confirm4-r1'
    journal=Path('/home/gaokuangda/cara_control/native-sensitivity8-confirm4-r1')
    run='cara-native-sensitivity8-confirm4-r1-20261104'
    scope.update(ROOT=project,CONTROL=ROOT,BASE=base,RUN=run,OUTPUT=project/'outputs'/run,
        IMAGE=base/'output.ext4',JOURNAL_DIR=journal,JOURNAL=journal/'control.journal',
        CPU_STAGE=ROOT,HELPER=ROOT/'src/wcomr/history104_storage_r2.py')
    scope['main']()
