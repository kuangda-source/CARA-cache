"""Bind unchanged Fidelity-v2 and accept the full eight-pair M1 denominator."""
import copy
import hashlib
import json
import math
from pathlib import Path

from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_read_write_artifacts_r1 import validate_manifest, SOURCE as ARTIFACT_SOURCE, PROTOCOL
from .gpu_budget_pool_v2 import finite
from .policy_price_terminal_r1 import require

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'src/wcomr/cara_read_write_scores_r1.py'
WORKER = 'scripts/score_cara_read_write_fidelity_r1.py'
SCORER_SOURCES = (WORKER, SOURCE, 'src/wcomr/cara_fast_fidelity_r1.py', ARTIFACT_SOURCE)
PRODUCTION_BOUND = dict(cpus=2, memory_GiB=8, wall_hours=2, max_pairs=8)
CPU_BOUND = dict(cpus=1, memory_GiB=8, wall_hours=.2, max_pairs=8)


def bind_scorer(packet, environment, *, cpu_validation=False):
    base = packet['manifest']
    validate_manifest(base)
    require(packet['status'] == 'COMPLETE14_FOUR_LATENT_RGB_CONTROLS_EIGHT_PAIRS_NOT_SCORED'
        and packet['CPU_fixture_only'] is base['CPU_fixture_only'] is cpu_validation
        and packet['release']['GPU_released'] is True and packet['release']['cost_settled'] is True
        and packet['release']['original_launch_sha256'] == base['original_launch_sha256']
        and packet['release']['collection_sha256'] == base['collection_sha256']
        and packet['reader_sha256'] == file_sha(ROOT/ARTIFACT_SOURCE),
        'Original complete14 released artifact packet and fixture mode required')
    shape = [93,64,64,3] if cpu_validation else [93,432,768,3]
    require(len(packet['decoded']) == 14 and all(v['shape'] == shape for v in packet['decoded'].values()),
        'Original complete14 full93 decoded geometry required')
    result = copy.deepcopy(base)
    result.update(scorer_source_sha256={p:file_sha(ROOT/p) for p in SCORER_SOURCES},
        artifact_packet_sha256=digest(packet), torch_home=str(environment['torch_home']),
        piq_site=str(environment['piq_site']), weights_sha256=copy.deepcopy(environment['weights_sha256']),
        CPU_bound=(CPU_BOUND if cpu_validation else PRODUCTION_BOUND).copy(), score_shape=shape,
        scoring_dispatch_allowed=False)
    return result


def validate_config(config, *, cpu_validation=False):
    require(config['CPU_fixture_only'] is cpu_validation
        and config['CPU_bound'] == (CPU_BOUND if cpu_validation else PRODUCTION_BOUND)
        and config['score_shape'] == ([93,64,64,3] if cpu_validation else [93,432,768,3])
        and config['scorer_source_sha256'] == {p:file_sha(ROOT/p) for p in SCORER_SOURCES}
        and config['protocol_sha256'] == digest(json.loads((ROOT/PROTOCOL).read_text())),
        'Original eight-pair Fidelity-v2 source/protocol/CPU boundary required')
    return validate_manifest(config)


def validate_rows(config, result, packet):
    ids = validate_manifest(config)
    require(result['status'] == 'COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
        and result['registered_pairs'] == ids and [r['id'] for r in result['rows']] == ids,
        'Complete ordered eight-pair score denominator required')
    for pair, row in zip(config['pairs'], result['rows']):
        require(row['candidate'] == pair['candidate'] and row['reference'] == pair['reference']
            and row['member'] == pair['candidate']['member'] and row['role'] == pair['candidate']['role']
            and row['status'] == 'COMPLETE' and row['frames'] == 93 and row['temporal_frame_pairs'] == 92
            and row['PTS_equal'] is True, 'Scored pair identity/full-frame/PTS differs')
        require(row['decoded_RGB_sha256'] == [packet['decoded'][pair[side]['slot_id']]['RGB_sha256']
            for side in ('candidate', 'reference')], 'Scored RGB differs from complete M1 artifacts')
        alex, ssim = row['Alex_frames'], row['SSIM_frames']
        require(len(alex) == len(ssim) == 93 and all(finite(v) for v in alex+ssim)
            and row['Alex'] == sum(alex)/93 and row['SSIM'] == sum(ssim)/93
            and row['Alex_worst'] == max(alex) and row['Alex_q95_higher'] == sorted(alex)[math.ceil(.95*92)]
            and row['Alex_first_worst_frame_zero_based'] == alex.index(max(alex)),
            'Original full93 finite frame curves/reductions required')
        mse = row['MSE_video']
        require(finite(mse) and mse >= 0, 'Finite nonnegative video MSE required')
        if mse == 0:
            require(row['PSNR_is_infinite'] is True and row['PSNR_video_dB'] == '+inf', 'Zero-MSE PSNR differs')
        else:
            require(row['PSNR_is_infinite'] is False and finite(row['PSNR_video_dB'])
                and math.isclose(row['PSNR_video_dB'], 10*math.log10(1/mse), rel_tol=1e-12, abs_tol=1e-10),
                'Whole-video PSNR reduction differs')
        for key in ('reference_temporal_L1', 'reference_gradient_L1', 'candidate_gradient_energy', 'reference_gradient_energy'):
            require(finite(row[key]) and row[key] >= 0, 'Invalid temporal/detail statistic: '+key)
        if row['reference_gradient_energy'] == 0:
            require(row['gradient_energy_ratio'] is None and row['gradient_ratio_status'] == 'ZERO_REFERENCE_ENERGY',
                'Zero-reference gradient status differs')
        else:
            require(row['gradient_ratio_status'] == 'FINITE' and finite(row['gradient_energy_ratio'])
                and math.isclose(row['gradient_energy_ratio'], row['candidate_gradient_energy']/row['reference_gradient_energy'],
                    rel_tol=1e-12, abs_tol=1e-12), 'Gradient energy ratio differs')
    return ids


def accept_scores(packet, config, manifest_sha256, result, execution, *, cpu_validation=False):
    require(config == bind_scorer(packet, {k:config[k] for k in ('torch_home', 'piq_site', 'weights_sha256')},
        cpu_validation=cpu_validation), 'Original M1 artifact/scorer configuration differs')
    require(manifest_sha256 == hashlib.sha256((json.dumps(config, indent=2, allow_nan=False)+'\n').encode()).hexdigest(),
        'Original canonical scoring manifest bytes differ')
    validate_config(config, cpu_validation=cpu_validation)
    require(result['manifest_sha256'] == manifest_sha256
        and result['analysis_scope_sha256'] == config['analysis_scope_sha256']
        and result['protocol_sha256'] == config['protocol_sha256']
        and result['worker_sha256'] == config['scorer_source_sha256'][WORKER]
        and result['CPU_fixture_only'] is cpu_validation and result['CUDA_initialized'] is False
        and result['GPU_submissions'] == 0 and result['source_actual_sha256'] == config['scorer_source_sha256'],
        'Original M1 scorer result/source differs')
    require(execution['manifest_sha256'] == manifest_sha256 and execution['result_sha256'] == digest(result)
        and execution['source_actual_sha256'] == config['scorer_source_sha256']
        and finite(execution['wall_seconds']) and 0 < execution['wall_seconds'] <= config['CPU_bound']['wall_hours']*3600,
        'Original bounded score execution identity differs')
    if cpu_validation:
        observation, identity = execution['original_observation'], result['original_identity']
        require(execution['kind'] == 'ACTUAL_CPU_FIXTURE_CHILD' and execution['exit_code'] == 0
            and execution['original_process_ended'] is True and execution['GPU_hidden'] is True
            and execution['original_identity'] == identity and observation['original_live'] is False,
            'Original bounded synthetic CPU child must exit')
        require(observation['status'] == 'ORIGINAL_NOT_LIVE'
            and observation['original_pid'] == identity['pid'] and observation['original_start_ticks'] == identity['start_ticks']
            and observation['observed_host_view'] == identity['host_view'], 'Original synthetic CPU handle identity differs')
    else:
        state, host = execution['container_state'], execution['host_config']
        require(state['Status'] == 'exited' and state['ExitCode'] == 0 and not state['Running']
            and state['Pid'] == 0 and not state['OOMKilled']
            and host['NanoCpus'] == 2*10**9 and host['Memory'] == host['MemorySwap'] == 8*2**30
            and host['CpusetCpus'] == '26,27' and host['DeviceRequests'] in (None, [])
            and host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] is True
            and execution['manifest_label_sha256'] == manifest_sha256 and execution['launch_id'] == config['launch_id'],
            'Original bounded GPU-hidden score container differs')
    ids = validate_rows(config, result, packet)
    return dict(status='ACCEPTED_COMPLETE8_READ_WRITE_SCORES', CPU_fixture_only=cpu_validation,
        scope_sha256=config['scope_sha256'], analysis_scope_sha256=config['scope_sha256'],
        protocol_sha256=config['protocol_sha256'], artifact_packet_sha256=digest(packet),
        manifest_sha256=manifest_sha256, new_result_sha256=digest(result), execution_sha256=digest(execution),
        new_scored_pairs=len(ids), reused_original_rows=0, rows=copy.deepcopy(result['rows']),
        independent_new_inputs=False, main_method_established=False, GPU_submissions=0, ledger_written=False)
