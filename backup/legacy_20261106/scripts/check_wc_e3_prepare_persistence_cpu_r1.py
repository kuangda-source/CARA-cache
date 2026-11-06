"""Affected metadata tests with the actual replay; no generator model or CUDA."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time


def fixture_batch(*, state, save, count=8, failure=None, fail_index=6):
    request = {'sample_name': 'CPU_PREPARE_FIXTURE', 'paths': [], 'status': 'STARTED'}
    state['requests'].append(request)
    replay = PreparedInputReplay(official_prepare)
    outputs = []
    rng_before = RNGState()
    for index in range(count):
        request['paths'].append({'status': 'STARTED'})
        rng_before.restore()
        if failure == 'before_prepare' and index == fail_index:
            raise ValueError('Injected before prepare')
        result = replay(seed=7)
        outputs.append((result, RNGState().signatures()))
        if failure in ('after_prepare', 'writer') and index == fail_index:
            raise ValueError('Injected ' + failure)
        request['paths'][-1]['status'] = 'COMPLETE_PARENT_PATH'
    request.update(status='COMPLETE_REQUEST', prepared_input_calls=replay.calls)
    save()
    return outputs, replay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0, str(args.source / 'src'))
    import numpy as np
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **k):
        raise RuntimeError('Prepare persistence CPU forbids CUDA or downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    from wcomr.prepared_input import PreparedInputReplay as original_replay, RNGState as original_rng
    from wcomr.prepared_input_persistence_r1 import bind_prepared_input_persistence
    from wcomr.mid_coverage import tree_digest
    reg = json.loads(args.registration.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert {n: sha(args.source / n) for n in reg['payload_sha256']} == reg['payload_sha256']
    assert not args.output.exists()
    def prepare(**kwargs):
        return {'x': torch.rand(2, 3), 'py': random.random(), 'np': np.random.rand(2), 'seed': kwargs['seed']}
    fixture_batch.__globals__.update(PreparedInputReplay=original_replay, RNGState=original_rng,
                                    official_prepare=prepare)
    checks = []
    # The ordinary batch bytes and all three CPU RNG transitions are unchanged.
    random.seed(4); np.random.seed(5); torch.manual_seed(6)
    start_rng = original_rng()
    old_state = {'requests': []}; old, _ = fixture_batch(state=old_state, save=lambda: None)
    start_rng.restore()
    state = {'requests': []}; writes = []
    persistent = bind_prepared_input_persistence(fixture_batch, state=state,
                                                save=lambda: writes.append(copy.deepcopy(state)))
    new, replay = persistent(state=state, save=lambda: writes.append(copy.deepcopy(state)))
    assert persistent.__code__ is fixture_batch.__code__
    assert persistent.__defaults__ is fixture_batch.__defaults__
    assert persistent.__kwdefaults__ is fixture_batch.__kwdefaults__
    assert fixture_batch.__globals__['PreparedInputReplay'] is original_replay
    assert [(tree_digest(v), r) for v, r in old] == [(tree_digest(v), r) for v, r in new]
    assert state == old_state and len(writes) == 9
    assert [len(q['requests'][0]['prepared_input_calls']) for q in writes[:8]] == list(range(1, 9))
    assert [len(q['requests'][0]['paths']) for q in writes[:8]] == list(range(1, 9))
    assert all(q['requests'][0]['paths'][-1]['status'] == 'STARTED' for q in writes[:8])
    state['requests'][0]['prepared_input_calls'][0]['source'] = 'MUTATED_RECEIPT_ONLY'
    assert replay.calls[0]['source'] == 'OFFICIAL_PREPARE_ONCE'
    checks.append('normal8_result_signatures_all_RNG_metadata_and_original_bytecode_equal')
    # Return the actual super result, with no extra copying of prepared tensors.
    class IdentityReplay:
        def __init__(self, official): self.calls = []
        def __call__(self):
            self.calls.append({'source': 'ACTUAL_IDENTITY_FIXTURE'})
            return identity_object
    identity_object = object()
    def identity_batch(): return PreparedInputReplay(None)()
    identity_batch.__globals__['PreparedInputReplay'] = IdentityReplay
    identity_state = {'requests': [{'status': 'STARTED', 'paths': [{'status': 'STARTED'}]}]}
    assert bind_prepared_input_persistence(identity_batch, state=identity_state, save=lambda: None)() is identity_object
    fixture_batch.__globals__['PreparedInputReplay'] = original_replay
    checks.append('returned_actual_result_object_identity_preserved')
    for failure, index, expected in [('before_prepare', 0, 0), ('before_prepare', 6, 6),
                                     ('after_prepare', 6, 7), ('writer', 6, 7)]:
        state = {'requests': []}; snapshots = []
        batch = bind_prepared_input_persistence(fixture_batch, state=state,
                                                 save=lambda: snapshots.append(copy.deepcopy(state)))
        try: batch(state=state, save=lambda: None, failure=failure, fail_index=index)
        except ValueError as error: assert str(error).startswith('Injected')
        else: raise AssertionError('Injected failure was swallowed')
        request = state['requests'][0]
        assert len(request.get('prepared_input_calls', [])) == expected
        assert len(snapshots) == expected and request['status'] == 'STARTED'
        assert sum(p['status'] == 'COMPLETE_PARENT_PATH' for p in request['paths']) == index
        checks.append(failure + '_' + str(index) + '_actual_evidence_only_retained')
    state = {'requests': []}
    def save_fault(): raise OSError('Injected metadata save failure')
    batch = bind_prepared_input_persistence(fixture_batch, state=state, save=save_fault)
    try: batch(state=state, save=lambda: None)
    except OSError as error: assert str(error) == 'Injected metadata save failure'
    else: raise AssertionError('save failure swallowed')
    assert len(state['requests'][0]['prepared_input_calls']) == 1
    assert state['requests'][0]['paths'][0]['status'] == 'STARTED'
    checks.append('save_fault_propagates_without_completed_path')
    # Exercise the same bound replay directly for failed actual preparation and changed requests.
    state = {'requests': [{'status': 'STARTED', 'paths': [{'status': 'STARTED'}]}]}
    batch = bind_prepared_input_persistence(fixture_batch, state=state, save=lambda: None)
    cls = batch.__globals__['PreparedInputReplay']
    def prepare_fault(**kwargs): raise ValueError('Injected official prepare failure')
    try: cls(prepare_fault)(seed=7)
    except ValueError as error: assert str(error) == 'Injected official prepare failure'
    else: raise AssertionError('prepare failure swallowed')
    assert 'prepared_input_calls' not in state['requests'][0]
    initial = original_rng(); replay = cls(prepare); replay(seed=7)
    initial.restore()
    try: replay(seed=8)
    except ValueError as error: assert str(error) == 'Prepared input request differs'
    else: raise AssertionError('changed request accepted')
    assert len(state['requests'][0]['prepared_input_calls']) == 1
    state['requests'].append({'status': 'STARTED', 'paths': [{'status': 'STARTED'}]})
    try: replay(seed=7)
    except ValueError as error: assert 'another request' in str(error)
    else: raise AssertionError('cross-request evidence accepted')
    assert 'prepared_input_calls' not in state['requests'][-1]
    checks.append('failed_prepare_changed_input_and_cross_request_refused')
    assert not torch.cuda.is_initialized()
    result = dict(status='E3_PREPARE_PERSISTENCE_AFFECTED_CPU_PASS_NOT_PRODUCTION_BATCH_OR_GPU',
                  checks=checks, checks_passed=len(checks), actual_original_replay_used=True,
                  fixture_paths=8, small_CPU_prepare_and_batch_fixture=True,
                  source_sha256=reg['payload_sha256'], historical_receipts_changed=False,
                  CPU_wall_seconds=time.perf_counter()-started, CUDA_initialized=False,
                  GPU_submissions=0, ledger_written=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'checks_passed', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__': main()
