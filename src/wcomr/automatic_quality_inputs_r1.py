"""Connect the accepted whole N07 capture to the preregistered N10 inputs.

This adapter reads metadata only. Actual weight/source checks, model CPU,
per-video decoding/scoring, cost and GPU admission remain scoring-run duties.
"""
from collections import Counter
import copy
import hashlib
import math
from pathlib import Path
import re
import subprocess

from .automatic_quality_r1 import DIMENSIONS, VBENCH_COMMIT, build_inputs, fingerprint, is_sha, sampling_spec
from .frozen_shared_inputs_r1 import SOURCE_FIELDS

PROTOCOL_ROLE = 'quality_measurement_protocol'
PROTOCOL_REF = 'manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'
PROTOCOL_STATUS = 'N10_MEASUREMENT_AND_CODE_PREREGISTERED_BEFORE_COMMON_TEST_RESOURCE_RUNTIME_AND_COST_PENDING'


def original_source_protocol(root, revision, raw):
    """Recover pre-run bytes from the original Git source, without any GPU/SSH."""
    if not isinstance(revision, str) or re.fullmatch('[0-9a-f]{40}', revision) is None:
        raise ValueError('The original real source commit is required for read-only protocol recovery')
    try:
        original = subprocess.check_output(['git', 'cat-file', 'blob', revision+':'+PROTOCOL_REF],
            cwd=Path(root), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise ValueError('Original source protocol unavailable; recover source evidence, do not regenerate videos') from error
    if original != raw:
        raise ValueError('Current protocol bytes differ from original pre-run Git source')
    return dict(method='ORIGINAL_SOURCE_GIT_BLOB', source_revision=revision, ref=PROTOCOL_REF,
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
        git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
        source_files_written=False, GPU_submissions=0, SSH_queries=0)


def prepare(value, accepted, protocol, evaluator_identity, *, capture_sha256, protocol_sha256, source_proof=None):
    """Keep every original formal row and bind the immutable pre-run protocol."""
    launch = value['launch']; config = value['config']; bound = value['bound_inputs']
    final = value['final']; registration = value['registration']
    if (value['status'] != 'N07_SHARED180_ORIGINAL_ONCE_CAPTURE' or value['mode'] != 'terminal'
            or accepted.get('terminal_receipt_audit_accepted') is not True
            or accepted.get('scientific_available_cohorts_with_registered_missingness') is not True
            or not is_sha(capture_sha256) or accepted['capture_sha256'] != capture_sha256
            or accepted['source_revision'] != launch['source_revision']
            or registration['source_revision'] != launch['source_revision']
            or value['config_sha256'] != launch['config_sha256']
            or value['registration_sha256'] != launch['registration_sha256']
            or value['bound_inputs_sha256'] != config['references']['bound_inputs']['sha256']
            or fingerprint(bound) != launch['bound_input_fingerprint']
            or final['bound_input_fingerprint'] != launch['bound_input_fingerprint']
            or final['source_revision'] != launch['source_revision']
            or final['config_sha256'] != value['config_sha256']
            or accepted['original_runner_paths'] != 180
            or accepted['scope_counts'] != config['scope_counts']
            or config['scope_counts']['total_paths'] != 180
            or config['scope_counts']['scientific_paths'] != 160
            or bound['planned_scope_counts'] != config['scope_counts']
            or set(value['payload_verified']) != set(registration['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())):
        raise ValueError('Use the accepted original whole N07 capture, original identities and all180 positions')
    binding = config['references'].get(PROTOCOL_ROLE)
    if not is_sha(protocol_sha256): raise ValueError('Original measurement protocol SHA required')
    if binding:
        if (binding['sha256'] != protocol_sha256
                or registration['payload_sha256'].get(binding['ref']) != protocol_sha256):
            raise ValueError('The declared original stage measurement protocol identity differs')
        protocol_ref, identity_source = binding['ref'], 'ORIGINAL_STAGE_REGISTRATION'
    else:
        # A bookkeeping omission never authorizes another generation. The
        # same bytes in the original launch commit are an independent pre-run
        # record; the CLI obtains this proof from Git, not a new server query.
        if (not source_proof or source_proof.get('method') != 'ORIGINAL_SOURCE_GIT_BLOB'
                or source_proof['source_revision'] != launch['source_revision']
                or source_proof['ref'] != PROTOCOL_REF or source_proof['sha256'] != protocol_sha256
                or source_proof['source_files_written'] or source_proof['GPU_submissions'] or source_proof['SSH_queries']):
            raise ValueError('Original stage or original Git source must already contain the measurement protocol')
        protocol_ref, identity_source = PROTOCOL_REF, 'ORIGINAL_SOURCE_GIT_BLOB_READONLY_RECOVERY'
    stamp, start = protocol.get('registered_unix'), launch.get('started_unix')
    if (protocol['status'] != PROTOCOL_STATUS or protocol['source_commit'] != VBENCH_COMMIT
            or tuple(protocol['dimensions']) != DIMENSIONS
            or protocol['scope_counts'] != dict(prompt_groups=8, seeds=[17, 43], methods=10,
                generation_positions=160, dimension_positions=960, new_generation_paths=0)
            or protocol['dimension_sampling'] != {d: sampling_spec(d) for d in DIMENSIONS}
            or protocol['final_N07_generation_outputs_seen']
            or protocol['final_N07_inputs_or_method_ids_selected']
            or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in (stamp, start))
            or not stamp < start):
        raise ValueError('Keep all six measurement definitions registered before original N07 dispatch')
    if (protocol['static_eligibility_policy']['missing_annotation_value'] is not False
            or protocol['static_eligibility_policy']['new_human_labeling_required']
            or protocol['static_eligibility_policy']['generated_video_based_selection_forbidden'] is not True):
        raise ValueError('Do not infer static eligibility from generated videos')
    # Original PAI text inputs contain exactly these eight fields and no static
    # annotation. Preserve all conditional slots as N/A; do not invent labels.
    sources = bound['source_bindings']
    if (len(sources) != 8 or len({r['name'] for r in sources}) != 8
            or any(set(r['original_fields']) != SOURCE_FIELDS for r in sources)
            or any('static_eligible' in c for c in bound['cases'])):
        raise ValueError('This bridge supports the registered original schema with no static annotations; register any future extension separately')
    cases = [dict(copy.deepcopy(c), static_eligible=False) for c in bound['cases']]
    case_index = {c['id']: c for c in cases}
    methods = bound['method_ids']
    if methods != config['method_ids'] or len(bound['argument_variants']) != 160:
        raise ValueError('Original common method selection and all160 arguments required')
    arguments = {(r['case_id'], r['method']): r['arguments'] for r in bound['argument_variants']}
    if set(arguments) != {(c['id'], m) for c in cases for m in methods}:
        raise ValueError('Original typed argument matrix is incomplete or duplicated')
    for (case_id, method), original in arguments.items():
        case = case_index[case_id]
        if (original['name'] != case_id or original['seed'] != case['seed']
                or original['prompt'] != case['prompt'] or original['guidance'] != 7
                or original['num_output_frames'] != 93 or original['resolution'] != '432,768'):
            raise ValueError('Quality metadata cannot substitute a filename prompt, another seed or another source request')
    rows = final['rows']; plan = bound['execution_plan']
    if len(rows) != 180 or [r['id'] for r in rows] != [r['id'] for r in plan]:
        raise ValueError('Retain all original180 rows in their original order')
    for row, planned in zip(rows, plan):
        if any(row[k] != planned[k] for k in ('id', 'section', 'case_id', 'method')):
            raise ValueError('A formal row or warm-up was reassigned')
    formal = [r for r in rows if r['section'] == 'TIMED']
    if len(formal) != 160 or len({(r['case_id'], r['method']) for r in formal}) != 160:
        raise ValueError('Exactly the original160 formal positions, including unavailable videos, are required')
    identity = copy.deepcopy(evaluator_identity)
    if identity.get('measurement_protocol_sha256', protocol_sha256) != protocol_sha256:
        raise ValueError('The declared evaluator belongs to another measurement protocol')
    identity['measurement_protocol_sha256'] = protocol_sha256
    bundle = build_inputs(cases, methods, formal, protocol['dimensions'], identity)
    return dict(status='N10_ACCEPTED_COMMON_OUTPUT_INPUTS_BOUND_NOT_METRIC_RUNTIME',
        source_N07_revision=launch['source_revision'], source_N07_capture_sha256=capture_sha256,
        source_N07_bound_inputs_fingerprint=launch['bound_input_fingerprint'],
        original_generation_status_counts=dict(Counter(r['status'] for r in formal)),
        measurement_protocol_ref=protocol_ref, measurement_protocol_sha256=protocol_sha256,
        measurement_protocol_identity_source=identity_source, protocol_source_proof=copy.deepcopy(source_proof),
        static_eligibility_source='ORIGINAL_EIGHT_FIELD_INPUT_SCHEMA_HAS_NO_STATIC_ANNOTATION',
        static_eligible_prompts=0, static_qualification_inferred_from_generated_videos=False,
        input_status_counts=dict(Counter(r['input_status'] for r in bundle['rows'])),
        input_bundle=bundle, actual_metric_model_CPU_accepted=False,
        scorer_resource_or_execution_authorization_granted=False,
        new_real_video_generations=0, real_quality_scores_generated=0,
        SSH_queries=0, GPU_submissions=0, server_ledger_written=False)
