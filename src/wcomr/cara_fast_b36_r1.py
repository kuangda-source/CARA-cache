"""Verified A32 handoff -> the unchanged B36 routes; no dispatch or finance.

Only complete terminal, settlement, scores and an immutable selection can bind
the continuation. Production resource admission remains the caller's boundary.
"""
import copy
from pathlib import Path
import tempfile

from .cara_fast_capture_r2 import captured_file, file_sha
from .cara_fast_collection_r2 import freeze_selection
from .cara_fast_execution_r2 import require
from .cara_fast_post_r2 import accept_scores
from .cara_fast_spec_r1 import digest
from .cara_fast_terminal_r2 import released_terminal, record

ROOT = Path(__file__).resolve().parents[2]
HANDOFF_FILES = ('capture','settlement','manifest','score_capture','accepted_scores','frozen')
COMMON_SOURCES = (
    'src/wcomr/cara_fast_spec_r1.py','src/wcomr/cara_fast_binding_r2.py',
    'src/wcomr/cara_fast_requests_r1.py','src/wcomr/cara_fast_requests_r2.py',
    'src/wcomr/cara_fast_collection_r2.py','src/wcomr/cara_fast_terminal_r2.py',
    'src/wcomr/cara_fast_post_r2.py','src/wcomr/cara_fast_fidelity_r1.py',
    'src/wcomr/cara_fast_scoring_manifest_r2.py','src/wcomr/wc_time_collection_r1.py',
    'src/wcomr/full_sampling.py','src/wcomr/paper_latency_r1.py',
    'src/wcomr/policy_generator_r1/production_sampling.py',
    'src/wcomr/policy_generator_r1/p2_native_sampling.py')


def read_handoff(paths):
    require(set(paths) == set(HANDOFF_FILES), 'Six explicit original handoff files required')
    return dict(files={name:captured_file(Path(paths[name])) for name in HANDOFF_FILES})


def bind_handoff(card, package, *, host, gpu_uuid, source_root=ROOT):
    """Revalidate original bytes and decisions without overwriting the A freeze."""
    require(set(package['files']) == set(HANDOFF_FILES), 'Complete original A32 handoff required')
    capture,settlement,manifest,score_capture,accepted,frozen = (
        record(package,name) for name in HANDOFF_FILES)
    release = released_terminal(capture,card,settlement)
    require(release['technical_accepted'] is True and release['GPU_released'] is True,
            'Complete accepted, settled and released A32 required')
    require(release['host'] == host and release['gpu_uuid'] == gpu_uuid,
            'B36 must continue on the same physical GPU; migration needs a new scope')
    registration = record(capture,'registration')
    common = {name:file_sha(Path(source_root)/name) for name in COMMON_SOURCES}
    require(all(registration['payload_sha256'].get(name) == expected
                for name,expected in common.items()), 'Shared A32 sampling/acceptance source changed')
    require(score_capture['status'] == 'FAST_A32_SCORE_TERMINAL_CAPTURE',
            'Original stopped CPU scorer required')
    scores = record(score_capture,'scores')
    validated = accept_scores(capture,card,settlement,manifest,
        package['files']['manifest']['sha256'],scores,score_capture['execution'])
    require(accepted == validated, 'Accepted score receipt differs from original complete scores')
    # Recompute the original deterministic decision in an isolated temp file.
    # The actual A freeze is never created, edited or replaced here.
    with tempfile.TemporaryDirectory(prefix='cara-b36-verify-') as directory:
        expected = freeze_selection(card,record(capture,'collection'),release,validated,
                                    Path(directory)/'verification-only.json')
    require(frozen == expected, 'Immutable A32 selection differs from its complete accepted evidence')
    launch = record(capture,'launch')
    return dict(schema='CARA_FAST_B36_BOUND_HANDOFF_R1',scope_sha256=card['scope_sha256'],
        host=host,gpu_uuid=gpu_uuid,A_launch_id=launch['launch_id'],
        frozen_file_sha256=package['files']['frozen']['sha256'],frozen=copy.deepcopy(frozen),
        package_sha256=digest(package),common_source_sha256=common,
        CPU_fixture_only=scores.get('CPU_METADATA_FIXTURE_ONLY_NO_METRIC_EXECUTION') is True,
        phase_A_GPU_released=True,phase_A_cost_settled=True,phase_A_technical_accepted=True,
        A_collection=record(capture,'collection'),authorizes_phase_B=False,GPU_dispatch_ready=False)


def make_requests(binding, *, cpu_validation=False, production_context=None, **kwargs):
    from .cara_fast_requests_r2 import Requests
    require(kwargs['host'] == binding['host']
            and kwargs['card']['scope_sha256'] == binding['scope_sha256'], 'Bound host/scope differs')
    require(all(binding.get(key) is True for key in (
        'phase_A_GPU_released','phase_A_cost_settled','phase_A_technical_accepted')), 'Unaccepted A32 binding')
    if not cpu_validation:
        context = production_context or {}
        require(binding['CPU_fixture_only'] is False, 'CPU fixture cannot enter production')
        require(context.get('phase') == 'B' and context.get('physical_paths') == 36
                and context.get('new_B36_authorization') is True
                and context.get('frozen_file_sha256') == binding['frozen_file_sha256']
                and context.get('gpu_uuid') == binding['gpu_uuid']
                and context.get('launch_id') not in (None,'',binding['A_launch_id']),
                'Separate admitted B36 context bound to the immutable A freeze required')
    class BRequests(Requests):
        def __call__(self, slot, output, *, timing=None):
            require(slot.get('phase') == 'B', 'B36 adapter cannot execute an A slot')
            return super().__call__(slot,output,timing=timing)
    return BRequests(**kwargs,cpu_validation=cpu_validation,production_context=production_context,
                     frozen=binding['frozen'])


def check_complete_B(card, collection, frozen, *, cpu_validation):
    expected = [slot for slot in card['physical_matrix'] if slot['phase'] == 'B']
    require(len(expected) == 36 and collection['phase'] == 'B'
            and collection['scope_sha256'] == card['scope_sha256']
            and collection['status'] == 'TERMINAL', 'Complete registered B36 required')
    rows = collection['rows']
    require([row['slot'] for row in rows] == expected
            and all(row['status'] == 'COMPLETE' for row in rows), 'Complete ordered B36 denominator required')
    schedules = {schedule['requested_steps']:schedule['actual_updates'] for schedule in card['schedules']}
    for row in rows:
        slot,result = row['slot'],row['result']
        role = card['roles'][slot['role']]
        name = frozen['selected'][role['family']]['candidate'] if role['kind'] == 'selection' else slot['role']
        actual = card['roles'][name]
        require(result['slot_id'] == slot['id'] and result['role'] == slot['role']
                and result['concrete_role'] == name and result['scope_sha256'] == card['scope_sha256']
                and result['CPU_fixture'] is cpu_validation, 'Concrete B36 route identity differs')
        require(result['solver_steps'] == result['guided_pairs'] == schedules[actual['requested_steps']],
                'Selected solver/update count differs')
        require(result['audit_enabled'] is False
                and all(result[key] == 0 for key in (
                    'in_timing_guided_copies','in_timing_hashes','research_checkpoints')),
                'Registered B36 must remain free of research audit work')
        if slot['eligible_clean_time']:
            require(0 < result['T_DD'] <= result['T_request'], 'Complete clean dual clocks required')
    return digest(collection)


def execute_B36(adapter, binding, output, *, before_request, save):
    """Run the entire registered B phase once, using the original collector."""
    from .wc_time_collection_r1 import collect_phase
    require(adapter.host == binding['host'] and adapter.frozen == binding['frozen']
            and adapter.card['scope_sha256'] == binding['scope_sha256'], 'B36 adapter/handoff differs')
    require(not adapter.seen, 'Fresh B36 adapter required; no split or replay')
    slots = [slot for slot in adapter.card['physical_matrix'] if slot['phase'] == 'B']
    require(len(slots) == 36 and all(not slot['audit_enabled'] for slot in slots), 'Exact clean B36 matrix required')
    def before(slot):
        require(slot['phase'] == 'B' and slot in slots, 'B36 must not execute an A slot')
        before_request(slot)
    def no_A_diagnostics(rows):
        raise ValueError('A diagnostics must never rerun inside B36')
    state = collect_phase(adapter,'B',output,before_request=before,save=save,
                          after_diagnostics=no_A_diagnostics)
    check_complete_B(adapter.card,state,binding['frozen'],cpu_validation=adapter.cpu_validation)
    return state


def formal_sources(card, binding, complete_B, *, cpu_validation):
    """Resolve all32 logical sources without counting eight reused A paths twice."""
    check_complete_B(card,complete_B,binding['frozen'],cpu_validation=cpu_validation)
    rows = {row['slot']['id']:row for row in binding['A_collection']['rows']+complete_B['rows']}
    resolved = []
    for position in card['formal_matrix']:
        source = position['source']
        if 'slot_id' in source:
            slot_id = source['slot_id']
        else:
            candidate = binding['frozen']['selected'][source['family']]['candidate']
            slot_id = source['selected_candidate_slot_ids'][candidate]
        row = rows[slot_id]
        require(row['status'] == 'COMPLETE' and row['slot']['member'] == position['member'],
                'Complete matched formal source required')
        resolved.append(dict(member=position['member'],role=position['role'],slot_id=slot_id,
            source_phase=row['slot']['phase'],reused_from_A=row['slot']['phase'] == 'A',
            concrete_role=row['result']['concrete_role']))
    require(len(resolved) == 32 and sum(row['reused_from_A'] for row in resolved) == 8,
            'Registered32 logical positions and eight original A sources required')
    return resolved
