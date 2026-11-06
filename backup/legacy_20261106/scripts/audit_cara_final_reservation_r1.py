"""Recheck the original final16/reserve16 identities; no outcomes or new selection."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from audit_cara_new_pool_delta_r1 import protected_pool, POOL
from wcomr.frozen_input_exposure_r1 import Identities
from wcomr.cara_final_exposure_r1 import identity_locations

BASELINE = 'reports/cara_DEV128_prelaunch_dual_exposure_reviewed_20261026.json'
DEV_SCOPE = 'manifests/cara_DEV128_scope_r1_20261026.json'
DEV_ACCEPTANCE = 'reports/cara_DEV128_A6000_accepted_20261027_0404.json'
SOURCES = ('src/wcomr/frozen_input_exposure_r1.py', 'src/wcomr/cara_final_exposure_r1.py')
PROJECTS = dict(four_card=['/data20t/gaokuangda/worldcache_workspace'],
    two_card=['/data20t/gaokuangda/worldcache_workspace', '/home/gaokuangda/data/gkd/worldcache_omr'])
REMOTE = r'''
import hashlib,json,os,pathlib,resource,signal,sys,time
p=json.load(sys.stdin)
for name,body in p['modules'].items():
 assert hashlib.sha256(body.encode()).hexdigest()==p['source_sha256'][name]
mem=int(next(line.split()[1] for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
assert mem>=12*2**30,'Preserve CPU headroom before metadata scan'
os.nice(10);assert 26 in os.sched_getaffinity(0);os.sched_setaffinity(0,{26})
resource.setrlimit(resource.RLIMIT_AS,(4*2**30,4*2**30));resource.setrlimit(resource.RLIMIT_CPU,(600,600))
signal.alarm(600);started=time.time()
frozen={};exec(compile(p['modules'][p['source_names'][0]],'FROZEN_IDENTITY_WALKER','exec'),frozen)
current={};exec(compile(p['modules'][p['source_names'][1]],'FINAL_RESERVATION_AUDIT','exec'),current)
index=frozen['Identities'](p['records']);rows=[]
for requested in p['projects']:
 row=current['collect_protected_outputs'](requested,index,set(p['protected']),p['known_clear_documents'])
 row['requested_project']=requested;rows.append(row)
fields=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split()
print(json.dumps(dict(status='FINAL_RESERVATION_IDENTITY_CAPTURE',host=p['host'],roots=rows,
 source_sha256=p['source_sha256'],pool_sha256=p['pool_sha256'],baseline_sha256=p['baseline_sha256'],
 capture_entry_sha256=p['capture_entry_sha256'],MemAvailable_before=mem,
 process=dict(pid=os.getpid(),start_ticks=int(fields[19]),CPU_affinity=sorted(os.sched_getaffinity(0)),
 memory_limit_GiB=4,CPU_seconds_limit=600,wall_seconds_limit=600),started_unix=started,ended_unix=time.time(),
 GPU_submissions=0,ledger_written=False,endpoint_values_exported=False,videos_or_tensors_decoded=False)))
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context():
    pool, prior, groups, roles, records = protected_pool(ROOT)
    baseline = json.loads((ROOT/BASELINE).read_bytes())
    if (baseline['status'] != 'DEV128_FIRST_USE_SCOPED_CLEAR_METADATA_REVIEWED'
            or not baseline['scoped_no_execution_evidence'] or baseline['endpoint_values_exported']
            or baseline['pool_sha256'] != sha(ROOT/POOL) or baseline['pool_reselected']
            or baseline['protected_remote_hits'] or baseline['remote']['read_errors']
            or baseline['local_read_errors'] or baseline['local_blockers']):
        raise ValueError('Original accepted pre-use identity baseline required')
    protected = {n for row in pool['members'] if row['role'] != 'NEW_DEV_RESERVED' for n in row['group_members']}
    if len(protected) != 32:
        raise ValueError('Original final16/reserve16 group membership differs')
    scope = json.loads((ROOT/DEV_SCOPE).read_bytes())
    used = json.loads((ROOT/DEV_ACCEPTANCE).read_bytes())
    if (scope['DEV_members'] != roles['NEW_DEV_RESERVED']
            or used['status'] != 'DEV128_COMPLETE_ORIGINALS_FINANCE_ACCEPTED'
            or not used['full_protocol_accepted']):
        raise ValueError('Original DEV16 use must remain separate from final/reserve32')
    return pool, baseline, protected, roles, records


def capture(host, config):
    pool, baseline, protected, roles, records = context()
    modules = {n:(ROOT/n).read_text() for n in SOURCES}
    known = {row['path'].split(':', 1)[1]:row['sha256']
        for row in baseline['remote']['documents'] if row['path'].startswith(host+':')}
    payload = dict(host=host, projects=PROJECTS[host], modules=modules, source_names=SOURCES,
        source_sha256={n:sha(ROOT/n) for n in SOURCES}, records=records, protected=sorted(protected),
        pool_sha256=sha(ROOT/POOL), baseline_sha256=sha(ROOT/BASELINE), known_clear_documents=known,
        capture_entry_sha256=sha(Path(__file__)))
    interpreter = ('python3' if host == 'four_card' else
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python')
    call = subprocess.run(['/usr/bin/ssh', '-F', str(config), '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=35', host+'_lan', interpreter+' -c '+shlex.quote(REMOTE)],
        input=json.dumps(payload), text=True, capture_output=True, timeout=660)
    if call.returncode:
        raise RuntimeError('Original identity-only read did not complete: '+call.stderr[-1000:])
    return json.loads(call.stdout)


def local_inventory(index, protected, baseline):
    known = {r['ref']:r['sha256'] for r in baseline['local_documents']}
    for name in (BASELINE, baseline['raw_audit_ref']):
        known[name] = sha(ROOT/name)
    if sha(ROOT/baseline['raw_audit_ref']) != baseline['raw_audit_sha256']:
        raise ValueError('Original raw exposure baseline changed')
    documents, mentions, errors = [], [], []
    reused = 0
    for folder in ('reports', 'plans', 'manifests', 'cards'):
        for path in sorted((ROOT/folder).rglob('*')):
            if (not path.is_file() or not str(path).endswith(('.json', '.json.gz', '.yaml', '.yml'))
                    or '.private.' in path.name or 'private' in path.parts):
                continue
            ref = str(path.relative_to(ROOT))
            try:
                raw = path.read_bytes(); fingerprint = hashlib.sha256(raw).hexdigest()
                documents.append(dict(ref=ref, sha256=fingerprint, bytes=len(raw)))
                if known.get(ref) == fingerprint:
                    reused += 1
                    continue
                payload = gzip.decompress(raw) if path.suffix == '.gz' else raw
                if path.suffix in ('.yaml', '.yml'):
                    import yaml
                    data = yaml.safe_load(payload)
                else:
                    data = json.loads(payload)
                hits = identity_locations(data, index, protected)
                if hits:
                    mentions.append(dict(ref=ref, sha256=fingerprint, identity_locations=hits))
            except (OSError, ValueError, RecursionError) as error:
                errors.append(dict(ref=ref, kind=type(error).__name__))
    return dict(documents=documents, prior_clear_documents_reused=reused, identity_mentions=mentions, read_errors=errors)


def audit(paths):
    pool, baseline, protected, roles, records = context()
    if len(paths) != 2:
        raise ValueError('Both original host identity captures required')
    captures = []
    for host, path in zip(('four_card', 'two_card'), paths):
        data = json.loads(path.read_bytes())
        if (data['host'] != host or data['status'] != 'FINAL_RESERVATION_IDENTITY_CAPTURE'
                or data['source_sha256'] != {n:sha(ROOT/n) for n in SOURCES}
                or data['capture_entry_sha256'] != sha(Path(__file__))
                or data['pool_sha256'] != sha(ROOT/POOL) or data['baseline_sha256'] != sha(ROOT/BASELINE)
                or [r['requested_project'] for r in data['roots']] != PROJECTS[host]
                or data['GPU_submissions'] != 0 or data['ledger_written'] or data['endpoint_values_exported']
                or data['videos_or_tensors_decoded']):
            raise ValueError('Complete source-bound original host/root coverage required')
        captures.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), **data))
    local = local_inventory(Identities(records), protected, baseline)
    clear = not (local['identity_mentions'] or local['read_errors'] or any(
        root['identity_hits'] or root['read_errors'] for capture in captures for root in capture['roots']))
    return dict(status='FINAL16_RESERVE16_SCOPED_IDENTITY_CLEAR' if clear else 'FINAL16_RESERVE16_IDENTITY_REVIEW_REQUIRED',
        observed_unix=time.time(), pool_ref=POOL, pool_sha256=sha(ROOT/POOL), baseline_ref=BASELINE,
        baseline_sha256=sha(ROOT/BASELINE), source_sha256={n:sha(ROOT/n) for n in SOURCES},
        audit_entry_sha256=sha(Path(__file__)), protected_roles={k:v for k,v in roles.items() if k!='NEW_DEV_RESERVED'},
        original_DEV16_members=roles['NEW_DEV_RESERVED'], original_DEV16_already_used=True,
        original_DEV16_scope_ref=DEV_SCOPE,original_DEV16_scope_sha256=sha(ROOT/DEV_SCOPE),
        original_DEV16_acceptance_ref=DEV_ACCEPTANCE,original_DEV16_acceptance_sha256=sha(ROOT/DEV_ACCEPTANCE),
        protected_group_count=32, source_bytes_match=True, pool_reselected=False, local=local, captures=captures,
        scoped_no_execution_evidence=clear, first_use_delta_required=True, final_method_frozen=False,
        final_GPU_dispatch_ready=False, endpoint_values_exported=False, videos_or_tensors_decoded=False,
        GPU_submissions=0, new_reserved_GPUh=0, ledger_written=False,
        limits=['Local registered JSON/gzip/YAML metadata and all JSON/gzip plus names under three registered project output roots',
            'No claim about unrecorded or external jobs/storage; missing/changed/oversized/unreadable records remain unresolved',
            'Read-only identity snapshot; not method freeze, GPU authorization or indefinite first-use clearance'])


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    read = sub.add_parser('capture'); read.add_argument('--host', choices=PROJECTS, required=True)
    read.add_argument('--ssh-config', type=Path, required=True)
    accept = sub.add_parser('audit'); accept.add_argument('--four-card', type=Path, required=True)
    accept.add_argument('--two-card', type=Path, required=True)
    for command in (read, accept):command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():raise ValueError('Fresh identity observation required; preserve original receipts')
    result = (capture(args.host, args.ssh_config) if args.action=='capture' else
        audit([args.four_card.resolve(), args.two_card.resolve()]))
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write('\n')
    print(json.dumps(dict(status=result['status'], GPU_submissions=0,
        roots=len(result.get('roots', [])), clear=result.get('scoped_no_execution_evidence'))))


if __name__ == '__main__':
    main()
