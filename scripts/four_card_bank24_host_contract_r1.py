"""Strict host-boundary checks; accepted legacy CPU evidence stays a dependency."""
import gzip
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import tarfile

LIFECYCLE_SOURCE = '2bd41dc8fa19f42353e03a7c78b7264b4b2695c6'
ENTRY_SOURCE = 'c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9'
COUNTS = dict(requests=6, methods=3, formal_paths=18, full_warmup_paths=6,
              total_paths=24, loads=1, new_teacher_pairs=0, new_Native_formal=6,
              ordinary_pairs=864, ordinary_CFG_calls=1728)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def archive_members(raw, expected, limit=64 << 20):
    """No aliases, links, traversal, duplicates, extra files or partial scopes."""
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            require(member.isfile() and not path.is_absolute()
                    and '..' not in path.parts and str(path) == member.name,
                    'Only canonical relative regular files are allowed')
            require(member.name in expected and member.name not in files,
                    'Unregistered or duplicate closure member')
            total += member.size
            require(total <= limit, 'Closure byte limit exceeded')
            data = archive.extractfile(member).read()
            require(len(data) == member.size and digest(data) == expected[member.name],
                    'Incomplete or changed frozen closure member')
            files[member.name] = data
    require(set(files) == set(expected), 'Complete frozen closure required')
    return files


def legacy_bindings(capture, accepted, entry, gate, config):
    reg = capture['registration']
    er = entry['registration']
    require(reg['source_revision'] == LIFECYCLE_SOURCE
            and er['source_revision'] == ENTRY_SOURCE, 'Original scientific revisions required')
    require(len(reg['payload_sha256']) == 1789 and len(er['payload_sha256']) == 1772,
            'Original dependency denominators required')
    require(all(reg['payload_sha256'].get(n) == h for n, h in er['payload_sha256'].items()),
            'Accepted entry must remain byte-identical inside lifecycle closure')
    require(accepted['lifecycle_CPU_accepted'] is True
            and accepted['source_revision'] == LIFECYCLE_SOURCE
            and accepted['registration_sha256'] == capture['registration_sha256']
            and accepted['entry_registration_sha256'] == entry['registration_sha256']
            and accepted['scope_counts'] == config['scope_counts'] == COUNTS,
            'Original CPU evidence or whole-card scope changed')
    proof = entry['files']['proof']['data']
    require(proof['source_revision'] == ENTRY_SOURCE
            and proof['config_sha256'] == digest((json.dumps(config, indent=2)+'\n').encode()),
            'Frozen entry configuration binding required')
    require(gate['status'] == 'FOUR_CAL_GATE_FROZEN_BEFORE_DEV_BANK'
            and len(gate['CAL_rows']) == 4 and gate['DEV_used_for_fit'] is False
            and gate['direction'] == 'LARGER_Z_KEEP_D'
            and gate['equality'] == 'Z_GE_THRESHOLD_D', 'Original four-CAL gate required')
    mean = sum(row['delta_RMS'] for row in gate['CAL_rows'])/4
    ranks = sorted(row['delta_RMS']/(mean+1e-12) for row in gate['CAL_rows'])
    require(math.isclose(mean, gate['mu_RMS'], rel_tol=1e-12)
            and math.isclose((ranks[1]+ranks[2])/2, gate['threshold'], rel_tol=1e-12),
            'Original mean and median-rank gate required')
    require(len(config['requests']) == 6
            and len({r['name'] for r in config['requests']}) == 6, 'Six original DEV requests required')
    for request in config['requests']:
        require(all(request[k] == v for k, v in dict(seed=0, guidance=7, num_steps=35,
                num_output_frames=93, resolution='432,768', inference_type='text2world').items()),
                'Request profile changed')
    return dict(lifecycle_files=1789, entry_files=1772, scope_counts=COUNTS,
                original_CPU_reexecuted=False, original_numerical_paths_reexecuted=0)


def quote_inventory(config, matrix, historical_quote):
    require(config['scope_counts'] == COUNTS and len(matrix) == 24,
            'Every formal and warm position must be quoted')
    require(sum(r['section'] == 'WARMUP' for r in matrix) == 6
            and sum(r['section'] == 'TIMED' for r in matrix) == 18,
            'Warm or formal denominator changed')
    require(historical_quote['scope_counts'] == COUNTS, 'Historical quote scope differs')
    observed = sum(r['observer'] for r in matrix)
    a_positions = sum(config['plans'][r['method']].count('A') for r in matrix)
    require(observed == 14 and a_positions == 8, 'Observer or A work changed')
    return dict(status='FOUR_CARD_WHOLE_BANK24_COST_INVENTORY_AWAITING_REAL_HOST_TIMING',
        scope_counts=COUNTS, positions=matrix, observer_paths=observed, A_positions=a_positions,
        old_host_quote_preserved=historical_quote,
        new_host_terms_seconds={name: None for name in (
            'import_setup_and_CUDA_compatibility', 'model_and_guardrail_load',
            'all24_whole_guarded_requests_including6_Native_and6_warm',
            'all36_warm_guided_and_endpoint_copies', 'observer_copies_and_hashes',
            'deferred_tensor_RGB_and_video_writes', 'unattributed_and_exit_cleanup',
            'failure_and_termination_allowance')},
        post_CPU_full93_frame_LPIPS_required=True,
        post_CPU_outside_GPU_bill_requires_UUID_release=True,
        forecast_complete_GPUh=None, billed_limit_GPUh=None,
        original_host_forecast_is_new_host_measurement=False,
        quote_complete=False, GPU_dispatch_ready=False)
