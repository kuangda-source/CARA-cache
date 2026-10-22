"""Bind the published R1 SSH transport to its actual accepted R2 target.

The ten CPU-accepted production payloads remain byte-identical. Only two
control-plane path literals are reversibly bound to the accepted target.
"""
import argparse,ast,hashlib,json,subprocess
from pathlib import Path
import wc_four_card_bank24_execution_r1 as original

ORIGINAL_SHA='3fa31cc293f08dcb55e9faa6941c1d0438a97abd744a3487ebf8d1756dd6f3f3'
OLD='wc-bank24-fourcard-full-execution-r1-20261022'
NEW='wc-bank24-fourcard-full-execution-r2-20261022'

def bind(code,launch,accepted):
    target='/data20t/gaokuangda/worldcache_workspace/.sync/'+NEW
    if not (launch.get('target_stage')==accepted.get('target_stage')==target
        and launch.get('source_revision')==accepted.get('source_revision')=='6d9cd4941d5b88aa01e87e5947a0a0d65fce7dad'
        and accepted.get('full_new_host_scope_production_CPU_accepted') is True):
        raise ValueError('Exact actual accepted R2 source/target required')
    if code.count(OLD)!=2 or NEW in code:raise ValueError('Original two control path literals differ')
    result=code.replace(OLD,NEW)
    if result.replace(NEW,OLD)!=code:raise ValueError('Control transport is not reversible')
    ast.parse(result,feature_version=(3,8))
    return result

def main():
    p=argparse.ArgumentParser()
    for name in ['CPU-launch-ref','CPU-capture','CPU-acceptance','unique-handoff','upstream-capture','upstream-acceptance','frozen-gate','output']:
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
    code=Path('scripts/wc_four_card_bank24_execution_r1.py').read_bytes()
    assert hashlib.sha256(code).hexdigest()==ORIGINAL_SHA
    L=json.loads(a.CPU_launch_ref.read_text());accepted=json.loads(a.CPU_acceptance.read_text())
    original.REMOTE_LAUNCH=bind(original.REMOTE_LAUNCH,L,accepted)
    print(json.dumps(original.launch_gpu(a)))

if __name__=='__main__':main()
