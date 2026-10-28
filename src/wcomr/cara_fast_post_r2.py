"""Exact A32 calibration pairs and independent full-frame score acceptance."""
import copy
import math
from pathlib import Path

from .cara_fast_execution_r2 import require
from .cara_fast_scoring_manifest_r2 import comparison_input_digest,validate_pair_identities
from .cara_fast_spec_r1 import digest
from .cara_fast_terminal_r2 import released_terminal
from .gpu_budget_pool_v2 import finite
from .policy_price_terminal_r1 import record

MODEL_SHA256='565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47'
SCORER_SOURCES=('scripts/score_cara_fast_fidelity_r1.py','src/wcomr/cara_fast_fidelity_r1.py',
                'src/wcomr/cara_fast_scoring_manifest_r2.py')


def calibration_manifest(capture,card,settlement):
    release=released_terminal(capture,card,settlement)
    require(release['technical_accepted'], 'Original A32 technical failure cannot enter scoring')
    state_sha=release['phase_state_sha256']
    launch=record(capture,'launch')
    require(release.get('phase')=='A' and release['scope_sha256']==card['scope_sha256']
            and release['phase_state_sha256']==state_sha
            and release['terminal_capture_sha256']==digest(capture)
            and all(release.get(key) is True for key in ('GPU_released','original_process_exited',
                                                        'cost_settled','technical_accepted')),
            'Accepted and centrally settled original A32 release required before scoring')
    require(all(release[key]==launch[key] for key in ('run_id','launch_id','host','gpu_uuid')),
            'Wrong released original launch')
    require(launch['model_sha256']==MODEL_SHA256, 'Frozen original 2B checkpoint identity required')
    registration=record(capture,'registration')
    sources={name:registration['payload_sha256'][name] for name in SCORER_SOURCES}
    overlay=Path(launch['stage']).parents[1]/'.sync'/('wc-time-score-CPU-'+launch['host']+'-r1-20261027')
    precision=digest(record(capture,'precision'))
    anchors={slot['member']:slot for slot in card['physical_matrix'] if slot['section']=='A_ANCHOR'}
    requests={row['name']:row for row in card['inputs']}

    def descriptor(slot):
        original=requests[slot['member']]
        request={**original,'seed':slot['seed'],'num_steps':card['roles'][slot['role']]['requested_steps']}
        artifact=capture['artifacts'][slot['id']]['video']
        argument_file=capture['artifacts'][slot['id']]['arguments']
        arguments=record(dict(files={'arguments':argument_file}),'arguments')
        return dict(artifact,slot_id=slot['id'],member=slot['member'],role=slot['role'],seed=slot['seed'],
            host=launch['host'],gpu_uuid=launch['gpu_uuid'],model_sha256=MODEL_SHA256,
            scope_sha256=card['scope_sha256'],precision=precision,
            comparison_input_sha256=comparison_input_digest(arguments),execution_request_sha256=digest(arguments),
            registered_request_sha256=digest({key:value for key,value in request.items() if key!='partition'}),
            argument_file_sha256=argument_file['sha256'],
            request_identity_kind='ACTUAL_SAVED_INFERENCE_ARGUMENTS_MATCH_REGISTERED_VARIANT')

    pairs=[dict(id=slot['id'],candidate=descriptor(slot),reference=descriptor(anchors[slot['member']]))
           for slot in card['physical_matrix'] if slot['section']=='A_CALIBRATION']
    require(len(pairs)==12 and {row['candidate']['member'] for row in pairs}==set(card['FIT']),
            'Exactly twelve FIT calibration pairs required')
    result=dict(schema='CARA_FAST_A32_SCORING_MANIFEST_R2',run_id=launch['run_id'],launch_id=launch['launch_id'],
        manifest_path=str(Path(launch['stage']).parents[1]/'outputs'/launch['run_id']/'A-score-CPU'/'manifest.json'),
        scope_sha256=card['scope_sha256'],protocol_sha256=card['fidelity_protocol_sha256'],
        phase_state_sha256=state_sha,release_sha256=digest(release),terminal_capture_sha256=digest(capture),
        CPU_bound=dict(cpus=2,memory_GiB=8,wall_hours=2,max_pairs=12),
        GPU_released=True,torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),
        weights_sha256={},scorer_source_sha256=sources,pairs=pairs,CHECK_accessed=False,authorizes_phase_B=False)
    validate_pair_identities(result)
    return result


def accept_scores(capture,card,settlement,manifest,manifest_file_sha256,result,execution):
    """Complete CLI output plus a stopped, GPU-hidden CPU execution is required."""
    require(manifest==calibration_manifest(capture,card,settlement), 'Scoring manifest differs from the original released A32')
    ids=validate_pair_identities(manifest)
    require(len(ids)==12 and manifest['CPU_bound']==dict(cpus=2,memory_GiB=8,wall_hours=2,max_pairs=12),
            'Original A32 scoring resource/denominator differs')
    state,config=execution['container_state'],execution['host_config']
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Running'] and not state['OOMKilled']
            and config['NanoCpus']==2*10**9 and config['Memory']==8*1024**3
            and config['DeviceRequests'] in (None,[]) and config['NetworkMode']=='none' and config['ReadonlyRootfs']
            and execution['manifest_sha256']==manifest_file_sha256
            and execution['manifest_label_sha256']==manifest_file_sha256,
            'Original bounded GPU-hidden scoring container did not exit cleanly')
    require(finite(execution['container_wall_seconds']) and 0<execution['container_wall_seconds']<=7200,
            'Original scoring container exceeded its registered two-hour resource bound')
    require(execution['source_actual_sha256']==manifest['scorer_source_sha256'], 'Scoring source changed')
    require(result['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
            and result['scope_sha256']==manifest['scope_sha256']
            and result['protocol_sha256']==manifest['protocol_sha256']
            and result['manifest_sha256']==manifest_file_sha256
            and result['worker_sha256']==manifest['scorer_source_sha256'][SCORER_SOURCES[0]]
            and result['CUDA_initialized'] is False and result['GPU_submissions']==0,
            'Bound original scoring CLI receipt differs')
    require(result['registered_pairs']==ids and [row['id'] for row in result['rows']]==ids,
            'Complete ordered calibration denominator required; no failed-subset selection')
    for pair,row in zip(manifest['pairs'],result['rows']):
        require(row['candidate']==pair['candidate'] and row['reference']==pair['reference']
                and row['status']=='COMPLETE' and row['frames']==93 and row['temporal_frame_pairs']==92
                and row['PTS_equal'] is True, 'Scored pair identity/frame/PTS differs')
        alex,ssim=row['Alex_frames'],row['SSIM_frames']
        require(len(alex)==len(ssim)==93 and all(finite(value) for value in alex+ssim),
                'Full finite frame curves required')
        require(row['Alex']==sum(alex)/93 and row['SSIM']==sum(ssim)/93
                and row['Alex_worst']==max(alex) and row['Alex_q95_higher']==sorted(alex)[math.ceil(.95*92)]
                and row['Alex_first_worst_frame_zero_based']==alex.index(max(alex)), 'Frame reductions differ')
        mse=row['MSE_video']
        require(finite(mse) and mse>=0, 'Finite nonnegative video MSE required')
        if mse==0:
            require(row['PSNR_is_infinite'] is True and row['PSNR_video_dB']=='+inf', 'Zero-MSE PSNR status differs')
        else:
            require(row['PSNR_is_infinite'] is False and finite(row['PSNR_video_dB'])
                    and math.isclose(row['PSNR_video_dB'],10*math.log10(1/mse),rel_tol=1e-12,abs_tol=1e-10),
                    'Whole-video PSNR reduction differs')
        for key in ('reference_temporal_L1','reference_gradient_L1','candidate_gradient_energy','reference_gradient_energy'):
            require(finite(row[key]) and row[key]>=0, 'Invalid temporal/detail statistic: '+key)
        if row['reference_gradient_energy']==0:
            require(row['gradient_energy_ratio'] is None and row['gradient_ratio_status']=='ZERO_REFERENCE_ENERGY',
                    'Zero-reference detail status differs')
        else:
            require(row['gradient_ratio_status']=='FINITE' and finite(row['gradient_energy_ratio'])
                    and math.isclose(row['gradient_energy_ratio'],
                        row['candidate_gradient_energy']/row['reference_gradient_energy'],rel_tol=1e-12,abs_tol=1e-12),
                    'Detail energy ratio differs')
        require(len(row['decoded_RGB_sha256'])==2 and all(isinstance(value,str) and len(value)==64
                and all(character in '0123456789abcdef' for character in value) for value in row['decoded_RGB_sha256']),
                'Full decoded RGB fingerprints required')
    return dict(status='ACCEPTED_COMPLETE',scope_sha256=manifest['scope_sha256'],
        protocol_sha256=manifest['protocol_sha256'],phase_state_sha256=manifest['phase_state_sha256'],
        manifest_sha256=manifest_file_sha256,result_sha256=digest(result),execution_sha256=digest(execution),
        rows=copy.deepcopy(result['rows']),CHECK_accessed=False,authorizes_phase_B=False,
        independent_new_inputs=False,endpoint_competitive_claim=False)
