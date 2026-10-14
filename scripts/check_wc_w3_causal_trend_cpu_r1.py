"""Necessary causal/schema/label/regret tests only; no actual trajectory fit."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise ValueError('New CPU receipt required')
    sys.path.insert(0,str(a.stage/'src'));started=time.perf_counter();stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(a.stage/'tests'),pattern='test_w3_causal_trend_r1.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    receipt={'status':'W3_T1_T2_11_CAUSAL_SCHEMA_WEIGHTED_TARGET_CPU_CHECKS_PASS_NOT_SCIENCE' if result.wasSuccessful() and result.testsRun==11 else 'W3_CAUSAL_CPU_FAILED',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'log':stream.getvalue(),
        'CPU_wall_seconds':time.perf_counter()-started,'GPU_submissions':0,'real_labels_or_method_regret_measured':False,
        'training_provenance':'SYNTHETIC_CPU_INTERFACE',
        'code_sha256':{n:hashlib.sha256((a.stage/n).read_bytes()).hexdigest() for n in
            ('src/wcomr/w3_causal_trend_r1.py','tests/test_w3_causal_trend_r1.py','scripts/check_wc_w3_causal_trend_cpu_r1.py')}}
    with a.output.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('log','code_sha256')}))
    if not result.wasSuccessful() or result.testsRun!=11:print(stream.getvalue());raise SystemExit(1)


if __name__=='__main__':main()
