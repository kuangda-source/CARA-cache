"""Accept original file witnesses only after the bounded CPU container exits."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts, instant, require, result_sha

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'plans/cara_next_stage_20261028/sq/S_REUSE_CPU_R1.json'


def accept(capture, scope, revision):
    state, launch, result = capture['container_state'], capture['launch'], capture['result']
    require(state['Status'] == 'exited' and state['ExitCode'] == 0 and not state['Error']
            and not any(state[k] for k in ('Running', 'Paused', 'Restarting', 'OOMKilled', 'Dead')),
            'Original CPU container must exit cleanly before witness acceptance')
    stage = 'cara-sq-s-reuse-cpu-two-card-r2-20261029'
    require(capture['status'] == 'SQ_CPU_PREPARATION_CAPTURE'
            and launch['stage'].endswith('/'+stage) and launch['container'] == stage+'-cpu'
            and launch['source_revision'] == revision and capture['source_hashes_equal']
            and capture['runtime_hashes_equal'], 'Original CPU handle/source/runtime differs')
    require(capture['image'] == 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
            and capture['host_config'] == dict(DeviceRequests=None, NanoCpus=2_000_000_000,
                Memory=8*2**30, MemorySwap=8*2**30, CpusetCpus='4,5', NetworkMode='none', ReadonlyRootfs=True),
            'Original CPU runtime/resource boundary differs')
    cpu_mounts(capture, 'two_card')
    require(result is not None and result_sha(result) == capture['result_sha256']
            and result['status'] == 'S_LEGACY_WITNESS_CPU_BYTES_AND_SIGNATURES_VERIFIED'
            and result['scope'] == scope and result['profile'] == 'two_card', 'Bound original result differs')
    require(result['torch_version'] == '2.7.1+cu128' and result['actual_platform']['system'] == 'Linux'
            and result['unit_controls']['tests'] == 5 and result['unit_controls']['skipped'] == 0,
            'Complete actual Linux CPU bridge controls required')
    require(result['old_OFF_candidate_verified'] is True and result['checkpoint_identity_unchanged'] is True
            and result['checkpoint_SHA_recomputed'] is False
            and all(result[k] is False for k in ('new_ON_equivalence_accepted', 'actual_Cosmos_weights',
                                                'real_generated_video', 'CUDA_initialized'))
            and all(result[k] == 0 for k in ('S_labels_collected', 'GPU_submissions', 'new_GPUh', 'ledger_writes')),
            'Witness audit exceeded the admitted CPU evidence boundary')
    require(scope['original_request']['policy'] == scope['proposed_parent_policy']
            and scope['physical_S_matrix_frozen'] is False, 'Changed parent or premature physical matrix freeze')
    refs = scope['metadata_files']+[scope['artifact_checks'][k] for k in
        ('request_artifact', 'guided_artifact', 'final_latent_artifact', 'video_artifact')]
    require(set(result['files']) == {r['path'] for r in refs}, 'Original file denominator differs')
    for ref in refs:
        row = result['files'][ref['path']]
        require(row['sha256'] == ref['sha256'] and len(row['identity']) == 5
                and row['identity'][2] == ref['bytes'] and row['single_read_seconds'] >= 0,
                'Actual original file bytes/SHA/identity differ')
    bridges = result['signatures']['guided']+[result['signatures']['final_latent']]
    old = scope['artifact_checks']['guided_tensors']+[scope['artifact_checks']['latent_tensor']]
    require(len(bridges) == len(old) == 37, 'All36 guided plus final latent required')
    for bridge, reference in zip(bridges, old):
        new = bridge['S_typed_tensor']
        require(bridge['legacy_raw_bytes'] == reference
                and {k: new[k] for k in ('dtype', 'shape')} == {k: reference[k] for k in ('dtype', 'shape')}
                and re.fullmatch('[0-9a-f]{64}', new['sha256']) is not None
                and new['sha256'] != reference['sha256'], 'Complete legacy/new tensor identities required')
    require(result['decoded_RGB93'] == scope['decoded_RGB93']
            and result['decoded_RGB93']['frames'] == 93, 'Complete decoded original RGB differs')
    wall = (instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0 < result['CPU_wall_seconds'] <= wall <= 1810
            and 0 < result['peak_RSS_KiB']*1024 < 8*2**30, 'CPU worker/container resource interval differs')
    return dict(passed=True, status='S_RETAINED_OFF_WITNESS_BYTES_ACCEPTED_PENDING_REAL_ON_AND_CARD_BINDING',
        source_revision=revision, verified_files=len(refs), complete_guided_steps=36, tensor_bridges=37,
        decoded_frames=93, original_host='two_card', original_GPU_UUID=scope['original_GPU_UUID'],
        original_policy_fingerprint=scope['proposed_parent_policy']['fingerprint'],
        real_ON_equivalence_accepted=False, physical_S_matrix_frozen=False, S_real_labels=0,
        complete_S_GPU_card_accepted=False, clean_timing_reused=False, GPU_submissions=0, ledger_writes=0,
        resources=dict(container_wall_seconds=wall, worker_wall_seconds=result['CPU_wall_seconds'],
            worker_CPU_seconds=result['CPU_seconds'], reaped_child_CPU_seconds=result['reaped_child_CPU_seconds'],
            worker_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,
            allocated_vCPU_seconds_upper_bound=2*wall, parent_RSS_is_not_cgroup_peak=True,
            transport_staging_and_git_CPU_unmetered=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Retain the original independent witness acceptance')
    scope = json.loads((ROOT/SCOPE).read_text())
    capture = json.loads(args.capture.read_text())
    revision = subprocess.check_output(['git', 'rev-parse', args.source_revision+'^{commit}'], cwd=ROOT, text=True).strip()
    result = accept(capture, scope, revision)
    controls = {}
    mutations = {
        'running_body_is_not_terminal': lambda c: c['container_state'].update(Running=True),
        'changed_source': lambda c: c.update(source_hashes_equal=False),
        'GPU_device_request': lambda c: c['host_config'].update(DeviceRequests=[{'Count': 1}]),
        'missing_guided_step': lambda c: c['result']['signatures']['guided'].pop(),
        'changed_legacy_tensor': lambda c: c['result']['signatures']['guided'][0]['legacy_raw_bytes'].update(sha256='0'*64),
        'changed_RGB': lambda c: c['result']['decoded_RGB93'].update(sha256='0'*64),
        'missing_file': lambda c: c['result']['files'].pop(next(iter(c['result']['files']))),
        'premature_ON_acceptance': lambda c: c['result'].update(new_ON_equivalence_accepted=True),
    }
    for name, mutate in mutations.items():
        altered = copy.deepcopy(capture)
        mutate(altered)
        altered['result_sha256'] = result_sha(altered['result'])
        try:
            accept(altered, scope, revision)
        except ValueError:
            controls[name] = True
        else:
            raise ValueError('Independent audit accepted forged receipt: '+name)
    result.update(capture_ref=str(args.capture.relative_to(ROOT) if args.capture.is_absolute() else args.capture),
        capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(), rejection_controls=controls,
        scope_ref=SCOPE, scope_sha256=hashlib.sha256((ROOT/SCOPE).read_bytes()).hexdigest())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
