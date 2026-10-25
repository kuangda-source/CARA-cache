"""Actual migrated production entry, complete lifecycle and CPU score probe."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import importlib.util
import unittest


def module(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    p = argparse.ArgumentParser()
    for k in ('project', 'stage', 'output'):
        p.add_argument('--'+k, type=Path, required=True)
    a = p.parse_args(); start = time.time()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    sys.path[:0] = [str(a.stage/'src'), str(a.stage/'scripts'), str(a.stage/'tests')]
    import torch
    torch.set_num_threads(1); assert not torch.cuda.is_initialized()
    from wcomr.policy_generator_r1.shared66_card import validate, RUN, COUNTS, sha, execution_quote
    c, reg, card = validate(a.project, a.stage)
    assert RUN == 'cara-shared-cal66-a6000-r1'
    # This actually enters the frozen class, real samplers, guardrails and codec;
    # previous Ada CPU evidence is not substituted for this host's entry.
    entry = a.stage/'A6000-real-entry.json'
    subprocess.run([sys.executable, str(a.stage/'scripts/check_cara_cal66_entry_cpu_r2.py'),
                    '--project', str(a.project), '--stage', str(a.stage), '--output', str(entry)],
                   check=True, timeout=1800)
    raw = json.loads(entry.read_text())
    assert raw['status'] == 'SHARED_CAL66_FROZEN_ENTRY_CPU_R2_COMPLETE_NOT_GPU'
    assert raw['actual_request_count'] == raw['guard_refusal_controls'] == 60
    assert raw['frozen_boundary']['preload_validated_slots'] == 66
    suite = unittest.defaultTestLoader.loadTestsFromModule(module(a.stage/'tests/test_cara_shared66_combination_r1.py', 'terminal'))
    result = unittest.TextTestRunner().run(suite); assert result.wasSuccessful()
    life = module(a.stage/'tests/check_cara_shared66_lifecycle_cpu_r1.py', 'life').run(a.stage, a.stage/'CPU-SM86-lifecycle')
    storage = module(a.stage/'tests/check_shared66_storage_cpu_r1.py', 'storage').run(a.stage, a.stage/'CPU-SM86-storage')
    binding = json.loads((a.stage/'quality-binding.json').read_text())
    quality_stage = Path(binding['registration']['stage'])
    qout = a.stage/'A6000-real-quality'
    env = dict(os.environ, PYTHONPATH=binding['dependency_overlay']+':'+str(quality_stage/'src')+':'+str(quality_stage/'scripts'))
    subprocess.run([sys.executable, str(quality_stage/'scripts/score_cara_cal66_quality_cpu_r1.py'),
                    '--binding', str(a.stage/'quality-binding.json'), '--declared-synthetic-CPU-probe',
                    '--output', str(qout)], env=env, check=True, timeout=1800)
    quality = json.loads((qout/'result.json').read_text())
    assert quality['status'] == 'CAL66_REAL_THREE_METRIC_93_FRAME_CPU_PROBE_PASS'
    assert quality['models_really_loaded'] and quality['frames'] == 93
    assert not torch.cuda.is_initialized()
    proof = dict(status='CAL66_A6000_PRODUCTION_COMBINATION_CPU_COMPLETE', source_revision=reg['source_revision'],
                 registration_sha256=sha(a.stage/'registration.json'), started_unix=start, ended_unix=time.time(),
                 run_id=RUN, scope_counts=COUNTS, real_entry=raw, real_entry_sha256=sha(entry),
                 lifecycle=life, storage_lifecycle=storage, terminal_tests=result.testsRun,
                 quality_probe=quality, quality_probe_sha256=sha(qout/'result.json'),
                 execution_quote=execution_quote(card), execution_source_sha256=reg['payload_sha256'],
                 CUDA_initialized=False, GPU_submissions=0, authoritative_ledger_written=False)
    with a.output.open('x') as f: json.dump(proof, f, indent=2); f.write('\n')
    print(json.dumps(dict(status=proof['status'], wall_seconds=proof['ended_unix']-start)))


if __name__ == '__main__':
    main()
