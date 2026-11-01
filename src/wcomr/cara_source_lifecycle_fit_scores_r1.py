"""Complete two-FIT internal calibration scores while the P1 allocation is held.

This is a distinct prospective boundary. Existing released-card readers keep
their release/settlement requirements. An internal score is usable by the fixed
P1 algorithm only; scientific acceptance still requires the whole card's
original terminal, release and unique settlement. Metrics are never rerun at
that later boundary.
"""
import copy
import json
import math
from pathlib import Path
import re

from .cara_budget_search_r1 import FIT_MEMBERS, SCHEDULE_SHA256
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'src/wcomr/cara_source_lifecycle_fit_scores_r1.py'
WORKER = 'scripts/score_cara_source_lifecycle_fit_r1.py'
SOURCES = (SOURCE, WORKER, 'src/wcomr/cara_fast_fidelity_r1.py')
BOUND = dict(cpus=2, memory_GiB=8, wall_seconds=600, max_pairs=2)


def validate_packet(packet, *, cpu_validation=False, verify_files=True):
    if (packet.get('schema') != 'CARA_V1_INTERNAL_COMPLETE_FIT_ARTIFACTS_R1'
            or packet.get('purpose') != 'P1_INTERNAL_FIT_CALIBRATION'
            or packet.get('CPU_fixture_only') is not cpu_validation
            or tuple(packet['FIT_members']) != FIT_MEMBERS
            or packet['schedule_sha256'] != SCHEDULE_SHA256
            or not re.fullmatch(r'[0-9a-f]{40}', packet['source_revision'])
            or not re.fullmatch(r'[0-9a-f]{32}', packet['launch_id'])
            or not re.fullmatch(r'[0-9a-f]{64}', packet['context_sha256'])
            or not re.fullmatch(r'[0-9a-f]{64}', packet['candidate_id'])
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', packet['query_id'])
            or len(packet['pairs']) != 2):
        raise ValueError('Bound original P1 complete two-FIT calibration cohort required')
    shape = [93, 64, 64, 3] if cpu_validation else [93, 432, 768, 3]
    if packet['score_shape'] != shape or [p['member'] for p in packet['pairs']] != list(FIT_MEMBERS):
        raise ValueError('Registered full93 geometry and ordered complete FIT required')
    for pair in packet['pairs']:
        for side in ('candidate', 'reference'):
            descriptor = pair[side]
            if (descriptor['member'] != pair['member'] or descriptor['seed'] != 0
                    or descriptor['candidate_id'] != (packet['candidate_id'] if side == 'candidate' else 'NATIVE35')
                    or not Path(descriptor['path']).is_absolute()
                    or not Path(descriptor['proof_path']).is_absolute()
                    or any(not re.fullmatch(r'[0-9a-f]{64}', descriptor[k]) for k in ('sha256', 'proof_sha256'))):
                raise ValueError('Same-input/seed bound candidate and complete Native reference required')
            if verify_files:
                proof_file = Path(descriptor['proof_path'])
                if file_sha(proof_file) != descriptor['proof_sha256'] or file_sha(descriptor['path']) != descriptor['sha256']:
                    raise ValueError('Original complete request/video bytes changed')
                proof = json.loads(proof_file.read_bytes())
                if (proof['status'] != 'COMPLETE' or proof['CPU_fixture_only'] is not cpu_validation
                        or proof['context_sha256'] != packet['context_sha256']
                        or proof['source_revision'] != packet['source_revision']
                        or proof['launch_id'] != packet['launch_id']
                        or proof['member'] != pair['member'] or proof['seed'] != 0
                        or proof['candidate_id'] != descriptor['candidate_id']
                        or proof['solver_steps'] != 36 or proof['guided_pairs'] != 36
                        or proof['video'] != {k: descriptor[k] for k in ('path', 'sha256')}
                        or proof['actual_updates'] != 36 or proof['fallback_count'] != 0):
                    raise ValueError('Full original free-running36 request completion differs')


def bind_scorer(packet, environment, *, cpu_validation=False):
    validate_packet(packet, cpu_validation=cpu_validation)
    return dict(schema='CARA_V1_INTERNAL_FIT_SCORER_R1', packet=copy.deepcopy(packet),
        packet_sha256=digest(packet), CPU_fixture_only=cpu_validation,
        CPU_bound=BOUND.copy(), source_sha256={p: file_sha(ROOT/p) for p in SOURCES},
        torch_home=str(environment['torch_home']), piq_site=str(environment['piq_site']),
        weights_sha256=copy.deepcopy(environment['weights_sha256']),
        internal_calibration_only=True, released_scientific_acceptance=False)


def validate_config(config, *, cpu_validation=False):
    if (config['schema'] != 'CARA_V1_INTERNAL_FIT_SCORER_R1'
            or config['CPU_fixture_only'] is not cpu_validation or config['CPU_bound'] != BOUND
            or config['source_sha256'] != {p: file_sha(ROOT/p) for p in SOURCES}
            or config['packet_sha256'] != digest(config['packet'])
            or config['internal_calibration_only'] is not True
            or config['released_scientific_acceptance'] is not False):
        raise ValueError('Original source-bound internal calibration scorer required')
    validate_packet(config['packet'], cpu_validation=cpu_validation)


def accept_rows(config, result):
    """Validate full fidelity reductions and return only complete fixed FIT rows."""
    packet = config['packet']
    if (result['status'] != 'COMPLETE_INTERNAL_FIT_NOT_SCIENTIFIC_ACCEPTANCE'
            or result['packet_sha256'] != config['packet_sha256']
            or result['config_sha256'] != digest(config)
            or result['source_sha256'] != config['source_sha256']
            or result['CPU_fixture_only'] is not config['CPU_fixture_only']
            or result['CUDA_initialized'] is not False or result['GPU_submissions'] != 0
            or len(result['rows']) != 2):
        raise ValueError('Complete original CPU-only two-FIT score result required')
    rows = []
    for expected, row in zip(packet['pairs'], result['rows']):
        curve, ssim = row['Alex_frames'], row['SSIM_frames']
        if (row['member'] != expected['member'] or row['candidate'] != expected['candidate']
                or row['reference'] != expected['reference'] or row['status'] != 'COMPLETE'
                or row['PTS_equal'] is not True or row['frames'] != 93 or row['temporal_frame_pairs'] != 92
                or len(curve) != 93 or len(ssim) != 93
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in curve+ssim)
                or any(v < 0 for v in curve) or row['Alex'] != sum(curve)/93
                or row['SSIM'] != sum(ssim)/93 or row['Alex_worst'] != max(curve)
                or row['Alex_q95_higher'] != sorted(curve)[math.ceil(.95*92)]
                or row['Alex_first_worst_frame_zero_based'] != curve.index(max(curve))):
            raise ValueError('Complete original93-frame metrics and bound input identities required')
        if (len(row['decoded_RGB_sha256']) != 2
                or any(not re.fullmatch(r'[0-9a-f]{64}', h) for h in row['decoded_RGB_sha256'])):
            raise ValueError('Original two decoded complete RGB hashes required')
        mse = row['MSE_video']
        if type(mse) not in (int, float) or not math.isfinite(mse) or mse < 0:
            raise ValueError('Finite nonnegative full-video MSE required')
        if mse == 0:
            if row['PSNR_is_infinite'] is not True or row['PSNR_video_dB'] != '+inf':
                raise ValueError('Zero-MSE infinite PSNR identity differs')
        elif (row['PSNR_is_infinite'] is not False
                or not math.isclose(row['PSNR_video_dB'], 10*math.log10(1/mse), rel_tol=1e-12)):
            raise ValueError('Whole-video PSNR differs')
        for key in ('reference_temporal_L1', 'reference_gradient_L1', 'candidate_gradient_energy', 'reference_gradient_energy'):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]) or row[key] < 0:
                raise ValueError('Finite original temporal and gradient statistics required')
        energy = row['reference_gradient_energy']
        if energy == 0:
            if row['gradient_energy_ratio'] is not None or row['gradient_ratio_status'] != 'ZERO_REFERENCE_ENERGY':
                raise ValueError('Original undefined zero-reference gradient identity differs')
        elif (row['gradient_ratio_status'] != 'FINITE' or not math.isclose(
                row['gradient_energy_ratio'], row['candidate_gradient_energy']/energy, rel_tol=1e-12)):
            raise ValueError('Original gradient ratio differs')
        rows.append(dict(member=row['member'], candidate_id=packet['candidate_id'], status='COMPLETE',
                         Alex_curve=copy.deepcopy(curve)))
    return rows


def accept_internal_scores(config, result, execution, *, cpu_validation=False):
    validate_config(config, cpu_validation=cpu_validation)
    rows = accept_rows(config, result)
    if (execution['config_sha256'] != digest(config) or execution['result_sha256'] != digest(result)
            or execution['original_process_ended'] is not True or execution['exit_code'] != 0
            or execution['GPU_hidden'] is not True or execution['source_sha256'] != config['source_sha256']
            or execution['original_identity'] != result['original_identity']
            or type(execution['wall_seconds']) not in (int, float)
            or not 0 < execution['wall_seconds'] <= BOUND['wall_seconds']):
        raise ValueError('Original terminated bounded internal score process required')
    if not cpu_validation:
        host, state = execution['host_config'], execution['container_state']
        if (state['Status'] != 'exited' or state['ExitCode'] != state['Pid'] or state['Pid'] != 0
                or any(state[k] for k in ('Running', 'Paused', 'Restarting', 'OOMKilled', 'Dead'))
                or host['NanoCpus'] != 2*10**9 or host['Memory'] != 8*2**30
                or host['MemorySwap'] != host['Memory'] or host['CpusetCpus'] != '26,27'
                or host['DeviceRequests'] not in (None, []) or host['NetworkMode'] != 'none'
                or host['ReadonlyRootfs'] is not True):
            raise ValueError('Original two-core8GiB/no-swap/network/GPU-hidden score container required')
    return dict(schema='CARA_V1_INTERNAL_COMPLETE_FIT_SCORES_R1',
        status='ACCEPTED_INTERNAL_CALIBRATION_ONLY', CPU_fixture_only=cpu_validation,
        packet_sha256=config['packet_sha256'], config_sha256=digest(config),
        result_sha256=digest(result), execution_sha256=digest(execution), rows=rows,
        full_fidelity_rows=copy.deepcopy(result['rows']), whole_card_scientific_accepted=False,
        requires_original_terminal_release_and_settlement=True, metrics_recomputed=0,
        GPU_submissions=0, ledger_written=False)
