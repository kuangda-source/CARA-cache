"""Whole available saved CPU vectors, real old videos and lifecycle controls."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    for name in ('project', 'stage'): parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True); args = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0, str(args.stage/'src'))
    from wcomr.p_reference_same_state_production_r1 import CONFIG, binding, sha, write, validate_contract
    from wcomr.p_reference_same_state_execution_r1 import PROTOCOL, validate_execution
    c = json.loads((args.stage/CONFIG).read_text()); p = json.loads((args.stage/PROTOCOL).read_text())
    assert not c['GPU_execution_selected']; validate_execution(c, p, args.stage)
    scope = validate_contract(c, args.stage)
    target = args.stage/'execution-CPU-receipt.json'; assert not target.exists(); start = time.perf_counter()
    r = {'status': 'P_REFERENCE_EXECUTION_CPU_RUNNING_NOT_GPU', 'pid': os.getpid(),
        'source_revision': args.source_revision, 'started_unix': time.time(), 'method_binding_sha256': binding(c),
        'protocol_sha256': sha(args.stage/PROTOCOL), 'budget_before_sha256': sha(args.project/'reports/budget.json'),
        'GPU_submissions': 0, 'ledger_written': False}
    write(target, r)
    try:
        import torch
        assert not torch.cuda.is_initialized(); torch.set_num_threads(2)
        def forbidden(*a, **k): raise RuntimeError('P-reference execution CPU forbids CUDA/downloads')
        torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
        from wcomr.p_reference_same_state_tensor_audit_r2 import audit, audit_point, READER_PROOF
        from wcomr.p_reference_same_state_terminal_r1 import pure_verifier
        original = args.project/'.sync/wc-p-reference-same-state-cpu-r3-20261011'
        before = json.loads((original/'receipt.json').read_text())
        assert before['exit_code'] == 0 and not any(Path('/proc/'+str(pid)).exists() for pid in (before['pid'], before['child_pid']))
        capture = json.loads((args.stage/c['sampling_CPU_capture_ref']).read_text())
        assert sha(original/'receipt.json') == capture['originals']['receipt.json']['sha256']
        assert sha(original/'result.json') == capture['originals']['result.json']['sha256']
        reg = json.loads((original/'registration.json').read_text())
        payload = {**reg['inherited_payload_sha256'], **reg['new_payload_sha256']}
        assert {n: sha(original/n) for n in payload} == payload == before['payload_after_sha256'] and len(payload) == 444
        v = json.loads((original/'result.json').read_text()); verify = pure_verifier(args.stage)
        assert [g['flow'] for g in v['checks']] == [False, True]
        shape = [1, 2048, 2, 8, 8]; flows = []; states = {}; points = []
        for group in v['checks']:
            arm = 'FLOW_ON' if group['flow'] else 'FLOW_OFF'; state = group['receipt']; states[arm] = state
            verify(state, scope)
            root = original/'CPU-artifacts'/('flow_ON' if group['flow'] else 'flow_OFF')
            raw = audit(state, root, torch.load, shape)
            assert (len(raw['files']), raw['actual_tensors_reloaded'], raw['actual_direct_tensor_comparisons']) == (44, 580, 210)
            assert raw['files'] == group['actual_tensor_audit']['files']
            indexed = {(x['event'], x['source'], x['age']): x for x in raw['all_five_independent_error_records']}
            for request in state['requests']:
                for row in request['paths']:
                    for event in row['origins']:
                        for branch in event['branches']:
                            for point in branch['age_points']:
                                independent = audit_point(point, root, torch.load, shape)
                                assert independent['all_five_guided_MSE'] == indexed[(event['event']['id'], branch['source'], point['age'])]['same_state_guided_MSE']
                                points.append((point, root, independent))
            flows.append(raw)
        assert len(points) == 48 and sum(x[2]['D_source_direct_equalities'] for x in points) == 96
        # Actual recorded point mutations must be rejected without changing
        # any original source or artifact. All perturbed metadata are copies.
        fault_controls = []; first, root, _ = points[0]
        for label in ('missing_readout', 'missing_restore', 'changed_D_hash', 'changed_shared_alpha',
                      'changed_source_age', 'false_branch_MSE', 'missing_head', 'changed_teacher_restore'):
            point = copy.deepcopy(first)
            if label == 'missing_readout': point['five_reference_readouts'].pop()
            elif label == 'missing_restore': point['serial_restore_guards'].pop()
            elif label == 'changed_D_hash': point['five_reference_readouts'][0]['true_D_full_state_sha256'] = 'BAD'
            elif label == 'changed_shared_alpha': point['five_reference_readouts'][0]['readout']['shared_alpha'] = 1
            elif label == 'changed_source_age': point['actual_source_and_decision_history']['working_source_ages'][0] += 1
            elif label == 'false_branch_MSE': point['five_reference_readouts'][0]['guided_moments']['diagnostics']['original_branch_MSE'][0] += 1
            elif label == 'missing_head': point['five_reference_readouts'][0]['actual_head_events'].pop()
            else: point['teacher_state_restored_before_actual_C'] = False
            try: audit_point(point, root, torch.load, shape)
            except ValueError: fault_controls.append(label)
            else: raise AssertionError('Partial-point reader accepted '+label)
        with tempfile.TemporaryDirectory(prefix='P_REFERENCE_ACTUAL_POINT_CPU_') as folder:
            temporary = Path(folder); raw = Path(first['artifact']['path']).read_bytes(); point = copy.deepcopy(first)
            path = temporary/'point.pt'; path.write_bytes(raw[:-1]); point['artifact']['path'] = str(path)
            try: audit_point(point, temporary, torch.load, shape)
            except ValueError: fault_controls.append('actual_truncated_file')
            else: raise AssertionError('Written truncated point accepted')
        def load(name, filename):
            spec = importlib.util.spec_from_file_location(name, args.stage/filename)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
        r['terminal_and_exact_authority_controls'] = load('P_REFERENCE_TERMINAL_CPU',
            'tests/check_p_reference_same_state_terminal_cpu_r1.py').run(args.stage, c, scope, states)
        r['whole_two_flow_supervisor_lifecycle_controls'] = load('P_REFERENCE_SUPERVISOR_CPU',
            'tests/check_p_reference_same_state_supervisor_cpu_r1.py').run(args.stage, c)
        # Complete decoding exercises the new reader's actual video boundary
        # on four existing original GPU videos, never the Toy CPU writer files.
        from wcomr.rv0_video_reader import probe_video, decoded_video
        old = args.project/'outputs/wc-e4c-matched-p-d-age124-offon4-suffix16-r1/model'
        receipt = json.loads((old/'receipt.json').read_text()); videos = []
        for request in receipt['batch']['requests']:
            for row in request['paths']:
                art = row['video_artifact']; path = Path(art['path']).resolve()
                assert path.is_relative_to(old.resolve()) and path.stat().st_size == art['bytes'] and sha(path) == art['sha256']
                metadata = probe_video(path); count = 0
                with decoded_video(path) as stream:
                    for frame, pts, base in stream:
                        assert frame.shape == (432, 768, 3) and pts == metadata['pts'][count] and base == metadata['time_base']; count += 1
                assert count == 93; videos.append({'path': str(path), 'sha256': art['sha256'], 'frames': count})
        assert len(videos) == 4 and not torch.cuda.is_initialized()
        assert sha(original/'result.json') == capture['originals']['result.json']['sha256']
        assert {n: sha(original/n) for n in payload} == payload
        r.update(status='P_REFERENCE_COMPLETE_EXECUTION_CPU_PASS_NOT_GPU', exit_code=0, CUDA_initialized=False,
            actual_reader={'files': 88, 'tensors': 1160, 'direct_comparisons': 420, 'points': 48,
                'D_source_equalities': 96, 'partial_point_refusals': fault_controls, 'reader_proof': READER_PROOF,
                'actual_old_GPU_video_frames_decoded': 372, 'actual_old_GPU_videos': videos},
            all_original_sampling_and_production_CPU_reused_not_rerun=True,
            no_new_scientific_metric_values_or_GPU_created=True)
    except BaseException as error:
        r.update(status='P_REFERENCE_EXECUTION_CPU_FAILED_NOT_GPU', exit_code=1,
            error_type=type(error).__name__, error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start, ended_unix=time.time(),
            method_payload_after_sha256={n: sha(args.stage/n) for n in c['payload_sha256']},
            execution_payload_after_sha256={n: sha(args.stage/n) for n in p['execution_payload_sha256']},
            budget_after_sha256=sha(args.project/'reports/budget.json'))
        if (r['method_payload_after_sha256'] != c['payload_sha256']
                or r['execution_payload_after_sha256'] != p['execution_payload_sha256']
                or r['budget_before_sha256'] != r['budget_after_sha256']):
            r.update(status='P_REFERENCE_EXECUTION_CPU_IDENTITY_FAILED', exit_code=1)
        write(target, r)
    print(json.dumps({k: r[k] for k in ('status', 'exit_code', 'CPU_wall_seconds', 'GPU_submissions')}))
    raise SystemExit(r['exit_code'])


if __name__ == '__main__': main()
