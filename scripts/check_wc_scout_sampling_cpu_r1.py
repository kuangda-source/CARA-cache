#!/usr/bin/env python3
"""Retain the old no-CUDA import boundary and replace only the full numerical scope."""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--kind',choices=['CAL12','BANK24'],required=True)
    for n in ('stage','runtime','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.environ['WC_SCOUT_KIND']=a.kind
    old=a.stage/'scripts/check_wc_drop1_full18_cpu_r1.py'
    reg=__import__('json').loads((a.stage/'registration.json').read_text())
    source=old.read_text()
    assert hashlib.sha256(source.encode()).hexdigest()==reg['payload_sha256']['scripts/check_wc_drop1_full18_cpu_r1.py']
    changes=[('from wcomr.drop1_full18_r1 import CONFIG,METHODS,matrix,validate_contract,CPU_STATUS',
              'from wcomr.scout_numeric_contract_r1 import CONFIG,METHODS,matrix,validate_contract,CPU_STATUS',1),
        ("len(matrix([r['name'] for r in config['requests']]))==18",f"len(matrix([r['name'] for r in config['requests']]))=={12 if a.kind=='CAL12' else 24}",1),
        ('check_drop1_full18_sampling_cpu_r1.py','check_scout_full_sampling_cpu_r1.py',1),
        ("CPU-drop1-artifacts",'CPU-scout-'+a.kind+'-artifacts',2),
        ("module.run(args.runtime,own_loader,args.stage/'CPU-scout-"+a.kind+"-artifacts')",
         "module.run(args.runtime,own_loader,args.stage/'CPU-scout-"+a.kind+"-artifacts',kind='"+a.kind+"')",1),
        ("value['actual_CPU_paths']==56",f"value['actual_CPU_paths']=={80 if a.kind=='CAL12' else 168}",1),
        ("c['complete_CPU_paths']==28",f"c['complete_CPU_paths']=={40 if a.kind=='CAL12' else 84}",1),
        ('all36_clean_outputs_actions_video_equal','full36_output_and_owner_controls',1)]
    for before,after,count in changes:
        if source.count(before)!=count:raise ValueError('Exact original CPU boundary substitution missing: '+before)
        source=source.replace(before,after)
    ast.parse(source)
    sys.argv=[str(old),'--stage',str(a.stage),'--runtime',str(a.runtime),'--output',str(a.output)]
    namespace=dict(__name__='scout_sampling_original_boundary',__file__=str(old))
    exec(compile(source,str(old)+'#explicit-independent-scout-scope','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
