#!/usr/bin/env python3
"""Run frozen CPU audit/score with one explicitly verified canonical-root fix.

The original GPU stage, selected config, GPU receipts and original CPU failure
remain immutable. No GPU launcher is exposed by this entry point.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase', choices=['audit', 'score'], required=True)
    for name in ['project', 'stage', 'repair-root', 'output']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--expected-source', required=True)
    p.add_argument('--terminal-audit', type=Path)
    args = p.parse_args()
    if args.output.exists() or args.repair_root.resolve() == args.stage.resolve():
        raise ValueError('Preserve original CPU/GPU identities and use a distinct repair output')
    manifest = json.loads((args.repair_root/'manifest.json').read_text())
    if (manifest['GPU_source_revision'] != args.expected_source or manifest['GPU_submissions'] != 0
            or manifest['change'] != 'CANONICALIZE_EXPECTED_OUTPUT_ROOT_ONLY'
            or sha(Path(__file__)) != manifest['repair_wrapper_sha256']):
        raise ValueError('Explicit frozen CPU repair provenance required')
    name = 'src/wcomr/rv0_small_human_evaluation.py'
    original, repaired = args.stage/name, args.repair_root/name
    old = "        root = Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic'\n"
    new = "        root = (Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic').resolve()\n"
    if (sha(original) != manifest['original_evaluation_sha256']
            or sha(repaired) != manifest['repaired_evaluation_sha256']
            or original.read_text().count(old) != 1
            or original.read_text().replace(old, new) != repaired.read_text()):
        raise ValueError('CPU repair must be exactly one root-normalization line')
    config = json.loads((args.stage/'human-config.json').read_text())
    if config['payload_sha256'][name] != sha(original):
        raise ValueError('Frozen GPU evaluator must still match its original payload')
    sys.path.insert(0, str(args.stage/'src'))
    import wcomr
    if Path(wcomr.__file__).resolve() != (args.stage/'src/wcomr/__init__.py').resolve():
        raise ValueError('Unmodified frozen dependency package required')
    spec = importlib.util.spec_from_file_location('wcomr.rv0_small_human_evaluation', repaired)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    script = args.stage/'scripts'/('audit_wc_w3_small_human_terminal.py' if args.phase == 'audit'
                                 else 'analyze_wc_w3_small_human_lpips_cpu.py')
    if sha(script) != config['payload_sha256']['scripts/'+script.name]:
        raise ValueError('Original CPU CLI source changed')
    argv = [str(script), '--project', str(args.project), '--stage', str(args.stage), '--output', str(args.output)]
    if args.phase == 'audit':
        argv += ['--expected-source', args.expected_source]
    else:
        if args.terminal_audit is None:
            raise ValueError('Successful independent terminal audit required before scoring')
        argv += ['--receipt', str(args.project/'outputs'/config['run_id']/'diagnostic/receipt.json'),
                 '--terminal-audit', str(args.terminal_audit)]
    sys.argv = argv
    runpy.run_path(str(script), run_name='__main__')
    # This provenance belongs to the new CPU result, never the original GPU receipt.
    result = json.loads(args.output.read_text())
    result['CPU_path_repair'] = {**manifest, 'repair_root': str(args.repair_root),
        'original_GPU_stage_unchanged': True, 'original_CLI_sha256': sha(script),
        'scope_or_trajectory_or_metric_rules_changed': False}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
