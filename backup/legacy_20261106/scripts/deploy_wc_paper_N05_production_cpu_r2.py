#!/usr/bin/env python3
"""Fresh R2 packaging closes every frozen config reference, preserving R1."""
import hashlib
import json
from pathlib import Path
import deploy_wc_paper_N05_production_cpu_r1 as original

STAGE='.sync/wc-paper-n05-core66-production-cpu-r2-20261016'

def complete_payload():
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/wc_paper_N05_core66_production_r1_20261016.json').read_text())
    references=[]
    for name,binding in config['references'].items():
        relative=Path(binding['ref'])
        assert not relative.is_absolute() and '..' not in relative.parts
        assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==binding['sha256'],name
        references.append(str(relative))
    return tuple(dict.fromkeys((*original.FILES,*references,
        'scripts/deploy_wc_paper_N05_production_cpu_r2.py','scripts/launch_wc_paper_N05_core66_r2.py')))

if __name__=='__main__':
    original.STAGE=STAGE
    original.FILES=complete_payload()
    original.main()
