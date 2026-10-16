"""Recompute complete same-state action outputs and preserve all price trials."""
import math
from statistics import mean,median

import torch

from .action_price16_collection_r1 import ACTIONS,ROUNDS
from .cfg_guided_w1_deployment import alpha_at
from .mid_coverage import tree_digest
from .post_probe_action_clock_r1 import BOUNDARY
from .cfg_paired_probe_forward import PaidProbe


def audit_scene(records,loader,*,expected_shape):
    if set(records)!={'AUDIT','LEAN'} or any(len(rows)!=4 for rows in records.values()):
        raise ValueError('All four source/phase cells in both complete modes required')
    cells={(source,phase) for source in ('D','P') for phase in ('EARLY','LATE')}
    output={};summaries=[];raw_files=0
    for mode,rows in records.items():
        if {(r['point']['source'],r['point']['phase']) for r in rows}!=cells:
            raise ValueError('Every actual source/phase cell must survive')
        for row in rows:
            p=row['point'];step=p['chosen']['step'];key=(p['source'],p['phase'])
            if (row['observation_mode']!=mode or len(row['restores'])!=16
                    or row['new_prices_used_in_parent'] or row['offline_trial_committed_to_parent']
                    or not row['each_trial_pays_two_real_probes_outside_incremental_clock']
                    or row['online_teacher_or_clean_latency_claim']
                    or p['phase']!=('EARLY' if step<25 else 'LATE')
                    or step-p['chosen']['source_birth']!=p['chosen']['age']):
                raise ValueError('Exact frozen state, full restoration and offline-only boundary required')
            payload=loader(row['artifact']);raw_files+=1
            names={a+'_'+b for a in ACTIONS for b in ('conditional','unconditional')}|{'actual_latent','timestep'}
            if set(payload)!=names or tree_digest(payload)!=row['artifact']['tensor_sha256']:
                raise ValueError('Original complete ten-tensor artifact identity required')
            if any(not isinstance(v,torch.Tensor) or not bool(torch.isfinite(v).all()) for v in payload.values()):
                raise ValueError('All original finite tensor contents required')
            for name,value in payload.items():
                if name!='timestep' and (value.dtype!=torch.float32 or list(value.shape)!=list(expected_shape)):
                    raise ValueError('Actual branch/latent FP32 geometry differs')
            plan=[(r,a) for r,order in ROUNDS for a in order]
            if [(r['round'],r['action']) for r in row['trials']]!=plan:
                raise ValueError('One complete warmup and all three formal orders required')
            packets=None;by_action={a:[] for a in ACTIONS};digests={}
            for trial in row['trials']:
                action=trial['action'];interval=trial['interval']
                pair=(payload[action+'_conditional'],payload[action+'_unconditional'])
                if (trial['observation_mode']!=mode or trial['heads_observed'] is not (mode=='AUDIT')
                        or trial['output_tree_sha256']!=tree_digest(pair)
                        or trial['actual_action']!=('P' if action=='P0' else 'C' if action=='A' else action)*2
                        or interval['status']!='PASS' or interval['boundary']!=BOUNDARY
                        or interval['selection_and_normal_commit_included'] is not True
                        or any(interval[k] for k in ('shared_probe_seconds_included',
                            'snapshot_restore_tensor_hash_or_write_included','complete_pair_or_clean_video_latency'))
                        or not math.isfinite(interval['synchronized_wall_seconds'])
                        or interval['synchronized_wall_seconds']<=0):
                    raise ValueError('Original mode, repeated output or paid-boundary interval differs')
                heads=(4 if p['source']=='D' else 6) if action=='A' else 2
                if trial['actual_heads']!=(heads if mode=='AUDIT' else None):
                    raise ValueError('Retain observed audit heads and explicit unavailable lean heads')
                if packets is None:packets=interval['paid_packets']
                if interval['paid_packets']!=packets:raise ValueError('Same-state paid prefix differs')
                try:paid=[PaidProbe(**v) for v in packets]
                except (TypeError,ValueError):raise ValueError('Complete original paid probe fields required')
                if (len(paid)!=2 or [p.slot for p in paid]!=[0,1]
                        or [p.counter for p in paid]!=[2*(step-1)%70,2*(step-1)%70+1]
                        or any(type(p.native_cache) is not bool or any(not math.isfinite(v)
                            for v in (p.delta_x,p.delta_y,p.dynamic_threshold)) for p in paid)):
                    raise ValueError('Actual same-step finite CFG paid prefixes required')
                if action=='A' and trial['A_readout']['shared_alpha']!=alpha_at('BETA1_ONE_PHASE',step):
                    raise ValueError('The original shared-stage A readout changed')
                digests[action]=trial['output_tree_sha256']
                if trial['round']!='WARMUP':by_action[action].append(interval['synchronized_wall_seconds'])
            dense=payload['D_conditional']+7*(payload['D_conditional']-payload['D_unconditional'])
            errors={}
            for action in ACTIONS:
                guided=payload[action+'_conditional']+7*(payload[action+'_conditional']-payload[action+'_unconditional'])
                errors[action]=float((guided.double()-dense.double()).square().mean())
            output[(mode,key)]=dict(output_digests=digests,packets=packets,input_sha256=row['input_sha256'])
            summaries.append(dict(scene=p['scene'],source=p['source'],phase=p['phase'],step=step,mode=mode,
                formal_seconds={a:dict(all_three=by_action[a],mean=mean(by_action[a]),median=median(by_action[a]),
                    minimum=min(by_action[a]),maximum=max(by_action[a])) for a in ACTIONS},
                absolute_same_state_guided_MSE=errors,
                MSE_is_not_video_quality=True,price_is_incremental_not_clean_latency=True))
    for key in cells:
        if output[('AUDIT',key)]!=output[('LEAN',key)]:
            raise ValueError('Audit and lean must return all same outputs from the same paid state')
    return dict(status='ACTION16_ALL_FOUR_CELLS_TWO_MODES_RAW_RECONSTRUCTED',raw_files=raw_files,
        raw_tensors=raw_files*10,retained_trial_intervals=128,formal_trial_intervals=96,
        all_audit_lean_outputs_and_prefixes_equal=True,observations=summaries,
        frozen_parameters_updated=False,new_quality_or_clean_speed_claim=False)
