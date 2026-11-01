"""Whole M1 collection inside a caller-admitted loaded-model allocation.

No transport, source installation, GPU admission, ledger action or scoring is
performed here. Every logical request and extra paid pair remains explicit.
"""
import copy
from pathlib import Path

from . import clean_speed20_r1 as clean
from .cara_fast_fidelity_r1 import file_sha
from .cara_read_write_plan_r1 import validate
from .cara_read_write_point_r1 import execute as point
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1 import p2_native_sampling, production_sampling
from .policy_generator_r1.frozen_request_arguments import request_variant
from .prepared_input import PreparedInputReplay
from .wc_time_collection_r1 import collect_phase


class Requests:
    def __init__(self, *, inference, samples, card, common, context, cpu_validation,
                 logical_copy_cap_bytes, CPU_storage_cap_bytes):
        self.profile = validate(card)
        if (context['scope_sha256'] != card['scope_sha256'] or context['host'] != 'two_card'
                or context['CPU_fixture_only'] is not cpu_validation
                or not context.get('launch_id') or not context.get('source_revision')
                or not context.get('admission_sha256')):
            raise ValueError('Caller-bound exact source/scope/admission context required')
        self.card, self.common = copy.deepcopy(card), common
        self.inference, self.samples = inference, samples
        self.cpu_validation = cpu_validation
        self.logical_cap, self.CPU_cap = logical_copy_cap_bytes, CPU_storage_cap_bytes
        self.slots = {s['id']: s for s in card['physical_matrix']}
        self.seen = set()
        self.prepared = {name: PreparedInputReplay(inference.pipe._get_data_batch_input) for name in card['FIT']}

    def __call__(self, slot, output):
        if self.slots.get(slot['id']) != slot or slot['id'] in self.seen:
            raise ValueError('Altered or already attempted physical slot; recover only')
        self.seen.add(slot['id'])
        role = self.card['roles'][slot['role']]
        sample = request_variant(self.samples[slot['member']], seed=0, num_steps=35)
        kwargs = dict(self.common, settings=copy.deepcopy(self.card['settings']),
                      calibration=None, specs={}, output=Path(output), audit=False)
        if role['kind'] == 'native':
            runner = p2_native_sampling.execute
            kwargs['schedule'] = self.card['schedule']
        else:
            runner = point if role['kind'] == 'point' else production_sampling.execute
            kwargs.update(profile=self.profile, policy=role['policy'])
            if role['kind'] == 'point':
                kwargs.update(corner=role['corner'], logical_copy_cap_bytes=self.logical_cap,
                              CPU_storage_cap_bytes=self.CPU_cap)
        with clean.patched(self.inference.pipe, '_get_data_batch_input', self.prepared[slot['member']]):
            result = execute_with_timing(runner, self.inference, sample, host='two_card',
                expected_updates=36, cpu_validation=self.cpu_validation, diagnostic=True, **kwargs)
        if result['status'] != 'COMPLETE' or result['solver_steps'] != 36 or result['guided_pairs'] != 36:
            raise ValueError('A complete guarded output is required for every registered slot')
        if role['kind'] == 'point':
            if result['physical_model_pairs'] != 37 or result['intervention']['corner'] != role['corner']:
                raise ValueError('Current paid intervention identity/count differs')
            expected = role['policy']['actions'].copy()
            expected[7] = 'D' if role['corner'][1] == '1' else 'C'
            if ([h['actual'] for h in result['semantic_history']] != expected
                    or any(h['fallback_reason'] is not None for h in result['semantic_history'])):
                raise ValueError('Counterfactual write or future frozen policy differs')
        elif role['kind'] == 'policy' and ([h['actual'] for h in result['semantic_history']] != role['policy']['actions']
                or any(h['fallback_reason'] is not None for h in result['semantic_history'])):
            raise ValueError('Independent control left its frozen policy')
        if any(result[k] != 0 for k in ('in_timing_guided_copies', 'in_timing_hashes', 'research_checkpoints')):
            raise ValueError('Unregistered whole-trajectory instrumentation')
        video = Path(result['video_path'])
        result.update(slot_id=slot['id'], member=slot['member'], role=slot['role'],
            scope_sha256=self.card['scope_sha256'], CPU_fixture_only=self.cpu_validation,
            physical_model_pairs=role['physical_pairs'], diagnostic_timing_only=True,
            T_DD=result['paper_denoise_decode_seconds'], T_request=result['full_request_seconds'],
            video_artifact=dict(path=str(video), bytes=video.stat().st_size, sha256=file_sha(video)),
            scientific_accepted=False)
        return result


def collect(adapter, output, *, before_request, save):
    state = collect_phase(adapter, 'B', output, before_request=before_request,
                          save=save, after_diagnostics=lambda rows: {'passed': True})
    if (len(state['rows']) != 14 or any(r['status'] != 'COMPLETE' for r in state['rows'])
            or sum(r['result']['physical_model_pairs'] for r in state['rows']) != 512):
        raise ValueError('Complete fourteen-request/512-pair denominator required')
    for member in adapter.card['FIT']:
        records = {r['slot']['role']: r['result']['intervention'] for r in state['rows']
                   if r['slot']['member'] == member and r['slot']['role'].startswith('RW')}
        if len({r['parent_state_sha256'] for r in records.values()}) != 1:
            raise ValueError('Four corners did not start from an identical complete parent')
    state.update(status='COMPLETE14_PENDING_RELEASE_NOT_SCORED',
                 scientific_score_pairs=8, physical_model_pairs=512,
                 diagnostic_timing_only=True, scientific_accepted=False)
    save(state)
    return state
