#!/usr/bin/env python3
"""Check contrast signs and invalid inputs, without inventing GPU arm receipts."""
import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'scripts/summarize_wc_timing_factorial_results_cpu.py'
s = importlib.util.spec_from_file_location('factorial_summary', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def check():
    cases = []
    losses = {'E0L0':4., 'E1L0':7., 'E0L1':2., 'E1L1':3.}
    r = m.signed_effects(losses)
    assert [r[k] for k in ('early_at_L0','early_at_L1','late_at_E0','late_at_E1','interaction')] == [3.,1.,-2.,-4.,-2.]
    cases.append('SIGNED_NEGATIVE_EFFECT_AND_INTERACTION_ALGEBRA')
    invalid = []
    for key in losses:
        bad = dict(losses); del bad[key]
        invalid.append(('MISSING_'+key, bad))
    for name, value in (('NAN',float('nan')), ('INFINITY',float('inf')), ('NEGATIVE',-1.), ('BOOL',True), ('TEXT','1')):
        invalid.append((name,dict(losses,E1L1=value)))
    invalid.append(('EXTRA_NONFACTORIAL_ARM',dict(losses,legacy_SD=0.)))
    for name, bad in invalid:
        try: m.signed_effects(bad)
        except AssertionError: cases.append('REJECT_'+name)
        else: raise AssertionError(name)
    return cases


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); start = time.perf_counter(); cases = check()
    result = {'status':'SIGNED_FACTORIAL_ALGEBRA_AND_INPUT_REJECTION_CPU_PASS_NOT_GPU_OR_NEW_RESULTS',
              'CPU_only':True,'controls':cases,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
              'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'CPU_wall_seconds':time.perf_counter()-start,'GPU_execution':False,
              'new_missing_arm_metrics':False,'quality_acceptance':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
