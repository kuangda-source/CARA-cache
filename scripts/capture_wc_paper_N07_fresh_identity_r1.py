#!/usr/bin/env python3
"""One identity-only output audit after accepted development/method freeze."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
N05_COLLECTION_UNIX = 1792123500  # 2026-10-16 12:05 Asia/Shanghai.


def before_audit(development, method_freeze, now):
    n05, n06 = development['N05'], development['N06']
    if (now < N05_COLLECTION_UNIX or n05['status'] not in ('N05_CORE66_INDEPENDENTLY_ACCEPTED',
            'N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED')
            or (n05['full_denominator'], n05['formal_denominator']) != (66, 44)
            or n06['status'] not in ('SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED',
                                    'SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED')
            or (n06['full_denominator'], n06['formal_denominator']) != (36, 24)
            or method_freeze['parameters_frozen_from'] != 'DEVELOPMENT_ONLY'
            or method_freeze['final_test_outputs_seen'] is not False
            or not development['latest_development_observed_unix'] <= method_freeze['freeze_unix'] <= now):
        raise ValueError('Accepted complete development and method freeze after the original N05 ETA required')
    from wcomr.frozen_input_selection_r1 import KNOWN_METHODS
    methods = method_freeze['method_ids']
    if (len(methods) != 10 or len(set(methods)) != 10 or not set(methods).issubset(KNOWN_METHODS)
            or not {'NATIVE35', 'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A'}.issubset(methods)
            or not any(m.startswith('WC_') for m in methods) or not any(m.startswith('RA_') for m in methods)):
        raise ValueError('Same complete ten-method freeze and strong simple comparators required')


REMOTE = r'''
import hashlib,json,pathlib,sys,time
payload=json.loads(sys.stdin.buffer.readline());root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
source=payload['module_source'];assert hashlib.sha256(source.encode()).hexdigest()==payload['module_sha256']
namespace={'__name__':'registered_identity_audit_only'};exec(compile(source,'GIT_BOUND_IDENTITY_ONLY_AUDIT','exec'),namespace)
ledger=root/'reports/gpu-budget-v2.json';before=ledger.read_bytes()
value=namespace['collect_outputs'](root,payload['records'])
def process(pid):
 try:
  fields=(pathlib.Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split()
  return dict(pid=pid,state=fields[0],start_ticks=int(fields[19]))
 except FileNotFoundError:return dict(pid=pid,state=None,start_ticks=None)
after=ledger.read_bytes();pool=json.loads(after)
value.update(namespace['registered_jobs'](pool,process))
if after!=before:value['read_errors'].append(dict(kind='ORIGINAL_V2_LEDGER_CHANGED_DURING_AUDIT'))
value.update(status='N07_FRESH_IDENTITY_ONLY_SERVER_OUTPUT_AUDIT',observed_unix=time.time(),
 method_freeze_sha256=payload['method_freeze_sha256'],catalog_sha256=payload['catalog_sha256'],
 module_sha256=payload['module_sha256'],original_v2_ledger_sha256=hashlib.sha256(after).hexdigest(),
 server_project_root=str(root),recording_or_semantic_independence_proven=False)
print(json.dumps(value,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--development', type=Path, required=True)
    parser.add_argument('--method-freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    sys.path.insert(0, str(ROOT / 'src'))
    development = json.loads(args.development.read_text()); freeze = json.loads(args.method_freeze.read_text())
    before_audit(development, freeze, time.time())
    script = Path(__file__).resolve(); module = ROOT / 'src/wcomr/frozen_input_exposure_r1.py'
    for path in (script, module):
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + str(path.relative_to(ROOT))], cwd=ROOT)
        assert committed == path.read_bytes(), 'Commit identity-only code before its single read-only query'
    catalog = ROOT / 'reports/dataset_source_group_audit_20260930.json'
    protocol = json.loads((ROOT / 'manifests/wc_paper_N07_common_input_protocol_r1_20261016.json').read_text())
    digest = hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert digest == protocol['frozen_sources'][str(catalog.relative_to(ROOT))]
    payload = dict(records=json.loads(catalog.read_text())['records'], module_source=module.read_text(),
        module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(), catalog_sha256=digest,
        method_freeze_sha256=hashlib.sha256(args.method_freeze.read_bytes()).hexdigest())
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen', 'python3 -c ' + shlex.quote(REMOTE)],
        input=json.dumps(payload, ensure_ascii=False, allow_nan=False).encode() + b'\n', capture_output=True, timeout=180)
    if call.returncode: raise RuntimeError(call.stderr.decode())
    value = json.loads(call.stdout)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(receipt=str(args.output), documents=len(value['documents']),
        identity_groups=len(value['identity_hits']), read_errors=len(value['read_errors']),
        all_registered_GPU_jobs_terminal=value['all_registered_GPU_jobs_terminal'], GPU_submissions=0)))
    if value['read_errors'] or not value['all_registered_GPU_jobs_terminal']:
        raise SystemExit('Preserve incomplete identity audit; do not select through its missing evidence')


if __name__ == '__main__': main()
