"""Bind the accepted private-volume provisioner to the selected card."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=HERE/'manifest.json')
    card=json.loads(parser.parse_args().manifest.read_text())
    size=card['storage']['private_output_GiB']
    original=ROOT/'scripts/provision_cara_f19_speed190_storage_r1.py'
    source=original.read_text()
    source=source.replace('os.posix_fallocate(fd, 0, 16*2**30)',
                          f'os.posix_fallocate(fd, 0, {size}*2**30)')
    source=source.replace('PRIVATE16',f'PRIVATE{size}')
    source=source.replace('image_bytes=16*2**30',f'image_bytes={size}*2**30')
    source=source.replace('free >= 32*2**30',f'free >= {size+16}*2**30')
    scope=dict(__name__='sensitivity_private_storage',__file__=str(original))
    exec(compile(source,str(original)+'#sensitivity-card','exec'),scope)
    project=ROOT.parents[1]
    run=card['run_id'];label=run[5:].rsplit('-',1)[0]
    base=project/'.sync/storage-reservations'/label
    journal=Path('/home/gaokuangda/cara_control')/label
    scope.update(ROOT=project,CONTROL=ROOT,BASE=base,RUN=run,OUTPUT=project/'outputs'/run,
        IMAGE=base/'output.ext4',JOURNAL_DIR=journal,JOURNAL=journal/'control.journal',
        CPU_STAGE=ROOT,HELPER=ROOT/'src/wcomr/history104_storage_r2.py')
    scope['main']()
    if 'pipeline' in card:(project/'outputs'/run/'native_states').mkdir()
