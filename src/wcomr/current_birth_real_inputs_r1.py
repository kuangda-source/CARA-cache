"""Read complete real inputs and matched Native provenance without installation."""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path

from .action_cost_ranking import BOUNDARY, build_ranking
from .cfg_guided_w1_deployment_production import bound_prior
from .real_working_epoch_parameters_r1 import build_parameters, digest, METHODS
from .source_aware_current_birth_control_r1 import CURRENT_BIRTH_RULE
from .source_aware_working_epoch_control_r2 import STRATEGIES

COST_PROOF = 'reports/wc_action_cost_real_r1_terminal_20261010_capture_and_independent_audit.json'
RANKING = 'reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json'
FLOORS = 'reports/wc_real_cost_creation_phase_prior_r1_bound_20261010.json'
PARENT_PROOF = 'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json'
SCRIPT_RESULT = 'reports/wc_current_birth_real_parameters_cpu_r1_results_20261010.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native(stage, proof, key):
    item = proof['files'][key]
    path = Path(stage) / item['local_path']
    if not path.resolve().is_relative_to((Path(stage) / 'reports').resolve()):
        raise ValueError('Native input metadata must remain within staged reports')
    packed = path.read_bytes()
    raw = gzip.decompress(packed)
    if (sha(path) != item['compressed_sha256'] or len(raw) != item['bytes']
            or hashlib.sha256(raw).hexdigest() != item['sha256']):
        raise ValueError('Original independently captured input metadata changed')
    return json.loads(raw)


def load(stage):
    stage = Path(stage)
    cost = json.loads((stage / COST_PROOF).read_text())
    parent = json.loads((stage / PARENT_PROOF).read_text())
    script = json.loads((stage / SCRIPT_RESULT).read_text())
    if (cost['GPU_exit_code'] != 0 or cost['CPU_exit_code'] != 0
            or not cost['independent_checks']['success']
            or not cost['independent_checks']['complete_8_parent_8_origin_6_mode_reconstruction']
            or parent['GPU_exit_code'] != 0 or parent['CPU_exit_code'] != 0
            or not parent['independent_checks']['success']
            or parent['independent_checks']['accepted_reference_slots'] != 4
            or script['status'] != 'CURRENT_BIRTH_REAL_PARAMETER_FULL64_SCRIPTED_CPU_PASS_NOT_COSMOS_ROLLOUT'
            or script['current_P_birth_rule'] != CURRENT_BIRTH_RULE
            or (script['complete_scripted_full36_paths'], script['complete_scripted_decisions'],
                script['healthy_state_roundtrips'], script['scripted_P_actions_not_real_P_calls']) != (64,2304,256,240)):
        raise ValueError('Complete accepted real inputs and current-rule script required')
    for name, value in script['source_sha256'].items():
        if sha(stage / name) != value:
            raise ValueError('Original scripted parameter source changed: ' + name)
    table = native(stage, cost, 'calibration_table')
    bound = json.loads((stage / RANKING).read_text())
    ranking = build_ranking(table['all_group_cost_seconds'], boundary=BOUNDARY,
        source_kind='INDEPENDENTLY_CAPTURED_REAL_FULL_ACTION_COST_CARD',
        source_sha256=cost['files']['calibration_table']['sha256'])
    if (json.loads(json.dumps(asdict(ranking))) != bound['ranking']
            or bound['source_proof_sha256'] != sha(stage / COST_PROOF)):
        raise ValueError('Complete 48-row / 144-timing ranking reconstruction differs')
    parent_config = native(stage, parent, 'config')
    calibration, threshold = bound_prior(parent_config, stage)
    floors = json.loads((stage / FLOORS).read_text())
    if floors['source_proof_sha256'] != sha(stage / COST_PROOF):
        raise ValueError('Creation floor belongs to another same-state source')
    specs = {}; bindings = []
    for strategy in STRATEGIES:
        specs[strategy], evidence = build_parameters(calibration, ranking, floors,
            strategy=strategy, floor_source_sha256=sha(stage / FLOORS))
        if evidence['all_eight_methods'] != next(b for b in script['parameter_bindings'] if b['strategy'] == strategy)['all_eight_methods']:
            raise ValueError('Real method parameters differ from the registered complete script')
        bindings.append({**evidence, 'current_P_birth_rule': CURRENT_BIRTH_RULE})
    runner = native(stage, parent, 'runner')
    references = runner['comparison']['references']
    requests = parent_config['preregistration']['requests']
    if len(references) != 4 or [r['sample_name'] for r in references] != [r['name'] for r in requests]:
        raise ValueError('Complete four Native reference slots required')
    for ref, request in zip(references, requests):
        if (ref['outcome'] != 'ACCEPTED' or ref['worldcache_enabled']
                or ref['CFG_calls'] != 72 or ref['solver_steps'] != 36
                or any(ref['request'][k] != value for k, value in request.items())
                or len(ref['guided_sha256']) != 36 or len(ref['prepared_input_calls']) != 1
                or not ref['official_forward_identity']):
            raise ValueError('Same original request, complete Native computation and prepared input required')
    evidence = {'current_P_birth_rule': CURRENT_BIRTH_RULE, 'methods': list(METHODS),
        'strategies': list(STRATEGIES), 'parameter_bindings': bindings,
        'actual_threshold_reconstruction': threshold, 'ranking_fingerprint': ranking.fingerprint,
        'complete_cost_rows': 48, 'timed_values': 144,
        'reference_source_revision': parent['source_revision'],
        'reference_model_context': runner['model_context'],
        'reference_project_input_sha256': parent_config['project_input_sha256'],
        'reference_runtime_source_sha256': parent_config['runtime_source_sha256'],
        'reference_sampling_protocol': parent_config['sampling_protocol'],
        'Native_artifacts': [r['artifact'] for r in references],
        'current_adaptive_trajectory_or_video_or_quality_claim': False,
        'model_or_controller_installed': False, 'GPU_submissions': 0,
        'ledger_written': False}
    evidence['binding_fingerprint'] = digest(evidence)
    return calibration, specs, references, parent_config, evidence
