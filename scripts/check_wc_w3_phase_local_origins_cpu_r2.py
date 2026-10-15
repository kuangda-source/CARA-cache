#!/usr/bin/env python3
import argparse,importlib.util,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
sys.path.insert(0,str(ROOT/'src'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    spec=importlib.util.spec_from_file_location('phase_local_origins',ROOT/'tests/check_w3_phase_local_origins_cpu_r2.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=module.check(a.runtime)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
