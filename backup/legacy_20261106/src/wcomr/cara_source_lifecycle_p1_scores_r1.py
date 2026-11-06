"""Full52 P1 quality positions with sealed internal scores and at most32 new pairs."""
import copy
import json
import math
from pathlib import Path
import re

from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest

ROOT=Path(__file__).resolve().parents[2]
SOURCE='src/wcomr/cara_source_lifecycle_p1_scores_r1.py'
WORKER='scripts/score_cara_source_lifecycle_p1_r1.py'
ARTIFACT_SOURCE='src/wcomr/cara_source_lifecycle_p1_artifacts_r1.py'
PROTOCOL='plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'
SOURCES=(SOURCE,WORKER,ARTIFACT_SOURCE,'src/wcomr/cara_source_lifecycle_p1_inventory_r1.py',
         'src/wcomr/cara_fast_fidelity_r1.py',PROTOCOL)
BOUND=dict(cpus=2,memory_GiB=8,wall_seconds=7200,max_pairs=32)


def pair_key(pair):
    return digest({k:pair[k] for k in ('member','candidate','reference')})


def validate_metric_pair(row,pair,decoded):
    """Unchanged Fidelity reductions, bound to fully decoded original artifacts."""
    if (row['status']!='COMPLETE' or row['member']!=pair['member']
            or row['candidate']!=pair['candidate'] or row['reference']!=pair['reference']
            or row['frames']!=93 or row['temporal_frame_pairs']!=92 or row['PTS_equal'] is not True
            or row['decoded_RGB_sha256']!=[decoded[pair[side]['proof_sha256']]['RGB_sha256'] for side in ('candidate','reference')]):
        raise ValueError('Complete original P1 pair/93-frame/PTS/RGB identity differs')
    alex,ssim=row['Alex_frames'],row['SSIM_frames']
    if (len(alex)!=93 or len(ssim)!=93 or any(type(v) not in (int,float) or not math.isfinite(v) for v in alex+ssim)
            or any(v<0 for v in alex) or row['Alex']!=sum(alex)/93 or row['SSIM']!=sum(ssim)/93
            or row['Alex_worst']!=max(alex) or row['Alex_q95_higher']!=sorted(alex)[math.ceil(.95*92)]
            or row['Alex_first_worst_frame_zero_based']!=alex.index(max(alex))):
        raise ValueError('Full finite93-frame original Fidelity curves/reductions required')
    mse=row['MSE_video']
    if type(mse) not in (int,float) or not math.isfinite(mse) or mse<0:
        raise ValueError('Finite nonnegative original video MSE required')
    if mse==0:
        if row['PSNR_is_infinite'] is not True or row['PSNR_video_dB']!='+inf':
            raise ValueError('Original zero-MSE PSNR identity differs')
    elif (row['PSNR_is_infinite'] is not False or type(row['PSNR_video_dB']) not in (int,float)
            or not math.isclose(row['PSNR_video_dB'],10*math.log10(1/mse),rel_tol=1e-12)):
        raise ValueError('Whole-video original PSNR reduction differs')
    for key in ('reference_temporal_L1','reference_gradient_L1','candidate_gradient_energy','reference_gradient_energy'):
        if type(row[key]) not in (int,float) or not math.isfinite(row[key]) or row[key]<0:
            raise ValueError('Finite original temporal/detail statistics required')
    energy=row['reference_gradient_energy']
    if energy==0:
        if row['gradient_energy_ratio'] is not None or row['gradient_ratio_status']!='ZERO_REFERENCE_ENERGY':
            raise ValueError('Original undefined zero-reference gradient ratio differs')
    elif (row['gradient_ratio_status']!='FINITE' or type(row['gradient_energy_ratio']) not in (int,float)
            or not math.isclose(row['gradient_energy_ratio'],row['candidate_gradient_energy']/energy,rel_tol=1e-12)):
        raise ValueError('Original gradient energy ratio differs')


def bind_post_scorer(packet,environment,*,cpu_validation=False):
    from .cara_source_lifecycle_p1_artifacts_r1 import validate_manifest
    manifest=packet['manifest']
    validate_manifest(manifest,cpu_validation=cpu_validation)
    if (packet['status']!='P1_RELEASED_FULL146_ARTIFACTS_INTERNAL_SCORES_REUSED_PENDING_NEW_PAIRS'
            or packet['CPU_fixture_only'] is not cpu_validation or packet['reader_sha256']!=file_sha(ROOT/ARTIFACT_SOURCE)
            or packet['release']['GPU_released'] is not True or packet['release']['cost_settled'] is not True
            or packet['release']['original_launch_sha256']!=manifest['original_launch_sha256']):
        raise ValueError('Complete original released/settled P1 artifact packet required')
    return dict(schema='CARA_V1_P1_POSTRELEASE_SCORER_R1',manifest=copy.deepcopy(manifest),
        artifact_packet_sha256=digest(packet),source_sha256={n:file_sha(ROOT/n) for n in SOURCES},
        CPU_fixture_only=cpu_validation,CPU_bound=BOUND.copy(),score_shape=([93,64,64,3] if cpu_validation else [93,432,768,3]),
        torch_home=str(environment['torch_home']),piq_site=str(environment['piq_site']),
        weights_sha256=copy.deepcopy(environment['weights_sha256']))


def validate_config(config,*,cpu_validation=False):
    from .cara_source_lifecycle_p1_artifacts_r1 import validate_manifest
    if (config['schema']!='CARA_V1_P1_POSTRELEASE_SCORER_R1' or config['CPU_fixture_only'] is not cpu_validation
            or config['CPU_bound']!=BOUND or config['source_sha256']!={n:file_sha(ROOT/n) for n in SOURCES}
            or config['score_shape']!=([93,64,64,3] if cpu_validation else [93,432,768,3])):
        raise ValueError('Original P1 released scorer source/geometry/CPU boundary differs')
    validate_manifest(config['manifest'],cpu_validation=cpu_validation)
    return [p['id'] for p in config['manifest']['new_pairs']]


def accept_scores(packet,config,result,execution,*,cpu_validation=False):
    expected=bind_post_scorer(packet,{k:config[k] for k in ('torch_home','piq_site','weights_sha256')},cpu_validation=cpu_validation)
    ids=validate_config(config,cpu_validation=cpu_validation)
    if (config!=expected or result['status']!='P1_COMPLETE_NEW_PAIRS_PENDING_INDEPENDENT_ACCEPTANCE'
            or result['config_sha256']!=digest(config) or result['source_sha256']!=config['source_sha256']
            or result['CPU_fixture_only'] is not cpu_validation or result['CUDA_initialized'] is not False
            or result['registered_pairs']!=ids or [r['id'] for r in result['rows']]!=ids
            or execution['config_sha256']!=digest(config) or execution['result_sha256']!=digest(result)
            or execution['original_identity']!=result['original_identity']
            or execution['source_sha256']!=config['source_sha256'] or result['GPU_submissions']!=0
            or execution['original_process_ended'] is not True or execution['exit_code']!=0
            or execution['GPU_hidden'] is not True or not 0<execution['wall_seconds']<=BOUND['wall_seconds']):
        raise ValueError('Complete original once-only released P1 score CPU result/execution required')
    if cpu_validation:
        observed=execution['original_observation'];identity=result['original_identity']
        if (execution['kind']!='ACTUAL_CPU_FIXTURE_CHILD' or observed['original_live'] is not False
                or observed['original_pid']!=identity['pid'] or observed['original_start_ticks']!=identity['start_ticks']
                or observed['observed_host_view']!=identity['host_view']):
            raise ValueError('Original bounded synthetic post-score CPU child must have ended')
    if not cpu_validation:
        state,host=execution['container_state'],execution['host_config']
        if (state['Status']!='exited' or state['Pid']!=state['ExitCode'] or state['Pid']!=0
                or any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
                or host['NanoCpus']!=2*10**9 or host['Memory']!=host['MemorySwap'] or host['Memory']!=8*2**30
                or host['CpusetCpus']!='26,27' or host['DeviceRequests'] not in (None,[])
                or host['NetworkMode']!='none' or host['ReadonlyRootfs'] is not True):
            raise ValueError('Original released2CPU/8GiB/GPU-hidden score container required')
    metrics={k:copy.deepcopy(v['metrics']) for k,v in packet['manifest']['internal_rows'].items()}
    for pair,row in zip(config['manifest']['new_pairs'],result['rows']):
        validate_metric_pair(row,pair,packet['decoded'])
        key=pair_key(pair)
        if key in metrics:
            raise ValueError('A sealed internal P1 score must never be recomputed')
        metrics[key]=copy.deepcopy(row)
    rows=[]
    for position in packet['manifest']['quality_positions']:
        key=position['pair_key']
        if key not in metrics:
            raise ValueError('Complete52 logical quality denominator required')
        validate_metric_pair(metrics[key],position,packet['decoded'])
        rows.append(dict(**copy.deepcopy(position),metrics=copy.deepcopy(metrics[key]),
                         metric_source='SEALED_INTERNAL' if key in packet['manifest']['internal_rows'] else 'ORIGINAL_NEW_POSTRELEASE'))
    return dict(status='P1_COMPLETE52_QUALITY_POSITIONS_ACCEPTED_PENDING_ANALYSIS_FREEZE',CPU_fixture_only=cpu_validation,
        run_id=packet['manifest']['run_id'],launch_id=packet['manifest']['launch_id'],scope_sha256=packet['manifest']['scope_sha256'],
        original_artifact_packet_sha256=digest(packet),config_sha256=digest(config),result_sha256=digest(result),
        execution_sha256=digest(execution),logical_quality_positions=52,new_scored_pairs=len(ids),
        reused_internal_unique_pairs=len(packet['manifest']['internal_rows']),internal_scores_recomputed=0,
        rows=rows,independent_new_inputs=False,scientific_method_established=False,
        GPU_submissions=0,ledger_written=False)
