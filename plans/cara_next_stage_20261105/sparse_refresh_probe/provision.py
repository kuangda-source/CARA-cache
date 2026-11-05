"""Bind the accepted private-volume provisioner to this probe's own stage."""
import argparse
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=HERE/'manifest.json')
    args=p.parse_args()
    # The shared provisioner derives CONTROL from its own __file__; use its
    # unchanged code at this card path so it creates only this card's volume.
    source=ROOT/'plans/cara_next_stage_20261104/sensitivity/provision.py'
    exec(compile(source.read_text(),str(source),'exec'),dict(__name__='__main__',__file__=__file__))
