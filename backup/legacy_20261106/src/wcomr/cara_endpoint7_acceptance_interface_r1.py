"""Read the original E1 artifacts through an explicit model-identity adapter.

The original launch bytes, registered source files and numerical reader stay
unchanged. Only the artifact reader's in-memory launch view gains the model
identity verified from its registered proposal and model asset. Financial
validation continues to read the untouched original launch.
"""
import copy
import json
from pathlib import Path
from types import FunctionType

from . import cara_s_endpoint_artifacts_r1 as artifacts
from . import cara_s_endpoint_pipeline_r1 as pipeline
from .cara_fast_b36_capture_r1 import file_sha
from .cara_s_endpoint_lifecycle_r1 import released_lifecycle
from .policy_price_terminal_r1 import record, require

SOURCE = 'src/wcomr/cara_endpoint7_acceptance_interface_r1.py'
ASSETS = 'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'


def model_identity(capture, proposal, assets, actual_model_sha256):
    """Join the real launch schema to independently registered model evidence."""
    launch = record(capture, 'launch')
    model = proposal['model_sha256']
    candidates = [row for row in assets['files']
                  if row['digest_kind'] == 'sha256' and row['digest'] == model
                  and 'models--nvidia--Cosmos-Predict2.5-2B/blobs/' in row['path']]
    require(len(candidates) == 1 and candidates[0]['bytes'] > 0,
            'One registered endpoint model asset required')
    require(actual_model_sha256 == model
            and launch.get('model_sha256', model) == model,
            'Actual or explicit launch model identity differs')
    require(launch['host'] == proposal['host'] == 'two_card'
            and launch['gpu_uuid'] == proposal['gpu_uuid'],
            'Original endpoint model host/GPU binding differs')
    return dict(model_sha256=model, registered_asset=copy.deepcopy(candidates[0]),
                original_launch_has_model_sha256='model_sha256' in launch,
                original_launch_sha256=capture['files']['launch']['sha256'])


def scoped_function(function, **bindings):
    """Reuse original bytecode with local dependencies; do not patch globals."""
    namespace = dict(function.__globals__, **bindings)
    result = FunctionType(function.__code__, namespace, function.__name__,
                          function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def released_artifacts(capture, expected_launch_sha256, settlement):
    release = released_lifecycle(capture, expected_launch_sha256, settlement)
    require(release['container_exit_success'] and release['GPU_released'],
            'Successful original settled GPU release required')
    launch = record(capture, 'launch')
    registration = record(capture, 'registration')
    stage = Path(launch['stage'])
    for name in (ASSETS, artifacts.PROPOSAL, artifacts.SOURCE, pipeline.SOURCE):
        require(file_sha(stage / name) == registration['payload_sha256'][name],
                'Original registered identity/reader source differs: ' + name)
    proposal = json.loads((stage / artifacts.PROPOSAL).read_text())
    assets = json.loads((stage / ASSETS).read_text())
    selected = [row for row in assets['files'] if row['digest'] == proposal['model_sha256']]
    require(len(selected) == 1, 'Unique original registered model required')
    relative = Path(selected[0]['path'])
    require(not relative.is_absolute() and '..' not in relative.parts,
            'Registered model path must stay inside the original project')
    model = stage.parents[1] / relative
    require(model.is_file() and model.stat().st_size == selected[0]['bytes'],
            'Original model asset size differs')
    identity = model_identity(capture, proposal, assets, file_sha(model))

    def artifact_record(original_capture, key):
        value = artifacts.record(original_capture, key)
        if key == 'launch':
            return dict(value, model_sha256=identity['model_sha256'])
        return value

    manifest_reader = scoped_function(artifacts.postrelease_manifest,
                                      record=artifact_record)
    original_pipeline = scoped_function(pipeline.released_artifacts,
                                        postrelease_manifest=manifest_reader)
    packet = original_pipeline(capture, expected_launch_sha256, settlement)
    packet['acceptance_interface_repair'] = dict(
        schema='CARA_E1_REGISTERED_MODEL_LAUNCH_VIEW_R1',
        adapter_source_sha256=file_sha(__file__), model_identity=identity,
        original_asset_spec_sha256=registration['payload_sha256'][ASSETS],
        original_proposal_sha256=registration['payload_sha256'][artifacts.PROPOSAL],
        original_reader_sha256=registration['payload_sha256'][artifacts.SOURCE],
        original_pipeline_sha256=registration['payload_sha256'][pipeline.SOURCE],
        original_launch_bytes_modified=False, original_sources_modified=False,
        numerical_reader_bytecode_unchanged=True)
    return packet
