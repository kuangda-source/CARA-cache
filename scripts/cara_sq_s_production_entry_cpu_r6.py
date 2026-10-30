"""Immutable native S CPU card; uses the existing direct two-card FRP alias."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import cara_sq_s_model_entry_cpu_r1 as previous
import cara_two_card_transport_r1 as transport
from cara_sq_two_card_cpu_r1 import CAPTURE
from wcomr.sq_s_spec_r2 import (EXECUTION_CRITICAL, SCOPE as GPU_SCOPE, PROFILE, IDENTITY,
    RESOURCE, ASSETS, MODE, RISK, HISTORY, PHYSICAL, QUOTES)

SCOPE = 'plans/cara_next_stage_20261028/sq/S_NATIVE_ENTRY_CPU_R6.json'
rule = json.loads((ROOT/RISK).read_text())
identity = json.loads((ROOT/IDENTITY).read_text())
quote_evidence = tuple(name for path in QUOTES.values()
    for name in json.loads((ROOT/path).read_text())['source_evidence_sha256'])
FILES = tuple(dict.fromkeys(previous.FILES + EXECUTION_CRITICAL +
    (GPU_SCOPE, PROFILE, IDENTITY, RESOURCE, ASSETS, MODE, RISK, HISTORY, SCOPE) +
    tuple(PHYSICAL.values()) + tuple(QUOTES.values()) + tuple(rule['legacy_source_ref'].values()) +
    (rule['method_ref'], rule['support_ref']) + tuple(identity['numerical_source_sha256']) + quote_evidence +
    tuple('tests/'+name+'.py' for name in json.loads((ROOT/SCOPE).read_text())['unit_modules']) +
    ('tests/test_sq_gpu_allocation_r1.py', 'tests/check_sq_s_production_entry_cpu_r5.py',
     'tests/check_sq_s_supervisor_cpu_r6.py', 'scripts/check_cara_sq_s_production_entry_cpu_r6.py',
     'scripts/cara_sq_s_production_entry_cpu_r6.py', 'scripts/audit_cara_sq_s_production_entry_cpu_r6.py',
     'reports/cara_sq_s_cli_composition_local_r5_20261030.json',
     'plans/cara_next_stage_20261028/sq/S_MODEL_ENTRY_CPU_RESOURCE_CONTRACT_R5.json')))
RUNTIME_EXTRA = tuple(dict.fromkeys(previous.previous.previous.RUNTIME_EXTRA +
    tuple(identity['runtime_source_sha256']) +
    ('cosmos_predict2/_src/imaginaire/utils/checkpoint_db.py', 'cosmos_predict2/_src/imaginaire/flags.py')))


def launch_source():
    code = previous.launch_source()
    for old, new in (
            ('cara-sq-s-model-entry-CPU-only-r1.lock', 'cara-sq-s-production-entry-CPU-only-r6.lock'),
            ('CARA_SQ_S_MODEL_ENTRY_CPU_R1', 'CARA_SQ_S_PRODUCTION_ENTRY_CPU_R6'),
            ('scripts/check_cara_sq_s_model_entry_cpu_r1.py', 'scripts/check_cara_sq_s_production_entry_cpu_r6.py')):
        if code.count(old) != 1: raise ValueError('Original CPU launch boundary changed: '+old)
        code = code.replace(old, new)
    return code


def capture_source():
    code = CAPTURE
    replacements = (
        ("print(json.dumps(dict(status='SQ_CPU_PREPARATION_CAPTURE'",
         "sys.path.insert(0,str(s/'src'))\nfrom wcomr.gpu_budget_pool_v2 import same_live_process\nprint(json.dumps(dict(original_CLI_live=same_live_process(L['identity']),status='SQ_CPU_PREPARATION_CAPTURE'"),
        ('observed_unix=time.time(),launch=L,',
         "observed_unix=time.time(),launch=L,registration=reg,registration_sha256=sha(s/'registration.json'),"))
    for before, after in replacements:
        if code.count(before) != 1: raise ValueError('Original CPU capture boundary changed')
        code = code.replace(before, after)
    return code


def remote(host, code, data=None, *, credential_file=None, docker_group=False):
    # The 1.7 MiB source requests hit the SSH observation limit over DERP.
    # Compress only transport bytes; original per-file SHA checks still run.
    if data is not None:
        data = base64.b64encode(gzip.compress(json.dumps(data).encode(), mtime=0)).decode()
        code = ('import base64,gzip,io,json,sys\n'
            'sys.stdin=io.StringIO(gzip.decompress(base64.b64decode(json.load(sys.stdin))).decode())\n'+code)
    if host == 'four_card': return transport.four_ssh(code, data, timeout=420)
    password = None
    command = shlex.quote('/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python')+' -c '+shlex.quote(code)
    payload = json.dumps(data) if data is not None else ''
    if docker_group:
        if credential_file is not None: transport.SECRET = credential_file
        password = transport.password()
        command = "sudo -S -p '' -u gaokuangda -g docker "+command
        payload = password+'\n'+payload
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', 'gkd_minchen', command],
        input=payload, text=True, capture_output=True, timeout=420)
    if result.returncode:
        error = result.stderr[-1800:]
        if password: error = error.replace(password, '[REDACTED]')
        raise RuntimeError('Native S CPU direct-FRP operation failed: '+error)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('recover', 'launch', 'capture'))
    parser.add_argument('--host', choices=('two_card', 'four_card'), required=True)
    parser.add_argument('--source-revision'); parser.add_argument('--launch-ref', type=Path)
    parser.add_argument('--credential-file', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError('Retain original native S CPU receipt')
    stage = 'cara-sq-s-production-entry-cpu-'+args.host.replace('_', '-')+'-r6-20261030'
    if args.command == 'launch':
        proof = json.loads((ROOT/f'reports/cara_sq_s_resource_guard_{args.host}_cpu_accepted_r1_20261029.json').read_text())
        capture_path = ROOT/proof['capture_ref']; capture = json.loads(capture_path.read_text())
        if (not proof['passed'] or capture['original_CLI_live'] is not False
                or capture['container_state']['Status'] != 'exited' or capture['container_state']['ExitCode'] != 0
                or hashlib.sha256(capture_path.read_bytes()).hexdigest() != proof['capture_sha256']):
            raise ValueError('Original same-host affected CPU component must be accepted and terminal')
        revision = subprocess.check_output(['git', 'rev-parse', (args.source_revision or 'HEAD')+'^{commit}'], cwd=ROOT, text=True).strip()
        published = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/codex/sq-production-entry-20261029'], cwd=ROOT, text=True).split()[0]
        if subprocess.run(['git', 'merge-base', '--is-ancestor', revision, published], cwd=ROOT).returncode:
            raise ValueError('Publish exact native S CPU source first')
        files = {name: subprocess.check_output(['git', 'show', revision+':'+name], cwd=ROOT) for name in FILES}
        if any(hashlib.sha256(files[name]).hexdigest() != value for name, value in proof['critical_source_sha256'].items()):
            raise ValueError('Original accepted S component changed')
        base = json.loads((ROOT/f'reports/cara_sq_s_resource_guard_{args.host}_cpu_launch_r1_20261029.json').read_text())
        value = remote(args.host, launch_source(), dict(stage_name=stage, profile=args.host,
            scope_name=SCOPE, manifest_sha256=json.loads((ROOT/SCOPE).read_text())['retained_manifest_sha256'],
            base=base, revision=revision, files={name: base64.b64encode(raw).decode() for name, raw in files.items()},
            hashes={name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
            runtime_extra_sha256={name: hashlib.sha256((ROOT/'cache/runtime'/name).read_bytes()).hexdigest() for name in RUNTIME_EXTRA}),
            credential_file=args.credential_file, docker_group=args.host == 'two_card')
    elif args.command == 'capture':
        original = json.loads(args.launch_ref.read_text())
        if not original['stage'].endswith('/'+stage): raise ValueError('Capture original native S CPU handle')
        value = remote(args.host, capture_source(), original, credential_file=args.credential_file,
            docker_group=args.host == 'two_card')
    else:
        code = "from pathlib import Path;import json;p=Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_S_NATIVE_ENTRY_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value = remote(args.host, code)
    with args.output.open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({key: value.get(key) for key in ('status', 'container_state', 'result_sha256')}))


if __name__ == '__main__': main()
