#!/usr/bin/env python3
"""CPU preparation only: bind clean assets or materialize frozen diagnostic grids."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_generator_r1.continuation_preparation import (
    generator_input, history_matrix, native_candidate_counts, select_native_by_time)
from wcomr.policy_generator_r1.interval_grammar import Profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('generator-input')
    for name in ('price-capture','price-acceptance','old-capture','old-acceptance','native-clock'):
        p.add_argument('--'+name, type=Path, required=True)
    for command in ('history-matrix', 'native-candidates', 'native-time-choice'):
        p = sub.add_parser(command); p.add_argument('--input', type=Path, required=True)
    sub.add_parser('native-schedules-cpu')
    for p in sub.choices.values():
        p.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    require_new = a.output
    if require_new.exists():
        raise ValueError('A new output receipt is required')
    read = lambda p: json.loads(p.read_text())
    if a.command == 'native-schedules-cpu':
        import importlib.util
        import torch
        path=ROOT/'vendor/CosmosPredict25/cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py'
        spec=importlib.util.spec_from_file_location('cara_actual_unipc_cpu',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows=[]
        for n in range(18,36):
            scheduler=module.FlowUniPCMultistepScheduler(num_train_timesteps=1000,shift=1,use_dynamic_shifting=False)
            scheduler.set_timesteps(n,device='cpu',shift=5.,use_kerras_sigma=True)
            rows.append(dict(requested_steps=n,actual_updates=len(scheduler.timesteps),
                             timesteps=scheduler.timesteps.tolist(),sigmas=scheduler.sigmas.tolist()))
        if torch.cuda.is_initialized():raise ValueError('CPU schedule capture initialized CUDA')
        value=dict(status='PINNED_UNIPC_18_TO_35_CPU_SCHEDULES_NOT_MODEL_EXECUTION',rows=rows,
            source_ref=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            settings=dict(num_train_timesteps=1000,shift=5.,use_dynamic_shifting=False,use_kerras_sigma=True),
            CUDA_initialized=False,production_entry_accepted=False)
    elif a.command == 'generator-input':
        new = read(a.price_capture); old = read(a.old_capture)
        acceptance = read(a.price_acceptance)
        for p,k in ((a.price_capture,'capture_sha256'),(a.old_capture,'capture_sha256')):
            proof = acceptance if p == a.price_capture else read(a.old_acceptance)
            if proof.get(k) != hashlib.sha256(p.read_bytes()).hexdigest():
                raise ValueError('Independent acceptance does not bind supplied capture bytes')
        raw = new['files']['bundle']['raw_utf8'].encode()
        # The old atomic writer used indent=2 plus LF. Reconstruct only if its
        # original captured SHA verifies the exact bytes, never invent a new SHA.
        old_record = old['files']['bundle']
        old_raw = (old_record['raw_utf8'].encode() if 'raw_utf8' in old_record else
                   (json.dumps(old_record['data'], ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
        if hashlib.sha256(old_raw).hexdigest() != old_record['sha256']:
            raise ValueError('Old bundle reconstruction did not reproduce original captured bytes')
        value = generator_input(raw, acceptance, old_raw,
                                read(a.old_acceptance), read(a.native_clock))
    else:
        d = read(a.input)
        if a.command == 'history-matrix':
            p = dict(d['profile']);p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates'])
            value = history_matrix(Profile(**p), d['roles'], d['members'])
        elif a.command == 'native-candidates':
            value = native_candidate_counts(d['schedule_rows'], d['target_seconds'], d['clean_native35_seconds'])
        else:
            value = select_native_by_time(d['rows'], candidates=d['candidates'], members=d['members'],
                target_seconds=d['target_seconds'], profile_identity=d['profile_identity'])
    value.update(prepared_unix=time.time(), preparation_command=a.command, GPU_submissions=0)
    with require_new.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(output=str(require_new), GPU_submissions=0)))


if __name__ == '__main__':
    main()
