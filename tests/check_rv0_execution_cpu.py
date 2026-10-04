"""Full-scope draft, simulated ledger ownership and all93 RGB stream controls."""
import copy
import io
import importlib.util
import json
import math
from pathlib import Path
import sys


def run(project):
    sys.path.insert(0, str(project/'src'))
    from wcomr.rv0_execution import validate_config, reserve_budget, settle_budget, validate_preparation_audits
    from wcomr.rv0_evaluation_plan import evaluation_plan
    from wcomr.rv0_video_reader import validate_probe, decode_stream
    config = json.loads((project/'configs/wc_rv0_causal_r1_draft.json').read_text())
    assert validate_config(config)['outputs'] == 18
    refused = []
    def refuse(label, operation):
        try: operation()
        except (ValueError, KeyError, FileNotFoundError): refused.append(label)
        else: raise AssertionError('Invalid execution evidence accepted: '+label)
    refuse('unselected_draft_GPU_launch', lambda: validate_config(config, selected=True))
    assert len(validate_preparation_audits(project, config)) == 2
    damaged = copy.deepcopy(config)
    damaged['preparation_audits']['causal_cpu_original']['sha256'] = None
    refuse('server_audit_SHA_absent', lambda: validate_preparation_audits(project, damaged))
    for name, value in [('sample_names', config['sample_names'][:1]), ('timeout_seconds', 1800),
                        ('child_timeout_seconds', 6900), ('CPU_scoring_after_GPU_release', False)]:
        damaged = copy.deepcopy(config); damaged[name] = value
        refuse('changed_'+name, lambda c=damaged: validate_config(c))
    damaged = copy.deepcopy(config); damaged['scope']['suffix_controls'] = 12
    refuse('reduced_full_suffix_denominator', lambda: validate_config(damaged))
    damaged = copy.deepcopy(config); damaged['payload_sha256']['src/wcomr/rv0_causal.py'] = '0'*64
    refuse('actual_CPU_core_source_drift', lambda: validate_config(damaged))
    # Selected metadata is a simulated accounting fixture only. It does not
    # satisfy real audit files or source/asset/admission gates and starts no job.
    simulated = copy.deepcopy(config); simulated.update(gpu_execution_selected=True, gpu_uuid='GPU-CPU-FAKE')
    for binding in simulated['preparation_audits'].values(): binding['sha256'] = 'a'*64
    before = json.loads((project/'reports/budget.json').read_text())
    reservation = reserve_budget(before, simulated, 12345)
    assert before['gpu_jobs_launched'] == 45 and reservation['gpu_jobs_launched'] == 46
    assert reservation['cap_gpu_hours'] == before['cap_gpu_hours'] == 13
    assert reservation['budget_authorization_history'] == before['budget_authorization_history']
    assert math.isclose(reservation['used_gpu_hours'], before['used_gpu_hours']+6900/3600)
    settled = settle_budget(reservation, before, simulated, 1000, 12345)
    assert math.isclose(settled['used_gpu_hours'], before['used_gpu_hours']+1000/3600)
    assert not any(k.endswith('_inflight') for k in settled)
    assert settled['gpu_jobs_launched'] == 46 and settled['cap_gpu_hours'] == 13
    actual_overrun = settle_budget(reservation, before, simulated, 8000, 12345)
    assert math.isclose(actual_overrun['used_gpu_hours'], before['used_gpu_hours']+8000/3600)
    assert actual_overrun['used_gpu_hours'] > 13  # Preserve actual cost, never clip it.
    for field, value in [('run_id', 'other'), ('supervisor_pid', 54321), ('reserved_seconds', 1800)]:
        damaged = copy.deepcopy(reservation); damaged['wc_rv0_causal_inflight'][field] = value
        refuse('reservation_owner_'+field, lambda c=damaged: settle_budget(c, before, simulated, 1000, 12345))
    for value in [math.nan, math.inf, -1, 0, True]:
        refuse('invalid_actual_wall_'+str(value), lambda v=value: settle_budget(reservation, before, simulated, v, 12345))
    damaged = copy.deepcopy(before); damaged['used_gpu_hours'] = 11.1
    refuse('complete_cap_exceeds_remaining', lambda: reserve_budget(damaged, simulated, 12345))
    raw = json.loads((project/'reports/wc_rv0_causal_cpu_r3_20261004.json').read_text())
    spec = importlib.util.spec_from_file_location('real_terminal_auditor_cpu', project/'scripts/audit_wc_rv0_causal_terminal.py')
    terminal = importlib.util.module_from_spec(spec); spec.loader.exec_module(terminal)
    plan_groups = 0
    for group in raw['controls']['controls']['checks'][:2]:
        receipt = group['receipt']; toy_config = {'sample_names': ['common', 'human']}
        assert terminal.audit_trajectories(receipt, 2)['complete_suffixes'] == 24
        for field in ['inputs', 'deep', 'record']:
            damaged = copy.deepcopy(receipt); child = damaged['requests'][0]['parents'][-1]['children'][0]
            if field == 'record': child['record']['parent_restored'] = False
            else: child[field].pop()
            try: terminal.audit_trajectories(damaged, 2)
            except AssertionError: refused.append('terminal_'+field+'_'+str(group['flow']))
            else: raise AssertionError('Terminal trajectory audit accepted '+field)
        plan = evaluation_plan(receipt, toy_config, real_GPU_required=False)
        assert (len(plan['files']), len(plan['pairs']), len(plan['bridges'])) == (18, 8, 2)
        assert [(p['scene'], p['CFG_slot'], p['action']) for p in plan['pairs']] == [
            (name, slot, action) for name in ['common', 'human'] for slot in (0, 1) for action in ['C', 'D']]
        for pair in plan['pairs']:
            native = next(r['parents'][0]['artifact'] for r in receipt['requests'] if r['sample_name'] == pair['scene'])
            assert pair['reference'] == native
        refuse('Toy_receipt_cannot_be_real_GPU_'+str(group['flow']), lambda r=receipt: evaluation_plan(r, toy_config))
        damaged = copy.deepcopy(receipt); damaged['requests'][0]['parents'][-1]['decoded_children'].pop()
        refuse('missing_C_D_video_'+str(group['flow']), lambda r=damaged: evaluation_plan(r, toy_config, real_GPU_required=False))
        plan_groups += 1
    probe = {'streams': [{'width': 768, 'height': 432, 'r_frame_rate': '16/1', 'avg_frame_rate': '16/1', 'time_base': '1/8192'}],
             'frames': [{'width': 768, 'height': 432, 'best_effort_timestamp': i*512} for i in range(93)]}
    metadata = validate_probe(probe)
    for label, mutate in [('missing93', lambda p: p['frames'].pop()),
                           ('duplicate_PTS', lambda p: p['frames'][1].update(best_effort_timestamp=0)),
                           ('missing_PTS', lambda p: p['frames'][1].pop('best_effort_timestamp')),
                           ('wrong_geometry', lambda p: p['frames'][50].update(width=384)),
                           ('wrong_FPS', lambda p: p['streams'][0].update(avg_frame_rate='8/1'))]:
        damaged = copy.deepcopy(probe); mutate(damaged)
        refuse('source_frame_'+label, lambda p=damaged: validate_probe(p))
    pixels = bytes([11, 22, 33])*(432*768)
    class Frames:
        def __init__(self, frames): self.remaining = frames
        def read(self, size):
            if not self.remaining: return b''
            if size == 1: return b'X'
            self.remaining -= 1; return pixels
    decoded = 0
    for rgb, pts, base in decode_stream(Frames(93), metadata):
        assert rgb.shape == (432, 768, 3) and rgb[0, 0].tolist() == [11, 22, 33]
        assert pts == decoded*512 and base == '1/8192'; decoded += 1
    assert decoded == 93
    refuse('truncated93_RGB_decode', lambda: list(decode_stream(Frames(92), metadata)))
    refuse('extra_RGB_frame', lambda: list(decode_stream(Frames(94), metadata)))
    refuse('short_RGB_frame', lambda: list(decode_stream(io.BytesIO(pixels[:-1]), metadata)))
    return {'status': 'FULL_CAUSAL_EXECUTION_PLAN_LEDGER_RGB_STREAM_CPU_CONTRACT_PASS_NOT_HOST_PARITY',
            'refusal_controls': len(refused), 'refused': refused,
            'complete_mock_plan_groups': plan_groups, 'Native_relative_C_D_pairs_per_group': 8,
            'decoded_fixture_frames': decoded, 'fixture_HWC': [432, 768, 3],
            'simulated_reservation_never_written': True, 'GPU_submissions': 0,
            'real_C_D_video_scores': 0, 'Torch_or_actual_FFmpeg_executed': False}


if __name__ == '__main__':
    print(json.dumps(run(Path(__file__).resolve().parents[1])))
