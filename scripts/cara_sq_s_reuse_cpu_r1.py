"""Recover or start one bounded original-host CPU artifact audit."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_batch_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import ssh

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-sq-s-reuse-cpu-two-card-r1-20261029'
SCOPE = 'plans/cara_next_stage_20261028/sq/S_REUSE_CPU_R1.json'
FILES = tuple(dict.fromkeys(previous.FILES + ('src/wcomr/sq_s_reuse_r1.py',
    'src/wcomr/rv0_video_reader.py', 'tests/test_sq_s_reuse_r1.py',
    'scripts/check_cara_sq_s_reuse_cpu_r1.py', SCOPE)))


def launch_source():
    code = previous.launch_source()
    for before, after in (
        ('cara-sq-s-batch-CPU-only-r1.lock', 'cara-sq-s-reuse-CPU-only-r1.lock'),
        ('CARA_SQ_S_BATCH_CPU_R1', 'CARA_SQ_S_REUSE_CPU_R1'),
        ('scripts/check_cara_sq_s_batch_cpu_r1.py', 'scripts/check_cara_sq_s_reuse_cpu_r1.py')):
        if code.count(before) != 1:
            raise ValueError('Accepted CPU boundary changed: '+before)
        code = code.replace(before, after)
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('recover', 'launch', 'capture'))
    parser.add_argument('--source-revision')
    parser.add_argument('--launch-ref', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Retain the original S reuse CPU receipt')
    if args.command == 'launch':
        accepted = json.loads((ROOT/'reports/cara_sq_s_batch_two_card_cpu_accepted_r1_20261029.json').read_text())
        original = json.loads((ROOT/accepted['capture_ref']).read_text())
        if (not accepted['passed'] or original['container_state']['Running']
                or original['container_state']['ExitCode'] != 0
                or hashlib.sha256((ROOT/accepted['capture_ref']).read_bytes()).hexdigest() != accepted['capture_sha256']):
            raise ValueError('First recover and accept the original S whole CPU terminal')
        revision = subprocess.check_output(['git', 'rev-parse', (args.source_revision or 'HEAD')+'^{commit}'],
                                           cwd=ROOT, text=True).strip()
        published = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'],
                                            cwd=ROOT, text=True).split()[0]
        if subprocess.run(['git', 'merge-base', '--is-ancestor', revision, published], cwd=ROOT).returncode:
            raise ValueError('Publish this exact CPU audit source first')
        files = {name: subprocess.check_output(['git', 'show', revision+':'+name], cwd=ROOT) for name in FILES}
        if any(hashlib.sha256(files[name]).hexdigest() != expected
               for name, expected in accepted['critical_source_sha256'].items()):
            raise ValueError('The original accepted S batch components changed')
        base = json.loads((ROOT/'reports/cara_sq_s_batch_two_card_cpu_launch_r1_20261029.json').read_text())
        value = ssh(launch_source(), dict(stage_name=STAGE, profile='two_card', scope_name=SCOPE,
            manifest_sha256=previous.MANIFEST_SHA, base=base, revision=revision,
            files={name: base64.b64encode(raw).decode() for name, raw in files.items()},
            hashes={name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
            runtime_extra_sha256={}), docker_group=True)
    elif args.command == 'capture':
        launch = json.loads(args.launch_ref.read_text())
        if not launch['stage'].endswith('/'+STAGE):
            raise ValueError('Recover the exact original forensic CPU stage')
        value = ssh(CAPTURE, launch, docker_group=True)
    else:
        code = "import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+STAGE+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_S_REUSE_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value = ssh(code, docker_group=True)
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({name: value.get(name) for name in ('status', 'container_state', 'result_sha256')}))


if __name__ == '__main__':
    main()
