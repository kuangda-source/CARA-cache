"""The registered 32 logical B positions, retaining eight original A sources."""
import copy
import math
from pathlib import Path

from .cara_fast_b36_r1 import formal_sources
from .cara_fast_b36_terminal_r1 import bound_A, released_terminal, record
from .cara_fast_execution_r2 import require
from .cara_fast_post_r2 import SCORER_SOURCES as ORIGINAL_SCORER_SOURCES
from .cara_fast_scoring_manifest_r2 import comparison_input_digest, validate_pair_identities
from .cara_fast_spec_r1 import digest
from .gpu_budget_pool_v2 import finite

SCORER_SOURCES=(*ORIGINAL_SCORER_SOURCES,'scripts/score_cara_fast_b36_fidelity_r1.py')


def formal_manifest(capture,card,settlement):
    release=released_terminal(capture,card,settlement)
    require(release['technical_accepted'], 'An incomplete or failed B36 cannot enter scoring')
    bound=bound_A(capture,card)
    launch=record(capture,'launch')
    original=record(capture['A32_handoff'],'capture')
    sources=formal_sources(card,bound,record(capture,'collection'),cpu_validation=False)
    rows={row['slot']['id']:row for row in bound['A_collection']['rows']+record(capture,'collection')['rows']}
    requests={row['name']:row for row in card['inputs']}
    precision=digest(record(capture,'precision'))

    def descriptor(position):
        row=rows[position['slot_id']]
        slot=row['slot']
        origin=original if position['reused_from_A'] else capture
        saved=origin['artifacts'][slot['id']]
        arguments=record(dict(files={'arguments':saved['arguments']}),'arguments')
        request={key:value for key,value in requests[slot['member']].items() if key!='partition'}
        request.update(seed=slot['seed'],num_steps=card['roles'][row['result']['concrete_role']]['requested_steps'])
        return dict(saved['video'],slot_id=slot['id'],member=slot['member'],role=position['role'],
            concrete_role=row['result']['concrete_role'],seed=slot['seed'],host=launch['host'],
            gpu_uuid=launch['gpu_uuid'],model_sha256=launch['model_sha256'],scope_sha256=card['scope_sha256'],
            precision=precision,source_phase=slot['phase'],reused_from_A=position['reused_from_A'],
            comparison_input_sha256=comparison_input_digest(arguments),execution_request_sha256=digest(arguments),
            registered_request_sha256=digest(request),argument_file_sha256=saved['arguments']['sha256'],
            request_identity_kind='ACTUAL_SAVED_INFERENCE_ARGUMENTS_MATCH_REGISTERED_VARIANT')

    anchors={position['member']:position for position in sources if position['role']=='NATIVE35'}
    pairs=[dict(id='B36_FORMAL_'+str(index+1).zfill(3),candidate=descriptor(position),
                reference=descriptor(anchors[position['member']])) for index,position in enumerate(sources)]
    require(len(pairs)==32 and len(anchors)==4 and sum(p['candidate']['reused_from_A'] for p in pairs)==8,
            'Exact32 logical positions, four Native self checks and eight A sources required')
    registration=record(capture,'registration')
    overlay=Path(launch['stage']).parents[1]/'.sync'/('wc-time-score-CPU-'+launch['host']+'-r1-20261027')
    manifest=dict(schema='CARA_FAST_B36_SCORING_MANIFEST_R1',run_id=launch['run_id'],launch_id=launch['launch_id'],
        manifest_path=str(Path(launch['stage']).parents[1]/'outputs'/launch['run_id']/'B-score-CPU'/'manifest.json'),
        scope_sha256=card['scope_sha256'],protocol_sha256=card['fidelity_protocol_sha256'],
        phase_state_sha256=release['phase_state_sha256'],release_sha256=digest(release),
        terminal_capture_sha256=digest(capture),A_launch_id=bound['A_launch_id'],
        A_output_root=str(Path(record(original,'launch')['stage']).parents[1]/'outputs'/record(original,'launch')['run_id']),
        frozen_file_sha256=bound['frozen_file_sha256'],reused_A_sources=8,formal_logical_positions=32,
        nonself_pairs=28,native_self_checks=4,CPU_bound=dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=32),
        GPU_released=True,torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),weights_sha256={},
        scorer_source_sha256={name:registration['payload_sha256'][name] for name in SCORER_SOURCES},
        pairs=pairs,CHECK_accessed=True,authorizes_replay=False,independent_new_inputs=False,
        reused_A_metric_pairs={pair['id']:pair['candidate']['slot_id'] for pair in pairs
            if pair['candidate']['reused_from_A'] and pair['candidate']['role']!='NATIVE35'},
        A_accepted_scores=copy.deepcopy(capture['A32_handoff']['files']['accepted_scores']),
        frozen_baseline_time_match={name:value['time_match'] for name,value in bound['frozen']['selected'].items()})
    require(len(manifest['reused_A_metric_pairs'])==6, 'Exactly six previously accepted A metrics must be reused')
    validate_pair_identities(manifest)
    return manifest


def new_pairs_manifest(manifest):
    result=copy.deepcopy(manifest)
    result['pairs']=[pair for pair in manifest['pairs'] if pair['id'] not in manifest['reused_A_metric_pairs']]
    require(len(result['pairs'])==26, 'Only26 new metric pairs; never rescore the six selected A pairs')
    return result


def assemble_scores(manifest,manifest_sha256,new_manifest,new_manifest_sha256,new_scores,new_scores_sha256):
    """Project only row identities; reused A metric values/curves remain byte-derived."""
    require(new_manifest==new_pairs_manifest(manifest), 'New scorer must see exactly the26 fresh pairs')
    ids=validate_pair_identities(new_manifest)
    require(new_scores['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
            and new_scores['registered_pairs']==ids and [row['id'] for row in new_scores['rows']]==ids
            and new_scores['manifest_sha256']==new_manifest_sha256
            and new_scores['scope_sha256']==manifest['scope_sha256']
            and new_scores['protocol_sha256']==manifest['protocol_sha256']
            and new_scores['worker_sha256']==manifest['scorer_source_sha256'][SCORER_SOURCES[0]]
            and new_scores['GPU_submissions']==0 and new_scores['CUDA_initialized'] is False,
            'Original scorer complete26 output/source differs')
    accepted=record(dict(files={'accepted':manifest['A_accepted_scores']}),'accepted')
    require(accepted['status']=='ACCEPTED_COMPLETE', 'Original complete accepted A metrics required')
    old={row['id']:row for row in accepted['rows']}
    fresh={row['id']:row for row in new_scores['rows']}
    rows=[]
    for pair in manifest['pairs']:
        key=pair['id']
        if key not in manifest['reused_A_metric_pairs']:
            require(fresh[key]['candidate']==pair['candidate'] and fresh[key]['reference']==pair['reference'],
                    'New score identity differs')
            rows.append(copy.deepcopy(fresh[key]))
            continue
        original_id=manifest['reused_A_metric_pairs'][key]
        row=old[original_id]
        for side in ('candidate','reference'):
            for field in ('path','sha256','bytes','slot_id','member','seed','host','gpu_uuid','model_sha256',
                          'scope_sha256','precision','comparison_input_sha256','execution_request_sha256','argument_file_sha256'):
                require(row[side][field]==pair[side][field], 'Reused A metric source differs: '+field)
        projected=copy.deepcopy(row)
        projected.update(id=key,member=pair['candidate']['member'],role=pair['candidate']['role'],
                         candidate=copy.deepcopy(pair['candidate']),reference=copy.deepcopy(pair['reference']),
                         reused_A_score_id=original_id,A_accepted_scores_sha256=manifest['A_accepted_scores']['sha256'])
        rows.append(projected)
    result=copy.deepcopy(new_scores)
    result.update(manifest_sha256=manifest_sha256,registered_pairs=validate_pair_identities(manifest),rows=rows,
        assembly_worker_sha256=manifest['scorer_source_sha256'][SCORER_SOURCES[-1]],
        new_manifest_sha256=new_manifest_sha256,new_scores_sha256=new_scores_sha256,
        newly_scored_pairs=26,reused_A_metric_pairs=copy.deepcopy(manifest['reused_A_metric_pairs']),
        A_accepted_scores_sha256=manifest['A_accepted_scores']['sha256'])
    return result


def accept_scores(capture,card,settlement,manifest,manifest_file_sha256,result,execution,*,new_manifest,new_scores):
    """The unchanged scorer's full curves and stopped CPU container are required."""
    require(manifest==formal_manifest(capture,card,settlement), 'Original B formal manifest differs')
    ids=validate_pair_identities(manifest)
    require(len(ids)==32 and manifest['CPU_bound']==dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=32),
            'Original B scoring resource/denominator differs')
    expected=assemble_scores(manifest,manifest_file_sha256,
        record(dict(files={'new_manifest':new_manifest}),'new_manifest'),new_manifest['sha256'],
        record(dict(files={'new_scores':new_scores}),'new_scores'),new_scores['sha256'])
    require(result==expected, 'Original26 output and six unchanged A score rows must form the complete32')
    state,config=execution['container_state'],execution['host_config']
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Running'] and not state['OOMKilled']
            and config['NanoCpus']==2*10**9 and config['Memory']==8*1024**3
            and config['MemorySwap']==8*1024**3 and config['CpusetCpus']=='26,27'
            and config['DeviceRequests'] in (None,[]) and config['NetworkMode']=='none' and config['ReadonlyRootfs']
            and execution['manifest_sha256']==manifest_file_sha256
            and execution['manifest_label_sha256']==manifest_file_sha256,
            'Original bounded GPU-hidden scoring container did not exit cleanly')
    require(finite(execution['container_wall_seconds']) and 0<execution['container_wall_seconds']<=14400,
            'Original scoring container exceeded its registered four-hour resource bound')
    require(execution['source_actual_sha256']==manifest['scorer_source_sha256'], 'Scoring source changed')
    require(result['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
            and result['scope_sha256']==manifest['scope_sha256']
            and result['protocol_sha256']==manifest['protocol_sha256']
            and result['manifest_sha256']==manifest_file_sha256
            and result['worker_sha256']==manifest['scorer_source_sha256'][SCORER_SOURCES[0]]
            and result['CUDA_initialized'] is False and result['GPU_submissions']==0,
            'Bound original scoring CLI receipt differs')
    require(result['registered_pairs']==ids and [row['id'] for row in result['rows']]==ids,
            'Complete ordered formal denominator required; no failed-subset selection')
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
        if pair['candidate']['role']=='NATIVE35':
            require(pair['candidate']==pair['reference'] and mse==0 and row['Alex']==0
                    and row['decoded_RGB_sha256'][0]==row['decoded_RGB_sha256'][1]
                    and math.isclose(row['SSIM'],1.,abs_tol=1e-6), 'Native self-check differs')
        require(len(row['decoded_RGB_sha256'])==2 and all(isinstance(value,str) and len(value)==64
                and all(character in '0123456789abcdef' for character in value) for value in row['decoded_RGB_sha256']),
                'Full decoded RGB fingerprints required')
    return dict(status='ACCEPTED_COMPLETE',scope_sha256=manifest['scope_sha256'],
        protocol_sha256=manifest['protocol_sha256'],phase_state_sha256=manifest['phase_state_sha256'],
        manifest_sha256=manifest_file_sha256,result_sha256=digest(result),execution_sha256=digest(execution),
        rows=copy.deepcopy(result['rows']),CHECK_accessed=True,authorizes_replay=False,
        formal_logical_positions=32,nonself_pairs=28,native_self_checks=4,reused_A_sources=8,
        A_launch_id=manifest['A_launch_id'],frozen_file_sha256=manifest['frozen_file_sha256'],
        frozen_baseline_time_match=copy.deepcopy(manifest['frozen_baseline_time_match']),
        independent_new_inputs=False,endpoint_competitive_claim=False)
