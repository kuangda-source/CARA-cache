"""Bind unchanged Fidelity-v2 computation and accept every new endpoint pair."""
import copy
import hashlib
import json
import math
from pathlib import Path

from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_scoring_manifest_r1 import validate_pair_identities
from .gpu_budget_pool_v2 import finite
from .policy_price_terminal_r1 import require

ROOT=Path(__file__).resolve().parents[2]
SOURCE='src/wcomr/cara_s_endpoint_scores_r1.py'
WORKER='scripts/score_cara_s_endpoint_fidelity_r1.py'
SCORER_SOURCES=(WORKER,SOURCE,'src/wcomr/cara_fast_fidelity_r1.py',
                'src/wcomr/cara_s_endpoint_scoring_manifest_r1.py')
PRODUCTION_BOUND=dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=12)
CPU_BOUND=dict(cpus=1,memory_GiB=8,wall_hours=.2,max_pairs=12)

def scorer_bound(manifest,cpu_validation):
    value=(CPU_BOUND if cpu_validation else PRODUCTION_BOUND).copy()
    if manifest.get('endpoint7'):
        value['max_pairs']=16
        if not cpu_validation:value['wall_hours']=2
    return value


def bind_scorer(packet,environment,*,cpu_validation=False):
    base=packet['manifest'];validate_pair_identities(base)
    require(packet['status']=='COMPLETE_ENDPOINT_ARTIFACTS_AND_CROSS_SCOPE_MANIFEST_NOT_SCORED'
            and packet['CPU_fixture_only'] is base['CPU_fixture_only'] is cpu_validation
            and base['release_sha256']==digest(packet['release'])
            and base['decoded_identity_sha256']==digest(packet['decoded'])
            and base['artifact_sha256']==digest(packet['artifacts'])
            and packet['release']['collection_sha256']==base['collection_sha256']
            and packet['release']['artifact_identity_accepted'] is False,
            'Original full artifact packet and fixture mode required')
    shape=[93,64,64,3] if cpu_validation else [93,432,768,3]
    require(packet['reader_sha256']==file_sha(ROOT/'src/wcomr/cara_s_endpoint_artifacts_r1.py')
            and packet['manifest_validator_sha256']==file_sha(ROOT/'src/wcomr/cara_s_endpoint_scoring_manifest_r1.py')
            and all(row['shape']==shape for row in packet['decoded'].values()),
            'Original artifact reader and scorer geometry required')
    result=copy.deepcopy(base)
    result.update(scorer_source_sha256={p:file_sha(ROOT/p) for p in SCORER_SOURCES},
        artifact_packet_sha256=digest(packet),torch_home=str(environment['torch_home']),
        piq_site=str(environment['piq_site']),weights_sha256=copy.deepcopy(environment['weights_sha256']),
        CPU_bound=scorer_bound(base,cpu_validation),
        score_shape=shape,
        scoring_dispatch_allowed=False)
    return result


def validate_config(config,*,cpu_validation=False):
    require(config['CPU_fixture_only'] is cpu_validation
            and config['CPU_bound']==scorer_bound(config,cpu_validation)
            and config['score_shape']==([93,64,64,3] if cpu_validation else [93,432,768,3]),
            'Exact production or explicit synthetic CPU scorer boundary required')
    require(config['scorer_source_sha256']=={p:file_sha(ROOT/p) for p in SCORER_SOURCES},
            'Original scorer source changed')
    protocol=ROOT/'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'
    require(config['protocol_sha256']==digest(json.loads(protocol.read_text())),
            'Original Fidelity-v2 protocol required')
    return validate_pair_identities(config)


def validate_rows(config,result,packet):
    ids=validate_pair_identities(config)
    require(result['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED'
            and result['registered_pairs']==ids and [r['id'] for r in result['rows']]==ids,
            'Complete ordered new score denominator required')
    native_rgb={c['control']['member']:c['RGB_sha256'] for c in config['identity_controls']
        if c['control']['kind']=='FRESH_VS_ORIGINAL_DECODED_RGB' and c['control']['role']=='NATIVE35'}
    for pair,row in zip(config['pairs'],result['rows']):
        require(row['candidate']==pair['candidate'] and row['reference']==pair['reference']
                and row['member']==pair['candidate']['member'] and row['role']==pair['candidate']['role']
                and row['status']=='COMPLETE' and row['frames']==93 and row['temporal_frame_pairs']==92
                and row['PTS_equal'] is True,'Scored pair identity/full-frame/PTS differs')
        require(row['decoded_RGB_sha256']==[packet['decoded'][pair['candidate']['slot_id']]['RGB_sha256'],
                native_rgb[pair['reference']['member']]],'Scored decoded RGB differs from accepted full artifacts')
        alex,ssim=row['Alex_frames'],row['SSIM_frames']
        require(len(alex)==len(ssim)==93 and all(finite(v) for v in alex+ssim),'Full finite frame curves required')
        require(row['Alex']==sum(alex)/93 and row['SSIM']==sum(ssim)/93
                and row['Alex_worst']==max(alex) and row['Alex_q95_higher']==sorted(alex)[math.ceil(.95*92)]
                and row['Alex_first_worst_frame_zero_based']==alex.index(max(alex)),'Full-frame reductions differ')
        mse=row['MSE_video'];require(finite(mse) and mse>=0,'Finite nonnegative video MSE required')
        if mse==0:
            require(row['PSNR_is_infinite'] is True and row['PSNR_video_dB']=='+inf','Zero-MSE PSNR status differs')
        else:
            require(row['PSNR_is_infinite'] is False and finite(row['PSNR_video_dB'])
                    and math.isclose(row['PSNR_video_dB'],10*math.log10(1/mse),rel_tol=1e-12,abs_tol=1e-10),
                    'Whole-video PSNR reduction differs')
        for key in ('reference_temporal_L1','reference_gradient_L1','candidate_gradient_energy','reference_gradient_energy'):
            require(finite(row[key]) and row[key]>=0,'Invalid temporal/detail statistic: '+key)
        if row['reference_gradient_energy']==0:
            require(row['gradient_energy_ratio'] is None and row['gradient_ratio_status']=='ZERO_REFERENCE_ENERGY',
                    'Zero-reference gradient status differs')
        else:
            require(row['gradient_ratio_status']=='FINITE' and finite(row['gradient_energy_ratio'])
                    and math.isclose(row['gradient_energy_ratio'],row['candidate_gradient_energy']/row['reference_gradient_energy'],
                                     rel_tol=1e-12,abs_tol=1e-12),'Gradient energy ratio differs')
    return ids


def accept_scores(packet,config,manifest_sha256,result,execution,*,cpu_validation=False):
    expected=bind_scorer(packet,{k:config[k] for k in ('torch_home','piq_site','weights_sha256')},cpu_validation=cpu_validation)
    require(config==expected,'Scoring configuration differs from complete original artifact packet')
    require(manifest_sha256==hashlib.sha256((json.dumps(config,indent=2,allow_nan=False)+'\n').encode()).hexdigest(),
            'Original canonical scoring manifest bytes differ')
    validate_config(config,cpu_validation=cpu_validation)
    require(result['manifest_sha256']==manifest_sha256
            and result['analysis_scope_sha256']==config['analysis_scope_sha256']
            and result['protocol_sha256']==config['protocol_sha256']
            and result['worker_sha256']==config['scorer_source_sha256'][WORKER]
            and result['CPU_fixture_only'] is cpu_validation and result['CUDA_initialized'] is False
            and result['GPU_submissions']==0 and result['source_actual_sha256']==config['scorer_source_sha256'],
            'Original scorer result/source differs')
    require(execution['manifest_sha256']==manifest_sha256
            and execution['result_sha256']==digest(result)
            and execution['source_actual_sha256']==config['scorer_source_sha256']
            and finite(execution['wall_seconds']) and 0<execution['wall_seconds']<=config['CPU_bound']['wall_hours']*3600,
            'Original bounded score execution identity differs')
    if cpu_validation:
        require(execution['kind']=='ACTUAL_CPU_FIXTURE_CHILD' and execution['exit_code']==0
                and execution['original_process_ended'] is True and execution['GPU_hidden'] is True,
                'Actual original synthetic CPU child must exit')
        observation=execution['original_observation'];identity=result['original_identity']
        require(execution['original_identity']==identity and observation['original_live'] is False
                and observation['status']=='ORIGINAL_NOT_LIVE'
                and observation['original_pid']==identity['pid']
                and observation['original_start_ticks']==identity['start_ticks']
                and observation['observed_host_view']==identity['host_view'],
                'Original synthetic CPU handle identity differs')
    else:
        state,host=execution['container_state'],execution['host_config']
        require(state['Status']=='exited' and state['ExitCode']==0 and not state['Running']
                and state['Pid']==0 and not state['OOMKilled']
                and host['NanoCpus']==2*10**9 and host['Memory']==host['MemorySwap']==8*1024**3
                and host['CpusetCpus']=='26,27' and host['DeviceRequests'] in (None,[])
                and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True
                and execution['manifest_label_sha256']==manifest_sha256
                and execution['launch_id']==config['launch_id'],'Original bounded score container differs')
    ids=validate_rows(config,result,packet)
    # Keep source rows byte-derived; logical aliases point to the same unique row.
    old=copy.deepcopy(config['reused_rows']);fresh=copy.deepcopy(result['rows'])
    sources={row['id']:row for row in old+fresh}
    require(len(sources)==12+len(ids),'Original and new source row IDs collide')
    return dict(status='ACCEPTED_COMPLETE28_ENDPOINT_SCORES' if config.get('endpoint7') else 'ACCEPTED_COMPLETE24_ENDPOINT_SCORES',CPU_fixture_only=cpu_validation,
        analysis_scope_sha256=config['analysis_scope_sha256'],protocol_sha256=config['protocol_sha256'],
        artifact_packet_sha256=digest(packet),manifest_sha256=manifest_sha256,new_result_sha256=digest(result),
        execution_sha256=digest(execution),formal_logical_positions=len(config['formal_positions']),positions=copy.deepcopy(config['formal_positions']),
        source_rows=sources,new_scored_pairs=len(ids),reused_original_rows=12,
        original_scores_sha256=config['original_scores_sha256'],original_reused_rows_sha256=digest(old),
        independent_new_inputs=False,endpoint_competitive_claim=False,GPU_submissions=0,ledger_written=False)
